"""Run the RVL-CDIP extraction robustness benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
from pdf_extraction_benchmark.utils.logger import configure_logging, get_logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the RVL-CDIP extraction robustness benchmark.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=None,
        help="Path to the RVL-CDIP category subset root (default: data/raw/rvl_cdip).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where benchmark outputs will be written.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Optional limit on the number of documents per category for a quick run.",
    )
    return parser.parse_args()


def main() -> None:
    """Execute the RVL-CDIP benchmark."""
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    configure_logging(project_root / "outputs" / "logs")
    logger = get_logger(__name__)

    pipeline = RvlCdipBenchmarkPipeline(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
    )
    summary = pipeline.run(sample_size_per_category=args.sample_size)
    logger.info(
        "RVL-CDIP benchmark complete: %s categories, %s documents",
        len(summary.categories),
        summary.total_documents,
    )
    for extractor_summary in summary.extractor_summaries.values():
        logger.info(
            "%s: success rate %.4f, mean latency %.2f ms",
            extractor_summary.extractor,
            extractor_summary.success_rate,
            extractor_summary.latency_ms.mean,
        )
    logger.info("Outputs written to %s", summary.output_dir)


if __name__ == "__main__":
    main()
