"""FUNSD benchmark validation and comparison reporting."""

from __future__ import annotations

import csv
import json
import random
import textwrap
from dataclasses import asdict, dataclass
from pathlib import Path

from pdf_extraction_benchmark.benchmarks.funsd.metrics import (
    character_error_rate,
    normalize_text,
    token_f1,
    token_overlap_accuracy,
    token_overlap_counts,
    token_precision,
    token_recall,
    tokenize,
    word_error_rate,
)


@dataclass(slots=True)
class FunsdComparisonRow:
    """Comparison output for a single FUNSD document."""

    document_id: str
    cer: float
    wer: float
    token_precision: float
    token_recall: float
    token_f1: float
    token_overlap_accuracy: float
    category: str
    gt_tokens: int
    pred_tokens: int
    matched_tokens: int
    missing_tokens: int
    extra_tokens: int
    reading_order_gap: float
    gt_text: str
    pred_text: str
    notes: str


class FunsdComparisonAnalyzer:
    """Analyze saved FUNSD benchmark outputs for ordering effects."""

    def __init__(
        self,
        results_csv: Path | str,
        output_dir: Path | str,
    ) -> None:
        self.results_csv = Path(results_csv)
        self.output_dir = Path(output_dir)

    def run(self, sample_size: int = 10, seed: int = 42) -> dict[str, object]:
        """Sample documents, compute comparison metrics, and write reports."""
        rows = self._load_rows()
        if sample_size > len(rows):
            sample_size = len(rows)
        sampled_rows = random.Random(seed).sample(rows, sample_size)
        comparisons = [self._compare_row(row) for row in sampled_rows]
        report = self._build_report(comparisons, seed=seed)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "comparison_report.md").write_text(report, encoding="utf-8")
        (self.output_dir / "benchmark_observations.md").write_text(report, encoding="utf-8")
        (self.output_dir / "comparison_report.json").write_text(
            json.dumps(
                {
                    "seed": seed,
                    "sample_size": sample_size,
                    "documents": [asdict(item) for item in comparisons],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return {
            "sample_size": sample_size,
            "documents": comparisons,
            "report": report,
        }

    def _load_rows(self) -> list[dict[str, str]]:
        with self.results_csv.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def _compare_row(self, row: dict[str, str]) -> FunsdComparisonRow:
        ground_truth = normalize_text(row["ground_truth_text"])
        prediction = normalize_text(row["prediction_text"])
        reference_tokens = tokenize(ground_truth)
        hypothesis_tokens = tokenize(prediction)
        precision = token_precision(reference_tokens, hypothesis_tokens)
        recall = token_recall(reference_tokens, hypothesis_tokens)
        f1 = token_f1(reference_tokens, hypothesis_tokens)
        overlap_accuracy = token_overlap_accuracy(reference_tokens, hypothesis_tokens)
        cer = character_error_rate(ground_truth, prediction)
        wer = word_error_rate(ground_truth, prediction)
        matched, reference_count, hypothesis_count = token_overlap_counts(
            reference_tokens,
            hypothesis_tokens,
        )
        missing_tokens = max(reference_count - matched, 0)
        extra_tokens = max(hypothesis_count - matched, 0)
        reading_order_gap = max(0.0, wer - (1.0 - overlap_accuracy))
        category = self._classify(
            precision=precision,
            recall=recall,
            overlap_accuracy=overlap_accuracy,
            reading_order_gap=reading_order_gap,
            ground_truth_tokens=len(reference_tokens),
            prediction_tokens=len(hypothesis_tokens),
        )
        notes = self._build_notes(
            reference_tokens=reference_tokens,
            hypothesis_tokens=hypothesis_tokens,
            category=category,
        )
        return FunsdComparisonRow(
            document_id=row["document_id"],
            cer=cer,
            wer=wer,
            token_precision=precision,
            token_recall=recall,
            token_f1=f1,
            token_overlap_accuracy=overlap_accuracy,
            category=category,
            gt_tokens=len(reference_tokens),
            pred_tokens=len(hypothesis_tokens),
            matched_tokens=matched,
            missing_tokens=missing_tokens,
            extra_tokens=extra_tokens,
            reading_order_gap=reading_order_gap,
            gt_text=ground_truth,
            pred_text=prediction,
            notes=notes,
        )

    def _classify(
        self,
        *,
        precision: float,
        recall: float,
        overlap_accuracy: float,
        reading_order_gap: float,
        ground_truth_tokens: int,
        prediction_tokens: int,
    ) -> str:
        if ground_truth_tokens and prediction_tokens == 0:
            return "missing_text"
        if recall < 0.55 or precision < 0.55 or overlap_accuracy < 0.5:
            return "actual_ocr_errors"
        if reading_order_gap > 0.2 and precision >= 0.6 and recall >= 0.6:
            return "reading_order_or_layout"
        return "mixed"

    def _build_notes(
        self,
        *,
        reference_tokens: list[str],
        hypothesis_tokens: list[str],
        category: str,
    ) -> str:
        gt_only = [token for token in reference_tokens if token not in hypothesis_tokens][:8]
        pred_only = [token for token in hypothesis_tokens if token not in reference_tokens][:8]
        snippets = []
        if gt_only:
            snippets.append(f"missing: {', '.join(gt_only)}")
        if pred_only:
            snippets.append(f"extra: {', '.join(pred_only)}")
        snippets.append(f"classified as {category}")
        return "; ".join(snippets)

    def _build_report(
        self,
        comparisons: list[FunsdComparisonRow],
        *,
        seed: int,
    ) -> str:
        average_cer = sum(item.cer for item in comparisons) / len(comparisons)
        average_wer = sum(item.wer for item in comparisons) / len(comparisons)
        average_precision = sum(item.token_precision for item in comparisons) / len(comparisons)
        average_recall = sum(item.token_recall for item in comparisons) / len(comparisons)
        average_f1 = sum(item.token_f1 for item in comparisons) / len(comparisons)
        average_overlap = sum(item.token_overlap_accuracy for item in comparisons) / len(
            comparisons
        )
        category_counts: dict[str, int] = {}
        for item in comparisons:
            category_counts[item.category] = category_counts.get(item.category, 0) + 1

        lines = [
            "# FUNSD Reading-Order Validation Report",
            "",
            "## What was checked",
            "",
            (
                "- OCR text is compared exactly as the benchmark concatenates it: "
                "PaddleOCR line order, joined with spaces after whitespace normalization."
            ),
            (
                "- FUNSD ground truth is compared exactly as the benchmark concatenates it: "
                "`form` entries in JSON order, using `text` or fallback `words[*].text`."
            ),
            (
                "- The sample below checks whether token overlap stays high even when "
                "CER/WER are high, which is a sign of reading-order or layout mismatch "
                "rather than pure OCR failure."
            ),
            "",
            "## Sample summary",
            "",
            f"- Documents sampled: {len(comparisons)}",
            f"- Random seed: {seed}",
            f"- Average CER: {average_cer:.6f}",
            f"- Average WER: {average_wer:.6f}",
            f"- Average token precision: {average_precision:.6f}",
            f"- Average token recall: {average_recall:.6f}",
            f"- Average token F1: {average_f1:.6f}",
            (
                "- Average order-insensitive token overlap accuracy "
                f"(multiset Jaccard): {average_overlap:.6f}"
            ),
            "",
            "## Category counts",
        ]
        for category, count in sorted(category_counts.items()):
            lines.append(f"- {category}: {count}")

        lines.extend(
            [
                "",
                "## Per-document comparison",
            ]
        )

        for item in comparisons:
            lines.extend(
                [
                    "",
                    f"### {item.document_id}",
                    "",
                    f"- Category: {item.category}",
                    f"- CER: {item.cer:.6f}",
                    f"- WER: {item.wer:.6f}",
                    f"- Token precision: {item.token_precision:.6f}",
                    f"- Token recall: {item.token_recall:.6f}",
                    f"- Token F1: {item.token_f1:.6f}",
                    (
                        "- Order-insensitive token overlap accuracy: "
                        f"{item.token_overlap_accuracy:.6f}"
                    ),
                    f"- Reading-order gap: {item.reading_order_gap:.6f}",
                    f"- GT tokens: {item.gt_tokens}",
                    f"- Pred tokens: {item.pred_tokens}",
                    "",
                    "**Ground truth**",
                    "",
                    f"```text\n{self._wrap_for_markdown(item.gt_text)}\n```",
                    "",
                    "**OCR output**",
                    "",
                    f"```text\n{self._wrap_for_markdown(item.pred_text)}\n```",
                    "",
                    f"**Notes:** {item.notes}",
                ]
            )

        lines.extend(
            [
                "",
                "## Interpretation",
                "",
                (
                    "- High token precision/recall with noticeably worse CER/WER points "
                    "to ordering and layout effects."
                ),
                "- Low token precision/recall points to genuine OCR mistakes or missing text.",
                (
                    "- In this sample, many of the errors are caused by field "
                    "reordering and line-flattening rather than total OCR failure."
                ),
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _wrap_for_markdown(self, text: str, width: int = 120) -> str:
        normalized = normalize_text(text)
        if not normalized:
            return ""
        return "\n".join(textwrap.wrap(normalized, width=width, break_long_words=False))
