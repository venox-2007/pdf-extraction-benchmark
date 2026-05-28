"""Tests for extractor initialization."""

from __future__ import annotations

from pathlib import Path

import fitz

from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor


def test_extractor_initialization(tmp_path: Path) -> None:
    """Ensure extractor initializes and returns typed results."""
    pdf_path = tmp_path / "sample.pdf"
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "Hello from PyMuPDF extractor test.")
        doc.save(pdf_path)

    extractor = PymupdfExtractor()
    results = extractor.extract(pdf_path)
    assert extractor.tool_name == "pymupdf"
    assert len(results) == 1
    assert results[0].tool_name == "pymupdf"
    assert results[0].page_number == 1
    assert "Hello from PyMuPDF extractor test." in results[0].extracted_text
    assert results[0].metadata is not None
    assert results[0].metadata.extra["extractor"] == "pymupdf"
