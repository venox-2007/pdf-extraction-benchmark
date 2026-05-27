\"\"\"latency benchmark implementation (placeholder).\"\"\"

from __future__ import annotations

from pdf_extraction_benchmark.benchmarks.base import BenchmarkResult


class LatencyBenchmark:
    \"\"\"Compute the latency score for benchmark runs.\"\"\"

    def evaluate(self) -> BenchmarkResult:
        \"\"\"Return a placeholder benchmark score.\"\"\"
        return BenchmarkResult(dimension=\"latency\", score=0.0, details={\"status\": \"not_implemented\"})
