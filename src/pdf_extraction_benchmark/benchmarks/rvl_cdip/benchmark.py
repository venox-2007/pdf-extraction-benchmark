"""RVL-CDIP category-based extraction robustness benchmark."""

from __future__ import annotations

import csv
import inspect
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean, median, pstdev

from pdf_extraction_benchmark.benchmarks.funsd.benchmark import MetricStatistics
from pdf_extraction_benchmark.extractors.opendataloader.extractor import OpendataloaderExtractor
from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor
from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor

DEFAULT_EXTRACTORS: dict[str, type[BaseExtractor]] = {
    "PyMuPDF": PymupdfExtractor,
    "OpenDataLoader": OpendataloaderExtractor,
}


@dataclass(slots=True)
class RvlCdipDocumentResult:
    """Per-document, per-extractor extraction result."""

    category: str
    document_id: str
    pdf_path: str
    extractor: str
    status: str
    page_count: int
    word_count: int
    char_count: int
    layout_region_count: int
    latency_ms: float
    error: str | None = None


@dataclass(slots=True)
class RvlCdipExtractorSummary:
    """Aggregate robustness metrics for one extractor across all documents."""

    extractor: str
    documents_evaluated: int
    documents_ok: int
    documents_failed: int
    success_rate: float
    latency_ms: MetricStatistics
    word_count: MetricStatistics
    char_count: MetricStatistics
    bbox_count: MetricStatistics


@dataclass(slots=True)
class RvlCdipCategorySummary:
    """Per-category success rate and mean word count, by extractor."""

    category: str
    documents: int
    extractor_success_rate: dict[str, float] = field(default_factory=dict)
    extractor_word_count: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class RvlCdipBenchmarkSummary:
    """Aggregate benchmark summary for the RVL-CDIP subset."""

    dataset_dir: str
    output_dir: str
    categories: list[str] = field(default_factory=list)
    total_documents: int = 0
    extractor_summaries: dict[str, RvlCdipExtractorSummary] = field(default_factory=dict)
    category_summaries: dict[str, RvlCdipCategorySummary] = field(default_factory=dict)
    documents: list[RvlCdipDocumentResult] = field(default_factory=list)


def _statistics_for(values: list[float]) -> MetricStatistics:
    if not values:
        return MetricStatistics(0.0, 0.0, 0.0, 0.0, 0.0)
    stddev = pstdev(values) if len(values) > 1 else 0.0
    return MetricStatistics(
        mean=round(mean(values), 6),
        median=round(median(values), 6),
        minimum=round(min(values), 6),
        maximum=round(max(values), 6),
        stddev=round(stddev, 6),
    )


