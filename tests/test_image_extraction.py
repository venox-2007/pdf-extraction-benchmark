"""Tests for the hybrid PDF image extraction module."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from pdf_extraction_benchmark.image_extractor import (
    _merge_rects,
    _text_coverage,
    extract_and_save_images,
    inject_image_markdown,
)
from pdf_extraction_benchmark.models.extraction_result import ExtractionResult

# ── helpers ───────────────────────────────────────────────────────────────────


def _make_png_bytes(width: int = 60, height: int = 60) -> bytes:
    """Return a minimal valid PNG as bytes using fitz."""
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height))
    pix.set_rect(pix.irect, (200, 100, 50))
    return pix.tobytes("png")


def _make_result(page_number: int, text: str) -> ExtractionResult:
    return ExtractionResult(
        tool_name="test",
        page_number=page_number,
        extracted_text=text,
    )


# ── test: single embedded raster image (Approach A via pdf_type="scanned") ───


def test_single_image_pdf(tmp_path: Path) -> None:
    """A scanned PDF with one embedded image produces exactly one extracted file."""
    pdf_path = tmp_path / "single.pdf"
    doc = fitz.open()
    page = doc.new_page()
    png = _make_png_bytes()
    page.insert_image(fitz.Rect(50, 50, 200, 200), stream=png)
    doc.save(str(pdf_path))
    doc.close()

    out_dir = tmp_path / "out_single"
    images = extract_and_save_images(pdf_path, out_dir, pdf_type="scanned")

    assert len(images) == 1
    assert Path(images[0].path).exists()
    assert images[0].page_number == 1
    assert images[0].image_index == 1
    assert images[0].strategy == "xobject"


# ── test: multiple embedded images (Approach A) ───────────────────────────────


def test_multiple_image_pdf(tmp_path: Path) -> None:
    """A scanned PDF with 3 images on different pages → 3 extracted files."""
    pdf_path = tmp_path / "multi.pdf"
    doc = fitz.open()
    png = _make_png_bytes()
    for _ in range(3):
        page = doc.new_page()
        page.insert_image(fitz.Rect(50, 50, 200, 200), stream=png)
    doc.save(str(pdf_path))
    doc.close()

    out_dir = tmp_path / "out_multi"
    images = extract_and_save_images(pdf_path, out_dir, pdf_type="scanned")

    assert len(images) == 3
    page_numbers = [img.page_number for img in images]
    assert page_numbers == [1, 2, 3]
    for img in images:
        assert Path(img.path).exists()
        assert img.width > 0
        assert img.height > 0


# ── test: text-only PDF → no images (Approach A) ─────────────────────────────


def test_no_image_pdf(tmp_path: Path) -> None:
    """A text-only scanned PDF produces zero extracted images."""
    pdf_path = tmp_path / "text_only.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Hello world — no images here.")
    doc.save(str(pdf_path))
    doc.close()

    out_dir = tmp_path / "out_text"
    images = extract_and_save_images(pdf_path, out_dir, pdf_type="scanned")

    assert images == []


# ── test: inject_image_markdown ordering ─────────────────────────────────────


def test_inject_markdown_ordering(tmp_path: Path) -> None:
    """Images on page 1 appear after page 1's text; page 2 text follows with no images."""
    # Build a PDF with one image on page 1 only
    pdf_path = tmp_path / "ordering.pdf"
    doc = fitz.open()
    png = _make_png_bytes()
    p1 = doc.new_page()
    p1.insert_image(fitz.Rect(50, 50, 200, 200), stream=png)
    doc.new_page()  # page 2 — no image
    doc.save(str(pdf_path))
    doc.close()

    out_dir = tmp_path / "out_order"
    images = extract_and_save_images(pdf_path, out_dir, pdf_type="scanned")
    assert len(images) >= 1

    results = [
        _make_result(1, "Page one text"),
        _make_result(2, "Page two text"),
    ]
    project_outputs = tmp_path / "outputs"
    project_outputs.mkdir()

    md = inject_image_markdown(results, images, project_outputs)

    # Page 1 text must appear before the figure reference
    p1_text_pos = md.find("Page one text")
    figure_pos = md.find("![Figure p1_")
    p2_text_pos = md.find("Page two text")

    assert p1_text_pos != -1
    assert figure_pos != -1
    assert p2_text_pos != -1
    assert p1_text_pos < figure_pos, "Figure ref should come after page 1 text"
    assert figure_pos < p2_text_pos, "Page 2 text should come after page 1 figure"


# ── unit tests for geometry helpers ──────────────────────────────────────────


def test_merge_rects_overlapping() -> None:
    """Two overlapping rectangles merge into one."""
    a = fitz.Rect(0, 0, 100, 100)
    b = fitz.Rect(80, 80, 200, 200)
    merged = _merge_rects([a, b], gap=0)
    assert len(merged) == 1
    assert merged[0].x1 == pytest.approx(200)
    assert merged[0].y1 == pytest.approx(200)


def test_merge_rects_with_gap() -> None:
    """Two rects within gap tolerance merge; two far apart do not."""
    a = fitz.Rect(0, 0, 100, 100)
    b = fitz.Rect(105, 0, 200, 100)  # 5 pts gap
    merged_tight = _merge_rects([a, b], gap=2)   # gap < 5 → no merge
    merged_wide = _merge_rects([a, b], gap=10)   # gap > 5 → merge
    assert len(merged_tight) == 2
    assert len(merged_wide) == 1


def test_text_coverage_empty() -> None:
    """Empty text_rects → coverage 0."""
    region = fitz.Rect(0, 0, 100, 100)
    assert _text_coverage(region, []) == pytest.approx(0.0)


def test_text_coverage_full() -> None:
    """A text rect that covers the whole region → coverage 1."""
    region = fitz.Rect(0, 0, 100, 100)
    text_r = fitz.Rect(0, 0, 100, 100)
    assert _text_coverage(region, [text_r]) == pytest.approx(1.0)
