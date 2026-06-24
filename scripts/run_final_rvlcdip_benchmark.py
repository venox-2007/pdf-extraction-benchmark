"""Run the FINAL RVL-CDIP benchmark on the curated 20-document corpus.

Orchestrates all five extractors (PyMuPDF, OpenDataLoader, Tesseract,
PaddleOCR, Docling) over the flat 20-file corpus at
`data/final_benchmark/rvl_cdip/` (10 categories x 2 documents each, embedded
in the filename, e.g. `advertisement_01.tif`).

This script does not alter any extractor or benchmark logic. It reuses the
existing `RvlCdipBenchmarkPipeline._evaluate_document` method (latency
timing, word/char/bbox counting, ok/error status) unmodified, and the
existing `RvlCdipExtractorSummary` / `RvlCdipCategorySummary` /
`RvlCdipBenchmarkSummary` dataclasses plus the `_statistics_for` aggregation
helper, also unmodified.

`RvlCdipBenchmarkPipeline._collect_documents` expects category subdirectories
of `*.pdf` files, which does not match this corpus's flat `*.tif` layout, so
document collection here is custom; everything downstream of "for this
document, run this extractor and record latency/word/char/bbox counts" is
the original, unmodified pipeline code.

Extractors run strictly sequentially in the order PyMuPDF -> OpenDataLoader
-> Tesseract -> PaddleOCR -> Docling. Each extractor is fully instantiated,
run across all 20 documents, and discarded before the next one is
constructed, so PaddleOCR and Docling are never held in memory together.
"""

from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import asdict
from pathlib import Path
from statistics import mean

# Preload torch's DLLs before paddle is ever imported (via the PaddleOCR
# extractor) to avoid the WinError127/shm.dll conflict observed when paddle
# loads first on Windows. Mirrors the existing fix in ui/app.py and
# scripts/run_rvlcdip_benchmark_full.py.
import torch  # noqa: F401,E402

_TORCH_PRELOADED = True  # forces a statement boundary so ruff keeps this import block separate

import fitz  # noqa: E402

from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import (  # noqa: E402
    RvlCdipBenchmarkPipeline,
    RvlCdipBenchmarkSummary,
    RvlCdipCategorySummary,
    RvlCdipDocumentResult,
    RvlCdipExtractorSummary,
    _statistics_for,
)
from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.opendataloader.extractor import (  # noqa: E402
    OpendataloaderExtractor,
)
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.tesseract.extractor import TesseractExtractor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "data" / "final_benchmark" / "rvl_cdip"
OUT_DIR = ROOT / "outputs" / "benchmark_results" / "final_60" / "rvl_cdip"
ARTIFACTS_DIR = OUT_DIR / "extraction_artifacts"

# These two extractors only accept PDF input at the source-code level; the
# corpus's .tif images are wrapped into a single-page PDF via fitz before
# extraction (same approach used by the final FUNSD script and the UI).
PDF_ONLY_EXTRACTORS = frozenset({"PyMuPDF", "OpenDataLoader"})

EXTRACTOR_ORDER = ["PyMuPDF", "OpenDataLoader", "Tesseract", "PaddleOCR", "Docling"]

_CATEGORY_SUFFIX_RE = re.compile(r"_\d+$")


def _category_from_stem(stem: str) -> str:
    return _CATEGORY_SUFFIX_RE.sub("", stem)


def _collect_documents() -> list[tuple[str, str, Path]]:
    """Return (category, document_id, image_path) tuples sorted by filename."""
    images = sorted(CORPUS_DIR.glob("*.tif"))
    if not images:
        raise FileNotFoundError(f"No .tif documents found in {CORPUS_DIR}")
    return [(_category_from_stem(p.stem), p.stem, p) for p in images]


