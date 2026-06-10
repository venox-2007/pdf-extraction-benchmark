"""Tests for exportable benchmark report helpers."""

from __future__ import annotations

import csv
import io
import json

from pdf_extraction_benchmark.reports.benchmark_report import (
    REPORT_FIELDS,
    build_report_rows,
    to_csv_bytes,
    to_json_bytes,
)

SUCCESS_ROW = {
    "extractor": "PyMuPDF",
    "latency_seconds": 0.107,
    "char_count": 9335,
    "word_count": 1367,
    "bbox_count": 7,
    "status": "success",
    "error_message": "",
}

FAILED_ROW = {
    "extractor": "Docling",
    "latency_seconds": 1.234,
    "char_count": 0,
    "word_count": 0,
    "bbox_count": 0,
    "status": "failed",
    "error_message": "Docling extraction failed: model load error",
}


def test_build_report_rows_maps_success_row_fields() -> None:
    rows = build_report_rows("native_1.pdf", [SUCCESS_ROW])

    assert rows == [
        {
            "document_name": "native_1.pdf",
            "extractor": "PyMuPDF",
            "extraction_time_seconds": 0.107,
            "character_count": 9335,
            "word_count": 1367,
            "bounding_box_count": 7,
            "status": "success",
            "error_message": "",
        }
    ]


def test_build_report_rows_includes_error_message_for_failures() -> None:
    rows = build_report_rows("native_1.pdf", [FAILED_ROW])

    assert rows[0]["status"] == "failed"
    assert rows[0]["error_message"] == "Docling extraction failed: model load error"
    assert rows[0]["character_count"] == 0


def test_build_report_rows_handles_mixed_success_and_failure() -> None:
    rows = build_report_rows("native_1.pdf", [SUCCESS_ROW, FAILED_ROW])

    assert [row["extractor"] for row in rows] == ["PyMuPDF", "Docling"]
    assert [row["status"] for row in rows] == ["success", "failed"]


def test_build_report_rows_empty_input_returns_empty_list() -> None:
    assert build_report_rows("native_1.pdf", []) == []


def test_build_report_rows_does_not_mutate_input() -> None:
    original = dict(SUCCESS_ROW)
    build_report_rows("native_1.pdf", [original])
    assert original == SUCCESS_ROW


def test_build_report_rows_handles_missing_optional_fields() -> None:
    sparse_row = {"extractor": "PaddleOCR", "status": "success"}

    rows = build_report_rows("native_1.pdf", [sparse_row])

    assert rows[0]["extraction_time_seconds"] is None
    assert rows[0]["character_count"] is None
    assert rows[0]["word_count"] is None
    assert rows[0]["bounding_box_count"] is None
    assert rows[0]["error_message"] == ""


def test_to_csv_bytes_produces_valid_csv_with_expected_header() -> None:
    rows = build_report_rows("native_1.pdf", [SUCCESS_ROW, FAILED_ROW])

    csv_bytes = to_csv_bytes(rows)
    text = csv_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    assert reader.fieldnames == REPORT_FIELDS
    parsed_rows = list(reader)
    assert len(parsed_rows) == 2
    assert parsed_rows[0]["extractor"] == "PyMuPDF"
    assert parsed_rows[0]["status"] == "success"
    assert parsed_rows[1]["extractor"] == "Docling"
    assert parsed_rows[1]["status"] == "failed"
    assert parsed_rows[1]["error_message"] == "Docling extraction failed: model load error"


def test_to_csv_bytes_handles_empty_rows() -> None:
    csv_bytes = to_csv_bytes([])
    text = csv_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    assert reader.fieldnames == REPORT_FIELDS
    assert list(reader) == []


def test_to_json_bytes_produces_valid_json_array() -> None:
    rows = build_report_rows("native_1.pdf", [SUCCESS_ROW, FAILED_ROW])

    json_bytes = to_json_bytes(rows)
    parsed = json.loads(json_bytes.decode("utf-8"))

    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[0]["document_name"] == "native_1.pdf"
    assert parsed[0]["extractor"] == "PyMuPDF"
    assert parsed[1]["error_message"] == "Docling extraction failed: model load error"


def test_to_json_bytes_handles_empty_rows() -> None:
    json_bytes = to_json_bytes([])
    assert json.loads(json_bytes.decode("utf-8")) == []


def test_to_csv_and_json_roundtrip_preserve_row_count() -> None:
    rows = build_report_rows(
        "scanned_5.pdf",
        [SUCCESS_ROW, FAILED_ROW, {**SUCCESS_ROW, "extractor": "PaddleOCR"}],
    )

    csv_text = to_csv_bytes(rows).decode("utf-8")
    csv_rows = list(csv.DictReader(io.StringIO(csv_text)))
    json_rows = json.loads(to_json_bytes(rows).decode("utf-8"))

    assert len(csv_rows) == len(json_rows) == 3
