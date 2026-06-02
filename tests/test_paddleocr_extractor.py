"""Tests for PaddleOCR extractor behavior and schema mapping."""

from __future__ import annotations

from pathlib import Path

import fitz

from pdf_extraction_benchmark.extractors.paddleocr import extractor as paddle_module
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor


class _FakePaddleOCR:
    """Small fake OCR engine for deterministic extractor tests."""

    def __init__(self, **_: object) -> None:
        pass

    def predict(self, _image: object, **_: object) -> list[object]:
        return [
            {
                "rec_polys": [
                    [[10, 10], [100, 10], [100, 30], [10, 30]],
                    [[12, 40], [120, 40], [120, 60], [12, 60]],
                ],
                "rec_texts": ["hello", "world"],
                "rec_scores": [0.95, 0.91],
            }
        ]


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


def test_paddleocr_extractor_returns_standardized_results(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Paddle extractor should emit page-wise ExtractionResult records."""
    monkeypatch.setattr(paddle_module, "PaddleOCR", _FakePaddleOCR)
    pdf_path = tmp_path / "sample.pdf"
    _create_pdf(pdf_path, pages=2)

    extractor = PaddleocrExtractor()
    results = extractor.extract(pdf_path)

    assert len(results) == 2
    assert results[0].tool_name == "paddleocr"
    assert results[0].page_number == 1
    assert "hello" in results[0].extracted_text
    assert "world" in results[0].extracted_text
    assert len(results[0].bounding_boxes) == 2
    assert len(results[0].confidence_scores) == 2
    assert results[0].metadata is not None
    assert results[0].metadata.extra["ocr_supported"] is True
    assert results[0].metadata.extra["ocr_used"] is True
    assert results[0].metadata.extra["total_text_blocks"] == 2


def test_paddleocr_extractor_supports_image_input(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Paddle extractor should OCR supported image files as one-page documents."""
    monkeypatch.setattr(paddle_module, "PaddleOCR", _FakePaddleOCR)
    image_path = tmp_path / "sample.png"
    _create_png(image_path)

    extractor = PaddleocrExtractor()
    results = extractor.extract(image_path)

    assert len(results) == 1
    assert results[0].tool_name == "paddleocr"
    assert results[0].page_number == 1
    assert "hello" in results[0].extracted_text
    assert "world" in results[0].extracted_text
    assert len(results[0].bounding_boxes) == 2
    assert len(results[0].confidence_scores) == 2
    assert results[0].metadata is not None
    assert results[0].metadata.source_file == "sample.png"
    assert results[0].metadata.extra["input_type"] == "image"
    assert results[0].metadata.extra["ocr_supported"] is True
    assert results[0].metadata.extra["ocr_used"] is True
    assert results[0].metadata.extra["total_page_count"] == 1


def test_paddleocr_extractor_handles_missing_dependency(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Extractor should raise a clear error when PaddleOCR package is unavailable."""
    monkeypatch.setattr(paddle_module, "PaddleOCR", None)
    pdf_path = tmp_path / "sample.pdf"
    _create_pdf(pdf_path, pages=1)

    try:
        PaddleocrExtractor()
    except RuntimeError as exc:
        assert "PaddleOCR is not installed" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when PaddleOCR dependency is missing.")
