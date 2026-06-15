"""Run Tesseract, PaddleOCR, and Docling on representative RVL-CDIP documents.

Captures extracted text samples for a qualitative side-by-side review across
invoice, form, resume, handwritten, and specification categories.
"""

from __future__ import annotations

import json
from pathlib import Path

# Import order matters on Windows: torch must load before paddle/docling
# to avoid a DLL search-path conflict (see ui/app.py for the same pattern).
import torch  # noqa: F401

from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor
from pdf_extraction_benchmark.extractors.tesseract.extractor import TesseractExtractor
from pdf_extraction_benchmark.utils.logger import configure_logging, get_logger

CATEGORIES = ["invoice", "form", "resume", "handwritten", "specification"]
SAMPLE_CHARS = 600


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    configure_logging(project_root / "outputs" / "logs")
    logger = get_logger(__name__)

    extractors = {
        "Tesseract": TesseractExtractor(),
        "PaddleOCR": PaddleocrExtractor(),
        "Docling": DoclingExtractor(output_root=project_root),
    }

    results: dict[str, dict[str, str]] = {}
    for category in CATEGORIES:
        pdf_path = project_root / "data" / "raw" / "rvl_cdip" / category / f"{category}_01.pdf"
        logger.info("Processing %s", pdf_path.name)
        results[category] = {"pdf_path": str(pdf_path)}
        for name, extractor in extractors.items():
            try:
                pages = extractor.extract(pdf_path)
                text = "\n".join(page.extracted_text for page in pages).strip()
                results[category][name] = text[:SAMPLE_CHARS]
                results[category][f"{name}_total_chars"] = str(len(text))
            except Exception as exc:  # noqa: BLE001
                logger.warning("%s failed on %s: %s", name, pdf_path.name, exc)
                results[category][name] = f"<error: {exc}>"
                results[category][f"{name}_total_chars"] = "0"

    output_dir = project_root / "outputs" / "benchmark_results" / "tesseract_evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "qualitative_samples.json"
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info("Qualitative samples written to %s", output_path)


if __name__ == "__main__":
    main()
