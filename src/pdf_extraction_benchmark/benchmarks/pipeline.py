"""Benchmark orchestration pipeline (placeholder)."""

from __future__ import annotations

from pathlib import Path

from pdf_extraction_benchmark.benchmarks.accuracy.benchmark import AccuracyBenchmark
from pdf_extraction_benchmark.benchmarks.latency.benchmark import LatencyBenchmark


class BenchmarkPipeline:
    """Run selected benchmark dimensions over extraction outputs."""

    def run(self, output_dir: Path) -> dict[str, float]:
        """Run placeholder benchmarks and return summarized scores."""
        output_dir.mkdir(parents=True, exist_ok=True)
        accuracy = AccuracyBenchmark().evaluate().score
        latency = LatencyBenchmark().evaluate().score
        return {"accuracy": accuracy, "latency": latency}
