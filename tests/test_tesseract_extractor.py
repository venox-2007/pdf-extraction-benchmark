"""Tests for Tesseract OCR extractor behavior and schema mapping."""

from __future__ import annotations

from pathlib import Path

import fitz

from pdf_extraction_benchmark.extractors.tesseract import extractor as tesseract_module
from pdf_extraction_benchmark.extractors.tesseract.extractor import TesseractExtractor


class _FakeOutput:
    """Stand-in for `pytesseract.Output`."""

    DICT = "dict"


def _fake_image_to_data(_image: object, output_type: str = "dict") -> dict[str, list[object]]:
    return {
        "text": ["hello", "world", ""],
        "conf": [95.0, 91.0, -1.0],
        "left": [10, 12, 0],
        "top": [10, 40, 0],
        "width": [90, 108, 0],
        "height": [20, 20, 0],
        "block_num": [1, 1, 1],
        "par_num": [1, 1, 1],
        "line_num": [1, 2, 2],
    }


def _create_pdf(path: Path, pages: int) -> None:
    with fitz.open() as doc:
        for idx in range(pages):
            page = doc.new_page()
            page.insert_text((72, 72), f"page {idx + 1}")
        doc.save(path)


def _create_png(path: Path) -> None:
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 120, 60), 0)
    pix.clear_with(255)
    pix.save(path)


def _patch_pytesseract(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(tesseract_module, "Output", _FakeOutput)
    monkeypatch.setattr(tesseract_module.pytesseract, "image_to_data", _fake_image_to_data)
    monkeypatch.setattr(tesseract_module.pytesseract, "get_tesseract_version", lambda: "5.0.0")


def test_tesseract_extractor_returns_standardized_results(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Tesseract extractor should emit page-wise ExtractionResult records."""
    _patch_pytesseract(monkeypatch)
    pdf_path = tmp_path / "sample.pdf"
    _create_pdf(pdf_path, pages=2)

    extractor = TesseractExtractor()
    results = extractor.extract(pdf_path)

    assert len(results) == 2
    assert results[0].tool_name == "tesseract"
    assert results[0].page_number == 1
    assert "hello" in results[0].extracted_text
    assert "world" in results[0].extracted_text
    assert len(results[0].bounding_boxes) == 2
    assert len(results[0].confidence_scores) == 2
    assert results[0].confidence_scores[0] == 0.95
    assert results[0].metadata is not None
    assert results[0].metadata.extra["status"] == "ok"
    assert results[0].metadata.extra["ocr_supported"] is True
    assert results[0].metadata.extra["ocr_used"] is True
    assert results[0].metadata.extra["total_text_blocks"] == 2
    assert results[0].metadata.extra["ocr_engine"] == "tesseract"


def test_tesseract_extractor_supports_image_input(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Tesseract extractor should OCR supported image files as one-page documents."""
    _patch_pytesseract(monkeypatch)
    image_path = tmp_path / "sample.png"
    _create_png(image_path)

    extractor = TesseractExtractor()
    results = extractor.extract(image_path)

    assert len(results) == 1
    assert results[0].tool_name == "tesseract"
    assert results[0].page_number == 1
    assert "hello" in results[0].extracted_text
    assert "world" in results[0].extracted_text
    assert len(results[0].bounding_boxes) == 2
    assert len(results[0].confidence_scores) == 2
    assert results[0].metadata is not None
    assert results[0].metadata.source_file == "sample.png"
    assert results[0].metadata.extra["input_type"] == "image"
    assert results[0].metadata.extra["ocr_supported"] is True
    assert results[0].metadata.extra["total_page_count"] == 1


def test_tesseract_extractor_handles_missing_dependency(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Extractor should raise a clear error when pytesseract package is unavailable."""
    monkeypatch.setattr(tesseract_module, "pytesseract", None)
    monkeypatch.setattr(tesseract_module, "Output", None)

    try:
        TesseractExtractor()
    except RuntimeError as exc:
        assert "pytesseract is not installed" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when pytesseract dependency is missing.")


def test_tesseract_extractor_handles_missing_binary(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Extractor should raise a clear error when the Tesseract binary is unavailable."""

    def _raise_not_found() -> str:
        raise tesseract_module.pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(tesseract_module.pytesseract, "get_tesseract_version", _raise_not_found)
    monkeypatch.setattr(tesseract_module.shutil, "which", lambda _cmd: None)
    monkeypatch.setattr(
        tesseract_module,
        "WINDOWS_TESSERACT_PATHS",
        (),
    )

    try:
        TesseractExtractor()
    except RuntimeError as exc:
        assert "Tesseract OCR binary not found" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when Tesseract binary is missing.")
