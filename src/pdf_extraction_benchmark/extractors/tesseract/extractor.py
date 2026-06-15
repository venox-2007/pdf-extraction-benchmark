"""Tesseract OCR extractor adapter implementation."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import fitz
from PIL import Image

try:
    import pytesseract
    from pytesseract import Output
except ImportError:  # pragma: no cover - optional runtime dependency
    pytesseract = None  # type: ignore[assignment]
    Output = None  # type: ignore[assignment]

from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor
from pdf_extraction_benchmark.models.extraction_result import (
    BoundingBox,
    ExtractionMetadata,
    ExtractionResult,
)
from pdf_extraction_benchmark.utils.logger import get_logger

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

# Pages are rasterized at 2x zoom (144 dpi via `fitz.Matrix(2.0, 2.0)`) before
# being handed to Tesseract, matching the PaddleOCR extractor's rendering so
# bounding boxes from both extractors share the same source DPI.
RENDER_ZOOM = 2.0

# Common install locations for the Tesseract binary on Windows, used as a
# fallback when it is installed but not yet on PATH for the current process.
WINDOWS_TESSERACT_PATHS = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


class TesseractExtractor(BaseExtractor):
    """Extractor adapter for OCR-focused extraction using Tesseract OCR."""

    tool_name = "tesseract"

    def __init__(self) -> None:
        """Initialize logger and verify the Tesseract OCR runtime is available."""
        self.logger = get_logger(__name__)
        if pytesseract is None or Output is None:
            raise RuntimeError(
                "pytesseract is not installed. Install with: pip install pytesseract"
            )
        self._configure_tesseract_cmd()
        try:
            self._version = str(pytesseract.get_tesseract_version())
        except Exception as exc:  # pragma: no cover - depends on local install
            raise RuntimeError(
                "Tesseract OCR binary not found. Install Tesseract OCR and ensure "
                "it is on PATH (see README for installation instructions)."
            ) from exc

    def _configure_tesseract_cmd(self) -> None:
        """Point pytesseract at the Tesseract binary if it is not on PATH."""
        if shutil.which(pytesseract.pytesseract.tesseract_cmd):
            return
        for candidate in WINDOWS_TESSERACT_PATHS:
            if Path(candidate).exists():
                pytesseract.pytesseract.tesseract_cmd = candidate
                return

    def _base_extra_metadata(self) -> dict[str, Any]:
        """Build metadata shared by all OCR outputs."""
        return {
            "extractor": self.tool_name,
            "ocr_supported": True,
            "ocr_used": True,
            "ocr_required": True,
            "layout_preservation": "ocr_boxes",
            "ocr_engine": "tesseract",
            "ocr_engine_version": self._version,
        }

    def extract(self, pdf_path: Path) -> list[ExtractionResult]:
        """Run OCR extraction for PDF pages or a single image file."""
        pdf_path = pdf_path.resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"Input file not found: {pdf_path}")
        if pdf_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            return self._extract_image(pdf_path)
        if pdf_path.suffix.lower() != ".pdf":
            raise FileNotFoundError(f"Invalid PDF or image path: {pdf_path}")

        extraction_ts = datetime.now(UTC).isoformat()
        results: list[ExtractionResult] = []
        total_confidence = 0.0
        total_blocks = 0

        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            for page_idx in range(total_pages):
                page = doc.load_page(page_idx)
                page_num = page_idx + 1
                page_start = perf_counter()

                try:
                    image = self._render_page_to_image(page)
                    ocr_data = self._run_ocr(image)
                except Exception as exc:  # pragma: no cover - runtime backend variability
                    page_latency_ms = round((perf_counter() - page_start) * 1000, 3)
                    self.logger.warning(
                        "Tesseract OCR failed on page %s of %s: %s",
                        page_num,
                        pdf_path.name,
                        exc,
                    )
                    results.append(
                        self._build_error_result(
                            page_num, pdf_path.name, page_latency_ms, extraction_ts, exc
                        )
                    )
                    continue

                page_text, page_boxes, page_confidences = self._parse_ocr_data(ocr_data)
                page_conf_avg = (
                    round(sum(page_confidences) / len(page_confidences), 4)
                    if page_confidences
                    else 0.0
                )
                page_latency_ms = round((perf_counter() - page_start) * 1000, 3)
                total_confidence += sum(page_confidences)
                total_blocks += len(page_confidences)

                results.append(
                    ExtractionResult(
                        tool_name=self.tool_name,
                        page_number=page_num,
                        extracted_text=page_text,
                        tables=[],
                        bounding_boxes=page_boxes,
                        confidence_scores=page_confidences,
                        metadata=ExtractionMetadata(
                            source_file=pdf_path.name,
                            latency_ms=page_latency_ms,
                            extra={
                                "status": "ok" if page_text else "no_text_detected",
                                **self._base_extra_metadata(),
                                "ocr_required": False,
                                "extraction_timestamp": extraction_ts,
                                "total_page_count": total_pages,
                                "total_text_blocks": len(page_confidences),
                                "average_confidence": page_conf_avg,
                            },
                        ),
                    )
                )

        elapsed_ms = sum(
            result.metadata.latency_ms or 0.0 for result in results if result.metadata
        )
        avg_conf = round(total_confidence / total_blocks, 4) if total_blocks > 0 else 0.0
        for result in results:
            if result.metadata is not None:
                result.metadata.extra["document_average_confidence"] = avg_conf
                result.metadata.extra["document_total_text_blocks"] = total_blocks
                result.metadata.extra["document_latency_ms"] = round(elapsed_ms, 3)
        return results

    def _extract_image(self, image_path: Path) -> list[ExtractionResult]:
        """Run OCR directly on a supported image file as a one-page document."""
        extraction_ts = datetime.now(UTC).isoformat()
        page_start = perf_counter()

        try:
            image = Image.open(image_path).convert("RGB")
            ocr_data = self._run_ocr(image)
        except Exception as exc:  # pragma: no cover - runtime backend variability
            page_latency_ms = round((perf_counter() - page_start) * 1000, 3)
            self.logger.warning("Tesseract OCR failed on image %s: %s", image_path.name, exc)
            return [
                self._build_error_result(1, image_path.name, page_latency_ms, extraction_ts, exc)
            ]

        page_text, page_boxes, page_confidences = self._parse_ocr_data(ocr_data)
        page_conf_avg = (
            round(sum(page_confidences) / len(page_confidences), 4)
            if page_confidences
            else 0.0
        )
        page_latency_ms = round((perf_counter() - page_start) * 1000, 3)

        return [
            ExtractionResult(
                tool_name=self.tool_name,
                page_number=1,
                extracted_text=page_text,
                tables=[],
                bounding_boxes=page_boxes,
                confidence_scores=page_confidences,
                metadata=ExtractionMetadata(
                    source_file=image_path.name,
                    latency_ms=page_latency_ms,
                    extra={
                        "status": "ok" if page_text else "no_text_detected",
                        "input_type": "image",
                        **self._base_extra_metadata(),
                        "extraction_timestamp": extraction_ts,
                        "total_page_count": 1,
                        "total_text_blocks": len(page_confidences),
                        "average_confidence": page_conf_avg,
                        "document_average_confidence": page_conf_avg,
                        "document_total_text_blocks": len(page_confidences),
                        "document_latency_ms": page_latency_ms,
                    },
                ),
            )
        ]

    def _build_error_result(
        self,
        page_num: int,
        source_file: str,
        latency_ms: float,
        extraction_ts: str,
        exc: Exception,
    ) -> ExtractionResult:
        """Build a schema-compatible result for an OCR runtime failure."""
        return ExtractionResult(
            tool_name=self.tool_name,
            page_number=page_num,
            extracted_text="",
            tables=[],
            bounding_boxes=[],
            confidence_scores=[],
            metadata=ExtractionMetadata(
                source_file=source_file,
                latency_ms=latency_ms,
                extra={
                    "status": "ocr_runtime_error",
                    **self._base_extra_metadata(),
                    "extraction_timestamp": extraction_ts,
                    "total_page_count": page_num,
                    "total_text_blocks": 0,
                    "average_confidence": 0.0,
                    "error": str(exc),
                },
            ),
        )

    def _render_page_to_image(self, page: fitz.Page) -> Image.Image:
        """Render PDF page to an RGB Pillow image for OCR."""
        pix = page.get_pixmap(matrix=fitz.Matrix(RENDER_ZOOM, RENDER_ZOOM), alpha=False)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    def _run_ocr(self, image: Image.Image) -> dict[str, list[Any]]:
        """Run Tesseract word-level OCR on `image` and return the raw data dict."""
        return pytesseract.image_to_data(image, output_type=Output.DICT)

    def _parse_ocr_data(
        self, data: dict[str, list[Any]]
    ) -> tuple[str, list[BoundingBox], list[float]]:
        """Convert Tesseract `image_to_data` output into text, boxes, and confidences."""
        lines: dict[tuple[int, int, int], list[str]] = {}
        boxes: list[BoundingBox] = []
        confidences: list[float] = []

        word_count = len(data.get("text", []))
        for idx in range(word_count):
            text = str(data["text"][idx]).strip()
            try:
                confidence = float(data["conf"][idx])
            except (TypeError, ValueError):
                confidence = -1.0
            if not text or confidence < 0:
                continue

            left = float(data["left"][idx])
            top = float(data["top"][idx])
            width = float(data["width"][idx])
            height = float(data["height"][idx])
            boxes.append(BoundingBox(x0=left, y0=top, x1=left + width, y1=top + height))
            confidences.append(round(confidence / 100.0, 4))

            line_key = (data["block_num"][idx], data["par_num"][idx], data["line_num"][idx])
            lines.setdefault(line_key, []).append(text)

        text = "\n".join(" ".join(words) for words in lines.values())
        return text, boxes, confidences
