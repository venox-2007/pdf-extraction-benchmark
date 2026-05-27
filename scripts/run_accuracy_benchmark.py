"""Run accuracy benchmark and store output."""

from __future__ import annotations

from pathlib import Path

from pdf_extraction_benchmark.benchmarks.accuracy.benchmark import AccuracyBenchmark
from pdf_extraction_benchmark.utils.logger import configure_logging, get_logger


def main() -> None:
    """Execute accuracy benchmark placeholder script."""
    project_root = Path(__file__).resolve().parents[1]
    configure_logging(project_root / "outputs" / "logs")
    logger = get_logger(__name__)

    result = AccuracyBenchmark().evaluate()
    out = project_root / "outputs" / "benchmarks" / "accuracy.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"{result.dimension}:{result.score}\n", encoding="utf-8")
    logger.info("Accuracy benchmark output saved to %s", out)


if __name__ == "__main__":
    main()
