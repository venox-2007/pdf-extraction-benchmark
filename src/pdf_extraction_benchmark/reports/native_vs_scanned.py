"""Native vs Scanned grouping and recommendation helpers.

These helpers operate purely on the flat report-row schema produced by
`pdf_extraction_benchmark.reports.benchmark_report.build_report_rows` and the
per-extractor aggregates from
`pdf_extraction_benchmark.reports.aggregation.compute_per_extractor_summary`,
so they reuse metrics already computed during extraction without
recomputing any of them.

Grouping is based on the ``pdf_type`` value already attached to each
comparison row by the Streamlit extraction loop (produced by
``PdfTypeClassifier``). Documents classified as ``"image"`` are grouped with
``"scanned"`` because both require OCR-capable extractors; documents
classified as ``"hybrid"`` are excluded from both groups since they don't
cleanly represent either category.
"""

from __future__ import annotations

from typing import Any

from pdf_extraction_benchmark.reports.aggregation import compute_per_extractor_summary
from pdf_extraction_benchmark.reports.benchmark_report import build_report_rows

NATIVE_GROUP = "native"
SCANNED_GROUP = "scanned"

# Maps a document's classified pdf_type to the analysis group it belongs to.
# "hybrid" documents are intentionally omitted (neither purely native nor scanned).
PDF_TYPE_TO_GROUP: dict[str, str] = {
    "native": NATIVE_GROUP,
    "scanned": SCANNED_GROUP,
    "image": SCANNED_GROUP,
}


def build_pdf_type_report_rows(
    documents: list[tuple[str, list[dict[str, Any]]]],
) -> dict[str, list[dict[str, Any]]]:
    """Group flat report rows into native/scanned buckets using ``pdf_type``.

    Parameters
    ----------
    documents:
        A list of ``(document_name, comparison_rows)`` pairs, one per
        processed document, where ``comparison_rows`` is the list already
        produced by the Streamlit extraction loop for that document
        (each row includes a ``"pdf_type"`` key from ``PdfTypeClassifier``).

    Returns
    -------
    dict[str, list[dict[str, Any]]]
        A mapping with keys ``"native"`` and ``"scanned"``, each containing
        the flat report rows (built via :func:`build_report_rows`) for
        documents/extractor runs belonging to that group.
    """
    grouped: dict[str, list[dict[str, Any]]] = {NATIVE_GROUP: [], SCANNED_GROUP: []}
    for document_name, comparison_rows in documents:
        report_rows = build_report_rows(document_name, comparison_rows)
        for report_row, comparison_row in zip(report_rows, comparison_rows, strict=False):
            pdf_type = str(comparison_row.get("pdf_type", "")).lower()
            group = PDF_TYPE_TO_GROUP.get(pdf_type)
            if group is None:
                continue
            row = dict(report_row)
            row["pdf_type"] = pdf_type
            grouped[group].append(row)
    return grouped


def compute_group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the document count and per-extractor aggregates for a group.

    Reuses :func:`compute_per_extractor_summary` for all numeric aggregates.
    """
    return {
        "total_documents": len({row.get("document_name") for row in rows}),
        "per_extractor": compute_per_extractor_summary(rows),
    }


def build_comparison_table_rows(per_extractor: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Build comparison-table rows (one per extractor) from per-extractor aggregates."""
    return [
        {
            "Extractor": extractor_name,
            "Avg Time (s)": round(summary["avg_extraction_time_seconds"], 3),
            "Avg Characters": round(summary["avg_character_count"], 1),
            "Avg Words": round(summary["avg_word_count"], 1),
            "Success Rate": f"{summary['success_rate'] * 100:.1f}%",
            "Bounding Box Count": round(summary["avg_bounding_box_count"], 1),
        }
        for extractor_name, summary in per_extractor.items()
    ]


def _most_reliable(per_extractor: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return the subset of extractors tied for the highest success rate."""
    max_success_rate = max(summary["success_rate"] for summary in per_extractor.values())
    return {
        name: summary
        for name, summary in per_extractor.items()
        if summary["success_rate"] == max_success_rate
    }


def recommend_native_extractor(per_extractor: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Recommend an extractor for native PDFs based on speed and reliability.

    Among extractors tied for the highest observed success rate, picks the
    one with the lowest average extraction time (fastest "no-OCR-needed"
    path), and reports its average character coverage for context.
    """
    if not per_extractor:
        return {
            "extractor": None,
            "reasoning": "No native PDF benchmark data available yet.",
        }

    reliable = _most_reliable(per_extractor)
    name, summary = min(reliable.items(), key=lambda item: item[1]["avg_extraction_time_seconds"])
    reasoning = (
        f"{name} is recommended for native PDFs: it has the fastest average "
        f"extraction time ({summary['avg_extraction_time_seconds']:.3f}s) among "
        f"extractors with the highest observed success rate "
        f"({summary['success_rate'] * 100:.0f}%), while still extracting "
        f"{summary['avg_character_count']:.0f} characters on average — strong "
        "text coverage without OCR overhead."
    )
    return {"extractor": name, "reasoning": reasoning}


def recommend_scanned_extractor(per_extractor: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Recommend an extractor for scanned PDFs based on text recovery and reliability.

    Among extractors tied for the highest observed success rate, picks the
    one with the highest average character count (best OCR text recovery).
    """
    if not per_extractor:
        return {
            "extractor": None,
            "reasoning": "No scanned PDF benchmark data available yet.",
        }

    reliable = _most_reliable(per_extractor)
    name, summary = max(reliable.items(), key=lambda item: item[1]["avg_character_count"])
    reasoning = (
        f"{name} is recommended for scanned PDFs: it recovers the most text on "
        f"average ({summary['avg_character_count']:.0f} characters) among "
        f"extractors with the highest observed success rate "
        f"({summary['success_rate'] * 100:.0f}%) on image-based documents, "
        "indicating consistent OCR text recovery."
    )
    return {"extractor": name, "reasoning": reasoning}


def recommend_table_heavy_extractor(
    *per_extractor_summaries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Recommend an extractor for table-heavy documents.

    No dedicated table-extraction accuracy benchmark exists in this project
    yet, so this recommendation is based on which extractors were actually
    run and which of those produce structured table output (``Docling`` is
    currently the only extractor that maps tables to row/column cells).
    """
    extractors_run: set[str] = set()
    for summary in per_extractor_summaries:
        extractors_run.update(summary.keys())

    if "Docling" in extractors_run:
        return {
            "extractor": "Docling",
            "reasoning": (
                "Docling is the only extractor in this benchmark run that produces "
                "structured table cells (rows/columns) rather than plain text, "
                "making it the recommended choice for table-heavy documents. "
                "No dedicated table-extraction accuracy benchmark exists yet."
            ),
        }
    return {
        "extractor": None,
        "reasoning": (
            "Run Docling on at least one document to evaluate table-heavy document extraction."
        ),
    }


def build_production_recommendation(
    native_per_extractor: dict[str, dict[str, Any]],
    scanned_per_extractor: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build the combined Native / Scanned / Table-heavy production recommendation."""
    return {
        "native": recommend_native_extractor(native_per_extractor),
        "scanned": recommend_scanned_extractor(scanned_per_extractor),
        "table_heavy": recommend_table_heavy_extractor(native_per_extractor, scanned_per_extractor),
    }
