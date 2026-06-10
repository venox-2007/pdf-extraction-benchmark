"""Benchmark report export and aggregation helpers."""

from pdf_extraction_benchmark.reports.aggregation import (
    build_multi_document_report_rows,
    compute_aggregate_summary,
    compute_per_extractor_summary,
)
from pdf_extraction_benchmark.reports.benchmark_report import (
    REPORT_FIELDS,
    build_report_rows,
    to_csv_bytes,
    to_json_bytes,
)

__all__ = [
    "REPORT_FIELDS",
    "build_multi_document_report_rows",
    "build_report_rows",
    "compute_aggregate_summary",
    "compute_per_extractor_summary",
    "to_csv_bytes",
    "to_json_bytes",
]
