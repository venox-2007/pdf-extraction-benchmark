"""Aggregation helpers for multi-document benchmark runs.

These helpers operate purely on the flat report-row schema produced by
`pdf_extraction_benchmark.reports.benchmark_report.build_report_rows`, so they
reuse metrics already computed during extraction without recomputing any of
them.
"""

from __future__ import annotations

from typing import Any

from pdf_extraction_benchmark.reports.benchmark_report import build_report_rows

EMPTY_AGGREGATE_SUMMARY: dict[str, Any] = {
    "total_documents": 0,
    "total_runs": 0,
    "success_rate": 0.0,
    "avg_extraction_time_seconds": 0.0,
    "avg_character_count": 0.0,
    "avg_word_count": 0.0,
    "avg_bounding_box_count": 0.0,
}


def build_multi_document_report_rows(
    documents: list[tuple[str, list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """Flatten per-document comparison rows into a single report-row list.

    Parameters
    ----------
    documents:
        A list of ``(document_name, comparison_rows)`` pairs, one per
        processed document, where ``comparison_rows`` is the list already
        produced by the Streamlit extraction loop for that document.

    Returns
    -------
    list[dict[str, Any]]
        Flat list of report rows (one per document/extractor combination),
        built via :func:`build_report_rows` for each document.
    """
    rows: list[dict[str, Any]] = []
    for document_name, comparison_rows in documents:
        rows.extend(build_report_rows(document_name, comparison_rows))
    return rows


def compute_aggregate_summary(report_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute overall aggregate benchmark statistics from report rows.

    Parameters
    ----------
    report_rows:
        Flat report rows as produced by :func:`build_report_rows` or
        :func:`build_multi_document_report_rows`.

    Returns
    -------
    dict[str, Any]
        Aggregate statistics with the keys ``total_documents``,
        ``total_runs``, ``success_rate``, ``avg_extraction_time_seconds``,
        ``avg_character_count``, ``avg_word_count``, and
        ``avg_bounding_box_count``. All values are ``0`` when
        ``report_rows`` is empty.
    """
    total_runs = len(report_rows)
    if total_runs == 0:
        return dict(EMPTY_AGGREGATE_SUMMARY)

    document_names = {row.get("document_name") for row in report_rows}
    successes = sum(1 for row in report_rows if row.get("status") == "success")

    def _avg(field: str) -> float:
        return sum(float(row.get(field) or 0) for row in report_rows) / total_runs

    return {
        "total_documents": len(document_names),
        "total_runs": total_runs,
        "success_rate": successes / total_runs,
        "avg_extraction_time_seconds": _avg("extraction_time_seconds"),
        "avg_character_count": _avg("character_count"),
        "avg_word_count": _avg("word_count"),
        "avg_bounding_box_count": _avg("bounding_box_count"),
    }


def compute_per_extractor_summary(
    report_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Compute aggregate benchmark statistics grouped by extractor.

    Parameters
    ----------
    report_rows:
        Flat report rows as produced by :func:`build_report_rows` or
        :func:`build_multi_document_report_rows`.

    Returns
    -------
    dict[str, dict[str, Any]]
        Mapping of extractor name to its aggregate summary, in the same
        schema as :func:`compute_aggregate_summary`.
    """
    rows_by_extractor: dict[str, list[dict[str, Any]]] = {}
    for row in report_rows:
        rows_by_extractor.setdefault(str(row.get("extractor", "")), []).append(row)

    return {
        extractor: compute_aggregate_summary(rows)
        for extractor, rows in rows_by_extractor.items()
    }