def _image_to_temp_pdf(image_path: Path, tmp_dir: Path) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pdf_bytes = fitz.open(str(image_path)).convert_to_pdf()
    tmp_path = tmp_dir / f"{image_path.stem}.pdf"
    tmp_path.write_bytes(pdf_bytes)
    return tmp_path


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
    documents: list[tuple[str, str, Path]],
) -> tuple[list[RvlCdipDocumentResult], float]:
    """Run one extractor across all documents using the unmodified
    RvlCdipBenchmarkPipeline._evaluate_document method."""
    print(f"\n=== {name} ===", flush=True)
    extractor = _make_extractor(name)
    # A throwaway single-extractor pipeline instance: only used so we can call
    # the existing, unmodified `_evaluate_document` method, which needs
    # `self.output_dir` for extractors whose `extract()` accepts an
    # `output_dir` kwarg (OpenDataLoader).
    pipeline = RvlCdipBenchmarkPipeline(
        dataset_dir=CORPUS_DIR,
        output_dir=ARTIFACTS_DIR / name,
        extractors={name: extractor},
    )
    tmp_pdf_dir = ARTIFACTS_DIR / name / "_wrapped_pdfs"

    results: list[RvlCdipDocumentResult] = []
    runtime_start = time.perf_counter()
    for category, document_id, image_path in documents:
        if name in PDF_ONLY_EXTRACTORS:
            input_path = _image_to_temp_pdf(image_path, tmp_pdf_dir)
        else:
            input_path = image_path
        result = pipeline._evaluate_document(category, input_path, name, extractor)
        # _evaluate_document uses pdf_path.stem for document_id, which matches
        # the wrapped-PDF stem (identical to the original image stem) for
        # PyMuPDF/OpenDataLoader, so document_id stays correct either way.
        results.append(result)
        status_line = (
            f"  {document_id} [{category}]: ok (words={result.word_count}, "
            f"latency={result.latency_ms:.1f}ms)"
            if result.status == "ok"
            else f"  {document_id} [{category}]: ERROR: {result.error}"
        )
        print(status_line, flush=True)

    total_runtime_s = time.perf_counter() - runtime_start
    return results, total_runtime_s


def _build_summary(
    documents: list[tuple[str, str, Path]],
    all_results: list[RvlCdipDocumentResult],
) -> RvlCdipBenchmarkSummary:
    categories = sorted({category for category, _doc_id, _path in documents})

    extractor_summaries: dict[str, RvlCdipExtractorSummary] = {}
    for extractor_name in EXTRACTOR_ORDER:
        extractor_results = [r for r in all_results if r.extractor == extractor_name]
        ok_results = [r for r in extractor_results if r.status == "ok"]
        failed_results = [r for r in extractor_results if r.status != "ok"]
        evaluated = len(extractor_results)
        extractor_summaries[extractor_name] = RvlCdipExtractorSummary(
            extractor=extractor_name,
            documents_evaluated=evaluated,
            documents_ok=len(ok_results),
            documents_failed=len(failed_results),
            success_rate=round(len(ok_results) / evaluated, 6) if evaluated else 0.0,
            latency_ms=_statistics_for([r.latency_ms for r in extractor_results]),
            word_count=_statistics_for([r.word_count for r in ok_results]),
            char_count=_statistics_for([r.char_count for r in ok_results]),
            bbox_count=_statistics_for([r.layout_region_count for r in ok_results]),
        )

    category_summaries: dict[str, RvlCdipCategorySummary] = {}
    for category in categories:
        category_results = [r for r in all_results if r.category == category]
        category_doc_count = len({r.document_id for r in category_results})
        success_rate: dict[str, float] = {}
        word_count: dict[str, float] = {}
        for extractor_name in EXTRACTOR_ORDER:
            extractor_results = [r for r in category_results if r.extractor == extractor_name]
            ok_count = sum(1 for r in extractor_results if r.status == "ok")
            success_rate[extractor_name] = (
                round(ok_count / len(extractor_results), 6) if extractor_results else 0.0
            )
            ok_results = [r for r in extractor_results if r.status == "ok"]
            word_count[extractor_name] = (
                round(mean(r.word_count for r in ok_results), 6) if ok_results else 0.0
            )
        category_summaries[category] = RvlCdipCategorySummary(
            category=category,
            documents=category_doc_count,
            extractor_success_rate=success_rate,
            extractor_word_count=word_count,
        )

    return RvlCdipBenchmarkSummary(
        dataset_dir=str(CORPUS_DIR),
        output_dir=str(OUT_DIR),
        categories=categories,
        total_documents=len(documents),
        extractor_summaries=extractor_summaries,
        category_summaries=category_summaries,
        documents=all_results,
    )


