"""Helpers for visualizing extracted bounding boxes on page images.

This module performs no extraction or bounding-box computation of its own.
It only renders page images (via PyMuPDF/Pillow) and overlays the
`BoundingBox` instances already produced by an extractor, so visualizations
always reflect the extraction results shown elsewhere in the dashboard.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import fitz
from PIL import Image, ImageDraw

from pdf_extraction_benchmark.models.extraction_result import BoundingBox, ExtractionResult

DEFAULT_DPI = 150
PDF_POINTS_DPI = 72.0
MAX_VISUALIZED_PAGES = 3

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

EXTRACTOR_COLORS: dict[str, str] = {
    "OpenDataLoader": "#3fb950",
    "PyMuPDF": "#58a6ff",
    "Docling": "#f1c40f",
    "PaddleOCR": "#e05d44",
    "Tesseract": "#a371f7",
}
DEFAULT_COLOR = "#ff5c5c"

# Bounding-box coordinate space produced by each extractor, in DPI. Most
# extractors report boxes in PDF point space (72 dpi). PaddleOCR and
# Tesseract run OCR on pages rasterized at 2x zoom (144 dpi via
# `fitz.Matrix(2.0, 2.0)`), so their boxes are in 144-dpi pixel space.
EXTRACTOR_SOURCE_DPI: dict[str, float] = {
    "PaddleOCR": 144.0,
    "Tesseract": 144.0,
}


def get_extractor_color(extractor_name: str) -> str:
    """Return a distinct display color for `extractor_name`.

    Falls back to `DEFAULT_COLOR` for extractors not in `EXTRACTOR_COLORS`.
    """
    return EXTRACTOR_COLORS.get(extractor_name, DEFAULT_COLOR)


def get_extractor_source_dpi(extractor_name: str) -> float:
    """Return the DPI of the coordinate space `extractor_name` reports boxes in.

    Falls back to `PDF_POINTS_DPI` (72 dpi) for extractors not listed in
    `EXTRACTOR_SOURCE_DPI`.
    """
    return EXTRACTOR_SOURCE_DPI.get(extractor_name, PDF_POINTS_DPI)


def render_page_image(input_path: Path, page_index: int, dpi: int = DEFAULT_DPI) -> Image.Image:
    """Render one page of `input_path` to an RGB Pillow image.

    Parameters
    ----------
    input_path:
        Path to the source PDF or image file.
    page_index:
        Zero-based page index. Must be ``0`` for non-PDF image inputs.
    dpi:
        Rasterization resolution for PDF pages.

    Returns
    -------
    PIL.Image.Image
        The rendered page (or the image file itself) as an RGB image.

    Raises
    ------
    FileNotFoundError
        If `input_path` does not exist.
    IndexError
        If `page_index` is out of range for the document.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix.lower() in IMAGE_SUFFIXES:
        if page_index != 0:
            raise IndexError(
                f"Page index {page_index} is out of range for image input {input_path.name}"
            )
        return Image.open(input_path).convert("RGB")

    with fitz.open(input_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"Page index {page_index} is out of range for {input_path.name} "
                f"({len(doc)} pages)"
            )
        page = doc.load_page(page_index)
        pix = page.get_pixmap(dpi=dpi)
        mode = "RGBA" if pix.alpha else "RGB"
        return Image.frombytes(mode, (pix.width, pix.height), pix.samples).convert("RGB")


def scale_bounding_box(
    bbox: BoundingBox, dpi: int = DEFAULT_DPI, source_dpi: float = PDF_POINTS_DPI
) -> tuple[float, float, float, float]:
    """Scale a bounding box from PDF point space (72 dpi) to pixel space at `dpi`."""
    scale = dpi / source_dpi
    return (bbox.x0 * scale, bbox.y0 * scale, bbox.x1 * scale, bbox.y1 * scale)


def draw_bounding_boxes(
    image: Image.Image,
    bounding_boxes: Sequence[BoundingBox],
    dpi: int = DEFAULT_DPI,
    source_dpi: float = PDF_POINTS_DPI,
    color: str = DEFAULT_COLOR,
    width: int = 2,
) -> Image.Image:
    """Return a copy of `image` with `bounding_boxes` drawn as colored rectangles.

    `image` is not modified in place. An empty `bounding_boxes` sequence
    returns an unmodified copy of `image`. `source_dpi` is the DPI of the
    coordinate space `bounding_boxes` are expressed in (see
    `get_extractor_source_dpi`).
    """
    annotated = image.copy()
    if not bounding_boxes:
        return annotated

    draw = ImageDraw.Draw(annotated)
    for bbox in bounding_boxes:
        x0, y0, x1, y1 = scale_bounding_box(bbox, dpi=dpi, source_dpi=source_dpi)
        draw.rectangle([x0, y0, x1, y1], outline=color, width=width)
    return annotated


def build_page_visualizations(
    input_path: Path,
    results: list[ExtractionResult],
    max_pages: int = MAX_VISUALIZED_PAGES,
    dpi: int = DEFAULT_DPI,
    source_dpi: float = PDF_POINTS_DPI,
    color: str = DEFAULT_COLOR,
    page_image_cache: dict[int, Image.Image] | None = None,
) -> list[dict[str, Any]]:
    """Build bounding-box overlay images for the first `max_pages` pages.

    Parameters
    ----------
    input_path:
        Path to the source PDF or image file the `results` were extracted
        from. The page is re-rendered for display only; bounding boxes are
        taken as-is from `results` and are never recomputed.
    results:
        Per-page extraction results, as produced by an extractor.
    max_pages:
        Maximum number of pages to visualize, ordered by `page_number`.
    dpi:
        Rasterization resolution used for the rendered page image.
    source_dpi:
        DPI of the coordinate space `results[*].bounding_boxes` are expressed
        in (see `get_extractor_source_dpi`). Used to scale boxes onto the
        page image rendered at `dpi`.
    color:
        Outline color for drawn bounding boxes.
    page_image_cache:
        Optional dict used to cache rendered base page images keyed by
        zero-based page index, so multiple extractors sharing the same
        document do not re-rasterize the same page.

    Returns
    -------
    list[dict[str, Any]]
        One entry per visualized page, each with keys ``page_number``
        (1-based), ``image`` (annotated `PIL.Image.Image`), and
        ``bbox_count`` (number of boxes drawn).
    """
    cache = page_image_cache if page_image_cache is not None else {}
    visualizations: list[dict[str, Any]] = []

    sorted_results = sorted(results, key=lambda result: result.page_number)[:max_pages]
    for result in sorted_results:
        page_index = result.page_number - 1
        if page_index not in cache:
            cache[page_index] = render_page_image(input_path, page_index, dpi=dpi)
        base_image = cache[page_index]
        annotated = draw_bounding_boxes(
            base_image, result.bounding_boxes, dpi=dpi, source_dpi=source_dpi, color=color
        )
        visualizations.append(
            {
                "page_number": result.page_number,
                "image": annotated,
                "bbox_count": len(result.bounding_boxes),
            }
        )

    return visualizations


def has_bounding_boxes(results: list[ExtractionResult]) -> bool:
    """Return True if any result in `results` has at least one bounding box."""
    return any(result.bounding_boxes for result in results)
