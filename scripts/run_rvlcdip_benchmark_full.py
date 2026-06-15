"""Run the RVL-CDIP benchmark on the full subset with all reliable extractors.

This is a one-off driver around the existing RvlCdipBenchmarkPipeline:
PyMuPDF and OpenDataLoader (registered by default) plus PaddleOCR and Docling
(OCR-capable extractors already used elsewhere in the project), since the
RVL-CDIP subset is entirely scanned/image-based.
"""

from __future__ import annotations

from pathlib import Path

# Import order matters on Windows: torch must load before paddle/docling
# to avoid a DLL search-path conflict (see ui/app.py for the same pattern).
import torch  # noqa: F401

from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import (
    DEFAULT_EXTRACTORS,
    RvlCdipBenchmarkPipeline,
)
from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor
from pdf_extraction_benchmark.utils.logger import configure_logging, get_logger


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    configure_logging(project_root / "outputs" / "logs")
    logger = get_logger(__name__)

    extractors = {name: cls() for name, cls in DEFAULT_EXTRACTORS.items()}
    extractors["PaddleOCR"] = PaddleocrExtractor()
    extractors["Docling"] = DoclingExtractor(output_root=project_root)

    pipeline = RvlCdipBenchmarkPipeline(extractors=extractors)
    summary = pipeline.run()

    logger.info(
        "RVL-CDIP full benchmark complete: %s categories, %s documents",
        len(summary.categories),
        summary.total_documents,
    )
    for extractor_summary in summary.extractor_summaries.values():
        logger.info(
            "%s: success rate %.4f, mean latency %.2f ms, mean words %.2f",
            extractor_summary.extractor,
            extractor_summary.success_rate,
            extractor_summary.latency_ms.mean,
            extractor_summary.word_count.mean,
        )
    logger.info("Outputs written to %s", summary.output_dir)


if __name__ == "__main__":
    main()
