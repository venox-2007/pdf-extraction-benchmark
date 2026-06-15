"""Run the FUNSD OCR accuracy benchmark using Tesseract.

Uses the existing FunsdBenchmarkPipeline (CER/WER/token metrics against
ground truth) with a Tesseract-backed `ocr_runner`, so results are directly
comparable to the existing PaddleOCR (`outputs/benchmark_results/funsd`) and
Docling (`outputs/benchmark_results/docling`) FUNSD results.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytesseract
from PIL import Image

from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline
from pdf_extraction_benchmark.extractors.tesseract.extractor import TesseractExtractor
from pdf_extraction_benchmark.utils.logger import configure_logging, get_logger

# Instantiating configures pytesseract's tesseract_cmd if it is not on PATH.
TesseractExtractor()


def _tesseract_ocr_runner(image_path: Path) -> str:
    image = Image.open(image_path).convert("RGB")
    return pytesseract.image_to_string(image)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the Tesseract FUNSD benchmark.")
    parser.add_argument("--dataset-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--sample-size", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    """Execute the Tesseract FUNSD benchmark."""
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    configure_logging(project_root / "outputs" / "logs")
    logger = get_logger(__name__)

    default_output_dir = project_root / "outputs" / "benchmark_results" / "funsd_tesseract"
    pipeline = FunsdBenchmarkPipeline(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir or default_output_dir,
        ocr_runner=_tesseract_ocr_runner,
    )
    summary = pipeline.run(sample_size=args.sample_size)
    logger.info(
        "Tesseract FUNSD benchmark complete: %s docs, average CER %.6f, average WER %.6f",
        summary.total_documents,
        summary.average_cer,
        summary.average_wer,
    )
    logger.info("Outputs written to %s", summary.output_dir)


if __name__ == "__main__":
    main()
