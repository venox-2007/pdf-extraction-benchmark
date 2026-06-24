"""Run the FINAL FUNSD benchmark on the curated 20-document corpus.

Orchestrates all five extractors (PyMuPDF, OpenDataLoader, Tesseract,
PaddleOCR, Docling) over `data/final_benchmark/funsd/` and scores each one
against ground truth using the existing FUNSD CER/WER/Token-F1 metrics
(`pdf_extraction_benchmark.benchmarks.funsd.metrics`, unmodified). This script
is purely an orchestration layer — it does not alter any extractor, metric,
or scoring logic; it only runs the existing PaddleOCR-only methodology across
all five tools.

Extractors are run strictly sequentially in the order PyMuPDF -> OpenDataLoader
-> Tesseract -> PaddleOCR -> Docling, one fully completing across all 20 docs
before the next starts, so PaddleOCR and Docling are never loaded together.
"""

from __future__ import annotations

import csv
import json
import re
import time
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean, median, pstdev

# Preload torch's DLLs before paddle is ever imported (via the PaddleOCR
# extractor) to avoid the WinError127/shm.dll conflict observed when paddle
# loads first on Windows. Mirrors the existing fix in ui/app.py and the
# import-order guard already present in docling/extractor.py.
import torch  # noqa: F401,E402

_TORCH_PRELOADED = True  # forces a statement boundary so ruff keeps this import block separate

import fitz  # noqa: E402

from pdf_extraction_benchmark.benchmarks.funsd.metrics import (  # noqa: E402
    character_error_rate,
    token_f1,
    tokenize,
    word_error_rate,
)
from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.opendataloader.extractor import (  # noqa: E402
    OpendataloaderExtractor,
)
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.tesseract.extractor import TesseractExtractor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "data" / "final_benchmark" / "funsd"
OUT_DIR = ROOT / "outputs" / "benchmark_results" / "final_60" / "funsd"
ARTIFACTS_DIR = OUT_DIR / "extraction_artifacts"

# These two extractors only accept PDF input at the source-code level; images
# are wrapped into a single-page PDF via fitz before extraction (same
# approach already used by the Streamlit UI and the PAN qualitative script).
PDF_ONLY_EXTRACTORS = frozenset({"PyMuPDF", "OpenDataLoader"})

EXTRACTOR_ORDER = ["PyMuPDF", "OpenDataLoader", "Tesseract", "PaddleOCR", "Docling"]


