"""Generate unified JSON-ready output payloads."""

from __future__ import annotations

from dataclasses import asdict

from pdf_extraction_benchmark.models.extraction_result import ExtractionResult


class UnifiedOutputParser:
    """Convert extraction results into a serializable dictionary payload."""

    def to_json_payload(self, results: list[ExtractionResult]) -> dict[str, object]:
        """Serialize extraction results for downstream storage/export."""
        return {
            "pages": [asdict(result) for result in results],
            "total_pages": len(results),
        }
