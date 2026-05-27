"""Tests for benchmark pipeline behavior."""

from __future__ import annotations

from pathlib import Path

from pdf_extraction_benchmark.benchmarks.pipeline import BenchmarkPipeline


def test_benchmark_pipeline(tmp_path: Path) -> None:
    """Ensure pipeline returns expected dimension keys."""
    scores = BenchmarkPipeline().run(tmp_path)
    assert "accuracy" in scores
    assert "latency" in scores
