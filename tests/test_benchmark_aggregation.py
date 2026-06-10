"""Tests for multi-document benchmark aggregation helpers."""

from __future__ import annotations

from pdf_extraction_benchmark.reports.aggregation import (
    EMPTY_AGGREGATE_SUMMARY,
    build_multi_document_report_rows,
    compute_aggregate_summary,
    compute_per_extractor_summary,
)

DOC1_ROWS = [
    {
        "extractor": "PyMuPDF",
        "latency_seconds": 0.1,
        "char_count": 1000,
        "word_count": 150,
        "bbox_count": 5,
        "status": "success",
        "error_message": "",
    },
    {
        "extractor": "OpenDataLoader",
        "latency_seconds": 0.5,
        "char_count": 900,
        "word_count": 140,
        "bbox_count": 10,
        "status": "success",
        "error_message": "",
    },
]

DOC2_ROWS = [
    {
        "extractor": "PyMuPDF",
        "latency_seconds": 0.3,
        "char_count": 2000,
        "word_count": 300,
        "bbox_count": 7,
        "status": "success",
        "error_message": "",
    },
    {
        "extractor": "OpenDataLoader",
        "latency_seconds": 0.0,
        "char_count": 0,
        "word_count": 0,
        "bbox_count": 0,
        "status": "failed",
        "error_message": "OpenDataLoader extraction failed: timeout",
    },
]


def test_build_multi_document_report_rows_concatenates_documents() -> None:
    rows = build_multi_document_report_rows(
        [("doc1.pdf", DOC1_ROWS), ("doc2.pdf", DOC2_ROWS)]
    )

    assert len(rows) == 4
    assert [row["document_name"] for row in rows] == [
        "doc1.pdf",
        "doc1.pdf",
        "doc2.pdf",
        "doc2.pdf",
    ]
    assert [row["extractor"] for row in rows] == [
        "PyMuPDF",
        "OpenDataLoader",
        "PyMuPDF",
        "OpenDataLoader",
    ]


def test_build_multi_document_report_rows_handles_single_document() -> None:
    rows = build_multi_document_report_rows([("doc1.pdf", DOC1_ROWS)])

    assert len(rows) == 2
    assert all(row["document_name"] == "doc1.pdf" for row in rows)


def test_build_multi_document_report_rows_handles_empty_input() -> None:
    assert build_multi_document_report_rows([]) == []


def test_compute_aggregate_summary_empty_rows_returns_empty_summary() -> None:
    assert compute_aggregate_summary([]) == EMPTY_AGGREGATE_SUMMARY


def test_compute_aggregate_summary_overall_statistics() -> None:
    rows = build_multi_document_report_rows(
        [("doc1.pdf", DOC1_ROWS), ("doc2.pdf", DOC2_ROWS)]
    )

    summary = compute_aggregate_summary(rows)

    assert summary["total_documents"] == 2
    assert summary["total_runs"] == 4
    assert summary["success_rate"] == 0.75
    assert summary["avg_extraction_time_seconds"] == (0.1 + 0.5 + 0.3 + 0.0) / 4
    assert summary["avg_character_count"] == (1000 + 900 + 2000 + 0) / 4
    assert summary["avg_word_count"] == (150 + 140 + 300 + 0) / 4
    assert summary["avg_bounding_box_count"] == (5 + 10 + 7 + 0) / 4


def test_compute_aggregate_summary_all_success() -> None:
    rows = build_multi_document_report_rows([("doc1.pdf", DOC1_ROWS)])

    summary = compute_aggregate_summary(rows)

    assert summary["success_rate"] == 1.0
    assert summary["total_documents"] == 1
    assert summary["total_runs"] == 2


def test_compute_per_extractor_summary_groups_by_extractor() -> None:
    rows = build_multi_document_report_rows(
        [("doc1.pdf", DOC1_ROWS), ("doc2.pdf", DOC2_ROWS)]
    )

    per_extractor = compute_per_extractor_summary(rows)

    assert set(per_extractor.keys()) == {"PyMuPDF", "OpenDataLoader"}

    pymupdf_summary = per_extractor["PyMuPDF"]
    assert pymupdf_summary["total_runs"] == 2
    assert pymupdf_summary["total_documents"] == 2
    assert pymupdf_summary["success_rate"] == 1.0
    assert pymupdf_summary["avg_extraction_time_seconds"] == (0.1 + 0.3) / 2
    assert pymupdf_summary["avg_character_count"] == (1000 + 2000) / 2

    odl_summary = per_extractor["OpenDataLoader"]
    assert odl_summary["total_runs"] == 2
    assert odl_summary["success_rate"] == 0.5
    assert odl_summary["avg_bounding_box_count"] == (10 + 0) / 2


def test_compute_per_extractor_summary_empty_input() -> None:
    assert compute_per_extractor_summary([]) == {}


def test_aggregate_summary_with_failed_document_still_counts_document() -> None:
    failed_doc_rows = [
        {
            "extractor": "PyMuPDF",
            "latency_seconds": 0.0,
            "char_count": 0,
            "word_count": 0,
            "bbox_count": 0,
            "status": "failed",
            "error_message": "boom",
        }
    ]
    rows = build_multi_document_report_rows(
        [("doc1.pdf", DOC1_ROWS), ("broken.pdf", failed_doc_rows)]
    )

    summary = compute_aggregate_summary(rows)

    assert summary["total_documents"] == 2
    assert summary["total_runs"] == 3
    assert summary["success_rate"] == 2 / 3
