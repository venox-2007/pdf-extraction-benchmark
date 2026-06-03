"""Run the FUNSD OCR benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline
from pdf_extraction_benchmark.utils.logger import configure_logging, get_logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the FUNSD OCR benchmark.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=None,
        help="Path to the FUNSD dataset root.",
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
        help="Optional limit for a small validation run before the full benchmark.",
    )
    return parser.parse_args()


def main() -> None:
    """Execute the FUNSD benchmark."""
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    configure_logging(project_root / "outputs" / "logs")
    logger = get_logger(__name__)

    pipeline = FunsdBenchmarkPipeline(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
    )
    summary = pipeline.run(sample_size=args.sample_size)
    logger.info(
        "FUNSD benchmark complete: %s docs, average CER %.6f, average WER %.6f",
        summary.total_documents,
        summary.average_cer,
        summary.average_wer,
    )
    logger.info("Outputs written to %s", summary.output_dir)


if __name__ == "__main__":
    main()
