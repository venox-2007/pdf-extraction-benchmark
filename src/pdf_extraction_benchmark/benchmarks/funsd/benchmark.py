"""FUNSD OCR benchmark pipeline."""

from __future__ import annotations

import csv
import json
import os
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean, median, pstdev

import matplotlib.pyplot as plt

try:
    from paddleocr import PaddleOCR
except ImportError:  # pragma: no cover - optional runtime dependency
    PaddleOCR = None  # type: ignore[assignment]

from pdf_extraction_benchmark.benchmarks.funsd.entity import (
    FunsdEntityResult,
    build_entity_observations_markdown,
    build_entity_summary,
    entity_results_payload,
    evaluate_entity_document,
    extract_ocr_lines,
)
from pdf_extraction_benchmark.benchmarks.funsd.metrics import (
    character_error_rate,
    token_f1,
    token_overlap_accuracy,
    token_overlap_counts,
    token_precision,
    token_recall,
    tokenize,
    word_error_rate,
)


@dataclass(slots=True)
class MetricStatistics:
    """Descriptive statistics for a numeric metric."""

    mean: float
    median: float
    minimum: float
    maximum: float
    stddev: float


@dataclass(slots=True)
class RankedDocument:
    """Lightweight ranking payload for best and worst documents."""

    document_id: str
    cer: float
    wer: float
    token_precision: float
    token_recall: float
    token_f1: float
    token_overlap_accuracy: float
    primary_failure_mode: str
    failure_patterns: str


@dataclass(slots=True)
class FunsdDocumentResult:
    """Per-document OCR benchmark result."""

    document_id: str
    image_path: str
    annotation_path: str
    prediction_text: str
    ground_truth_text: str
    cer: float
    wer: float
    token_precision: float
    token_recall: float
    token_f1: float
    token_overlap_accuracy: float
    prediction_char_count: int
    ground_truth_char_count: int
    prediction_word_count: int
    ground_truth_word_count: int
    primary_failure_mode: str
    failure_patterns: str
    status: str
    error: str | None = None


@dataclass(slots=True)
class FunsdBenchmarkSummary:
    """Aggregate benchmark summary for FUNSD."""

    dataset_dir: str
    total_documents: int
    evaluated_documents: int
    average_cer: float
    average_wer: float
    average_token_precision: float
    average_token_recall: float
    average_token_f1: float
    average_token_overlap_accuracy: float
    metric_statistics: dict[str, MetricStatistics] = field(default_factory=dict)
    best_document: str | None = None
    best_cer: float | None = None
    worst_document: str | None = None
    worst_cer: float | None = None
    top_10_best: list[RankedDocument] = field(default_factory=list)
    top_10_worst: list[RankedDocument] = field(default_factory=list)
    failure_mode_counts: dict[str, int] = field(default_factory=dict)
    chart_paths: dict[str, str] = field(default_factory=dict)
    output_dir: str = ""


