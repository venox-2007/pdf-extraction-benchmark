"""Tests for Docling extractor behavior."""

from __future__ import annotations

from pathlib import Path

import fitz

import pdf_extraction_benchmark.extractors.docling.extractor as docling_module
from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor


class _FakeDocument:
    def __init__(self) -> None:
        self.tables = []

    def export_to_dict(self) -> dict[str, object]:
        return {
            "pages": {"1": {"size": {"width": 595.0, "height": 842.0}, "page_no": 1}},
            "texts": [
                {
                    "text": "Hello Docling",
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {"l": 72.0, "t": 100.0, "r": 160.0, "b": 80.0},
                        }
                    ],
                }
            ],
            "tables": [],
        }

    def export_to_markdown(self) -> str:
        return "Hello Docling"


class _FakeConversion:
    def __init__(self) -> None:
        self.document = _FakeDocument()


class _FakeConverter:
    def convert(self, _source: str) -> _FakeConversion:
        return _FakeConversion()


def test_docling_extractor_returns_schema_results(tmp_path: Path, monkeypatch) -> None:
    """Docling should produce unified extraction results and save outputs."""
    monkeypatch.setattr(docling_module, "DocumentConverter", lambda: _FakeConverter())

    pdf_path = tmp_path / "sample.pdf"
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "Hello Docling")
        doc.save(pdf_path)

    extractor = DoclingExtractor(output_root=tmp_path)
    results = extractor.extract(pdf_path)

    assert extractor.tool_name == "docling"
    assert len(results) == 1
    assert results[0].tool_name == "docling"
    assert results[0].page_number == 1
    assert "Hello Docling" in results[0].extracted_text
    assert results[0].metadata is not None
    assert results[0].metadata.extra["extractor"] == "docling"
    assert results[0].metadata.extra["layout_preservation"] == "docling_markdown"
    assert (tmp_path / "outputs" / "docling" / "sample" / "result.json").exists()
    assert (tmp_path / "outputs" / "docling" / "sample" / "result.md").exists()


def test_docling_extractor_rejects_unsupported_type(tmp_path: Path, monkeypatch) -> None:
    """Docling should reject file types it cannot handle (e.g. .docx, .csv)."""
    monkeypatch.setattr(docling_module, "DocumentConverter", lambda: _FakeConverter())
    extractor = DoclingExtractor(output_root=tmp_path)
    bad_path = tmp_path / "document.docx"
    bad_path.write_bytes(b"not a real docx")

    try:
        extractor.extract(bad_path)
    except FileNotFoundError as exc:
        assert "does not support" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected FileNotFoundError for unsupported file type")
