"""Shared Surya runtime helpers for extraction and benchmarking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import fitz
from PIL import Image, ImageSequence

from pdf_extraction_benchmark.models.extraction_result import (
    BoundingBox,
    ExtractionMetadata,
    ExtractionResult,
)
from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser
from pdf_extraction_benchmark.utils.logger import get_logger

try:  # pragma: no cover - optional runtime dependency
    from surya.inference import SuryaInferenceManager
    from surya.inference.parsers import clean_block_html
    from surya.layout import LayoutPredictor
    from surya.recognition import RecognitionPredictor
    from surya.settings import settings
except ImportError:  # pragma: no cover - optional runtime dependency
    SuryaInferenceManager = None  # type: ignore[assignment]
    LayoutPredictor = None  # type: ignore[assignment]
    RecognitionPredictor = None  # type: ignore[assignment]
    clean_block_html = None  # type: ignore[assignment]
    settings = None  # type: ignore[assignment]

logger = get_logger(__name__)


@dataclass(slots=True)
class SuryaPageArtifact:
    """Raw Surya outputs for one page."""

    page_number: int
    image: Image.Image
    layout_result: Any
    ocr_result: Any
    source_kind: str


@dataclass(slots=True)
class SuryaDocumentArtifact:
    """Raw Surya outputs for a whole document."""

    source_path: Path
    backend: str
    pages: list[SuryaPageArtifact]


@dataclass(slots=True)
class _LoadedPage:
    """Preprocessed page image ready for Surya."""

    page_number: int
    image: Image.Image
    source_kind: str


class _HTMLTextExtractor(HTMLParser):
    """Extract visible text from a small HTML fragment."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self._chunks.append(data)

    def get_text(self) -> str:
        return "".join(self._chunks)


def load_document_pages(input_path: Path, render_dpi: int = 192) -> list[_LoadedPage]:
    """Load a PDF or image file into page-sized PIL images."""
    path = input_path.resolve()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf_pages(path, render_dpi=render_dpi)
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        return _load_image_pages(path)
    raise FileNotFoundError(f"Unsupported input for Surya: {path}")


def run_document(
    input_path: Path,
    *,
    backend: str | None = None,
    render_dpi: int = 192,
    manager: SuryaInferenceManager | None = None,
    layout_predictor: LayoutPredictor | None = None,
    recognition_predictor: RecognitionPredictor | None = None,
) -> SuryaDocumentArtifact:
    """Run layout + OCR for a document and return raw Surya artifacts."""
    if SuryaInferenceManager is None or LayoutPredictor is None or RecognitionPredictor is None:
        raise RuntimeError(
            "Surya is not installed. Install with: uv add surya-ocr"
        )
    loaded_pages = load_document_pages(input_path, render_dpi=render_dpi)
    if not loaded_pages:
        return SuryaDocumentArtifact(
            source_path=input_path.resolve(),
            backend=backend or "",
            pages=[],
        )

    local_manager = manager or SuryaInferenceManager(method=backend)
    local_layout_predictor = layout_predictor or LayoutPredictor(local_manager)
    local_recognition_predictor = recognition_predictor or RecognitionPredictor(local_manager)

    images = [page.image for page in loaded_pages]
    layout_results = local_layout_predictor(images)
    ocr_results = local_recognition_predictor(images, layout_results=layout_results, full_page=True)

    pages: list[SuryaPageArtifact] = []
    for loaded_page, layout_result, ocr_result in zip(
        loaded_pages,
        layout_results,
        ocr_results,
        strict=True,
    ):
        pages.append(
            SuryaPageArtifact(
                page_number=loaded_page.page_number,
                image=loaded_page.image,
                layout_result=layout_result,
                ocr_result=ocr_result,
                source_kind=loaded_page.source_kind,
            )
        )

    return SuryaDocumentArtifact(
        source_path=input_path.resolve(),
        backend=getattr(local_manager, "method", backend or ""),
        pages=pages,
    )