def _extractor_table(summaries: dict[str, RvlCdipExtractorSummary]) -> str:
    rows = [
        "| Extractor | Evaluated | OK | Failed | Success Rate | Mean Latency (ms) | "
        "Mean Char Count | Mean Word Count | Mean BBox Count |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in EXTRACTOR_ORDER:
        s = summaries.get(name)
        if s is None:
            continue
        rows.append(
            f"| {s.extractor} | {s.documents_evaluated} | {s.documents_ok} | "
            f"{s.documents_failed} | {s.success_rate:.4f} | {s.latency_ms.mean:.2f} | "
            f"{s.char_count.mean:.2f} | {s.word_count.mean:.2f} | {s.bbox_count.mean:.2f} |"
        )
    return "\n".join(rows)


def _category_table(
    summaries: dict[str, RvlCdipCategorySummary],
    extractor_names: list[str],
) -> str:
    header = "| Category | Documents | " + " | ".join(extractor_names) + " |"
    separator = "| --- | ---: | " + " | ".join(["---:"] * len(extractor_names)) + " |"
    rows = [header, separator]
    for category in sorted(summaries):
        s = summaries[category]
        rates = " | ".join(
            f"{s.extractor_success_rate.get(name, 0.0):.2f}" for name in extractor_names
        )
        rows.append(f"| {s.category} | {s.documents} | {rates} |")
    return "\n".join(rows)


def _write_outputs(summary: RvlCdipBenchmarkSummary, total_runtime_s: float) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUT_DIR / "rvl_cdip_summary.csv"
    fieldnames = list(asdict(summary.documents[0]).keys()) if summary.documents else []
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in summary.documents:
            writer.writerow(asdict(result))

    json_path = OUT_DIR / "rvl_cdip_summary.json"
    payload = asdict(summary)
    payload["extractor_order"] = EXTRACTOR_ORDER
    payload["total_runtime_s"] = round(total_runtime_s, 3)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_path = OUT_DIR / "benchmark_observations.md"
    lines = [
        "# Final RVL-CDIP Benchmark — Curated 20-Document Corpus",
        "",
        f"- Dataset directory: `{summary.dataset_dir}`",
        f"- Categories: {len(summary.categories)}",
        f"- Total documents: {summary.total_documents}",
        f"- Extractor order: {' -> '.join(EXTRACTOR_ORDER)}",
        f"- Total runtime: {total_runtime_s:.1f}s",
        "",
        "## Extractor Robustness",
        "",
        _extractor_table(summary.extractor_summaries),
        "",
        "## Per-Category Success Rate",
        "",
        _category_table(summary.category_summaries, EXTRACTOR_ORDER),
        "",
        "## Notes",
        "",
        "- RVL-CDIP provides category labels, not text-level ground truth, so "
        "this benchmark reports extraction robustness (success rate, latency, "
        "output volume, bbox/layout count) rather than CER/WER-style accuracy, "
        "identical to the existing RVL-CDIP benchmark methodology.",
        "- OpenDataLoader runs in its default Java-only mode (no hybrid OCR "
        "backend); scanned/image-only pages may yield zero/low word counts "
        "without indicating a failure.",
        "- PyMuPDF and OpenDataLoader require PDF input; each `.tif` document "
        "is wrapped into a single-page PDF via fitz before extraction.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nWrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    documents = _collect_documents()
    print(f"Collected {len(documents)} documents from {CORPUS_DIR}")

    all_results: list[RvlCdipDocumentResult] = []
    runtimes: dict[str, float] = {}
    overall_start = time.perf_counter()

    for extractor_name in EXTRACTOR_ORDER:
        results, runtime_s = _run_extractor(extractor_name, documents)
        all_results.extend(results)
        runtimes[extractor_name] = runtime_s

    overall_runtime_s = time.perf_counter() - overall_start

    summary = _build_summary(documents, all_results)
    _write_outputs(summary, overall_runtime_s)

    print(f"\nOverall runtime: {overall_runtime_s:.1f}s")
    for name in EXTRACTOR_ORDER:
        s = summary.extractor_summaries[name]
        print(
            f"  {name}: {runtimes[name]:.1f}s total "
            f"({s.documents_ok}/{s.documents_evaluated} ok)"
        )


if __name__ == "__main__":
    main()
