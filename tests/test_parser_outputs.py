"""Tests for parser output shape."""

from __future__ import annotations

from pdf_extraction_benchmark.models.extraction_result import ExtractionResult
from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser


def test_parser_output_structure() -> None:
    """Ensure parser returns expected JSON payload structure."""
    results = [ExtractionResult(tool_name="demo", page_number=1, extracted_text="hello")]
    payload = UnifiedOutputParser().to_json_payload(results)
    assert payload["total_pages"] == 1
    assert isinstance(payload["pages"], list)
