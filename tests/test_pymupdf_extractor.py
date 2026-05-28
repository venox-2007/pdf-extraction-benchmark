"""Focused tests for PyMuPDF extractor behavior."""

from __future__ import annotations

from pathlib import Path

import fitz

from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor


def _build_pdf(pdf_path: Path, texts: list[str]) -> None:
    """Create a synthetic PDF with one text line per page."""
    with fitz.open() as doc:
        for text in texts:
            page = doc.new_page()
            if text:
                page.insert_text((72, 72), text)
        doc.save(pdf_path)


def test_pymupdf_extractor_page_count_and_structure(tmp_path: Path) -> None:
    """Extractor should return one standardized result per PDF page."""
    pdf_path = tmp_path / "three_pages.pdf"
    _build_pdf(pdf_path, ["alpha page", "beta page", "gamma page"])

    extractor = PymupdfExtractor()
    results = extractor.extract(pdf_path)

    assert len(results) == 3
    assert [result.page_number for result in results] == [1, 2, 3]
    assert all(result.tool_name == "pymupdf" for result in results)
    assert all(result.metadata is not None for result in results)
    assert all(result.metadata.extra["total_page_count"] == 3 for result in results)
    assert all(result.metadata.extra["ocr_supported"] is False for result in results)


def test_pymupdf_extractor_flags_ocr_required_for_image_heavy_pages(tmp_path: Path) -> None:
    """Image-heavy pages with very low text should be flagged as OCR required."""
    pdf_path = tmp_path / "scan_like.pdf"
    with fitz.open() as doc:
        page = doc.new_page()
        rect = fitz.Rect(50, 50, 300, 300)
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 200, 200), 0)
        pix.clear_with(180)
        page.insert_image(rect, pixmap=pix)
        doc.save(pdf_path)

    extractor = PymupdfExtractor()
    results = extractor.extract(pdf_path)

    assert len(results) == 1
    assert results[0].metadata is not None
    assert results[0].metadata.extra["ocr_required"] is True
    assert results[0].metadata.extra["status"] == "ocr_required"