class FunsdBenchmarkPipeline:
    """Run PaddleOCR against FUNSD and score it against ground truth."""

    def __init__(
        self,
        dataset_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
        chart_dir: Path | str | None = None,
        ocr_runner: Callable[[Path], str] | None = None,
        ocr_line_runner: Callable[[Path], object] | None = None,
    ) -> None:
        self.project_root = Path(__file__).resolve().parents[4]
        self.dataset_dir = (
            Path(dataset_dir)
            if dataset_dir is not None
            else self.project_root / "datasets" / "FUNSD"
        )
        self.output_dir = (
            Path(output_dir)
            if output_dir is not None
            else self.project_root / "outputs" / "benchmark_results" / "funsd"
        )
        self.chart_dir = (
            Path(chart_dir)
            if chart_dir is not None
            else self.project_root / "outputs" / "charts" / "funsd"
        )
        self._ocr_runner = ocr_runner
        self._ocr_line_runner = ocr_line_runner
        self._ocr_engine: PaddleOCR | None = None

    def run(self, sample_size: int | None = None) -> FunsdBenchmarkSummary:
        """Run the benchmark and persist CSV, JSON, charts, and markdown outputs."""
        documents = self._collect_documents()
        if sample_size is not None:
            documents = documents[:sample_size]

        results: list[FunsdDocumentResult] = []
        entity_results: list[FunsdEntityResult] = []
        for image_path, annotation_path in documents:
            document_result, entity_result = self._evaluate_document(image_path, annotation_path)
            results.append(document_result)
            entity_results.append(entity_result)
        chart_paths = self._generate_charts(results)
        summary = self._build_summary(results, chart_paths)
        self._write_outputs(results, summary)
        entity_summary = build_entity_summary(entity_results, self.dataset_dir, self.output_dir)
        self._write_entity_outputs(entity_results, entity_summary)
        return summary

    def _collect_documents(self) -> list[tuple[Path, Path]]:
        images_dir = self.dataset_dir / "images"
        annotations_dir = self.dataset_dir / "annotations"
        if not images_dir.exists():
            raise FileNotFoundError(f"FUNSD images directory not found: {images_dir}")
        if not annotations_dir.exists():
            raise FileNotFoundError(f"FUNSD annotations directory not found: {annotations_dir}")

        image_paths = sorted(
            path
            for path in images_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
        )
        documents: list[tuple[Path, Path]] = []
        for image_path in image_paths:
            annotation_path = annotations_dir / f"{image_path.stem}.json"
            if annotation_path.exists():
                documents.append((image_path, annotation_path))
        if not documents:
            raise FileNotFoundError(
                f"No matching FUNSD image/annotation pairs found in {self.dataset_dir}"
            )
        return documents

    def _evaluate_document(
        self,
        image_path: Path,
        annotation_path: Path,
    ) -> tuple[FunsdDocumentResult, FunsdEntityResult]:
        ground_truth_text = self._extract_ground_truth_text(annotation_path)
        prediction_text, raw_ocr_result = self._extract_prediction_artifacts(image_path)
        normalized_prediction = self.normalize_text(prediction_text)
        normalized_ground_truth = self.normalize_text(ground_truth_text)

        reference_tokens = tokenize(normalized_ground_truth)
        hypothesis_tokens = tokenize(normalized_prediction)
        cer = character_error_rate(normalized_ground_truth, normalized_prediction)
        wer = word_error_rate(normalized_ground_truth, normalized_prediction)
        precision = token_precision(reference_tokens, hypothesis_tokens)
        recall = token_recall(reference_tokens, hypothesis_tokens)
        f1 = token_f1(reference_tokens, hypothesis_tokens)
        overlap_accuracy = token_overlap_accuracy(reference_tokens, hypothesis_tokens)
        failure_patterns = self._categorize_failure_patterns(
            normalized_ground_truth,
            normalized_prediction,
            reference_tokens,
            hypothesis_tokens,
            cer,
            wer,
            precision,
            recall,
            overlap_accuracy,
        )

        document_result = FunsdDocumentResult(
            document_id=image_path.stem,
            image_path=str(image_path),
            annotation_path=str(annotation_path),
            prediction_text=normalized_prediction,
            ground_truth_text=normalized_ground_truth,
            cer=cer,
            wer=wer,
            token_precision=precision,
            token_recall=recall,
            token_f1=f1,
            token_overlap_accuracy=overlap_accuracy,
            prediction_char_count=len(normalized_prediction),
            ground_truth_char_count=len(normalized_ground_truth),
            prediction_word_count=len(hypothesis_tokens),
            ground_truth_word_count=len(reference_tokens),
            primary_failure_mode=failure_patterns[0],
            failure_patterns=" | ".join(failure_patterns),
            status="ok",
        )
        entity_result = evaluate_entity_document(
            document_id=image_path.stem,
            image_path=image_path,
            annotation_path=annotation_path,
            raw_ocr_result=raw_ocr_result,
            cer=cer,
            wer=wer,
        )
        return document_result, entity_result

    def _extract_prediction_artifacts(self, image_path: Path) -> tuple[str, object]:
        if self._ocr_line_runner is not None:
            raw_result = self._ocr_line_runner(image_path)
            prediction_text = self._extract_text_from_raw_result(raw_result)
            if self._ocr_runner is not None:
                prediction_text = self._ocr_runner(image_path)
            return prediction_text, raw_result

        if self._ocr_runner is not None:
            prediction_text = self._ocr_runner(image_path)
            dummy_result = [
                [
                    [0.0, 0.0],
                    [1.0, 0.0],
                    [1.0, 1.0],
                    [0.0, 1.0],
                ],
                (prediction_text, 1.0),
            ]
            return prediction_text, dummy_result

        if PaddleOCR is None:
            raise RuntimeError(
                "PaddleOCR is not installed. Install with: pip install paddleocr paddlepaddle"
            )

        if self._ocr_engine is None:
            os.environ.setdefault("FLAGS_use_mkldnn", "0")
            os.environ.setdefault("FLAGS_enable_pir_api", "0")
            os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
            self._ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

        raw_result = self._ocr_engine.ocr(str(image_path), cls=True)
        prediction_text = self._extract_text_from_raw_result(raw_result)
        return prediction_text, raw_result

    def _extract_text_from_raw_result(self, raw_result: object) -> str:
        lines = extract_ocr_lines(raw_result)
        texts = []
        for line in lines:
            normalized = self.normalize_text(line.text)
            if normalized:
                texts.append(normalized)
        return "\n".join(texts)

    def _extract_ground_truth_text(self, annotation_path: Path) -> str:
        with annotation_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        segments: list[str] = []
        for entry in data.get("form", []):
            entry_text = self.normalize_text(str(entry.get("text", "")))
            if not entry_text:
                entry_text = self.normalize_text(
                    " ".join(
                        word.get("text", "")
                        for word in entry.get("words", [])
                        if word.get("text", "")
                    )
                )
            if entry_text:
                segments.append(entry_text)
        return "\n".join(segments)

    def _categorize_failure_patterns(
        self,
        ground_truth_text: str,
        prediction_text: str,
        reference_tokens: list[str],
        hypothesis_tokens: list[str],
        cer: float,
        wer: float,
        precision: float,
        recall: float,
        overlap_accuracy: float,
    ) -> list[str]:
        patterns: list[str] = []
        reference_digits = self._digit_token_count(reference_tokens)
        hypothesis_digits = self._digit_token_count(hypothesis_tokens)

        if ground_truth_text and (
            not prediction_text
            or recall < 0.55
            or len(hypothesis_tokens) < len(reference_tokens) * 0.75
        ):
            patterns.append("Missing text")

        if precision >= 0.7 and recall >= 0.7 and cer >= 0.08:
            patterns.append("Character substitutions")

        if (
            (reference_digits >= 4 or hypothesis_digits >= 4)
            and self._numeric_mismatch_ratio(reference_tokens, hypothesis_tokens) >= 0.35
        ):
            patterns.append("Numeric errors")

        if (
            overlap_accuracy >= 0.45
            and wer >= 0.3
            and self._reading_order_gap(wer, overlap_accuracy) >= 0.15
        ):
            patterns.append("Layout issues")

        if self._looks_table_like(ground_truth_text, prediction_text):
            patterns.append("Table-related errors")

        if not patterns:
            patterns.append("Mixed")
        return patterns

    def _digit_token_count(self, tokens: list[str]) -> int:
        return sum(1 for token in tokens if any(character.isdigit() for character in token))

    def _numeric_mismatch_ratio(
        self,
        reference_tokens: list[str],
        hypothesis_tokens: list[str],
    ) -> float:
        reference_numeric = [
            token for token in reference_tokens if any(ch.isdigit() for ch in token)
        ]
        hypothesis_numeric = [
            token for token in hypothesis_tokens if any(ch.isdigit() for ch in token)
        ]
        matched, reference_count, hypothesis_count = token_overlap_counts(
            reference_numeric,
            hypothesis_numeric,
        )
        denominator = max(reference_count, hypothesis_count, 1)
        return 1.0 - (matched / denominator)

    def _reading_order_gap(self, wer_value: float, overlap_accuracy: float) -> float:
        return max(0.0, wer_value - (1.0 - overlap_accuracy))

    def _looks_table_like(self, ground_truth_text: str, prediction_text: str) -> bool:
        combined_text = f"{ground_truth_text} {prediction_text}"
        slash_tokens = combined_text.count("/") + combined_text.count("-")
        numeric_tokens = sum(
            1
            for token in tokenize(combined_text)
            if any(character.isdigit() for character in token)
        )
        token_total = max(len(tokenize(combined_text)), 1)
        return slash_tokens >= 8 or numeric_tokens / token_total >= 0.25

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize line endings and collapse whitespace."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def character_error_rate(cls, reference: str, hypothesis: str) -> float:
        """Backward-compatible helper retained for tests."""
        return character_error_rate(reference, hypothesis)

    @classmethod
    def word_error_rate(cls, reference: str, hypothesis: str) -> float:
        """Backward-compatible helper retained for tests."""
        return word_error_rate(reference, hypothesis)

    def _build_summary(
        self,
        results: list[FunsdDocumentResult],
        chart_paths: dict[str, str],
    ) -> FunsdBenchmarkSummary:
        metric_statistics = self._compute_metric_statistics(results)
        sorted_by_cer = sorted(
            results,
            key=lambda result: (result.cer, result.wer, result.document_id),
        )
        sorted_by_worst = sorted(
            results,
            key=lambda result: (-result.cer, -result.wer, result.document_id),
        )
        failure_mode_counts = self._build_failure_mode_counts(results)

        return FunsdBenchmarkSummary(
            dataset_dir=str(self.dataset_dir),
            total_documents=len(results),
            evaluated_documents=len(results),
            average_cer=metric_statistics["cer"].mean,
            average_wer=metric_statistics["wer"].mean,
            average_token_precision=metric_statistics["token_precision"].mean,
            average_token_recall=metric_statistics["token_recall"].mean,
            average_token_f1=metric_statistics["token_f1"].mean,
            average_token_overlap_accuracy=metric_statistics["token_overlap_accuracy"].mean,
            metric_statistics=metric_statistics,
            best_document=sorted_by_cer[0].document_id if sorted_by_cer else None,
            best_cer=sorted_by_cer[0].cer if sorted_by_cer else None,
            worst_document=sorted_by_worst[0].document_id if sorted_by_worst else None,
            worst_cer=sorted_by_worst[0].cer if sorted_by_worst else None,
            top_10_best=[self._to_ranking(result) for result in sorted_by_cer[:10]],
            top_10_worst=[self._to_ranking(result) for result in sorted_by_worst[:10]],
            failure_mode_counts=failure_mode_counts,
            chart_paths=chart_paths,
            output_dir=str(self.output_dir),
        )

    def _compute_metric_statistics(
        self,
        results: list[FunsdDocumentResult],
    ) -> dict[str, MetricStatistics]:
        metric_names = [
            "cer",
            "wer",
            "token_precision",
            "token_recall",
            "token_f1",
            "token_overlap_accuracy",
        ]
        statistics_map: dict[str, MetricStatistics] = {}
        for metric_name in metric_names:
            values = [getattr(result, metric_name) for result in results]
            statistics_map[metric_name] = self._statistics_for(values)
        return statistics_map

    def _statistics_for(self, values: list[float]) -> MetricStatistics:
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

    def _build_failure_mode_counts(self, results: list[FunsdDocumentResult]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for result in results:
            for pattern in result.failure_patterns.split(" | "):
                counts[pattern] = counts.get(pattern, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

    def _to_ranking(self, result: FunsdDocumentResult) -> RankedDocument:
        return RankedDocument(
            document_id=result.document_id,
            cer=result.cer,
            wer=result.wer,
            token_precision=result.token_precision,
            token_recall=result.token_recall,
            token_f1=result.token_f1,
            token_overlap_accuracy=result.token_overlap_accuracy,
            primary_failure_mode=result.primary_failure_mode,
            failure_patterns=result.failure_patterns,
        )

    def _generate_charts(self, results: list[FunsdDocumentResult]) -> dict[str, str]:
        self.chart_dir.mkdir(parents=True, exist_ok=True)
        chart_specs = {
            "cer": (
                [result.cer for result in results],
                "CER distribution",
                "CER",
                "cer_distribution.png",
            ),
            "wer": (
                [result.wer for result in results],
                "WER distribution",
                "WER",
                "wer_distribution.png",
            ),
            "token_f1": (
                [result.token_f1 for result in results],
                "Token F1 distribution",
                "Token F1",
                "f1_distribution.png",
            ),
        }
        chart_paths: dict[str, str] = {}
        for metric_name, (values, title, xlabel, file_name) in chart_specs.items():
            chart_path = self.chart_dir / file_name
            self._save_distribution_chart(values, title, xlabel, chart_path, metric_name)
            chart_paths[metric_name] = self._display_path(chart_path)
        return chart_paths

    def _save_distribution_chart(
        self,
        values: list[float],
        title: str,
        xlabel: str,
        output_path: Path,
        metric_name: str,
    ) -> None:
        plt.style.use("seaborn-v0_8-whitegrid")
        fig, axis = plt.subplots(figsize=(8, 5))
        bins = min(20, max(6, len(values) // 4 or 6))
        axis.hist(values, bins=bins, color="#4f46e5", alpha=0.8, edgecolor="white")
        axis.set_title(title)
        axis.set_xlabel(xlabel)
        axis.set_ylabel("Document count")

        stat = self._statistics_for(values)
        axis.axvline(stat.mean, color="#dc2626", linestyle="--", linewidth=2, label="Mean")
        axis.axvline(stat.median, color="#16a34a", linestyle=":", linewidth=2, label="Median")
        axis.legend()
        axis.text(
            0.99,
            0.98,
            f"min={stat.minimum:.3f}\nmax={stat.maximum:.3f}\nstd={stat.stddev:.3f}",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=9,
            bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
        )

        fig.tight_layout()
        fig.savefig(output_path, dpi=180)
        plt.close(fig)

    def _display_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            return str(path.resolve())

    def _write_outputs(
        self,
        results: list[FunsdDocumentResult],
        summary: FunsdBenchmarkSummary,
    ) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        csv_path = self.output_dir / "funsd_results.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            fieldnames = list(asdict(results[0]).keys()) if results else []
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            if results:
                writer.writeheader()
                for result in results:
                    writer.writerow(asdict(result))

        summary_path = self.output_dir / "funsd_summary.json"
        summary_payload = asdict(summary)
        summary_payload["documents"] = [asdict(result) for result in results]
        summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

        observations_path = self.output_dir / "benchmark_observations.md"
        observations_path.write_text(
            self._build_observations_markdown(results, summary),
            encoding="utf-8",
        )

    def _write_entity_outputs(
        self,
        results: list[FunsdEntityResult],
        summary: object,
    ) -> None:
        entity_results_path = self.output_dir / "entity_results.csv"
        with entity_results_path.open("w", newline="", encoding="utf-8") as handle:
            fieldnames = list(asdict(results[0]).keys()) if results else []
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            if results:
                writer.writeheader()
                for result in results:
                    writer.writerow(asdict(result))

        entity_summary_path = self.output_dir / "entity_summary.json"
        summary_payload = asdict(summary)
        summary_payload["documents"] = entity_results_payload(results)
        entity_summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

        entity_observations_path = self.output_dir / "entity_observations.md"
        entity_observations_path.write_text(
            build_entity_observations_markdown(results, summary),
            encoding="utf-8",
        )

    def _build_observations_markdown(
        self,
        results: list[FunsdDocumentResult],
        summary: FunsdBenchmarkSummary,
    ) -> str:
        lines = [
            "# FUNSD Benchmark Report",
            "",
            "## Dataset",
            "",
            f"- Dataset size: {summary.total_documents} documents",
            f"- Documents evaluated: {summary.evaluated_documents}",
            f"- Dataset directory: `{summary.dataset_dir}`",
            "",
            "## Average Metrics",
            "",
            self._metrics_table(summary.metric_statistics),
            "",
            "## Distributions",
            "",
            f"- CER chart: `{summary.chart_paths.get('cer', 'n/a')}`",
            f"- WER chart: `{summary.chart_paths.get('wer', 'n/a')}`",
            f"- F1 chart: `{summary.chart_paths.get('token_f1', 'n/a')}`",
            "",
            "## Best 10 Documents",
            "",
            self._ranking_table(summary.top_10_best, ascending=True),
            "",
            "## Worst 10 Documents",
            "",
            self._ranking_table(summary.top_10_worst, ascending=False),
            "",
            "## Failure Modes",
            "",
            self._failure_modes_section(summary.failure_mode_counts),
            "",
            "## Recommendations",
            "",
            (
                "- Treat CER and WER as useful but not sufficient for FUNSD because "
                "they are sensitive to both OCR mistakes and document structure."
            ),
            (
                "- Use token precision/recall/F1 to separate content capture from "
                "ordering noise."
            ),
            (
                "- Inspect table-heavy or numeric-heavy documents separately because "
                "they show the largest layout and digit-related drift."
            ),
            (
                "- Use the distribution charts to flag documents that sit far outside "
                "the cluster as likely preprocessing or extraction failures."
            ),
            "",
            "## Notes",
            "",
            (
                "- The CSV now includes CER, WER, token precision, token recall, "
                "token F1, and order-insensitive token overlap accuracy for every "
                "document."
            ),
            (
                "- Failure categories are heuristic and are intended for reporting, "
                "not as ground truth labels."
            ),
            (
                "- The top and worst examples are ranked primarily by CER, with WER "
                "and token metrics included for context."
            ),
        ]
        return "\n".join(lines).replace("\n\n\n", "\n\n").rstrip() + "\n"

    def _metrics_table(self, stats: dict[str, MetricStatistics]) -> str:
        header = "| Metric | Mean | Median | Min | Max | Std Dev |"
        separator = "| --- | ---: | ---: | ---: | ---: | ---: |"
        rows = [header, separator]
        labels = {
            "cer": "CER",
            "wer": "WER",
            "token_precision": "Token Precision",
            "token_recall": "Token Recall",
            "token_f1": "Token F1",
            "token_overlap_accuracy": "Token Overlap Accuracy",
        }
        for metric_name, label in labels.items():
            stat = stats[metric_name]
            rows.append(
                f"| {label} | {stat.mean:.6f} | {stat.median:.6f} | {stat.minimum:.6f} | "
                f"{stat.maximum:.6f} | {stat.stddev:.6f} |"
            )
        return "\n".join(rows)

    def _ranking_table(self, items: list[RankedDocument], *, ascending: bool) -> str:
        if not items:
            return "_No documents available._"
        rows = [
            "| Rank | Document | CER | WER | Token F1 | Primary Failure Mode |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
        for index, item in enumerate(items, start=1):
            rows.append(
                f"| {index} | {item.document_id} | {item.cer:.6f} | {item.wer:.6f} | "
                f"{item.token_f1:.6f} | {item.primary_failure_mode} |"
            )
        return "\n".join(rows)

    def _failure_modes_section(self, counts: dict[str, int]) -> str:
        if not counts:
            return "_No failure modes identified._"
        rows = [
            "| Failure mode | Documents |",
            "| --- | ---: |",
        ]
        for mode, count in counts.items():
            rows.append(f"| {mode} | {count} |")
        return "\n".join(rows)
