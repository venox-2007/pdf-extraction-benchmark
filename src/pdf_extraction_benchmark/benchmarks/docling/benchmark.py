"""Docling FUNSD benchmark pipeline and comparison report generation."""

from __future__ import annotations

import json
import shutil
import tempfile
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

import fitz
import pandas as pd
import torch  # noqa: F401

from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline
from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor


def _safe_package_version(package_name: str) -> str:
    """Return a package version string or a stable fallback."""
    try:
        return package_version(package_name)
    except PackageNotFoundError:
        return "unknown"


class DoclingBenchmarkPipeline:
    """Run Docling on FUNSD and generate benchmark artifacts."""

    def __init__(
        self,
        dataset_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
        chart_dir: Path | str | None = None,
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
            else self.project_root / "outputs" / "benchmark_results" / "docling"
        )
        self.chart_dir = (
            Path(chart_dir)
            if chart_dir is not None
            else self.project_root / "outputs" / "charts" / "docling"
        )
        self._extractor = DoclingExtractor(output_root=self.project_root)
        self._artifact_cache: dict[Path, object] = {}
        self._result_cache: dict[Path, list] = {}

    def run(self, sample_size: int | None = None):
        """Run Docling on the FUNSD dataset and persist benchmark outputs."""
        inner = FunsdBenchmarkPipeline(
            dataset_dir=self.dataset_dir,
            output_dir=self.output_dir,
            chart_dir=self.chart_dir,
            ocr_runner=self._ocr_text,
            ocr_line_runner=self._ocr_lines,
        )
        summary = inner.run(sample_size=sample_size)
        self._rename_outputs()
        self._write_docling_report()
        self._write_comparison_report()
        return summary

    def _get_artifact(self, image_path: Path):
        """Convert an FUNSD image into a temporary PDF and cache the Docling artifact."""
        resolved = image_path.resolve()
        artifact = self._artifact_cache.get(resolved)
        if artifact is not None:
            return artifact

        with tempfile.TemporaryDirectory(prefix="docling_funsd_") as temp_dir:
            temp_pdf = Path(temp_dir) / f"{resolved.stem}.pdf"
            self._image_to_pdf(resolved, temp_pdf)
            artifact = self._extractor._convert_document(temp_pdf)  # noqa: SLF001
            results = self._extractor._build_page_results(artifact)  # noqa: SLF001
            self._extractor._save_outputs(artifact, results)  # noqa: SLF001
            self._artifact_cache[resolved] = artifact
            self._result_cache[resolved] = results
        return artifact

    def _get_results(self, image_path: Path):
        resolved = image_path.resolve()
        results = self._result_cache.get(resolved)
        if results is not None:
            return results
        artifact = self._get_artifact(image_path)
        self._result_cache[resolved] = self._extractor._build_page_results(artifact)  # noqa: SLF001
        return self._result_cache[resolved]

    def _ocr_text(self, image_path: Path) -> str:
        artifact = self._get_artifact(image_path)
        results = self._result_cache.get(image_path.resolve())
        if results is None:
            results = self._extractor._build_page_results(artifact)  # noqa: SLF001
        if not results:
            return ""
        return "\n\n".join(result.extracted_text for result in results).strip()

    def _ocr_lines(self, image_path: Path) -> list[dict[str, object]]:
        artifact = self._get_artifact(image_path)
        return self._build_line_payloads(artifact, image_path)

    def _build_line_payloads(self, artifact, image_path: Path) -> list[dict[str, object]]:
        """Build FUNSD-compatible line payloads from the first page of the artifact."""
        page_numbers = sorted(
            {
                int(page_no)
                for page_no in artifact.exported.get("pages", {}).keys()
                if str(page_no).isdigit()
            }
        )
        page_number = page_numbers[0] if page_numbers else 1
        page_entries = artifact.exported.get("pages", {})
        page_size = page_entries.get(str(page_number), {}).get("size", {})
        page_height = float(page_size.get("height", 0.0) or 0.0)
        text_items = [
            item
            for item in artifact.exported.get("texts", [])
            if self._extractor._item_page_number(item) == page_number  # noqa: SLF001
        ]

        line_payloads: list[dict[str, object]] = []
        for line_index, item in enumerate(text_items):
            text = self._extractor._normalize_text(self._extractor._item_text(item))  # noqa: SLF001
            if not text:
                continue
            bbox = self._extractor._item_bbox(item, page_height)  # noqa: SLF001
            if bbox is None:
                continue
            line_payloads.append(
                {
                    "text": text,
                    "box": [
                        [bbox.x0, bbox.y1],
                        [bbox.x1, bbox.y1],
                        [bbox.x1, bbox.y0],
                        [bbox.x0, bbox.y0],
                    ],
                    "confidence": 1.0,
                    "label": "text",
                    "raw_label": "text",
                    "reading_order": line_index,
                }
            )
        return line_payloads

    def _image_to_pdf(self, image_path: Path, pdf_path: Path) -> None:
        """Convert a FUNSD image to a one-page PDF for Docling."""
        with fitz.open() as doc:
            page = doc.new_page()
            page.insert_image(page.rect, filename=str(image_path))
            doc.save(str(pdf_path))

    def _rename_outputs(self) -> None:
        """Copy FUNSD-named benchmark files to Docling-specific filenames."""
        source_pairs = {
            "funsd_results.csv": "benchmark_results.csv",
            "funsd_summary.json": "benchmark_summary.json",
            "benchmark_observations.md": "benchmark_observations.md",
            "entity_results.csv": "entity_results.csv",
            "entity_summary.json": "entity_summary.json",
            "entity_observations.md": "entity_observations.md",
        }
        for source_name, target_name in source_pairs.items():
            source_path = self.output_dir / source_name
            target_path = self.output_dir / target_name
            if not source_path.exists():
                continue
            if source_name == target_name:
                text = source_path.read_text(encoding="utf-8")
                text = text.replace(
                    "# FUNSD OCR Benchmark Report",
                    "# Docling FUNSD Benchmark Report",
                )
                text = text.replace(
                    "FUNSD OCR Benchmark Report",
                    "Docling FUNSD Benchmark Report",
                )
                target_path.write_text(text, encoding="utf-8")
                continue
            shutil.copyfile(source_path, target_path)

        summary_path = self.output_dir / "benchmark_summary.json"
        if summary_path.exists():
            summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
            summary_payload["benchmark_name"] = "docling"
            summary_payload["extractor_name"] = "Docling"
            summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    def _write_docling_report(self) -> None:
        """Write a short Docling-specific benchmark summary."""
        summary_path = self.output_dir / "benchmark_summary.json"
        observations_path = self.output_dir / "benchmark_observations.md"
        if not summary_path.exists():
            return
        summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
        lines = [
            "# Docling FUNSD Benchmark Report",
            "",
            "## Overview",
            "",
            f"- Dataset size: {summary_payload.get('total_documents', 0)} documents",
            f"- Evaluated documents: {summary_payload.get('evaluated_documents', 0)}",
            f"- Output directory: `{self.output_dir}`",
            "",
            "## Runtime Notes",
            "",
            "- Docling runs as a local PDF conversion pipeline and preserves "
            "reading order, page structure, and tables when the source "
            "contains them.",
            "- On Windows, the Hugging Face cache needs symlink support "
            "disabled or Developer Mode/admin privileges enabled.",
            "- FUNSD images are converted to temporary PDFs before conversion "
            "so Docling can process them with its PDF pipeline.",
            "",
        ]
        if observations_path.exists():
            previous = observations_path.read_text(encoding="utf-8")
            tail = "\n".join(previous.splitlines()[1:])
            lines.append("## Detailed Findings")
            lines.append("")
            lines.append(tail)
            lines.append("")
        observations_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _write_comparison_report(self) -> None:
        """Compare Docling metrics against the existing PaddleOCR FUNSD benchmark."""
        docling_csv = self.output_dir / "benchmark_results.csv"
        paddle_csv = self.output_dir.parent / "funsd" / "funsd_results.csv"
        if not docling_csv.exists() or not paddle_csv.exists():
            return

        docling_df = pd.read_csv(docling_csv)
        paddle_df = pd.read_csv(paddle_csv)
        common = docling_df.merge(
            paddle_df,
            on="document_id",
            suffixes=("_docling", "_paddle"),
        )
        if common.empty:
            return

        common["cer_delta"] = common["cer_paddle"] - common["cer_docling"]
        common["wer_delta"] = common["wer_paddle"] - common["wer_docling"]
        common["f1_delta"] = common["token_f1_docling"] - common["token_f1_paddle"]
        common["precision_delta"] = (
            common["token_precision_docling"] - common["token_precision_paddle"]
        )
        common["recall_delta"] = common["token_recall_docling"] - common["token_recall_paddle"]
        common["overlap_delta"] = (
            common["token_overlap_accuracy_docling"] - common["token_overlap_accuracy_paddle"]
        )

        better_docling = common.sort_values(
            by=["f1_delta", "cer_delta", "document_id"],
            ascending=[False, False, True],
        ).head(5)
        better_paddle = common.sort_values(
            by=["f1_delta", "cer_delta", "document_id"],
            ascending=[True, True, True],
        ).head(5)

        report_lines = [
            "# Docling vs PaddleOCR on FUNSD",
            "",
            "## Average Comparison",
            "",
            f"- Docling average CER: {docling_df['cer'].mean():.6f}",
            f"- PaddleOCR average CER: {paddle_df['cer'].mean():.6f}",
            f"- Docling average WER: {docling_df['wer'].mean():.6f}",
            f"- PaddleOCR average WER: {paddle_df['wer'].mean():.6f}",
            f"- Docling average Token F1: {docling_df['token_f1'].mean():.6f}",
            f"- PaddleOCR average Token F1: {paddle_df['token_f1'].mean():.6f}",
            "",
            "## Reading Order and Structure",
            "",
            "- Docling tends to preserve document flow as structured markdown, "
            "which helps reading order when text is grouped into blocks and "
            "sections.",
            "- PaddleOCR typically emits flatter line-by-line text, which can "
            "be more sensitive to layout reordering but may be simpler on "
            "sparse scanned pages.",
            "- Docling is better suited to table and form structure "
            "preservation when its layout model recognizes the regions "
            "correctly.",
            "",
            "## Documents Where Docling Performs Better",
            "",
            _comparison_table(better_docling),
            "",
            "## Documents Where PaddleOCR Performs Better",
            "",
            _comparison_table(better_paddle),
            "",
            "## Interpretation",
            "",
            "- Docling is a stronger fit when structure preservation and "
            "markdown-like document reconstruction matter.",
            "- PaddleOCR can remain competitive when the source is a simple "
            "scan and the main goal is raw text capture.",
        ]
        comparison_path = self.output_dir / "docling_vs_paddleocr.md"
        comparison_path.write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")


def _comparison_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No overlapping documents available._"
    rows = [
        "| Document | Docling CER | Paddle CER | CER Δ | Docling Token F1 | "
        "Paddle Token F1 | F1 Δ |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in frame.iterrows():
        rows.append(
            "| "
            f"{row['document_id']} | {row['cer_docling']:.6f} | {row['cer_paddle']:.6f} | "
            f"{row['cer_delta']:.6f} | {row['token_f1_docling']:.6f} | "
            f"{row['token_f1_paddle']:.6f} | {row['f1_delta']:.6f} |"
        )
    return "\n".join(rows)
