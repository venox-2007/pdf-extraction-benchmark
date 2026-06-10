"""Tests for bounding box visualization helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from pdf_extraction_benchmark.models.extraction_result import (
    BoundingBox,
    ExtractionResult,
)
from pdf_extraction_benchmark.visualization.bbox_overlay import (
    DEFAULT_COLOR,
    build_page_visualizations,
    draw_bounding_boxes,
    get_extractor_color,
    get_extractor_source_dpi,
    has_bounding_boxes,
    render_page_image,
    scale_bounding_box,
)

NATIVE_PDF = Path(__file__).resolve().parents[1] / "data" / "raw" / "native" / "native_1.pdf"
SCANNED_PDF = Path(__file__).resolve().parents[1] / "data" / "raw" / "scanned" / "scanned_1.pdf"


def test_get_extractor_color_known_and_unknown() -> None:
    assert get_extractor_color("PyMuPDF") != DEFAULT_COLOR
    assert get_extractor_color("SomeUnknownExtractor") == DEFAULT_COLOR


def test_get_extractor_source_dpi_paddleocr_and_default() -> None:
    assert get_extractor_source_dpi("PaddleOCR") == 144.0
    assert get_extractor_source_dpi("PyMuPDF") == 72.0
    assert get_extractor_source_dpi("Unknown") == 72.0


def test_scale_bounding_box() -> None:
    bbox = BoundingBox(x0=10.0, y0=20.0, x1=30.0, y1=40.0)

    x0, y0, x1, y1 = scale_bounding_box(bbox, dpi=144, source_dpi=72.0)

    assert (x0, y0, x1, y1) == (20.0, 40.0, 60.0, 80.0)


def test_render_page_image_native_pdf() -> None:
    image = render_page_image(NATIVE_PDF, page_index=0, dpi=72)

    assert image.mode == "RGB"
    assert image.width > 0
    assert image.height > 0


def test_render_page_image_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        render_page_image(Path("does/not/exist.pdf"), page_index=0)


def test_render_page_image_out_of_range_page_raises() -> None:
    with pytest.raises(IndexError):
        render_page_image(NATIVE_PDF, page_index=10_000)


def test_draw_bounding_boxes_with_boxes_modifies_image() -> None:
    base = Image.new("RGB", (200, 200), color="white")
    bboxes = [BoundingBox(x0=10.0, y0=10.0, x1=50.0, y1=50.0)]

    annotated = draw_bounding_boxes(base, bboxes, dpi=72, source_dpi=72.0, color="#ff0000")

    assert annotated is not base
    assert list(annotated.getdata()) != list(base.getdata())


def test_draw_bounding_boxes_empty_list_returns_unmodified_copy() -> None:
    base = Image.new("RGB", (50, 50), color="white")

    annotated = draw_bounding_boxes(base, [], dpi=72)

    assert annotated is not base
    assert list(annotated.getdata()) == list(base.getdata())


def test_has_bounding_boxes_true_and_false() -> None:
    with_boxes = [
        ExtractionResult(
            tool_name="PyMuPDF",
            page_number=1,
            extracted_text="hello",
            bounding_boxes=[BoundingBox(x0=0, y0=0, x1=10, y1=10)],
        )
    ]
    without_boxes = [
        ExtractionResult(
            tool_name="PaddleOCR",
            page_number=1,
            extracted_text="hello",
            bounding_boxes=[],
        )
    ]

    assert has_bounding_boxes(with_boxes) is True
    assert has_bounding_boxes(without_boxes) is False


def test_build_page_visualizations_returns_entries_with_bbox_count() -> None:
    results = [
        ExtractionResult(
            tool_name="PyMuPDF",
            page_number=1,
            extracted_text="hello",
            bounding_boxes=[
                BoundingBox(x0=10, y0=10, x1=100, y1=50),
                BoundingBox(x0=20, y0=60, x1=120, y1=90),
            ],
        )
    ]

    visualizations = build_page_visualizations(NATIVE_PDF, results, dpi=72)

    assert len(visualizations) == 1
    assert visualizations[0]["page_number"] == 1
    assert visualizations[0]["bbox_count"] == 2
    assert isinstance(visualizations[0]["image"], Image.Image)


def test_build_page_visualizations_empty_bboxes_gives_zero_count() -> None:
    results = [
        ExtractionResult(
            tool_name="PaddleOCR",
            page_number=1,
            extracted_text="",
            bounding_boxes=[],
        )
    ]

    visualizations = build_page_visualizations(NATIVE_PDF, results, dpi=72)

    assert len(visualizations) == 1
    assert visualizations[0]["bbox_count"] == 0


def test_build_page_visualizations_limits_to_max_pages() -> None:
    results = [
        ExtractionResult(tool_name="PyMuPDF", page_number=page, extracted_text="")
        for page in range(1, 10)
    ]

    visualizations = build_page_visualizations(NATIVE_PDF, results, max_pages=3, dpi=72)

    assert len(visualizations) == 3
    assert [viz["page_number"] for viz in visualizations] == [1, 2, 3]


def test_build_page_visualizations_reuses_page_image_cache() -> None:
    results_a = [
        ExtractionResult(
            tool_name="PyMuPDF",
            page_number=1,
            extracted_text="",
            bounding_boxes=[BoundingBox(x0=0, y0=0, x1=10, y1=10)],
        )
    ]
    results_b = [
        ExtractionResult(
            tool_name="OpenDataLoader",
            page_number=1,
            extracted_text="",
            bounding_boxes=[BoundingBox(x0=5, y0=5, x1=15, y1=15)],
        )
    ]

    cache: dict[int, Image.Image] = {}
    build_page_visualizations(NATIVE_PDF, results_a, dpi=72, page_image_cache=cache)
    assert 0 in cache
    cached_image = cache[0]

    build_page_visualizations(NATIVE_PDF, results_b, dpi=72, page_image_cache=cache)
    assert cache[0] is cached_image


def test_build_page_visualizations_missing_file_raises() -> None:
    results = [ExtractionResult(tool_name="PyMuPDF", page_number=1, extracted_text="")]

    with pytest.raises(FileNotFoundError):
        build_page_visualizations(Path("does/not/exist.pdf"), results, dpi=72)


def test_render_page_image_scanned_pdf() -> None:
    image = render_page_image(SCANNED_PDF, page_index=0, dpi=72)

    assert image.mode == "RGB"
    assert image.width > 0
    assert image.height > 0
