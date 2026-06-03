"""FUNSD benchmark package."""

from __future__ import annotations

from pdf_extraction_benchmark.benchmarks.funsd.benchmark import (
    FunsdBenchmarkPipeline,
    FunsdDocumentResult,
    FunsdBenchmarkSummary,
)

__all__ = [
    "FunsdBenchmarkPipeline",
    "FunsdDocumentResult",
    "FunsdBenchmarkSummary",
]
