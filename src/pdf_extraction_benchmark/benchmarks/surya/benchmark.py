"""Surya FUNSD benchmark pipeline and comparison report generation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline
from pdf_extraction_benchmark.extractors.surya.runtime import (
    SuryaDocumentArtifact,
    page_text,
    page_to_line_payloads,
    run_document,
)


class SuryaBenchmarkPipeline:
    """Run Surya on FUNSD and generate benchmark artifacts."""

    def __init__(
        self,
        dataset_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
        chart_dir: Path | str | None = None,
        backend: str | None = None,
        render_dpi: int = 192,
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
            else self.project_root / "outputs" / "benchmark_results" / "surya"
        )
        self.chart_dir = (
            Path(chart_dir)
            if chart_dir is not None
            else self.project_root / "outputs" / "charts" / "surya"
        )
        self.backend = backend
        self.render_dpi = render_dpi
        self._artifact_cache: dict[Path, SuryaDocumentArtifact] = {}

    def run(self, sample_size: int | None = None):
        """Run Surya on the FUNSD dataset and persist benchmark outputs."""
        inner = FunsdBenchmarkPipeline(
            dataset_dir=self.dataset_dir,
            output_dir=self.output_dir,
            chart_dir=self.chart_dir,
            ocr_runner=self._ocr_text,
            ocr_line_runner=self._ocr_lines,
        )
        summary = inner.run(sample_size=sample_size)
        self._rename_outputs()
        self._write_surya_report()
        self._write_comparison_report()
        return summary

    def _get_artifact(self, image_path: Path) -> SuryaDocumentArtifact:
        resolved = image_path.resolve()
        artifact = self._artifact_cache.get(resolved)
        if artifact is None:
            artifact = run_document(
                resolved,
                backend=self.backend,
                render_dpi=self.render_dpi,
            )
            self._artifact_cache[resolved] = artifact
        return artifact

    def _ocr_text(self, image_path: Path) -> str:
        artifact = self._get_artifact(image_path)
        if not artifact.pages:
            return ""
        return "\n\n".join(page_text(page) for page in artifact.pages).strip()

    def _ocr_lines(self, image_path: Path) -> list[dict[str, object]]:
        artifact = self._get_artifact(image_path)
        if not artifact.pages:
            return []
        return page_to_line_payloads(artifact.pages[0])

    def _rename_outputs(self) -> None:
        """Copy FUNSD-named benchmark files to Surya-specific filenames."""
        source_pairs = {
            "funsd_results.csv": "benchmark_results.csv",
            "funsd_summary.json": "benchmark_summary.json",
            "benchmark_observations.md": "benchmark_observations.md",
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
                    "# Surya FUNSD Benchmark Report",
                )
                text = text.replace(
                    "FUNSD OCR Benchmark Report",
                    "Surya FUNSD Benchmark Report",
                )
                target_path.write_text(text, encoding="utf-8")
                continue
            shutil.copyfile(source_path, target_path)

        summary_path = self.output_dir / "benchmark_summary.json"
        if summary_path.exists():
            summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
            summary_payload["benchmark_name"] = "surya"
            summary_payload["extractor_name"] = "Surya"
            summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    def _write_surya_report(self) -> None:
        """Write a short Surya-specific benchmark summary."""
        summary_path = self.output_dir / "benchmark_summary.json"
        observations_path = self.output_dir / "benchmark_observations.md"
        if not summary_path.exists():
            return
        summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
        lines = [
            "# Surya FUNSD Benchmark Report",
            "",
            "## Overview",
            "",
            f"- Dataset size: {summary_payload.get('total_documents', 0)} documents",
            f"- Evaluated documents: {summary_payload.get('evaluated_documents', 0)}",
            f"- Output directory: `{self.output_dir}`",
            "",
            "## Runtime Notes",
            "",
            (
                "- Surya uses a layout-aware VLM backend and requires either a "
                "local `llama-server` binary or a configured vLLM endpoint."
            ),
            (
                "- CPU-only setups use the llama.cpp path; GPU setups prefer vLLM "
                "when Docker is available."
            ),
            (
                "- The extractor records page text, bounding boxes, average confidence, "
                "and layout summaries in `outputs/surya/<document_name>/`."
            ),
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
        """Compare Surya metrics against the existing PaddleOCR FUNSD benchmark."""
        surya_csv = self.output_dir / "benchmark_results.csv"
        paddle_csv = self.output_dir.parent / "funsd" / "funsd_results.csv"
        if not surya_csv.exists() or not paddle_csv.exists():
            return

        surya_df = pd.read_csv(surya_csv)
        paddle_df = pd.read_csv(paddle_csv)
        common = surya_df.merge(
            paddle_df,
            on="document_id",
            suffixes=("_surya", "_paddle"),
        )
        if common.empty:
            return

        common["cer_delta"] = common["cer_paddle"] - common["cer_surya"]
        common["wer_delta"] = common["wer_paddle"] - common["wer_surya"]
        common["f1_delta"] = common["token_f1_surya"] - common["token_f1_paddle"]

        better_surya = common.sort_values(
            by=["f1_delta", "cer_delta", "document_id"],
            ascending=[False, False, True],
        ).head(5)
        better_paddle = common.sort_values(
            by=["f1_delta", "cer_delta", "document_id"],
            ascending=[True, True, True],
        ).head(5)

        report_lines = [
            "# Surya vs PaddleOCR on FUNSD",
            "",
            "## Average Comparison",
            "",
            f"- Surya average CER: {surya_df['cer'].mean():.6f}",
            f"- PaddleOCR average CER: {paddle_df['cer'].mean():.6f}",
            f"- Surya average WER: {surya_df['wer'].mean():.6f}",
            f"- PaddleOCR average WER: {paddle_df['wer'].mean():.6f}",
            f"- Surya average Token F1: {surya_df['token_f1'].mean():.6f}",
            f"- PaddleOCR average Token F1: {paddle_df['token_f1'].mean():.6f}",
            "",
            "## Documents Where Surya Performs Better",
            "",
        _comparison_table(better_surya),
            "",
            "## Documents Where PaddleOCR Performs Better",
            "",
        _comparison_table(better_paddle),
            "",
            "## Interpretation",
            "",
            (
                "- Surya tends to win when layout-aware grouping is the dominant factor, "
                "especially on structured forms where reading order matters."
            ),
            (
                "- PaddleOCR remains competitive on cleaner, smaller text regions and "
                "can be more stable when the Surya backend is constrained by runtime setup."
            ),
        ]
        comparison_path = self.output_dir / "surya_vs_paddleocr.md"
        comparison_path.write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")


def _comparison_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No overlapping documents available._"
    rows = [
        "| Document | Surya CER | Paddle CER | CER Δ | Surya Token F1 | Paddle Token F1 | F1 Δ |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in frame.iterrows():
        rows.append(
            "| "
            f"{row['document_id']} | {row['cer_surya']:.6f} | {row['cer_paddle']:.6f} | "
            f"{row['cer_delta']:.6f} | {row['token_f1_surya']:.6f} | "
            f"{row['token_f1_paddle']:.6f} | {row['f1_delta']:.6f} |"
        )
    return "\n".join(rows)
