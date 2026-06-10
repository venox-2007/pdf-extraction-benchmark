"""Build exportable benchmark reports (CSV/JSON) from existing comparison rows.

This module performs no extraction or metric computation of its own. It only
reshapes and serializes the `comparison_rows` already produced by the Streamlit
extraction loop, so exported reports always match what is shown on screen.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

REPORT_FIELDS: list[str] = [
    "document_name",
    "extractor",
    "extraction_time_seconds",
    "character_count",
    "word_count",
    "bounding_box_count",
    "status",
    "error_message",
]


def build_report_rows(
    document_name: str, comparison_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Reshape comparison rows into the flat report schema.

    Reuses the values already computed for the Comparison Analysis dashboard
    (`latency_seconds`, `char_count`, `word_count`, `bbox_count`, `status`,
    `error_message`) without recomputing any metric.
    """
    report_rows: list[dict[str, Any]] = []
    for row in comparison_rows:
        report_rows.append(
            {
                "document_name": document_name,
                "extractor": row.get("extractor", ""),
                "extraction_time_seconds": row.get("latency_seconds"),
                "character_count": row.get("char_count"),
                "word_count": row.get("word_count"),
                "bounding_box_count": row.get("bbox_count"),
                "status": row.get("status", ""),
                "error_message": row.get("error_message") or "",
            }
        )
    return report_rows


def to_csv_bytes(report_rows: list[dict[str, Any]]) -> bytes:
    """Serialize report rows to CSV bytes (UTF-8, header included)."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=REPORT_FIELDS)
    writer.writeheader()
    for row in report_rows:
        writer.writerow({field: row.get(field, "") for field in REPORT_FIELDS})
    return buffer.getvalue().encode("utf-8")


def to_json_bytes(report_rows: list[dict[str, Any]]) -> bytes:
    """Serialize report rows to indented JSON bytes (UTF-8)."""
    return json.dumps(report_rows, indent=2, ensure_ascii=False).encode("utf-8")
