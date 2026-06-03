"""FUNSD benchmark package."""

from __future__ import annotations

from pdf_extraction_benchmark.benchmarks.funsd.analysis import (
    FunsdComparisonAnalyzer,
    FunsdComparisonRow,
)
from pdf_extraction_benchmark.benchmarks.funsd.benchmark import (
    FunsdBenchmarkPipeline,
    FunsdBenchmarkSummary,
    FunsdDocumentResult,
)

__all__ = [
    "FunsdBenchmarkPipeline",
    "FunsdDocumentResult",
    "FunsdBenchmarkSummary",
    "FunsdComparisonAnalyzer",
    "FunsdComparisonRow",
]
