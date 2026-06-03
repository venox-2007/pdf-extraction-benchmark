"""FUNSD benchmark package."""

from __future__ import annotations

from pdf_extraction_benchmark.benchmarks.funsd.benchmark import (
    FunsdBenchmarkPipeline,
    FunsdBenchmarkSummary,
    FunsdDocumentResult,
    MetricStatistics,
    RankedDocument,
)

__all__ = [
    "FunsdBenchmarkPipeline",
    "FunsdDocumentResult",
    "FunsdBenchmarkSummary",
    "MetricStatistics",
    "RankedDocument",
]