def build_extraction_results(document: SuryaDocumentArtifact) -> list[ExtractionResult]:
    """Convert raw Surya artifacts into the unified extraction schema."""
    source_file = document.source_path.name
    results: list[ExtractionResult] = []
    total_pages = len(document.pages)
    document_confidence = 0.0
    document_blocks = 0

    for page in document.pages:
        text, boxes, confidences, layout_summary = _page_payload(page)
        page_confidence = (
            round(sum(confidences) / len(confidences), 4) if confidences else 0.0
        )
        document_confidence += sum(confidences)
        document_blocks += len(confidences)

        results.append(
            ExtractionResult(
                tool_name="surya",
                page_number=page.page_number,
                extracted_text=text,
                bounding_boxes=boxes,
                confidence_scores=confidences,
                metadata=ExtractionMetadata(
                    source_file=source_file,
                    extra={
                        "status": "ok" if text else "no_text_detected",
                        "extractor": "surya",
                        "ocr_supported": True,
                        "ocr_used": True,
                        "ocr_required": True,
                        "layout_preservation": "surya_blocks",
                        "surya_backend": document.backend,
                        "surya_device": settings.TORCH_DEVICE_MODEL if settings else "",
                        "surya_model_name": settings.SURYA_MODEL_CHECKPOINT if settings else "",
                        "surya_layout_block_count": len(page.layout_result.bboxes),
                        "surya_text_block_count": len(confidences),
                        "surya_layout_summary": layout_summary,
                        "surya_source_kind": page.source_kind,
                        "total_page_count": total_pages,
                        "total_text_blocks": len(confidences),
                        "average_confidence": page_confidence,
                        "document_average_confidence": (
                            round(document_confidence / document_blocks, 4)
                            if document_blocks
                            else 0.0
                        ),
                        "document_total_text_blocks": document_blocks,
                    },
                ),
            )
        )

    document_average_confidence = (
        round(document_confidence / document_blocks, 4) if document_blocks else 0.0
    )
    for result in results:
        if result.metadata is None:
            continue
        result.metadata.extra["document_average_confidence"] = document_average_confidence
        result.metadata.extra["document_total_text_blocks"] = document_blocks

    return results


