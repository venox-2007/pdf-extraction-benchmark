"""PDF type classifier for native/hybrid/scanned detection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(slots=True)
class PdfTypeClassification:
    """Structured output for PDF type detection."""

    pdf_type: str
    confidence: float
    reasoning: str
    page_count: int
    text_pages: int
    image_heavy_pages: int
    avg_text_density: float
    avg_image_ratio: float
    total_text_chars: int

    @property
    def reason(self) -> str:
        """Backward-compatible alias for legacy callers."""
        return self.reasoning


class PdfTypeClassifier:
    """Classify PDFs as native, hybrid, or scanned using page-level signals."""

    def classify(self, pdf_path: Path) -> PdfTypeClassification:
        """Classify a PDF from page-level text and image density signals."""
        with fitz.open(pdf_path) as doc:
            page_count = len(doc)
            if page_count == 0:
                return PdfTypeClassification(
                    pdf_type="scanned",
                    confidence=0.6,
                    reasoning="No pages found in document.",
                    page_count=0,
                    text_pages=0,
                    image_heavy_pages=0,
                    avg_text_density=0.0,
                    avg_image_ratio=0.0,
                    total_text_chars=0,
                )

            text_pages = 0
            image_heavy_pages = 0
            text_chars_total = 0
            text_density_sum = 0.0
            image_ratio_sum = 0.0

            for page in doc:
                text = page.get_text("text").strip()
                images = page.get_images(full=True)
                words = len(text.split())
                text_chars = len(text)
                text_chars_total += text_chars

                page_area = max(page.rect.width * page.rect.height, 1.0)
                image_area = 0.0
                for image in images:
                    try:
                        xref = image[0]
                        rects = page.get_image_rects(xref)
                        image_area += sum(rect.width * rect.height for rect in rects)
                    except Exception:
                        continue
                image_ratio = min(1.0, image_area / page_area) if images else 0.0
                image_ratio_sum += image_ratio

                text_density = words / (page_area / 100000.0)
                text_density_sum += text_density

                has_meaningful_text = words >= 20 or text_density >= 20
                image_dominant = image_ratio >= 0.45 or (len(images) >= 2 and image_ratio >= 0.25)
                if has_meaningful_text:
                    text_pages += 1
                if image_dominant:
                    image_heavy_pages += 1

        text_ratio = text_pages / page_count
        image_ratio = image_heavy_pages / page_count
        avg_text_density = text_density_sum / page_count
        avg_image_ratio = image_ratio_sum / page_count

        if text_ratio >= 0.75 and image_ratio <= 0.3 and avg_image_ratio <= 0.2:
            confidence = self._clamp_confidence(0.82 + min(text_ratio - 0.75, 0.18))
            return PdfTypeClassification(
                pdf_type="native",
                confidence=confidence,
                reasoning=(
                    f"Native PDF detected: text-rich pages {text_pages}/{page_count}, "
                    f"image-heavy pages {image_heavy_pages}/{page_count}."
                ),
                page_count=page_count,
                text_pages=text_pages,
                image_heavy_pages=image_heavy_pages,
                avg_text_density=round(avg_text_density, 3),
                avg_image_ratio=round(avg_image_ratio, 3),
                total_text_chars=text_chars_total,
            )

        if text_ratio <= 0.25 and image_ratio >= 0.55 and avg_image_ratio >= 0.28:
            confidence = self._clamp_confidence(0.85 + min(image_ratio - 0.5, 0.15))
            return PdfTypeClassification(
                pdf_type="scanned",
                confidence=confidence,
                reasoning=(
                    "Scanned PDF detected: "
                    f"low text presence ({text_pages}/{page_count} text-rich pages) and "
                    f"strong image dominance ({image_heavy_pages}/{page_count} image-heavy pages)."
                ),
                page_count=page_count,
                text_pages=text_pages,
                image_heavy_pages=image_heavy_pages,
                avg_text_density=round(avg_text_density, 3),
                avg_image_ratio=round(avg_image_ratio, 3),
                total_text_chars=text_chars_total,
            )

        return PdfTypeClassification(
            pdf_type="hybrid",
            confidence=self._clamp_confidence(0.72 + min(text_ratio, 0.18)),
            reasoning=(
                f"Hybrid PDF detected: {image_heavy_pages}/{page_count} pages are image-heavy, "
                f"while {text_pages}/{page_count} pages contain meaningful extractable text."
            ),
            page_count=page_count,
            text_pages=text_pages,
            image_heavy_pages=image_heavy_pages,
            avg_text_density=round(avg_text_density, 3),
            avg_image_ratio=round(avg_image_ratio, 3),
            total_text_chars=text_chars_total,
        )

    def _clamp_confidence(self, value: float) -> float:
        """Clamp confidence to [0.0, 1.0] and round for UI display."""
        return round(min(1.0, max(0.0, value)), 2)
