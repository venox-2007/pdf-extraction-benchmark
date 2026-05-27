"""PDF type classifier for native/scanned/mixed detection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(slots=True)
class PdfTypeClassification:
    """Structured output for PDF type detection."""

    pdf_type: str
    confidence: float
    reason: str
    page_count: int
    text_pages: int
    image_heavy_pages: int


class PdfTypeClassifier:
    """Classify PDFs as native, scanned, or mixed using lightweight heuristics."""

    def classify(self, pdf_path: Path) -> PdfTypeClassification:
        """Classify a PDF from page-level text and image density signals."""
        with fitz.open(pdf_path) as doc:
            page_count = len(doc)
            if page_count == 0:
                return PdfTypeClassification(
                    pdf_type="scanned",
                    confidence=0.6,
                    reason="No pages found in document.",
                    page_count=0,
                    text_pages=0,
                    image_heavy_pages=0,
                )

            text_pages = 0
            image_heavy_pages = 0

            for page in doc:
                text = page.get_text("text").strip()
                images = page.get_images(full=True)
                words = len(text.split())
                has_meaningful_text = words >= 20
                if has_meaningful_text:
                    text_pages += 1
                if images and not has_meaningful_text:
                    image_heavy_pages += 1

        text_ratio = text_pages / page_count
        image_ratio = image_heavy_pages / page_count

        if text_ratio >= 0.8:
            confidence = self._clamp_confidence(0.85 + min(text_ratio - 0.8, 0.2))
            return PdfTypeClassification(
                pdf_type="native",
                confidence=confidence,
                reason="Most pages contain extractable text.",
                page_count=page_count,
                text_pages=text_pages,
                image_heavy_pages=image_heavy_pages,
            )

        if text_ratio <= 0.2 and image_ratio >= 0.5:
            confidence = self._clamp_confidence(0.85 + min(image_ratio - 0.5, 0.15))
            return PdfTypeClassification(
                pdf_type="scanned",
                confidence=confidence,
                reason="No extractable text detected on most pages; image-heavy structure observed.",
                page_count=page_count,
                text_pages=text_pages,
                image_heavy_pages=image_heavy_pages,
            )

        return PdfTypeClassification(
            pdf_type="mixed",
            confidence=self._clamp_confidence(0.75),
            reason="Document contains both text-rich and image-heavy pages.",
            page_count=page_count,
            text_pages=text_pages,
            image_heavy_pages=image_heavy_pages,
        )

    def _clamp_confidence(self, value: float) -> float:
        """Clamp confidence to [0.0, 1.0] and round for UI display."""
        return round(min(1.0, max(0.0, value)), 2)