def save_document_outputs(
    document: SuryaDocumentArtifact,
    results: list[ExtractionResult],
    project_root: Path | None = None,
) -> tuple[Path, Path]:
    """Write result.json and result.md under outputs/surya/<document_name>/."""
    project_root = project_root or Path(__file__).resolve().parents[4]
    output_dir = project_root / "outputs" / "surya" / document.source_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    json_payload = UnifiedOutputParser().to_json_payload(results)
    json_payload["document_metadata"] = {
        "source_file": document.source_path.name,
        "backend": document.backend,
        "page_count": len(document.pages),
        "model_name": settings.SURYA_MODEL_CHECKPOINT if settings else "",
        "device": settings.TORCH_DEVICE_MODEL if settings else "",
    }
    json_path = output_dir / "result.json"
    md_path = output_dir / "result.md"
    json_path.write_text(json.dumps(json_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(build_document_markdown(document, results), encoding="utf-8")
    return json_path, md_path


def build_document_markdown(
    document: SuryaDocumentArtifact,
    results: list[ExtractionResult],
) -> str:
    """Render a concise human-readable extraction report."""
    lines = [
        "# Surya Extraction Report",
        "",
        f"- Source file: `{document.source_path.name}`",
        f"- Backend: `{document.backend}`",
        f"- Device: `{settings.TORCH_DEVICE_MODEL if settings else ''}`",
        f"- Pages: {len(results)}",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"## Page {result.page_number}",
                "",
                f"- Status: `{result.metadata.extra.get('status', '') if result.metadata else ''}`",
                f"- Confidence: {(_average(result.confidence_scores)):.4f}",
                f"- Text length: {len(result.extracted_text)}",
                "",
            ]
        )
        if result.extracted_text.strip():
            lines.append(result.extracted_text)
            lines.append("")
        if result.bounding_boxes:
            lines.append("### Bounding Boxes")
            for index, bbox in enumerate(result.bounding_boxes, start=1):
                lines.append(
                    f"- Box {index}: ({bbox.x0:.1f}, {bbox.y0:.1f}, {bbox.x1:.1f}, {bbox.y1:.1f})"
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def page_to_line_payloads(page: SuryaPageArtifact) -> list[dict[str, Any]]:
    """Convert one Surya page result into FUNSD-compatible line payloads."""
    line_payloads: list[dict[str, Any]] = []
    blocks = sorted(
        getattr(page.ocr_result, "blocks", []),
        key=lambda block: getattr(block, "reading_order", 0),
    )
    for block in blocks:
        text = block_html_to_text(getattr(block, "html", ""))
        if not text:
            continue
        line_payloads.append(
            {
                "text": text,
                "box": _polygon_to_points(getattr(block, "polygon", [])),
                "confidence": float(getattr(block, "confidence", 0.0) or 0.0),
                "label": getattr(block, "label", ""),
                "raw_label": getattr(block, "raw_label", ""),
                "reading_order": int(getattr(block, "reading_order", 0) or 0),
            }
        )
    return line_payloads


def page_text(page: SuryaPageArtifact) -> str:
    """Convert the OCR HTML blocks into plain text."""
    texts: list[str] = []
    for line in page_to_line_payloads(page):
        normalized = str(line.get("text", "")).strip()
        if normalized:
            texts.append(normalized)
    return "\n".join(texts).strip()


def page_confidence(page: SuryaPageArtifact) -> float:
    """Average OCR confidence across blocks in a page."""
    confidences = [
        float(getattr(block, "confidence", 0.0) or 0.0)
        for block in getattr(page.ocr_result, "blocks", [])
    ]
    return round(_average(confidences), 4)


def _page_payload(page: SuryaPageArtifact) -> tuple[str, list[BoundingBox], list[float], str]:
    """Return the extracted text, boxes, confidences, and layout summary."""
    text = page_text(page)
    boxes: list[BoundingBox] = []
    confidences: list[float] = []
    for block in sorted(
        getattr(page.ocr_result, "blocks", []),
        key=lambda item: getattr(item, "reading_order", 0),
    ):
        polygon = getattr(block, "polygon", [])
        bbox = _polygon_to_bbox(polygon)
        if bbox is not None:
            boxes.append(bbox)
        confidences.append(float(getattr(block, "confidence", 0.0) or 0.0))
    layout_summary = _layout_summary(page.layout_result)
    return text, boxes, confidences, layout_summary


def _layout_summary(layout_result: Any) -> str:
    """Compress layout metadata into a short text summary."""
    boxes = getattr(layout_result, "bboxes", []) or []
    if not boxes:
        return ""
    counts: dict[str, int] = {}
    for box in boxes:
        label = str(getattr(box, "label", "") or "")
        counts[label] = counts.get(label, 0) + 1
    return ", ".join(f"{label}:{count}" for label, count in sorted(counts.items()))


def _load_pdf_pages(pdf_path: Path, *, render_dpi: int) -> list[_LoadedPage]:
    pages: list[_LoadedPage] = []
    zoom = render_dpi / 72.0
    with fitz.open(pdf_path) as doc:
        for index in range(len(doc)):
            page = doc.load_page(index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            pages.append(
                _LoadedPage(page_number=index + 1, image=image, source_kind="pdf_page")
            )
    return pages


def _load_image_pages(image_path: Path) -> list[_LoadedPage]:
    pages: list[_LoadedPage] = []
    with Image.open(image_path) as image_file:
        for index, frame in enumerate(ImageSequence.Iterator(image_file)):
            pages.append(
                _LoadedPage(
                    page_number=index + 1,
                    image=frame.convert("RGB").copy(),
                    source_kind="image_frame",
                )
            )
    return pages


def _polygon_to_bbox(points: Any) -> BoundingBox | None:
    """Convert a Surya polygon into an axis-aligned bounding box."""
    if not isinstance(points, list) or not points:
        return None
    xs: list[float] = []
    ys: list[float] = []
    for point in points:
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            try:
                xs.append(float(point[0]))
                ys.append(float(point[1]))
            except (TypeError, ValueError):
                continue
    if not xs or not ys:
        return None
    return BoundingBox(x0=min(xs), y0=min(ys), x1=max(xs), y1=max(ys))


def _polygon_to_points(points: Any) -> list[list[float]]:
    """Normalize a polygon into JSON-friendly point lists."""
    normalized: list[list[float]] = []
    if not isinstance(points, list):
        return normalized
    for point in points:
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            try:
                normalized.append([float(point[0]), float(point[1])])
            except (TypeError, ValueError):
                continue
    return normalized


def block_html_to_text(html: str) -> str:
    """Convert a Surya HTML block into plain text."""
    cleaned = clean_block_html(html) if clean_block_html is not None else html
    if not cleaned:
        return ""
    parser = _HTMLTextExtractor()
    parser.feed(cleaned)
    text = unescape(parser.get_text())
    return " ".join(text.split()).strip()


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
