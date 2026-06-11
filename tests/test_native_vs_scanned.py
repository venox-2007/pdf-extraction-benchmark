"""Tests for native vs scanned grouping and recommendation helpers."""

from __future__ import annotations

from pdf_extraction_benchmark.reports.native_vs_scanned import (
    NATIVE_GROUP,
    SCANNED_GROUP,
    build_comparison_table_rows,
    build_pdf_type_report_rows,
    build_production_recommendation,
    compute_group_summary,
    recommend_native_extractor,
    recommend_scanned_extractor,
    recommend_table_heavy_extractor,
)

NATIVE_DOC_ROWS = [
    {
        "extractor": "PyMuPDF",
        "latency_seconds": 0.5,
        "char_count": 1000,
        "word_count": 150,
        "bbox_count": 10,
        "status": "success",
        "error_message": "",
        "pdf_type": "native",
    },
    {
        "extractor": "Docling",
        "latency_seconds": 2.0,
        "char_count": 1100,
        "word_count": 160,
        "bbox_count": 20,
        "status": "success",
        "error_message": "",
        "pdf_type": "native",
    },
]

SCANNED_DOC_ROWS = [
    {
        "extractor": "PyMuPDF",
        "latency_seconds": 0.4,
        "char_count": 0,
        "word_count": 0,
        "bbox_count": 0,
        "status": "success",
        "error_message": "",
        "pdf_type": "scanned",
    },
    {
        "extractor": "PaddleOCR",
        "latency_seconds": 5.0,
        "char_count": 900,
        "word_count": 140,
        "bbox_count": 30,
        "status": "success",
        "error_message": "",
        "pdf_type": "scanned",
    },
]

HYBRID_DOC_ROWS = [
    {
        "extractor": "PyMuPDF",
        "latency_seconds": 0.6,
        "char_count": 500,
        "word_count": 80,
        "bbox_count": 5,
        "status": "success",
        "error_message": "",
        "pdf_type": "hybrid",
    },
]


def test_build_pdf_type_report_rows_groups_by_pdf_type() -> None:
    documents = [
        ("native_doc.pdf", NATIVE_DOC_ROWS),
        ("scanned_doc.pdf", SCANNED_DOC_ROWS),
        ("hybrid_doc.pdf", HYBRID_DOC_ROWS),
    ]

    grouped = build_pdf_type_report_rows(documents)

    assert {row["extractor"] for row in grouped[NATIVE_GROUP]} == {"PyMuPDF", "Docling"}
    assert {row["extractor"] for row in grouped[SCANNED_GROUP]} == {"PyMuPDF", "PaddleOCR"}
    assert all(row["document_name"] == "native_doc.pdf" for row in grouped[NATIVE_GROUP])
    # Hybrid documents are excluded from both groups.
    assert sum(len(rows) for rows in grouped.values()) == len(NATIVE_DOC_ROWS) + len(
        SCANNED_DOC_ROWS
    )


def test_build_pdf_type_report_rows_groups_image_with_scanned() -> None:
    image_rows = [
        {
            "extractor": "PaddleOCR",
            "latency_seconds": 4.0,
            "char_count": 800,
            "word_count": 120,
            "bbox_count": 25,
            "status": "success",
            "error_message": "",
            "pdf_type": "image",
        }
    ]

    grouped = build_pdf_type_report_rows([("image_doc.pdf", image_rows)])

    assert grouped[NATIVE_GROUP] == []
    assert len(grouped[SCANNED_GROUP]) == 1


def test_compute_group_summary_returns_documents_and_per_extractor() -> None:
    grouped = build_pdf_type_report_rows([("native_doc.pdf", NATIVE_DOC_ROWS)])

    summary = compute_group_summary(grouped[NATIVE_GROUP])

    assert summary["total_documents"] == 1
    assert set(summary["per_extractor"].keys()) == {"PyMuPDF", "Docling"}
    assert summary["per_extractor"]["PyMuPDF"]["avg_extraction_time_seconds"] == 0.5


