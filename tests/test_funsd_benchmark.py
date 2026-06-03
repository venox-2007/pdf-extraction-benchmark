"""Tests for the FUNSD benchmark pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline


def test_ground_truth_parser_uses_text_and_words(tmp_path: Path) -> None:
    """Ensure FUNSD parsing uses entry text and word fallback."""
    annotation_path = tmp_path / "sample.json"
    annotation_path.write_text(
        json.dumps(
            {
                "form": [
                    {"text": "Invoice", "words": [{"text": "Invoice"}]},
                    {"text": "", "words": [{"text": "PO"}, {"text": "Number"}]},
                    {"text": "  Total\nAmount  ", "words": []},
                ]
            }
        ),
        encoding="utf-8",
    )

    pipeline = FunsdBenchmarkPipeline(
        dataset_dir=tmp_path,
        output_dir=tmp_path / "out",
        ocr_runner=lambda _path: "Invoice PO Number Total Amount",
    )
    parsed = pipeline._extract_ground_truth_text(annotation_path)
    assert parsed == "Invoice\nPO Number\nTotal Amount"


def test_run_writes_outputs(tmp_path: Path) -> None:
    """Ensure benchmark writes CSV, JSON, and markdown output files."""
    images_dir = tmp_path / "images"
    annotations_dir = tmp_path / "annotations"
    images_dir.mkdir()
    annotations_dir.mkdir()

    (images_dir / "doc1.png").write_bytes(b"")
    (annotations_dir / "doc1.json").write_text(
        json.dumps(
            {
                "form": [
                    {
                        "text": "Hello world",
                        "words": [{"text": "Hello"}, {"text": "world"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    pipeline = FunsdBenchmarkPipeline(
        dataset_dir=tmp_path,
        output_dir=tmp_path / "out",
        ocr_runner=lambda _path: "Hello world",
    )
    summary = pipeline.run()

    assert summary.total_documents == 1
    assert summary.average_cer == 0.0
    assert summary.average_wer == 0.0
    assert (tmp_path / "out" / "funsd_results.csv").exists()
    assert (tmp_path / "out" / "funsd_summary.json").exists()
    assert (tmp_path / "out" / "benchmark_observations.md").exists()


def test_metrics_match_edit_distance() -> None:
    """Ensure CER and WER use normalized Levenshtein distance."""
    assert FunsdBenchmarkPipeline.character_error_rate("abc", "adc") == 1 / 3
    assert FunsdBenchmarkPipeline.word_error_rate("hello world", "hello there") == 1 / 2
