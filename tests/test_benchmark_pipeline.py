"""Tests for benchmark pipeline — real pipeline smoke tests."""

from __future__ import annotations

from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline
from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline


def test_funsd_pipeline_importable() -> None:
    """FunsdBenchmarkPipeline is importable and has required class methods."""
    assert hasattr(FunsdBenchmarkPipeline, "character_error_rate")
    assert hasattr(FunsdBenchmarkPipeline, "word_error_rate")


def test_rvl_cdip_pipeline_importable() -> None:
    """RvlCdipBenchmarkPipeline is importable."""
    assert RvlCdipBenchmarkPipeline is not None
