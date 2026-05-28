"""PyMuPDF extractor adapter implementation."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import fitz

from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor
from pdf_extraction_benchmark.models.extraction_result import (
    BoundingBox,
    ExtractionMetadata,
    ExtractionResult,
)
from pdf_extraction_benchmark.utils.logger import get_logger


class PymupdfExtractor(BaseExtractor):
    """Extractor adapter for native text extraction using PyMuPDF."""

    tool_name = "pymupdf"

    def __init__(self) -> None:
        """Initialize extractor logger."""
        self.logger = get_logger(__name__)

    def extract(self, pdf_path: Path) -> list[ExtractionResult]:
        """Extract page-wise text and blocks into standardized results."""
        pdf_path = pdf_path.resolve()
        if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
            raise FileNotFoundError(f"Invalid PDF path: {pdf_path}")

        extraction_ts = datetime.now(UTC).isoformat()
        results: list[ExtractionResult] = []

        try:
            with fitz.open(pdf_path) as doc:
                total_pages = len(doc)
                raw_metadata = self._normalize_metadata(doc.metadata or {})

                for page_idx in range(total_pages):
                    page = doc.load_page(page_idx)
                    page_number = page_idx + 1
                    page_text = page.get_text("text", sort=True).strip()
                    blocks = page.get_text("blocks", sort=True)

                    bounding_boxes: list[BoundingBox] = []
                    text_blocks: list[dict[str, Any]] = []
                    for block_idx, block in enumerate(blocks):
                        if not isinstance(block, (tuple, list)) or len(block) < 5:
                            continue

                        x0, y0, x1, y1 = block[0], block[1], block[2], block[3]
                        block_text = str(block[4] or "").strip()
                        bbox = self._to_bbox(x0=x0, y0=y0, x1=x1, y1=y1)
                        if bbox is not None:
                            bounding_boxes.append(bbox)
                        if block_text:
                            text_blocks.append(
                                {
                                    "block_index": block_idx,
                                    "text": block_text,
                                    "bbox": [float(x0), float(y0), float(x1), float(y1)],
                                }
                            )

                    image_count = len(page.get_images(full=True))
                    word_count = len(page_text.split())
                    ocr_required = word_count < 20 and image_count > 0
                    status = "ocr_required" if ocr_required else "ok"

                    results.append(
                        ExtractionResult(
                            tool_name=self.tool_name,
                            page_number=page_number,
                            extracted_text=page_text,
                            tables=[],
                            bounding_boxes=bounding_boxes,
                            confidence_scores=[],
                            metadata=ExtractionMetadata(
                                source_file=pdf_path.name,
                                extra={
                                    "status": status,
                                    "extractor": self.tool_name,
                                    "ocr_supported": False,
                                    "ocr_required": ocr_required,
                                    "layout_preservation": "basic",
                                    "extraction_timestamp": extraction_ts,
                                    "total_page_count": total_pages,
                                    "word_count": word_count,
                                    "image_count": image_count,
                                    "text_blocks": text_blocks,
                                    "pdf_metadata": raw_metadata,
                                },
                            ),
                        )
                    )
        except Exception as exc:  # pragma: no cover - library/runtime errors
            self.logger.exception("PyMuPDF extraction failed for %s", pdf_path)
            raise RuntimeError(f"PyMuPDF extraction failed: {exc}") from exc

        return results

    def _to_bbox(self, x0: Any, y0: Any, x1: Any, y1: Any) -> BoundingBox | None:
        """Convert coordinate values to BoundingBox."""
        try:
            return BoundingBox(x0=float(x0), y0=float(y0), x1=float(x1), y1=float(y1))
        except (TypeError, ValueError):
            return None

    def _normalize_metadata(self, value: dict[str, Any]) -> dict[str, str]:
        """Normalize PDF metadata values into string dictionary."""
        normalized: dict[str, str] = {}
        for key, raw in value.items():
            if raw is None:
                continue
            text = str(raw).strip()
            if text:
                normalized[str(key)] = text
        return normalized