def _normalize_text(text: str) -> str:
    """Identical normalization used by FunsdBenchmarkPipeline.normalize_text."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_ground_truth_text(annotation_path: Path) -> str:
    """Identical logic to FunsdBenchmarkPipeline._extract_ground_truth_text."""
    with annotation_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    segments: list[str] = []
    for entry in data.get("form", []):
        entry_text = _normalize_text(str(entry.get("text", "")))
        if not entry_text:
            entry_text = _normalize_text(
                " ".join(
                    word.get("text", "")
                    for word in entry.get("words", [])
                    if word.get("text", "")
                )
            )
        if entry_text:
            segments.append(entry_text)
    return "\n".join(segments)


def _collect_documents() -> list[tuple[str, Path, Path]]:
    images = sorted(CORPUS_DIR.glob("*.png"))
    documents: list[tuple[str, Path, Path]] = []
    for image_path in images:
        annotation_path = CORPUS_DIR / f"{image_path.stem}.json"
        if annotation_path.exists():
            documents.append((image_path.stem, image_path, annotation_path))
    if not documents:
        raise FileNotFoundError(f"No matching FUNSD image/annotation pairs found in {CORPUS_DIR}")
    return documents


def _image_to_temp_pdf(image_path: Path, tmp_dir: Path) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pdf_bytes = fitz.open(str(image_path)).convert_to_pdf()
    tmp_path = tmp_dir / f"{image_path.stem}.pdf"
    tmp_path.write_bytes(pdf_bytes)
    return tmp_path


@dataclass(slots=True)
class DocResult:
    """Per-document, per-extractor benchmark result."""

    document_id: str
    extractor: str
    status: str
    latency_ms: float
    word_count: int
    char_count: int
    markdown_length: int
    cer: float
    wer: float
    token_f1: float
    error: str | None = None


@dataclass(slots=True)
class MetricStats:
    mean: float
    median: float
    minimum: float
    maximum: float
    stddev: float


def _stats(values: list[float]) -> MetricStats:
    if not values:
        return MetricStats(0.0, 0.0, 0.0, 0.0, 0.0)
    stddev = pstdev(values) if len(values) > 1 else 0.0
    return MetricStats(
        mean=round(mean(values), 6),
        median=round(median(values), 6),
        minimum=round(min(values), 6),
        maximum=round(max(values), 6),
        stddev=round(stddev, 6),
    )


@dataclass(slots=True)
class ExtractorSummary:
    extractor: str
    documents_evaluated: int
    documents_ok: int
    documents_failed: int
    success_rate: float
    total_runtime_s: float
    average_latency_ms: float
    average_word_count: float
    average_markdown_length: float
    average_cer: float
    average_wer: float
    average_token_f1: float
    latency_ms_stats: MetricStats = field(default_factory=lambda: MetricStats(0, 0, 0, 0, 0))
    cer_stats: MetricStats = field(default_factory=lambda: MetricStats(0, 0, 0, 0, 0))
    wer_stats: MetricStats = field(default_factory=lambda: MetricStats(0, 0, 0, 0, 0))
    token_f1_stats: MetricStats = field(default_factory=lambda: MetricStats(0, 0, 0, 0, 0))


def _make_extractor(name: str):
    if name == "PyMuPDF":
        return PymupdfExtractor()
    if name == "OpenDataLoader":
        return OpendataloaderExtractor()
    if name == "Tesseract":
        return TesseractExtractor()
    if name == "PaddleOCR":
        return PaddleocrExtractor()
    if name == "Docling":
        return DoclingExtractor(output_root=ROOT)
    raise ValueError(f"Unknown extractor: {name}")


def _run_extractor(
    name: str,
    documents: list[tuple[str, Path, Path]],
    ground_truths: dict[str, str],
) -> tuple[list[DocResult], float]:
    print(f"\n=== {name} ===", flush=True)
    extractor = _make_extractor(name)
    tmp_pdf_dir = ARTIFACTS_DIR / name / "_wrapped_pdfs"
    artifacts_out = ARTIFACTS_DIR / name

    results: list[DocResult] = []
    runtime_start = time.perf_counter()
    for document_id, image_path, _annotation_path in documents:
        ground_truth_text = ground_truths[document_id]
        start = time.perf_counter()
        try:
            if name in PDF_ONLY_EXTRACTORS:
                input_path = _image_to_temp_pdf(image_path, tmp_pdf_dir)
                extract_kwargs: dict[str, object] = {}
                if name == "OpenDataLoader":
                    doc_out = artifacts_out / document_id
                    doc_out.mkdir(parents=True, exist_ok=True)
                    extract_kwargs["output_dir"] = doc_out
                page_results = extractor.extract(input_path, **extract_kwargs)
            else:
                page_results = extractor.extract(image_path)

            latency_ms = (time.perf_counter() - start) * 1000
            combined_text = "\n".join(
                r.extracted_text for r in page_results if r.extracted_text
            )
            normalized_prediction = _normalize_text(combined_text)
            word_count = len(normalized_prediction.split())
            char_count = len(normalized_prediction)

            markdown_length = 0
            if name == "Docling" and page_results and page_results[0].metadata:
                markdown_length = int(
                    page_results[0].metadata.extra.get("document_markdown_length", 0)
                )
            elif name == "OpenDataLoader":
                md_file = artifacts_out / document_id / f"{input_path.stem}.md"
                if md_file.exists():
                    markdown_length = len(md_file.read_text(encoding="utf-8", errors="ignore"))

            cer = character_error_rate(ground_truth_text, normalized_prediction)
            wer = word_error_rate(ground_truth_text, normalized_prediction)
            f1 = token_f1(tokenize(ground_truth_text), tokenize(normalized_prediction))

            results.append(
                DocResult(
                    document_id=document_id,
                    extractor=name,
                    status="ok",
                    latency_ms=round(latency_ms, 3),
                    word_count=word_count,
                    char_count=char_count,
                    markdown_length=markdown_length,
                    cer=round(cer, 6),
                    wer=round(wer, 6),
                    token_f1=round(f1, 6),
                )
            )
            print(f"  {document_id}: ok (cer={cer:.3f} wer={wer:.3f} f1={f1:.3f})", flush=True)
        except Exception as exc:  # noqa: BLE001 - continue across remaining docs
            latency_ms = (time.perf_counter() - start) * 1000
            results.append(
                DocResult(
                    document_id=document_id,
                    extractor=name,
                    status="error",
                    latency_ms=round(latency_ms, 3),
                    word_count=0,
                    char_count=0,
                    markdown_length=0,
                    cer=0.0,
                    wer=0.0,
                    token_f1=0.0,
                    error=str(exc),
                )
            )
            print(f"  {document_id}: ERROR: {exc}", flush=True)
            traceback.print_exc()

    total_runtime_s = time.perf_counter() - runtime_start
    return results, total_runtime_s


def _build_extractor_summary(
    name: str,
    results: list[DocResult],
    total_runtime_s: float,
) -> ExtractorSummary:
    ok_results = [r for r in results if r.status == "ok"]
    failed_results = [r for r in results if r.status != "ok"]
    evaluated = len(results)
    success_rate = round(len(ok_results) / evaluated, 6) if evaluated else 0.0

    latencies = [r.latency_ms for r in results]
    word_counts = [r.word_count for r in ok_results]
    markdown_lengths = [r.markdown_length for r in ok_results]
    cers = [r.cer for r in ok_results]
    wers = [r.wer for r in ok_results]
    f1s = [r.token_f1 for r in ok_results]

    return ExtractorSummary(
        extractor=name,
        documents_evaluated=evaluated,
        documents_ok=len(ok_results),
        documents_failed=len(failed_results),
        success_rate=success_rate,
        total_runtime_s=round(total_runtime_s, 3),
        average_latency_ms=round(mean(latencies), 3) if latencies else 0.0,
        average_word_count=round(mean(word_counts), 3) if word_counts else 0.0,
        average_markdown_length=round(mean(markdown_lengths), 3) if markdown_lengths else 0.0,
        average_cer=round(mean(cers), 6) if cers else 0.0,
        average_wer=round(mean(wers), 6) if wers else 0.0,
        average_token_f1=round(mean(f1s), 6) if f1s else 0.0,
        latency_ms_stats=_stats(latencies),
        cer_stats=_stats(cers),
        wer_stats=_stats(wers),
        token_f1_stats=_stats(f1s),
    )


def _write_csv(all_results: list[DocResult]) -> Path:
    csv_path = OUT_DIR / "funsd_summary.csv"
    fieldnames = list(asdict(all_results[0]).keys()) if all_results else []
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in all_results:
            writer.writerow(asdict(result))
    return csv_path


def _write_json(
    all_results: list[DocResult],
    extractor_summaries: dict[str, ExtractorSummary],
    total_runtime_s: float,
) -> Path:
    json_path = OUT_DIR / "funsd_summary.json"
    payload = {
        "dataset_dir": str(CORPUS_DIR),
        "output_dir": str(OUT_DIR),
        "total_documents": len({r.document_id for r in all_results}),
        "extractor_order": EXTRACTOR_ORDER,
        "total_runtime_s": round(total_runtime_s, 3),
        "extractor_summaries": {
            name: asdict(summary) for name, summary in extractor_summaries.items()
        },
        "documents": [asdict(result) for result in all_results],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return json_path


def _write_observations(
    extractor_summaries: dict[str, ExtractorSummary],
    total_runtime_s: float,
) -> Path:
    md_path = OUT_DIR / "benchmark_observations.md"
    lines = [
        "# Final FUNSD Benchmark — Curated 20-Document Corpus",
        "",
        "Dataset: `data/final_benchmark/funsd/` (20 documents)",
        f"Extractor order: {' -> '.join(EXTRACTOR_ORDER)}",
        f"Total runtime: {total_runtime_s:.1f}s",
        "",
        "| Extractor | Success | CER | WER | Token F1 | Avg latency (ms) "
        "| Avg words | Avg markdown len |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for name in EXTRACTOR_ORDER:
        s = extractor_summaries.get(name)
        if s is None:
            continue
        lines.append(
            f"| {name} | {s.documents_ok}/{s.documents_evaluated} | {s.average_cer:.4f} "
            f"| {s.average_wer:.4f} | {s.average_token_f1:.4f} | {s.average_latency_ms:.1f} "
            f"| {s.average_word_count:.1f} | {s.average_markdown_length:.1f} |"
        )
    lines.append("")
    lines.append("## Per-extractor runtime")
    lines.append("")
    for name in EXTRACTOR_ORDER:
        s = extractor_summaries.get(name)
        if s is None:
            continue
        lines.append(f"- **{name}**: {s.total_runtime_s:.1f}s total, {s.documents_failed} failed")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    documents = _collect_documents()
    print(f"Collected {len(documents)} documents from {CORPUS_DIR}")

    ground_truths = {
        document_id: _normalize_text(_extract_ground_truth_text(annotation_path))
        for document_id, _image_path, annotation_path in documents
    }

    all_results: list[DocResult] = []
    extractor_summaries: dict[str, ExtractorSummary] = {}
    overall_start = time.perf_counter()

    for extractor_name in EXTRACTOR_ORDER:
        results, runtime_s = _run_extractor(extractor_name, documents, ground_truths)
        all_results.extend(results)
        extractor_summaries[extractor_name] = _build_extractor_summary(
            extractor_name, results, runtime_s
        )

    overall_runtime_s = time.perf_counter() - overall_start

    csv_path = _write_csv(all_results)
    json_path = _write_json(all_results, extractor_summaries, overall_runtime_s)
    md_path = _write_observations(extractor_summaries, overall_runtime_s)

    print(f"\nWrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"\nOverall runtime: {overall_runtime_s:.1f}s")
    for name in EXTRACTOR_ORDER:
        s = extractor_summaries[name]
        print(f"  {name}: {s.total_runtime_s:.1f}s ({s.documents_ok}/{s.documents_evaluated} ok)")


if __name__ == "__main__":
    main()
