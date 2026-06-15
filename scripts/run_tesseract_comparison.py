"""Compare Tesseract OCR against PaddleOCR and Docling on an RVL-CDIP sample.

One-off driver around the existing RvlCdipBenchmarkPipeline, using a small
sample (default 2 docs/category) to report extraction time, character count,
word count, bounding box count, and success rate for each extractor.
"""

from __future__ import annotations

from pathlib import Path

# Import order matters on Windows: torch must load before paddle/docling
# to avoid a DLL search-path conflict (see ui/app.py for the same pattern).
import torch  # noqa: F401

from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor
from pdf_extraction_benchmark.extractors.tesseract.extractor import TesseractExtractor
from pdf_extraction_benchmark.utils.logger import configure_logging, get_logger


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    configure_logging(project_root / "outputs" / "logs")
    logger = get_logger(__name__)

    extractors = {
        "Tesseract": TesseractExtractor(),
        "PaddleOCR": PaddleocrExtractor(),
        "Docling": DoclingExtractor(output_root=project_root),
    }

    pipeline = RvlCdipBenchmarkPipeline(
        output_dir=project_root / "outputs" / "benchmark_results" / "rvl_cdip_tesseract_comparison",
        extractors=extractors,
    )
    summary = pipeline.run(sample_size_per_category=2)

    logger.info(
        "Tesseract comparison complete: %s categories, %s documents",
        len(summary.categories),
        summary.total_documents,
    )
    for extractor_summary in summary.extractor_summaries.values():
        logger.info(
            "%s: success rate %.4f, mean latency %.2f ms, mean chars %.2f, "
            "mean words %.2f, mean bboxes %.2f",
            extractor_summary.extractor,
            extractor_summary.success_rate,
            extractor_summary.latency_ms.mean,
            extractor_summary.char_count.mean,
            extractor_summary.word_count.mean,
            extractor_summary.bbox_count.mean,
        )
    logger.info("Outputs written to %s", summary.output_dir)


if __name__ == "__main__":
    main()