class RvlCdipBenchmarkPipeline:
    """Run registered extractors over the RVL-CDIP category subset.

    Unlike the FUNSD pipeline, RVL-CDIP carries no per-document text ground
    truth, so this benchmark focuses on cross-category extraction robustness
    (success rate, latency, and output volume per extractor) rather than
    CER/WER-style accuracy scoring.
    """

    def __init__(
        self,
        dataset_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
        extractors: dict[str, BaseExtractor] | None = None,
    ) -> None:
        self.project_root = Path(__file__).resolve().parents[4]
        self.dataset_dir = (
            Path(dataset_dir)
            if dataset_dir is not None
            else self.project_root / "data" / "raw" / "rvl_cdip"
        )
        self.output_dir = (
            Path(output_dir)
            if output_dir is not None
            else self.project_root / "outputs" / "benchmark_results" / "rvl_cdip"
        )
        self.extractors = extractors or {
            name: extractor_cls() for name, extractor_cls in DEFAULT_EXTRACTORS.items()
        }

    def run(
        self,
        sample_size_per_category: int | None = None,
        categories: list[str] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> RvlCdipBenchmarkSummary:
        """Run the benchmark and persist CSV, JSON, and markdown outputs."""
        documents = self._collect_documents(sample_size_per_category, categories)
        results: list[RvlCdipDocumentResult] = []
        total_steps = len(documents) * len(self.extractors)
        for category, pdf_path in documents:
            for extractor_name, extractor in self.extractors.items():
                results.append(
                    self._evaluate_document(category, pdf_path, extractor_name, extractor)
                )
                if progress_callback is not None:
                    progress_callback(len(results), total_steps)

        category_names = sorted({category for category, _ in documents})
        summary = self._build_summary(documents, results, category_names)
        self._write_outputs(results, summary)
        return summary

    def _collect_documents(
        self,
        sample_size_per_category: int | None,
        categories: list[str] | None = None,
    ) -> list[tuple[str, Path]]:
        if not self.dataset_dir.exists():
            raise FileNotFoundError(f"RVL-CDIP dataset directory not found: {self.dataset_dir}")

        documents: list[tuple[str, Path]] = []
        category_dirs = sorted(
            path for path in self.dataset_dir.iterdir() if path.is_dir()
        )
        if categories is not None:
            selected = set(categories)
            category_dirs = [path for path in category_dirs if path.name in selected]
        for category_dir in category_dirs:
            pdf_paths = sorted(category_dir.glob("*.pdf"))
            if sample_size_per_category is not None:
                pdf_paths = pdf_paths[:sample_size_per_category]
            for pdf_path in pdf_paths:
                documents.append((category_dir.name, pdf_path))

        if not documents:
            raise FileNotFoundError(f"No category PDFs found in {self.dataset_dir}")
        return documents

    def _evaluate_document(
        self,
        category: str,
        pdf_path: Path,
        extractor_name: str,
        extractor: BaseExtractor,
    ) -> RvlCdipDocumentResult:
        start = time.perf_counter()
        try:
            extract_kwargs: dict[str, Path] = {}
            if "output_dir" in inspect.signature(extractor.extract).parameters:
                artifacts_dir = self.output_dir / "extraction_artifacts" / extractor_name / category
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                extract_kwargs["output_dir"] = artifacts_dir
            page_results = extractor.extract(pdf_path, **extract_kwargs)
            latency_ms = (time.perf_counter() - start) * 1000
            word_count = sum(len(result.extracted_text.split()) for result in page_results)
            char_count = sum(len(result.extracted_text) for result in page_results)
            layout_region_count = sum(len(result.bounding_boxes) for result in page_results)
            return RvlCdipDocumentResult(
                category=category,
                document_id=pdf_path.stem,
                pdf_path=str(pdf_path),
                extractor=extractor_name,
                status="ok",
                page_count=len(page_results),
                word_count=word_count,
                char_count=char_count,
                layout_region_count=layout_region_count,
                latency_ms=round(latency_ms, 3),
            )
        except Exception as exc:  # noqa: BLE001 - record extractor failures per document
            latency_ms = (time.perf_counter() - start) * 1000
            return RvlCdipDocumentResult(
                category=category,
                document_id=pdf_path.stem,
                pdf_path=str(pdf_path),
                extractor=extractor_name,
                status="error",
                page_count=0,
                word_count=0,
                char_count=0,
                layout_region_count=0,
                latency_ms=round(latency_ms, 3),
                error=str(exc),
            )

    def _build_summary(
        self,
        documents: list[tuple[str, Path]],
        results: list[RvlCdipDocumentResult],
        categories: list[str],
    ) -> RvlCdipBenchmarkSummary:
        extractor_summaries: dict[str, RvlCdipExtractorSummary] = {}
        for extractor_name in self.extractors:
            extractor_results = [r for r in results if r.extractor == extractor_name]
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
            category_results = [r for r in results if r.category == category]
            category_doc_count = len({r.document_id for r in category_results})
            success_rate: dict[str, float] = {}
            word_count: dict[str, float] = {}
            for extractor_name in self.extractors:
                extractor_results = [
                    r for r in category_results if r.extractor == extractor_name
                ]
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
            dataset_dir=str(self.dataset_dir),
            output_dir=str(self.output_dir),
            categories=categories,
            total_documents=len(documents),
            extractor_summaries=extractor_summaries,
            category_summaries=category_summaries,
            documents=results,
        )

    def _write_outputs(
        self,
        results: list[RvlCdipDocumentResult],
        summary: RvlCdipBenchmarkSummary,
    ) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        csv_path = self.output_dir / "rvl_cdip_results.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            fieldnames = list(asdict(results[0]).keys()) if results else []
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            if results:
                writer.writeheader()
                for result in results:
                    writer.writerow(asdict(result))

        summary_path = self.output_dir / "rvl_cdip_summary.json"
        summary_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")

        observations_path = self.output_dir / "benchmark_observations.md"
        observations_path.write_text(
            self._build_observations_markdown(summary), encoding="utf-8"
        )

    def _build_observations_markdown(self, summary: RvlCdipBenchmarkSummary) -> str:
        lines = [
            "# RVL-CDIP Benchmark Report",
            "",
            "## Dataset",
            "",
            f"- Dataset directory: `{summary.dataset_dir}`",
            f"- Categories: {len(summary.categories)}",
            f"- Total documents: {summary.total_documents}",
            "",
            "## Extractor Robustness",
            "",
            self._extractor_table(summary.extractor_summaries),
            "",
            "## Per-Category Success Rate",
            "",
            self._category_table(summary.category_summaries, list(summary.extractor_summaries)),
            "",
            "## Notes",
            "",
            (
                "- RVL-CDIP provides category labels, not text-level ground truth, so "
                "this benchmark reports extraction robustness (success rate, latency, "
                "output volume) rather than CER/WER-style accuracy."
            ),
            (
                "- OpenDataLoader runs in its default Java-only mode here (no hybrid "
                "OCR backend); scanned/image-only pages may yield low word counts "
                "without indicating a failure."
            ),
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _extractor_table(self, summaries: dict[str, RvlCdipExtractorSummary]) -> str:
        if not summaries:
            return "_No extractors evaluated._"
        rows = [
            "| Extractor | Evaluated | OK | Failed | Success Rate | Mean Latency (ms) | "
            "Mean Char Count | Mean Word Count | Mean BBox Count |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for summary in summaries.values():
            rows.append(
                f"| {summary.extractor} | {summary.documents_evaluated} | "
                f"{summary.documents_ok} | {summary.documents_failed} | "
                f"{summary.success_rate:.4f} | {summary.latency_ms.mean:.2f} | "
                f"{summary.char_count.mean:.2f} | {summary.word_count.mean:.2f} | "
                f"{summary.bbox_count.mean:.2f} |"
            )
        return "\n".join(rows)

    def _category_table(
        self,
        summaries: dict[str, RvlCdipCategorySummary],
        extractor_names: list[str],
    ) -> str:
        if not summaries:
            return "_No categories evaluated._"
        header = "| Category | Documents | " + " | ".join(extractor_names) + " |"
        separator = "| --- | ---: | " + " | ".join(["---:"] * len(extractor_names)) + " |"
        rows = [header, separator]
        for summary in summaries.values():
            rates = " | ".join(
                f"{summary.extractor_success_rate.get(name, 0.0):.2f}"
                for name in extractor_names
            )
            rows.append(f"| {summary.category} | {summary.documents} | {rates} |")
        return "\n".join(rows)
