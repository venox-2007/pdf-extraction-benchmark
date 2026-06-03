"""Generate a FUNSD reading-order validation report from saved benchmark results."""

from __future__ import annotations

import argparse
from pathlib import Path

from pdf_extraction_benchmark.benchmarks.funsd.analysis import FunsdComparisonAnalyzer
from pdf_extraction_benchmark.utils.logger import configure_logging, get_logger


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Analyze FUNSD benchmark ordering effects.")
    parser.add_argument(
        "--results-csv",
        type=Path,
        default=Path("outputs/benchmark_results/funsd/funsd_results.csv"),
        help="Path to the saved FUNSD benchmark CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/benchmark_results/funsd"),
        help="Directory where the analysis report will be written.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=10,
        help="Number of random documents to include in the comparison report.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the comparison report generation."""
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    configure_logging(project_root / "outputs" / "logs")
    logger = get_logger(__name__)

    analyzer = FunsdComparisonAnalyzer(args.results_csv, args.output_dir)
    payload = analyzer.run(sample_size=args.sample_size, seed=args.seed)
    logger.info(
        "FUNSD comparison report written for %s sampled documents to %s",
        payload["sample_size"],
        args.output_dir,
    )


if __name__ == "__main__":
    main()
