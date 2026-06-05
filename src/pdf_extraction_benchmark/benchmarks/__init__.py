"""Benchmark package."""

from __future__ import annotations

from pdf_extraction_benchmark.benchmarks.funsd.benchmark import (
    FunsdBenchmarkPipeline,
    FunsdBenchmarkSummary,
    FunsdDocumentResult,
    MetricStatistics,
    RankedDocument,
)
from pdf_extraction_benchmark.benchmarks.funsd.entity import (
    EntityExample,
    FunsdEntityResult,
    FunsdEntitySummary,
    RankedEntityDocument,
)
from pdf_extraction_benchmark.benchmarks.surya.benchmark import SuryaBenchmarkPipeline

__all__ = [
    "FunsdBenchmarkPipeline",
    "FunsdBenchmarkSummary",
    "FunsdDocumentResult",
    "MetricStatistics",
    "RankedDocument",
    "EntityExample",
    "FunsdEntityResult",
    "FunsdEntitySummary",
    "RankedEntityDocument",
    "SuryaBenchmarkPipeline",
]