def test_build_comparison_table_rows_shape() -> None:
    grouped = build_pdf_type_report_rows([("native_doc.pdf", NATIVE_DOC_ROWS)])
    per_extractor = compute_group_summary(grouped[NATIVE_GROUP])["per_extractor"]

    table_rows = build_comparison_table_rows(per_extractor)

    assert {row["Extractor"] for row in table_rows} == {"PyMuPDF", "Docling"}
    pymupdf_row = next(row for row in table_rows if row["Extractor"] == "PyMuPDF")
    assert pymupdf_row["Avg Time (s)"] == 0.5
    assert pymupdf_row["Avg Characters"] == 1000.0
    assert pymupdf_row["Avg Words"] == 150.0
    assert pymupdf_row["Success Rate"] == "100.0%"
    assert pymupdf_row["Bounding Box Count"] == 10.0


def test_recommend_native_extractor_picks_fastest_among_reliable() -> None:
    grouped = build_pdf_type_report_rows([("native_doc.pdf", NATIVE_DOC_ROWS)])
    per_extractor = compute_group_summary(grouped[NATIVE_GROUP])["per_extractor"]

    recommendation = recommend_native_extractor(per_extractor)

    assert recommendation["extractor"] == "PyMuPDF"
    assert "PyMuPDF" in recommendation["reasoning"]


def test_recommend_scanned_extractor_picks_highest_character_recovery() -> None:
    grouped = build_pdf_type_report_rows([("scanned_doc.pdf", SCANNED_DOC_ROWS)])
    per_extractor = compute_group_summary(grouped[SCANNED_GROUP])["per_extractor"]

    recommendation = recommend_scanned_extractor(per_extractor)

    assert recommendation["extractor"] == "PaddleOCR"
    assert "PaddleOCR" in recommendation["reasoning"]


def test_recommend_native_extractor_with_no_data() -> None:
    recommendation = recommend_native_extractor({})

    assert recommendation["extractor"] is None
    assert "No native PDF benchmark data" in recommendation["reasoning"]


def test_recommend_scanned_extractor_with_no_data() -> None:
    recommendation = recommend_scanned_extractor({})

    assert recommendation["extractor"] is None
    assert "No scanned PDF benchmark data" in recommendation["reasoning"]


def test_recommend_table_heavy_extractor_with_docling() -> None:
    grouped = build_pdf_type_report_rows([("native_doc.pdf", NATIVE_DOC_ROWS)])
    per_extractor = compute_group_summary(grouped[NATIVE_GROUP])["per_extractor"]

    recommendation = recommend_table_heavy_extractor(per_extractor)

    assert recommendation["extractor"] == "Docling"


def test_recommend_table_heavy_extractor_without_docling() -> None:
    recommendation = recommend_table_heavy_extractor({"PyMuPDF": {}})

    assert recommendation["extractor"] is None
    assert "Run Docling" in recommendation["reasoning"]


def test_build_production_recommendation_has_all_categories() -> None:
    native_grouped = build_pdf_type_report_rows([("native_doc.pdf", NATIVE_DOC_ROWS)])
    scanned_grouped = build_pdf_type_report_rows([("scanned_doc.pdf", SCANNED_DOC_ROWS)])
    native_per_extractor = compute_group_summary(native_grouped[NATIVE_GROUP])["per_extractor"]
    scanned_per_extractor = compute_group_summary(scanned_grouped[SCANNED_GROUP])["per_extractor"]

    recommendation = build_production_recommendation(native_per_extractor, scanned_per_extractor)

    assert set(recommendation.keys()) == {"native", "scanned", "table_heavy"}
    assert recommendation["native"]["extractor"] == "PyMuPDF"
    assert recommendation["scanned"]["extractor"] == "PaddleOCR"
    assert recommendation["table_heavy"]["extractor"] == "Docling"
