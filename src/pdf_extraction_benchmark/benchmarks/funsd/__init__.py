"""FUNSD benchmark package."""

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

__all__ = [
    "FunsdBenchmarkPipeline",
    "FunsdDocumentResult",
    "FunsdBenchmarkSummary",
    "MetricStatistics",
    "RankedDocument",
    "EntityExample",
    "FunsdEntityResult",
    "FunsdEntitySummary",
    "RankedEntityDocument",
]
