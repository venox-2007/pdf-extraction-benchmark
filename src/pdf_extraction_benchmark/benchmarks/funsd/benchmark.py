"""FUNSD OCR benchmark pipeline."""

from __future__ import annotations

import csv
import json
import os
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

try:
    from paddleocr import PaddleOCR
except ImportError:  # pragma: no cover - optional runtime dependency
    PaddleOCR = None  # type: ignore[assignment]


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
    prediction_char_count: int
    ground_truth_char_count: int
    prediction_word_count: int
    ground_truth_word_count: int
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
    best_document: str | None
    best_cer: float | None
    worst_document: str | None
    worst_cer: float | None
    output_dir: str


class FunsdBenchmarkPipeline:
    """Run PaddleOCR against FUNSD and score it against ground truth."""

    def __init__(
        self,
        dataset_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
        ocr_runner: Callable[[Path], str] | None = None,
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
        self._ocr_runner = ocr_runner
        self._ocr_engine: PaddleOCR | None = None

    def run(self, sample_size: int | None = None) -> FunsdBenchmarkSummary:
        """Run the benchmark and persist CSV, JSON, and markdown outputs."""
        documents = self._collect_documents()
        if sample_size is not None:
            documents = documents[:sample_size]

        results = [
            self._evaluate_document(image_path, annotation_path)
            for image_path, annotation_path in documents
        ]
        summary = self._build_summary(results)
        self._write_outputs(results, summary)
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

    def _evaluate_document(self, image_path: Path, annotation_path: Path) -> FunsdDocumentResult:
        ground_truth_text = self._extract_ground_truth_text(annotation_path)
        prediction_text = self._extract_prediction_text(image_path)
        normalized_prediction = self.normalize_text(prediction_text)
        normalized_ground_truth = self.normalize_text(ground_truth_text)

        cer = self.character_error_rate(normalized_ground_truth, normalized_prediction)
        wer = self.word_error_rate(normalized_ground_truth, normalized_prediction)

        return FunsdDocumentResult(
            document_id=image_path.stem,
            image_path=str(image_path),
            annotation_path=str(annotation_path),
            prediction_text=normalized_prediction,
            ground_truth_text=normalized_ground_truth,
            cer=cer,
            wer=wer,
            prediction_char_count=len(normalized_prediction),
            ground_truth_char_count=len(normalized_ground_truth),
            prediction_word_count=len(self._tokenize_words(normalized_prediction)),
            ground_truth_word_count=len(self._tokenize_words(normalized_ground_truth)),
            status="ok",
        )

    def _extract_prediction_text(self, image_path: Path) -> str:
        if self._ocr_runner is not None:
            return self._ocr_runner(image_path)

        if PaddleOCR is None:
            raise RuntimeError(
                "PaddleOCR is not installed. Install with: pip install paddleocr paddlepaddle"
            )

        if self._ocr_engine is None:
            os.environ.setdefault("FLAGS_use_mkldnn", "0")
            os.environ.setdefault("FLAGS_enable_pir_api", "0")
            os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
            self._ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

        result = self._ocr_engine.ocr(str(image_path), cls=True)
        lines = self._flatten_ocr_result(result)
        texts = [normalized for text in lines if (normalized := self.normalize_text(text))]
        return "\n".join(texts)

    def _flatten_ocr_result(self, result: object) -> list[str]:
        if result is None:
            return []
        if isinstance(result, list):
            if self._looks_like_ocr_line(result):
                text = self._extract_ocr_text(result)
                return [text] if text else []

            lines: list[str] = []
            for item in result:
                lines.extend(self._flatten_ocr_result(item))
            return lines
        return []

    def _looks_like_ocr_line(self, value: object) -> bool:
        if not isinstance(value, list) or len(value) != 2:
            return False
        if not isinstance(value[1], (list, tuple)) or len(value[1]) < 1:
            return False
        return isinstance(value[1][0], str)

    def _extract_ocr_text(self, line: list[object]) -> str:
        line_data = line[1]
        if not isinstance(line_data, (list, tuple)) or not line_data:
            return ""
        text = line_data[0]
        return text if isinstance(text, str) else ""

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

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize line endings and collapse whitespace."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _tokenize_words(text: str) -> list[str]:
        return [word for word in re.split(r"\s+", text.strip()) if word]

    @classmethod
    def character_error_rate(cls, reference: str, hypothesis: str) -> float:
        """Compute character error rate using normalized edit distance."""
        if not reference and not hypothesis:
            return 0.0
        if not reference:
            return 1.0
        distance = cls._levenshtein(list(reference), list(hypothesis))
        return distance / len(reference)

    @classmethod
    def word_error_rate(cls, reference: str, hypothesis: str) -> float:
        """Compute word error rate using normalized token edit distance."""
        reference_words = cls._tokenize_words(reference)
        hypothesis_words = cls._tokenize_words(hypothesis)
        if not reference_words and not hypothesis_words:
            return 0.0
        if not reference_words:
            return 1.0
        distance = cls._levenshtein(reference_words, hypothesis_words)
        return distance / len(reference_words)

    @staticmethod
    def _levenshtein(reference: list[str], hypothesis: list[str]) -> int:
        if not reference:
            return len(hypothesis)
        if not hypothesis:
            return len(reference)

        previous = list(range(len(hypothesis) + 1))
        for reference_index, reference_item in enumerate(reference, start=1):
            current = [reference_index]
            for hypothesis_index, hypothesis_item in enumerate(hypothesis, start=1):
                substitution_cost = 0 if reference_item == hypothesis_item else 1
                current.append(
                    min(
                        previous[hypothesis_index] + 1,
                        current[hypothesis_index - 1] + 1,
                        previous[hypothesis_index - 1] + substitution_cost,
                    )
                )
            previous = current
        return previous[-1]

    def _build_summary(self, results: list[FunsdDocumentResult]) -> FunsdBenchmarkSummary:
        evaluated_results = [result for result in results if result.ground_truth_text]
        best_result = min(
            evaluated_results,
            key=lambda result: (result.cer, result.wer),
            default=None,
        )
        worst_result = max(
            evaluated_results,
            key=lambda result: (result.cer, result.wer),
            default=None,
        )
        average_cer = round(mean(result.cer for result in results), 6) if results else 0.0
        average_wer = round(mean(result.wer for result in results), 6) if results else 0.0

        return FunsdBenchmarkSummary(
            dataset_dir=str(self.dataset_dir),
            total_documents=len(results),
            evaluated_documents=len(evaluated_results),
            average_cer=average_cer,
            average_wer=average_wer,
            best_document=best_result.document_id if best_result else None,
            best_cer=best_result.cer if best_result else None,
            worst_document=worst_result.document_id if worst_result else None,
            worst_cer=worst_result.cer if worst_result else None,
            output_dir=str(self.output_dir),
        )

    def _write_outputs(
        self,
        results: list[FunsdDocumentResult],
        summary: FunsdBenchmarkSummary,
    ) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        csv_path = self.output_dir / "funsd_results.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=list(asdict(results[0]).keys()) if results else [],
            )
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

    def _build_observations_markdown(
        self,
        results: list[FunsdDocumentResult],
        summary: FunsdBenchmarkSummary,
    ) -> str:
        best = next(
            (result for result in results if result.document_id == summary.best_document),
            None,
        )
        worst = next(
            (result for result in results if result.document_id == summary.worst_document),
            None,
        )
        sample_rows = sorted(results, key=lambda result: result.cer)[:5]

        lines = [
            "# FUNSD Benchmark Observations",
            "",
            "## Method",
            "",
            "- FUNSD ground truth is read from each annotation JSON file's `form` array.",
            (
                "- Each entry uses `text` when present; otherwise the "
                "`words[*].text` values are joined."
            ),
            (
                "- The extracted strings are normalized by converting line endings to `\\n` "
                "and collapsing whitespace."
            ),
            "- CER is the Levenshtein edit distance divided by the reference character count.",
            "- WER is the Levenshtein edit distance divided by the reference word count.",
            "",
            "## Summary",
            "",
            f"- Documents processed: {summary.total_documents}",
            f"- Documents with ground truth: {summary.evaluated_documents}",
            f"- Average CER: {summary.average_cer:.6f}",
            f"- Average WER: {summary.average_wer:.6f}",
            f"- Best document: {summary.best_document or 'n/a'}",
            f"- Worst document: {summary.worst_document or 'n/a'}",
            "",
            "## Best/Worst",
            "",
            (
                f"- Best CER: {summary.best_cer:.6f}"
                if summary.best_cer is not None
                else "- Best CER: n/a"
            ),
            (
                f"- Worst CER: {summary.worst_cer:.6f}"
                if summary.worst_cer is not None
                else "- Worst CER: n/a"
            ),
            "",
            "## Sample Results",
            "",
            "| Document | CER | WER | GT chars | Pred chars |",
            "| --- | --- | --- | --- | --- |",
        ]
        for result in sample_rows:
            lines.append(
                (
                    "| {document_id} | {cer:.4f} | {wer:.4f} | "
                    "{ground_truth_char_count} | {prediction_char_count} |"
                ).format(**asdict(result))
            )

        if best is not None and worst is not None:
            lines.extend(
                [
                    "",
                    "## Notes",
                    "",
                    f"- Lowest error document: `{best.document_id}`.",
                    f"- Highest error document: `{worst.document_id}`.",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"
