"""Compare OpenDataLoader standard vs hybrid mode against PaddleOCR and Docling.

One-off driver around the existing RvlCdipBenchmarkPipeline, reusing the same
48-document sample (3 docs/category) as outputs/benchmark_results/rvl_cdip_sample48.
Adds an "OpenDataLoader Hybrid" entry via a small BaseExtractor wrapper that
passes a `hybrid_url` (from the optional Docling/rapidocr hybrid server) into
OpendataloaderExtractor.extract().
"""

from __future__ import annotations

from pathlib import Path

# Import order matters on Windows: torch must load before paddle/docling
# to avoid a DLL search-path conflict (see ui/app.py for the same pattern).
import torch  # noqa: F401

from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor
from pdf_extraction_benchmark.extractors.opendataloader.extractor import OpendataloaderExtractor
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor
from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor
from pdf_extraction_benchmark.models.extraction_result import ExtractionResult
from pdf_extraction_benchmark.utils.logger import configure_logging, get_logger
from pdf_extraction_benchmark.utils.opendataloader_hybrid import ensure_hybrid_server


class OpendataloaderHybridExtractor(BaseExtractor):
    """OpenDataLoader extractor with the Docling/rapidocr hybrid backend enabled."""

    tool_name = "opendataloader_hybrid"

    def __init__(self, hybrid_url: str) -> None:
        self._delegate = OpendataloaderExtractor()
        self._hybrid_url = hybrid_url

    def extract(self, pdf_path: Path, output_dir: Path | None = None) -> list[ExtractionResult]:
        return self._delegate.extract(pdf_path, output_dir=output_dir, hybrid_url=self._hybrid_url)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    configure_logging(project_root / "outputs" / "logs")
    logger = get_logger(__name__)

    logger.info("Ensuring OpenDataLoader hybrid server is running...")
    hybrid_url = ensure_hybrid_server()
    logger.info("Hybrid server ready at %s", hybrid_url)

    extractors = {
        "OpenDataLoader": OpendataloaderExtractor(),
        "OpenDataLoader Hybrid": OpendataloaderHybridExtractor(hybrid_url=hybrid_url),
        "PaddleOCR": PaddleocrExtractor(),
        "Docling": DoclingExtractor(output_root=project_root),
    }

    pipeline = RvlCdipBenchmarkPipeline(
        output_dir=project_root / "outputs" / "benchmark_results" / "rvl_cdip_hybrid_comparison",
        extractors=extractors,
    )
    summary = pipeline.run(sample_size_per_category=3)

    logger.info(
        "RVL-CDIP hybrid comparison complete: %s categories, %s documents",
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
