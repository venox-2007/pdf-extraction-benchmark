"""PaddleOCR extractor adapter implementation."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import fitz
import numpy as np

try:
    from paddleocr import PaddleOCR
except ImportError:  # pragma: no cover - optional runtime dependency
    PaddleOCR = None  # type: ignore[assignment]

from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor
from pdf_extraction_benchmark.models.extraction_result import (
    BoundingBox,
    ExtractionMetadata,
    ExtractionResult,
)
from pdf_extraction_benchmark.utils.logger import get_logger

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


class PaddleocrExtractor(BaseExtractor):
    """Extractor adapter for OCR-focused extraction using PaddleOCR."""

    tool_name = "paddleocr"

    def __init__(self) -> None:
        """Initialize logger and OCR engine."""
        self.logger = get_logger(__name__)
        if PaddleOCR is None:
            raise RuntimeError(
                "PaddleOCR is not installed. Install with: pip install paddleocr paddlepaddle"
            )
        # Runtime compatibility flags for certain Windows CPU Paddle builds.
        os.environ.setdefault("FLAGS_use_mkldnn", "0")
        os.environ.setdefault("FLAGS_enable_pir_api", "0")
        os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
        self._ocr = PaddleOCR(use_angle_cls=True, lang="en")

    def extract(self, pdf_path: Path) -> list[ExtractionResult]:
        """Run OCR extraction for PDF pages or a single image file."""
        pdf_path = pdf_path.resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"Input file not found: {pdf_path}")
        if pdf_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            return self._extract_image(pdf_path)
        if pdf_path.suffix.lower() != ".pdf":
            raise FileNotFoundError(f"Invalid PDF or image path: {pdf_path}")

        start = perf_counter()
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
                    image = self._render_page_to_rgb(page)
                    ocr_lines = self._run_ocr(image)
                except Exception as exc:  # pragma: no cover - runtime backend variability
                    page_latency_ms = round((perf_counter() - page_start) * 1000, 3)
                    self.logger.warning(
                        "PaddleOCR runtime failed on page %s of %s: %s",
                        page_num,
                        pdf_path.name,
                        exc,
                    )
                    results.append(
                        ExtractionResult(
                            tool_name=self.tool_name,
                            page_number=page_num,
                            extracted_text="",
                            tables=[],
                            bounding_boxes=[],
                            confidence_scores=[],
                            metadata=ExtractionMetadata(
                                source_file=pdf_path.name,
                                latency_ms=page_latency_ms,
                                extra={
                                    "status": "ocr_runtime_error",
                                    "extractor": self.tool_name,
                                    "ocr_supported": True,
                                    "ocr_used": True,
                                    "ocr_required": True,
                                    "layout_preservation": "ocr_boxes",
                                    "extraction_timestamp": extraction_ts,
                                    "total_page_count": total_pages,
                                    "total_text_blocks": 0,
                                    "average_confidence": 0.0,
                                    "error": str(exc),
                                },
                            ),
                        )
                    )
                    continue

                page_texts: list[str] = []
                page_confidences: list[float] = []
                page_boxes: list[BoundingBox] = []

                for line in ocr_lines:
                    bbox = self._to_bbox(line[0])
                    text, confidence = self._to_text_and_confidence(line[1])
                    if bbox is not None:
                        page_boxes.append(bbox)
                    if text:
                        page_texts.append(text)
                    if confidence is not None:
                        page_confidences.append(confidence)

                page_conf_avg = (
                    round(sum(page_confidences) / len(page_confidences), 4)
                    if page_confidences
                    else 0.0
                )
                page_latency_ms = round((perf_counter() - page_start) * 1000, 3)
                total_confidence += sum(page_confidences)
                total_blocks += len(page_texts)

                results.append(
                    ExtractionResult(
                        tool_name=self.tool_name,
                        page_number=page_num,
                        extracted_text="\n".join(page_texts).strip(),
                        tables=[],
                        bounding_boxes=page_boxes,
                        confidence_scores=page_confidences,
                        metadata=ExtractionMetadata(
                            source_file=pdf_path.name,
                            latency_ms=page_latency_ms,
                            extra={
                                "status": "ok" if page_texts else "no_text_detected",
                                "extractor": self.tool_name,
                                "ocr_supported": True,
                                "ocr_used": True,
                                "ocr_required": False,
                                "layout_preservation": "ocr_boxes",
                                "extraction_timestamp": extraction_ts,
                                "total_page_count": total_pages,
                                "total_text_blocks": len(page_texts),
                                "average_confidence": page_conf_avg,
                            },
                        ),
                    )
                )

        elapsed_ms = round((perf_counter() - start) * 1000, 3)
        avg_conf = round(total_confidence / total_blocks, 4) if total_blocks > 0 else 0.0
        for result in results:
            if result.metadata is not None:
                result.metadata.extra["document_average_confidence"] = avg_conf
                result.metadata.extra["document_total_text_blocks"] = total_blocks
                result.metadata.extra["document_latency_ms"] = elapsed_ms
        return results

    def _extract_image(self, image_path: Path) -> list[ExtractionResult]:
        """Run OCR directly on a supported image file as a one-page document."""
        start = perf_counter()
        extraction_ts = datetime.now(UTC).isoformat()
        page_start = perf_counter()

        try:
            image = self._load_image_to_rgb(image_path)
            ocr_lines = self._run_ocr(image)
        except Exception as exc:  # pragma: no cover - runtime backend variability
            page_latency_ms = round((perf_counter() - page_start) * 1000, 3)
            self.logger.warning("PaddleOCR runtime failed on image %s: %s", image_path.name, exc)
            return [
                ExtractionResult(
                    tool_name=self.tool_name,
                    page_number=1,
                    extracted_text="",
                    tables=[],
                    bounding_boxes=[],
                    confidence_scores=[],
                    metadata=ExtractionMetadata(
                        source_file=image_path.name,
                        latency_ms=page_latency_ms,
                        extra={
                            "status": "ocr_runtime_error",
                            "extractor": self.tool_name,
                            "input_type": "image",
                            "ocr_supported": True,
                            "ocr_used": True,
                            "ocr_required": True,
                            "layout_preservation": "ocr_boxes",
                            "extraction_timestamp": extraction_ts,
                            "total_page_count": 1,
                            "total_text_blocks": 0,
                            "average_confidence": 0.0,
                            "error": str(exc),
                        },
                    ),
                )
            ]

        page_texts: list[str] = []
        page_confidences: list[float] = []
        page_boxes: list[BoundingBox] = []

        for line in ocr_lines:
            bbox = self._to_bbox(line[0])
            text, confidence = self._to_text_and_confidence(line[1])
            if bbox is not None:
                page_boxes.append(bbox)
            if text:
                page_texts.append(text)
            if confidence is not None:
                page_confidences.append(confidence)

        page_conf_avg = (
            round(sum(page_confidences) / len(page_confidences), 4)
            if page_confidences
            else 0.0
        )
        page_latency_ms = round((perf_counter() - page_start) * 1000, 3)
        elapsed_ms = round((perf_counter() - start) * 1000, 3)

        return [
            ExtractionResult(
                tool_name=self.tool_name,
                page_number=1,
                extracted_text="\n".join(page_texts).strip(),
                tables=[],
                bounding_boxes=page_boxes,
                confidence_scores=page_confidences,
                metadata=ExtractionMetadata(
                    source_file=image_path.name,
                    latency_ms=page_latency_ms,
                    extra={
                        "status": "ok" if page_texts else "no_text_detected",
                        "extractor": self.tool_name,
                        "input_type": "image",
                        "ocr_supported": True,
                        "ocr_used": True,
                        "ocr_required": True,
                        "layout_preservation": "ocr_boxes",
                        "extraction_timestamp": extraction_ts,
                        "total_page_count": 1,
                        "total_text_blocks": len(page_texts),
                        "average_confidence": page_conf_avg,
                        "document_average_confidence": page_conf_avg,
                        "document_total_text_blocks": len(page_texts),
                        "document_latency_ms": elapsed_ms,
                    },
                ),
            )
        ]

    def _render_page_to_rgb(self, page: fitz.Page) -> np.ndarray:
        """Render PDF page to RGB image array for OCR."""
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8)
        return img.reshape(pix.height, pix.width, pix.n)

    def _load_image_to_rgb(self, image_path: Path) -> np.ndarray:
        """Load an image file into an RGB image array for OCR."""
        pix = fitz.Pixmap(str(image_path))
        if pix.alpha or pix.n != 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        img = np.frombuffer(pix.samples, dtype=np.uint8)
        return img.reshape(pix.height, pix.width, pix.n)

    def _run_ocr(self, image: np.ndarray) -> list[Any]:
        """Run PaddleOCR on an RGB page image."""
        if hasattr(self._ocr, "predict"):
            try:
                raw = self._ocr.predict(image)
            except TypeError:
                raw = self._ocr.ocr(image, cls=True)
        else:
            raw = self._ocr.ocr(image, cls=True)

        if not raw:
            return []
        first = raw[0] if isinstance(raw, list) else raw
        if isinstance(first, list):
            return first
        if isinstance(first, dict):
            polys = first.get("rec_polys", []) or first.get("dt_polys", [])
            texts = first.get("rec_texts", [])
            scores = first.get("rec_scores", [])
            lines: list[Any] = []
            for idx in range(min(len(polys), len(texts))):
                conf = float(scores[idx]) if idx < len(scores) else 0.0
                lines.append([polys[idx], (texts[idx], conf)])
            return lines
        return []

    def _to_bbox(self, points: Any) -> BoundingBox | None:
        """Convert 4-point polygon box to axis-aligned bounding box."""
        if not isinstance(points, list) or len(points) < 4:
            return None
        try:
            xs = [float(point[0]) for point in points]
            ys = [float(point[1]) for point in points]
        except (TypeError, ValueError, IndexError):
            return None
        return BoundingBox(x0=min(xs), y0=min(ys), x1=max(xs), y1=max(ys))

    def _to_text_and_confidence(self, payload: Any) -> tuple[str, float | None]:
        """Extract normalized text and confidence from PaddleOCR line payload."""
        if isinstance(payload, (list, tuple)) and len(payload) >= 2:
            text = str(payload[0]).strip()
            try:
                confidence = float(payload[1])
            except (TypeError, ValueError):
                confidence = None
            return text, confidence
        return "", None


