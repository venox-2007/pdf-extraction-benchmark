"""Tests for extractor initialization."""

from __future__ import annotations

from pathlib import Path

from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor


def test_extractor_initialization() -> None:
    """Ensure extractor initializes and returns typed results."""
    extractor = PymupdfExtractor()
    results = extractor.extract(Path("sample.pdf"))
    assert extractor.tool_name == "pymupdf"
    assert len(results) == 1
    assert results[0].tool_name == "pymupdf"
