"""Minimal professional Streamlit app for PDF extraction benchmarking."""

from __future__ import annotations

import json
import re
import sys
import time
from importlib import import_module
from pathlib import Path
from typing import Any

import fitz
import pandas as pd
import streamlit as st

# Import torch before paddle: on Windows, paddle's DLL search path additions
# break torch's shm.dll loading (WinError 127) if paddle loads first. Importing
# torch here ensures its DLLs are loaded before PaddleocrExtractor pulls in paddle.
import torch  # noqa: E402,F401

# Ensure local src package imports resolve when launching Streamlit directly.
SRC_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import (  # noqa: E402
    RvlCdipBenchmarkPipeline,
    RvlCdipBenchmarkSummary,
)
from pdf_extraction_benchmark.classifiers.pdf_type_classifier import PdfTypeClassifier  # noqa: E402
from pdf_extraction_benchmark.extractors.opendataloader.extractor import (  # noqa: E402
    OpendataloaderExtractor,
)
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.tesseract.extractor import TesseractExtractor  # noqa: E402
from pdf_extraction_benchmark.models.extraction_result import (  # noqa: E402
    ExtractionMetadata,
    ExtractionResult,
)
from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser  # noqa: E402
from pdf_extraction_benchmark.reports.aggregation import (  # noqa: E402
    build_multi_document_report_rows,
    compute_aggregate_summary,
    compute_per_extractor_summary,
)
from pdf_extraction_benchmark.reports.benchmark_report import (  # noqa: E402
    to_csv_bytes,
    to_json_bytes,
)
from pdf_extraction_benchmark.reports.native_vs_scanned import (  # noqa: E402
    NATIVE_GROUP,
    SCANNED_GROUP,
    build_comparison_table_rows,
    build_pdf_type_report_rows,
    build_production_recommendation,
    compute_group_summary,
    recommend_native_extractor,
    recommend_scanned_extractor,
)
from pdf_extraction_benchmark.utils.logger import configure_logging  # noqa: E402
from pdf_extraction_benchmark.utils.opendataloader_hybrid import (  # noqa: E402
    ensure_hybrid_server,
)
from pdf_extraction_benchmark.visualization.bbox_overlay import (  # noqa: E402
    build_page_visualizations,
    get_extractor_color,
    get_extractor_source_dpi,
    has_bounding_boxes,
)

APP_NAME = "DocuVision AI"
APP_SUBTITLE = "Clean PDF intelligence with multiple extraction backends"
SUPPORTED_UPLOAD_TYPES = ["pdf", "png", "jpg", "jpeg", "tif", "tiff"]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

RECOMMENDATIONS = {
    "native": ["OpenDataLoader", "PyMuPDF"],
    "hybrid": ["PaddleOCR + PyMuPDF", "OpenDataLoader + OCR fallback"],
    "scanned": ["PaddleOCR", "Docling", "Tesseract"],
    "image": ["PaddleOCR", "Tesseract"],
}

EXTRACTOR_OPTIONS = {
    "OpenDataLoader": OpendataloaderExtractor,
    "PyMuPDF": PymupdfExtractor,
    "Docling": None,
    "PaddleOCR": PaddleocrExtractor,
    "Tesseract": TesseractExtractor,
}

EXTRACTOR_CAPABILITIES = {
    "OpenDataLoader": {
        "ocr_supported": True,
        "supports_pdf": True,
        "supports_image": False,
        "markdown_support": True,
        "layout_preservation_support": True,
    },
    "PyMuPDF": {
        "ocr_supported": False,
        "supports_pdf": True,
        "supports_image": False,
        "markdown_support": False,
        "layout_preservation_support": True,
    },
    "Docling": {
        "ocr_supported": True,
        "supports_pdf": True,
        "supports_image": False,
        "markdown_support": True,
        "layout_preservation_support": True,
    },
    "PaddleOCR": {
        "ocr_supported": True,
        "supports_pdf": True,
        "supports_image": True,
        "markdown_support": False,
        "layout_preservation_support": False,
    },
    "Tesseract": {
        "ocr_supported": True,
        "supports_pdf": True,
        "supports_image": True,
        "markdown_support": False,
        "layout_preservation_support": False,
    },
}

PADDLEOCR_LANGUAGE_OPTIONS = {
    "English": "english",
    "Multilingual (Hindi/Marathi/Devanagari)": "multilingual",
}

RVL_CDIP_EXTRACTOR_ORDER = ["PyMuPDF", "OpenDataLoader", "PaddleOCR", "Docling", "Tesseract"]
RVL_CDIP_SAMPLE_SIZE_OPTIONS = [1, 3, 5, 10]
RVL_CDIP_LOW_YIELD_WORD_THRESHOLD = 20.0

OPENDATALOADER_MODE_OPTIONS = {
    "Auto (Recommended)": "auto",
    "Standard": "standard",
    "Hybrid": "hybrid",
}

OPENDATALOADER_MODE_DESCRIPTIONS = {
    "auto": (
        "Auto: uses OpenDataLoader's standard pipeline for native PDFs and "
        "switches to Hybrid OCR mode for scanned/image PDFs. This is the "
        "existing default behavior."
    ),
    "standard": (
        "Standard: always uses OpenDataLoader's native pipeline. The hybrid "
        "OCR server is never started or used, even for scanned PDFs."
    ),
    "hybrid": (
        "Hybrid: always uses OpenDataLoader Hybrid mode (Docling/OCR "
        "backend), including for native PDFs. The hybrid server is started "
        "if it isn't already running."
    ),
}


def _extractor_slug(extractor_name: str) -> str:
    """Convert extractor display name into output folder slug."""
    return extractor_name.lower().replace(" ", "")


def _paddleocr_language_label(language_mode: str) -> str:
    """Convert a PaddleOCR language mode into a UI label."""
    for label, value in PADDLEOCR_LANGUAGE_OPTIONS.items():
        if value == language_mode:
            return label
    return "English"


def _detect_input_type(input_path: Path) -> str:
    """Return a display-friendly input type for supported uploads."""
    if input_path.suffix.lower() == ".pdf":
        return "PDF"
    if input_path.suffix.lower() in IMAGE_EXTENSIONS:
        return "Image"
    return "Unsupported"


def _build_unsupported_image_result(
    extractor_name: str,
    input_path: Path,
) -> list[ExtractionResult]:
    """Return a schema-compatible unsupported result for PDF-only extractors."""
    return [
        ExtractionResult(
            tool_name=_extractor_slug(extractor_name),
            page_number=1,
            extracted_text="",
            tables=[],
            bounding_boxes=[],
            confidence_scores=[],
            metadata=ExtractionMetadata(
                source_file=input_path.name,
                extra={
                    "status": "unsupported_for_image_input",
                    "extractor": _extractor_slug(extractor_name),
                    "input_type": "image",
                    "ocr_supported": False,
                    "ocr_used": False,
                    "ocr_required": True,
                    "total_page_count": 1,
                    "reason": f"{extractor_name} supports PDF input only.",
                },
            ),
        )
    ]


def _create_extractor(extractor_name: str, paddleocr_language_mode: str) -> Any:
    """Instantiate the selected extractor with any UI-provided configuration."""
    extractor_cls = EXTRACTOR_OPTIONS[extractor_name]
    if extractor_name == "Docling":
        extractor_cls = import_module(
            "pdf_extraction_benchmark.extractors.docling.extractor"
        ).DoclingExtractor
    if extractor_name == "PaddleOCR":
        return extractor_cls(language_mode=paddleocr_language_mode)
    return extractor_cls()


def _get_result_status(results: list[ExtractionResult]) -> str:
    """Extract the first explicit result status, if available."""
    for result in results:
        if result.metadata is None:
            continue
        status = result.metadata.extra.get("status")
        if isinstance(status, str) and status:
            return status
    return ""


def _inject_styles() -> None:
    """Apply lightweight styling for clean spacing and typography."""
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 1.4rem;
                max-width: 1050px;
            }
            h1, h2, h3 {
                letter-spacing: 0.2px;
            }
            .subtitle {
                color: #a8b3c7;
                margin-top: -0.2rem;
                margin-bottom: 1rem;
                font-size: 0.95rem;
            }
            .meta-card {
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 10px;
                padding: 0.8rem;
                background: rgba(15, 23, 42, 0.25);
            }
            .summary-card {
                border: 1px solid rgba(148, 163, 184, 0.22);
                border-radius: 12px;
                padding: 0.9rem 1rem;
                background: rgba(15, 23, 42, 0.28);
                margin-bottom: 0.8rem;
            }
            .summary-title {
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: #9fb2d8;
                margin-bottom: 0.3rem;
            }
            .summary-value {
                font-size: 1.15rem;
                font-weight: 700;
                color: #e6edf9;
            }
            .doc-card-native {
                border-left: 4px solid #3fb950;
            }
            .doc-card-hybrid {
                border-left: 4px solid #f1c40f;
            }
            .doc-card-scanned {
                border-left: 4px solid #58a6ff;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _read_text_safely(path: Path) -> str:
    """Read text using robust fallback decoding for Windows-generated files."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="cp1252")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1")


def _save_outputs(
    json_payload: dict[str, object],
    markdown_text: str,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Save unified JSON and markdown outputs for one extractor run."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_output = output_dir / "result.json"
    md_output = output_dir / "result.md"
    json_output.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    md_output.write_text(markdown_text, encoding="utf-8")
    return json_output, md_output


def _build_scanned_page_image_markdown(
    pdf_path: Path,
    markdown_root_dir: Path,
    extractor_slug: str,
) -> str:
    """Render full-page PNGs and return markdown image links for scanned PDFs."""
    image_dir = markdown_root_dir / extractor_slug / "images" / pdf_path.stem
    image_dir.mkdir(parents=True, exist_ok=True)

    lines = ["## Scanned Page Images", ""]
    with fitz.open(pdf_path) as doc:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(dpi=150)
            image_path = image_dir / f"page_{page_index + 1}.png"
            pix.save(image_path)
            relative = image_path.relative_to(markdown_root_dir).as_posix()
            lines.append(f"### Page {page_index + 1}")
            lines.append(f"![Page {page_index + 1}]({relative})")
            lines.append("")

    return "\n".join(lines).strip()


def _build_comparison_observations(
    rows: list[dict[str, object]],
    classification: Any | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Generate run-specific findings and a recommendation card payload."""
    notes: list[str] = []
    recommendation = {"primary": "-", "secondary": "-", "reason": "No extractor results available."}
    if not rows:
        return notes, recommendation

    completed_rows = [row for row in rows if str(row.get("status", "")) != "failed"]
    completed_rows = completed_rows if completed_rows else rows
    usable_rows = [
        row
        for row in completed_rows
        if str(row.get("status", "")).startswith("success") and int(row.get("text_length", 0)) > 0
    ]
    quality_rows = usable_rows if usable_rows else completed_rows
    pdf_type = str(rows[0].get("pdf_type", "unknown")).lower()
    classifier_reason = ""
    if classification is not None:
        classifier_reason = str(getattr(classification, "reasoning", "")).strip()

    fastest = min(completed_rows, key=lambda row: float(row.get("latency_seconds", 0.0)))
    most_text = max(quality_rows, key=lambda row: int(row.get("text_length", 0)))
    richest_markdown = max(quality_rows, key=lambda row: int(row.get("markdown_length", 0)))

    ocr_required = pdf_type in {"image", "scanned", "hybrid"} or any(
        int(row.get("ocr_required_pages", 0)) > 0 for row in rows
    )
    notes.append(
        "OCR-capable extraction is needed for this document."
        if ocr_required
        else "Direct text extraction is enough for this document."
    )

    fastest_name = str(fastest.get("extractor", "-"))
    fastest_latency = float(fastest.get("latency_seconds", 0.0))
    fastest_text_length = int(fastest.get("text_length", 0))
    if fastest_text_length > 0:
        notes.append(
            f"{fastest_name} was fastest ({fastest_latency:.3f}s) with "
            f"{fastest_text_length:,} chars extracted."
        )
    else:
        notes.append(
            f"{fastest_name} was fastest ({fastest_latency:.3f}s), but produced no usable text."
        )

    most_text_name = str(most_text.get("extractor", "-"))
    most_text_length = int(most_text.get("text_length", 0))
    notes.append(f"{most_text_name} recovered the most usable text ({most_text_length:,} chars).")
    if str(richest_markdown.get("extractor", "")) != most_text_name:
        notes.append(
            f"{richest_markdown['extractor']} produced the richest markdown "
            f"({int(richest_markdown.get('markdown_length', 0)):,} chars)."
        )

    failed = [
        str(row.get("extractor", "")) for row in rows if str(row.get("status", "")) == "failed"
    ]
    limited = [
        str(row.get("extractor", ""))
        for row in rows
        if "limited" in str(row.get("status", ""))
        or "empty" in str(row.get("status", ""))
        or (
            pdf_type == "scanned"
            and not bool(row.get("ocr_supported"))
            and int(row.get("text_length", 0))
            < max(100, int(most_text.get("text_length", 0)) // 10)
        )
    ]
    if failed:
        notes.append(f"Failed extractor(s): {', '.join(failed)}.")
    elif limited:
        notes.append(f"Limited/low-text output: {', '.join(limited)}.")
    else:
        notes.append("All selected extractors completed successfully.")

    ocr_rows = [row for row in quality_rows if bool(row.get("ocr_supported"))]
    ocr_winner = max(ocr_rows, key=lambda row: int(row.get("text_length", 0))) if ocr_rows else None

    if pdf_type == "scanned":
        primary = (
            str(ocr_winner.get("extractor")) if ocr_winner else str(most_text.get("extractor"))
        )
        secondary = (
            str(fastest.get("extractor")) if str(fastest.get("extractor")) != primary else "-"
        )
        reason = (
            f"Scanned PDF detected. `{primary}` recovered the most usable text for this run."
            if primary != "-"
            else "Scanned PDF detected. OCR-capable extractor is recommended."
        )
    elif pdf_type == "image":
        primary = (
            str(ocr_winner.get("extractor")) if ocr_winner else str(most_text.get("extractor"))
        )
        secondary = (
            str(fastest.get("extractor")) if str(fastest.get("extractor")) != primary else "-"
        )
        reason = (
            f"Image input detected. `{primary}` recovered the most usable OCR text."
            if primary != "-"
            else "Image input detected. OCR-capable extraction is recommended."
        )
    elif pdf_type == "hybrid":
        primary = str(most_text.get("extractor"))
        secondary = (
            str(ocr_winner.get("extractor")) if ocr_winner else str(fastest.get("extractor"))
        )
        if secondary == primary:
            secondary = (
                str(fastest.get("extractor")) if str(fastest.get("extractor")) != primary else "-"
            )
        reason = (
            "Hybrid PDF detected with both text and image-heavy signals. "
            f"Use `{primary}` as primary and `{secondary}` as secondary for OCR recovery."
        )
    else:
        primary = str(most_text.get("extractor"))
        secondary = (
            str(fastest.get("extractor")) if str(fastest.get("extractor")) != primary else "-"
        )
        reason = (
            "Native PDF detected with strong extractable text. "
            f"`{primary}` gave the strongest text result on this run."
        )

    if classifier_reason:
        reason = f"{reason} Classifier: {classifier_reason}"
    recommendation = {"primary": primary, "secondary": secondary, "reason": reason}

    return notes[:5], recommendation


def _render_recommendation_card(recommendation: dict[str, str]) -> None:
    """Render a concise recommendation card for this PDF run."""
    if not recommendation:
        return
    st.markdown("### Recommended Pipeline")
    st.markdown(
        (
            '<div class="summary-card">'
            '<div class="summary-title">Primary</div>'
            f'<div class="summary-value">{recommendation.get("primary", "-")}</div>'
            '<div style="margin-top:0.7rem" class="summary-title">Secondary</div>'
            f'<div class="summary-value">{recommendation.get("secondary", "-")}</div>'
            '<div style="margin-top:0.7rem"><b>Reason:</b> '
            f"{recommendation.get('reason', '-')}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def _build_markdown_from_results(results: list[Any], extractor_name: str) -> str:
    """Build plain markdown-like text from standardized extraction results."""
    parts: list[str] = []
    for result in results:
        page_text = result.extracted_text.strip()
        if page_text:
            parts.append(page_text)
    return "\n\n".join(parts).strip()


def _render_document_summary(meta: dict[str, Any]) -> None:
    """Render document summary and classification card."""
    pdf_type = str(meta.get("pdf_type", "unknown")).lower()
    card_type = f"doc-card-{pdf_type}" if pdf_type in {"native", "hybrid", "scanned"} else ""
    recommendations = ", ".join(RECOMMENDATIONS.get(pdf_type, []))
    input_type = str(meta.get("input_type", "PDF"))
    st.markdown("### Document Summary")
    st.markdown(
        (
            f'<div class="summary-card {card_type}">'
            f'<div class="summary-title">File</div>'
            f'<div class="summary-value">{meta.get("file_name", "-")}</div>'
            f'<div style="margin-top:0.7rem" class="summary-title">Input Type</div>'
            f'<div class="summary-value">{input_type}</div>'
            f'<div style="margin-top:0.7rem" class="summary-title">Document Type</div>'
            f'<div class="summary-value">{str(meta.get("pdf_type", "unknown")).title()}</div>'
            f'<div style="margin-top:0.7rem"><b>Confidence:</b> '
            f"{meta.get('classification_confidence', 0.0) * 100:.0f}%</div>"
            f'<div style="margin-top:0.35rem"><b>Why this type:</b> '
            f"{meta.get('classification_reasoning', '-')}</div>"
            f'<div style="margin-top:0.35rem"><b>Recommended Extractors:</b> '
            f"{recommendations}</div>"
            f"</div>"
        ),
        unsafe_allow_html=True,
    )


def _render_overview_cards(meta: dict[str, Any], comparison_rows: list[dict[str, Any]]) -> None:
    """Render extraction overview metric cards."""
    st.markdown("### Extraction Overview")
    total_pages = meta.get("total_pdf_pages", 0)
    processed_pages = 0
    total_time = 0.0
    if comparison_rows:
        processed_pages = max(int(row.get("processed_pages", 0)) for row in comparison_rows)
        total_time = sum(float(row.get("latency_seconds", 0.0)) for row in comparison_rows)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pages", str(total_pages))
    c2.metric("Processed Pages", str(processed_pages))
    c3.metric("Extraction Time", f"{total_time:.2f}s")
    c4.metric("Selected Extractors", str(len(meta.get("selected_extractors", []))))


def _format_comparison_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Format comparison rows with compact highlights and labels."""
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    fastest_idx = df["latency_seconds"].astype(float).idxmin()
    text_idx = df["text_length"].astype(int).idxmax()
    df["extractor"] = [
        f"{name} (fastest)"
        if idx == fastest_idx
        else f"{name} (most text)"
        if idx == text_idx
        else name
        for idx, name in enumerate(df["extractor"])
    ]
    df["status"] = df["status"].map(
        lambda s: "success" if s == "success" else f"warning: {s}" if s else "warning: unknown"
    )
    df = df.rename(
        columns={
            "extractor": "Extractor",
            "latency_seconds": "Time (s)",
            "total_pages": "Total Pages",
            "processed_pages": "Processed Pages",
            "text_length": "Text Length",
            "markdown_length": "Markdown Length",
            "ocr_required_pages": "OCR Pages",
            "status": "Status",
            "pdf_type": "Type",
        }
    )
    display_cols = [
        "Extractor",
        "Time (s)",
        "Total Pages",
        "Processed Pages",
        "Text Length",
        "Markdown Length",
        "OCR Pages",
        "Status",
        "Type",
    ]
    return df[display_cols]


def _build_comparison_analysis_df(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Build the side-by-side comparison table for the Comparison Analysis section."""
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df = df.rename(
        columns={
            "extractor": "Extractor",
            "latency_seconds": "Extraction Time (s)",
            "char_count": "Character Count",
            "word_count": "Word Count",
            "bbox_count": "Bounding Box Count",
        }
    )
    return df[
        [
            "Extractor",
            "Extraction Time (s)",
            "Character Count",
            "Word Count",
            "Bounding Box Count",
        ]
    ]


def _build_capabilities_df(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Build the static per-extractor capabilities table."""
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df = df.rename(
        columns={
            "extractor": "Extractor",
            "markdown_support": "Markdown Support",
            "layout_preservation_support": "Layout Preservation Support",
        }
    )
    return df[["Extractor", "Markdown Support", "Layout Preservation Support"]]


def _render_comparison_charts(rows: list[dict[str, Any]]) -> None:
    """Render bar charts comparing key metrics across extractors."""
    df = pd.DataFrame(rows).set_index("extractor")

    st.caption("Extraction Time (s)")
    st.bar_chart(df[["latency_seconds"]])
    st.caption("Character & Word Count")
    st.bar_chart(df[["char_count", "word_count"]])
    st.caption("Bounding Box Count")
    st.bar_chart(df[["bbox_count"]])


def _build_best_per_category(rows: list[dict[str, Any]]) -> dict[str, str]:
    """Determine the best extractor for each comparison category."""
    successful_rows = [row for row in rows if row.get("status") == "success"]
    if not successful_rows:
        return {}

    best: dict[str, str] = {}
    best["Fastest Extractor"] = min(successful_rows, key=lambda row: row["latency_seconds"])[
        "extractor"
    ]
    best["Most Bounding Boxes Detected"] = max(successful_rows, key=lambda row: row["bbox_count"])[
        "extractor"
    ]

    return best


def _render_best_per_category_card(best: dict[str, str]) -> None:
    """Render the 'Best Tool Per Category' summary card."""
    if not best:
        return
    st.markdown("### Best Tool Per Category")
    rows_html = "".join(
        '<div style="margin-top:0.5rem">'
        f'<span class="summary-title">{category}</span><br>'
        f'<span class="summary-value">{extractor_name}</span>'
        "</div>"
        for category, extractor_name in best.items()
    )
    st.markdown(
        f'<div class="summary-card">{rows_html}</div>',
        unsafe_allow_html=True,
    )


def _render_comparison_analysis(rows: list[dict[str, Any]]) -> None:
    """Render the full Comparison Analysis section: table, charts, and best-tool card."""
    if not rows:
        return
    st.markdown("## Comparison Analysis")

    st.markdown("#### Side-by-Side Metrics")
    st.dataframe(_build_comparison_analysis_df(rows), width="stretch")

    st.markdown("#### Visual Comparison")
    _render_comparison_charts(rows)

    _render_best_per_category_card(_build_best_per_category(rows))

    st.markdown("### Capabilities")
    st.caption(
        "Markdown and layout preservation support are static per-extractor "
        "capabilities, not measurements derived from this document."
    )
    st.dataframe(_build_capabilities_df(rows), width="stretch")


def _table_to_dataframe(table: Any) -> pd.DataFrame:
    """Convert an ExtractedTable into a 2D grid for display."""
    if not table.cells:
        return pd.DataFrame()
    max_row = max(cell.row for cell in table.cells)
    max_col = max(cell.col for cell in table.cells)
    grid = [["" for _ in range(max_col + 1)] for _ in range(max_row + 1)]
    for cell in table.cells:
        grid[cell.row][cell.col] = cell.text
    return pd.DataFrame(grid)


def _render_markdown_output_preview(markdown_text: str) -> None:
    """Render the shared markdown-output preview block."""
    st.markdown("**Markdown Output Preview**")
    if markdown_text.strip():
        preview = markdown_text.strip()[:1000]
        st.code(preview + ("..." if len(markdown_text.strip()) > 1000 else ""), language="markdown")
    else:
        st.caption("No markdown output produced for this document.")


def _render_layout_structure_preview(results: list[Any]) -> None:
    """Render the shared layout-structure (bounding box) preview block."""
    st.markdown("**Layout Structure Preview**")
    layout_rows = [
        {
            "Page": result.page_number,
            "Layout Regions": len(result.bounding_boxes),
            "First Region (x0, y0, x1, y1)": (
                f"({result.bounding_boxes[0].x0:.1f}, {result.bounding_boxes[0].y0:.1f}, "
                f"{result.bounding_boxes[0].x1:.1f}, {result.bounding_boxes[0].y1:.1f})"
                if result.bounding_boxes
                else "-"
            ),
        }
        for result in results
    ]
    if layout_rows:
        st.dataframe(pd.DataFrame(layout_rows), width="stretch")
    else:
        st.caption("No layout structure detected for this document.")


def _render_docling_advanced_features(results: list[Any], markdown_text: str) -> None:
    """Render Docling-specific document understanding features."""
    all_tables = [table for result in results for table in result.tables]

    st.markdown("**Tables Detected**")
    st.write(len(all_tables))

    st.markdown("**Table Preview**")
    if all_tables:
        for table_index, table in enumerate(all_tables[:3], start=1):
            st.caption(f"Table {table_index} (`{table.table_id}`)")
            st.dataframe(_table_to_dataframe(table), width="stretch")
    else:
        st.caption("No tables detected in this document.")

    _render_markdown_output_preview(markdown_text)
    _render_layout_structure_preview(results)


def _render_opendataloader_advanced_features(results: list[Any], markdown_text: str) -> None:
    """Render OpenDataLoader document understanding features.

    OpenDataLoader does not produce structured table cells (`_map_kids_to_results`
    leaves `tables` empty), but it does produce real markdown output and
    layout bounding boxes, so those previews reuse the same rendering as Docling.
    """
    st.markdown("**Tables Detected**")
    st.caption("Not Supported")

    st.markdown("**Table Preview**")
    st.caption("Not Supported")

    _render_markdown_output_preview(markdown_text)
    _render_layout_structure_preview(results)


def _render_unsupported_advanced_features() -> None:
    """Render placeholder rows for extractors without advanced document features."""
    st.dataframe(
        pd.DataFrame(
            {
                "Feature": [
                    "Tables Detected",
                    "Table Preview",
                    "Markdown Output Preview",
                    "Layout Structure Preview",
                ],
                "Status": ["Not Supported", "Not Supported", "N/A", "Not Supported"],
            }
        ),
        width="stretch",
        hide_index=True,
    )


def _build_document_benchmark_df(report_rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Build the display dataframe for the Document Benchmark Results table.

    Reuses the flat report-row schema (document name, extractor, extraction
    time, character/word/bbox counts, status, error message) without
    recomputing any metric.
    """
    if not report_rows:
        return pd.DataFrame()
    df = pd.DataFrame(report_rows)
    df = df.rename(
        columns={
            "document_name": "Document Name",
            "extractor": "Extractor",
            "extraction_time_seconds": "Extraction Time (s)",
            "character_count": "Character Count",
            "word_count": "Word Count",
            "bounding_box_count": "Bounding Box Count",
            "status": "Status",
            "error_message": "Error Message",
        }
    )
    return df[
        [
            "Document Name",
            "Extractor",
            "Extraction Time (s)",
            "Character Count",
            "Word Count",
            "Bounding Box Count",
            "Status",
            "Error Message",
        ]
    ]


def _render_document_benchmark_results(report_rows: list[dict[str, Any]]) -> None:
    """Render the 'Document Benchmark Results' table for all processed documents."""
    if not report_rows:
        return
    st.markdown("## Document Benchmark Results")
    st.dataframe(_build_document_benchmark_df(report_rows), width="stretch")


def _build_aggregate_summary_df(per_extractor_summary: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """Build the per-extractor aggregate statistics table."""
    if not per_extractor_summary:
        return pd.DataFrame()
    rows = []
    for extractor_name, summary in per_extractor_summary.items():
        rows.append(
            {
                "Extractor": extractor_name,
                "Total Runs": summary["total_runs"],
                "Success Rate": f"{summary['success_rate'] * 100:.1f}%",
                "Avg Extraction Time (s)": round(summary["avg_extraction_time_seconds"], 3),
                "Avg Character Count": round(summary["avg_character_count"], 1),
                "Avg Word Count": round(summary["avg_word_count"], 1),
                "Avg Layout Regions": round(summary["avg_bounding_box_count"], 1),
            }
        )
    return pd.DataFrame(rows)


def _render_aggregate_summary(report_rows: list[dict[str, Any]]) -> None:
    """Render the 'Aggregate Benchmark Summary' section.

    Computes overall and per-extractor aggregate statistics from the flat
    report rows already produced for the Document Benchmark Results table,
    without recomputing any underlying metric.
    """
    if not report_rows:
        return
    overall = compute_aggregate_summary(report_rows)
    per_extractor = compute_per_extractor_summary(report_rows)

    st.markdown("## Aggregate Benchmark Summary")

    st.markdown("#### Overall")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Documents Processed", str(overall["total_documents"]))
    c2.metric("Total Benchmark Runs", str(overall["total_runs"]))
    c3.metric("Success Rate", f"{overall['success_rate'] * 100:.1f}%")
    c4, c5, c6 = st.columns(3)
    c4.metric("Avg Extraction Time (s)", f"{overall['avg_extraction_time_seconds']:.3f}")
    c5.metric("Avg Character Count", f"{overall['avg_character_count']:.1f}")
    c6.metric("Avg Word Count", f"{overall['avg_word_count']:.1f}")
    st.metric("Avg Layout Regions", f"{overall['avg_bounding_box_count']:.1f}")

    st.markdown("#### Per Extractor")
    st.dataframe(_build_aggregate_summary_df(per_extractor), width="stretch")


def _render_extractor_recommendation_card(title: str, recommendation: dict[str, Any]) -> None:
    """Render a 'Best Extractor' style card with a recommendation and reasoning."""
    extractor_name = recommendation.get("extractor") or "Not enough data"
    reasoning = recommendation.get("reasoning", "")
    st.markdown(
        f'<div class="summary-card">'
        f'<span class="summary-title">{title}</span><br>'
        f'<span class="summary-value">{extractor_name}</span>'
        f'<div style="margin-top:0.5rem">{reasoning}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_production_recommendation_card(recommendation: dict[str, dict[str, Any]]) -> None:
    """Render the final 'Production Recommendation' card covering all document categories."""
    labels = {
        "native": "Native PDFs",
        "scanned": "Scanned PDFs",
        "table_heavy": "Table-heavy Documents",
    }
    rows_html = "".join(
        '<div style="margin-top:0.75rem">'
        f'<span class="summary-title">{labels[category]}</span><br>'
        f'<span class="summary-value">{value.get("extractor") or "Not enough data"}</span>'
        f'<div style="margin-top:0.25rem">{value.get("reasoning", "")}</div>'
        "</div>"
        for category, value in recommendation.items()
    )
    st.markdown(
        f'<div class="summary-card">{rows_html}</div>',
        unsafe_allow_html=True,
    )


def _render_pdf_type_group_analysis(
    title: str, group_rows: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Render Summary Metrics, Comparison Table, charts, and best-extractor card for one group.

    `group_rows` is the flat report-row list for one pdf_type group, already
    built via `build_pdf_type_report_rows`. Returns the per-extractor summary
    so it can be reused for the production recommendation section.
    """
    if not group_rows:
        st.caption(f"No {title.lower()} processed yet.")
        return {}

    overall = compute_aggregate_summary(group_rows)
    group_summary = compute_group_summary(group_rows)
    per_extractor = group_summary["per_extractor"]

    st.markdown("#### Summary Metrics")
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Total {title}", str(group_summary["total_documents"]))
    c2.metric("Avg Processing Time (s)", f"{overall['avg_extraction_time_seconds']:.3f}")
    c3.metric("Success Rate", f"{overall['success_rate'] * 100:.1f}%")
    c4, c5 = st.columns(2)
    c4.metric("Avg Character Count", f"{overall['avg_character_count']:.1f}")
    c5.metric("Avg Word Count", f"{overall['avg_word_count']:.1f}")

    st.markdown("#### Comparison Table")
    st.dataframe(pd.DataFrame(build_comparison_table_rows(per_extractor)), width="stretch")

    st.markdown("#### Visual Comparison")
    chart_df = pd.DataFrame(
        {
            extractor_name: {
                "avg_extraction_time_seconds": summary["avg_extraction_time_seconds"],
                "success_rate": summary["success_rate"],
            }
            for extractor_name, summary in per_extractor.items()
        }
    ).T
    st.caption("Average Extraction Time by Extractor (s)")
    st.bar_chart(chart_df[["avg_extraction_time_seconds"]])
    st.caption("Success Rate by Extractor")
    st.bar_chart(chart_df[["success_rate"]])

    return per_extractor


def _render_native_vs_scanned_analysis(documents: list[dict[str, Any]]) -> None:
    """Render the 'Native vs Scanned Analysis' tab.

    Groups all processed documents' extractor runs into native and scanned
    buckets using the `pdf_type` already assigned by `PdfTypeClassifier`
    during extraction (see `_process_document`), then reuses
    `reports/aggregation.py` helpers to compute per-extractor statistics for
    each bucket without recomputing any underlying metric.
    """
    if not documents:
        st.info("Run an extraction to see the native vs scanned analysis.")
        return

    grouped = build_pdf_type_report_rows(
        [(doc["file_name"], doc["comparison_rows"]) for doc in documents]
    )

    st.markdown("## Native PDF Analysis")
    native_per_extractor = _render_pdf_type_group_analysis(
        "Native Documents", grouped[NATIVE_GROUP]
    )
    if native_per_extractor:
        _render_extractor_recommendation_card(
            "Best Native Extractor", recommend_native_extractor(native_per_extractor)
        )

    st.markdown("## Scanned PDF Analysis")
    if "OpenDataLoader" in {row.get("extractor") for row in grouped[SCANNED_GROUP]}:
        st.caption(
            "OpenDataLoader (scanned): OCR via Docling hybrid backend "
            "(docling-fast + rapidocr) — not an independent OCR engine."
        )
    scanned_per_extractor = _render_pdf_type_group_analysis(
        "Scanned Documents", grouped[SCANNED_GROUP]
    )
    if scanned_per_extractor:
        _render_extractor_recommendation_card(
            "Best Scanned Extractor", recommend_scanned_extractor(scanned_per_extractor)
        )

    if native_per_extractor or scanned_per_extractor:
        st.markdown("## Production Recommendation")
        _render_production_recommendation_card(
            build_production_recommendation(native_per_extractor, scanned_per_extractor)
        )


def _render_export_controls(report_rows: list[dict[str, Any]], file_stem: str) -> None:
    """Render CSV/JSON download buttons for the current benchmark results.

    `report_rows` is the flat report-row list (one row per document/extractor
    combination) already built via `build_multi_document_report_rows`; this
    function only serializes and renders, performing no computation of its
    own.
    """
    if not report_rows:
        return

    csv_bytes = to_csv_bytes(report_rows)
    json_bytes = to_json_bytes(report_rows)

    st.markdown("### Export Results")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download CSV",
            data=csv_bytes,
            file_name=f"{file_stem}_benchmark_report.csv",
            mime="text/csv",
            key="download_benchmark_csv",
        )
    with col2:
        st.download_button(
            label="Download JSON",
            data=json_bytes,
            file_name=f"{file_stem}_benchmark_report.json",
            mime="application/json",
            key="download_benchmark_json",
        )


def _render_advanced_document_features(
    extractor_results: dict[str, list[Any]],
    extractor_markdown: dict[str, str],
) -> None:
    """Render extractor-specific advanced document understanding features.

    These capabilities are not supported uniformly across extractors and are
    intentionally kept separate from the side-by-side comparison metrics.
    """
    if not extractor_results:
        return

    st.markdown("## Advanced Document Features")
    st.caption(
        "Extractor-specific document understanding capabilities. These highlight "
        "what makes each extractor unique and are not part of the comparison "
        "metrics above. Docling's richer table, markdown, and layout extraction "
        "is part of why it can take longer than the other extractors."
    )

    for extractor_name, results in extractor_results.items():
        with st.expander(extractor_name, expanded=(extractor_name == "Docling")):
            if extractor_name == "Docling":
                _render_docling_advanced_features(
                    results, extractor_markdown.get(extractor_name, "")
                )
            elif extractor_name == "OpenDataLoader":
                _render_opendataloader_advanced_features(
                    results, extractor_markdown.get(extractor_name, "")
                )
            else:
                _render_unsupported_advanced_features()


def _render_extractor_bbox_visualization(
    extractor_name: str,
    results: list[Any],
    input_path: Path,
    page_image_cache: dict[int, Any],
) -> None:
    """Render bounding-box overlays for one extractor's results.

    Bounding boxes are taken as-is from `results`; pages are re-rendered for
    display only via `build_page_visualizations`. Renders a
    "Bounding Boxes Not Available" notice when `results` contain no boxes,
    and a warning (without raising) if page rendering fails.
    """
    if not has_bounding_boxes(results):
        st.caption("Bounding Boxes Not Available")
        return

    try:
        visualizations = build_page_visualizations(
            input_path=input_path,
            results=results,
            source_dpi=get_extractor_source_dpi(extractor_name),
            color=get_extractor_color(extractor_name),
            page_image_cache=page_image_cache,
        )
    except Exception as exc:
        st.warning(f"Could not render bounding box visualization for {extractor_name}: {exc}")
        return

    if not visualizations:
        st.caption("Bounding Boxes Not Available")
        return

    columns = st.columns(len(visualizations))
    for column, viz in zip(columns, visualizations, strict=False):
        with column:
            st.image(
                viz["image"],
                caption=(
                    f"{extractor_name} | Page {viz['page_number']} | {viz['bbox_count']} boxes"
                ),
                width="stretch",
            )


def _render_bounding_box_visualization(documents: list[dict[str, Any]], project_root: Path) -> None:
    """Render the 'Bounding Box Visualization' section for all processed documents.

    Reuses the per-extractor `ExtractionResult` objects already produced by
    extraction (stored in `documents`); no extraction or bounding-box
    computation happens here. Page images are rasterized fresh for display
    and cached per document/page so multiple extractors share the same base
    image.
    """
    documents_with_results = [doc for doc in documents if doc.get("per_extractor_results")]
    if not documents_with_results:
        return

    st.markdown("## Bounding Box Visualization")
    st.caption(
        "Bounding boxes are drawn from the extraction results above. "
        "Only the first 1-3 pages are shown per extractor for performance."
    )

    input_dir = project_root / "data" / "processed"
    show_document_headers = len(documents_with_results) > 1

    for doc in documents_with_results:
        file_name = doc["file_name"]
        per_extractor_results: dict[str, list[Any]] = doc["per_extractor_results"]
        input_path = input_dir / file_name

        if show_document_headers:
            st.markdown(f"### {file_name}")

        page_image_cache: dict[int, Any] = {}
        for extractor_name, results in per_extractor_results.items():
            st.markdown(f"**{extractor_name}**")
            _render_extractor_bbox_visualization(
                extractor_name, results, input_path, page_image_cache
            )


def _resolve_opendataloader_hybrid_url(
    opendataloader_mode: str,
    pdf_type: str,
    run_status: Any,
    document_name: str,
) -> str | None:
    """Resolve the `hybrid_url` to pass to `OpendataloaderExtractor.extract`.

    - "standard": never use the hybrid server.
    - "hybrid": always ensure the hybrid server is available, regardless of
      `pdf_type`.
    - "auto" (default): preserve the existing behavior - only use the hybrid
      server for scanned/image/hybrid PDFs.
    """
    if opendataloader_mode == "standard":
        return None

    if opendataloader_mode == "hybrid":
        needs_hybrid = True
    else:
        needs_hybrid = pdf_type in {"scanned", "image", "hybrid"}

    if not needs_hybrid:
        return None

    try:
        return ensure_hybrid_server()
    except RuntimeError:
        run_status.write(
            f"OpenDataLoader hybrid OCR server unavailable for "
            f"`{document_name}`; falling back to text-layer-only mode."
        )
        return None


def _process_document(
    uploaded: Any,
    selected_extractors: list[str],
    paddleocr_language_mode: str,
    opendataloader_mode: str,
    project_root: Path,
    output_root_dir: Path,
    output_markdown_dir: Path,
    run_status: Any,
    progress_bar: Any,
    progress_offset: int,
    progress_total: int,
) -> dict[str, Any]:
    """Run the selected extractors against a single uploaded document.

    Encapsulates the per-document extraction pipeline (classification,
    per-extractor extraction with partial-failure handling, and comparison
    row construction) so it can be reused for both single- and
    multi-document benchmark runs.

    Parameters
    ----------
    uploaded:
        A Streamlit `UploadedFile` for the document to process.
    selected_extractors:
        Display names of the extractors to run.
    paddleocr_language_mode:
        PaddleOCR language mode key (e.g. ``"english"``).
    opendataloader_mode:
        OpenDataLoader mode key: ``"auto"``, ``"standard"``, or ``"hybrid"``.
    project_root, output_root_dir, output_markdown_dir:
        Filesystem locations used for input staging and extractor outputs.
    run_status, progress_bar:
        Streamlit status/progress widgets shared across the whole run.
    progress_offset, progress_total:
        This document's starting position and the overall step count across
        all documents/extractors, used to advance `progress_bar` smoothly.

    Returns
    -------
    dict[str, Any]
        Per-document state: `file_name`, `per_extractor_results`,
        `per_extractor_payloads`, `per_extractor_markdown`,
        `per_extractor_paths`, `per_extractor_text`, `comparison_rows`,
        `meta`, `observations`, `recommendation`, `classification`, and
        `warnings`.
    """
    input_dir = project_root / "data" / "processed"
    input_dir.mkdir(parents=True, exist_ok=True)
    input_path = input_dir / uploaded.name
    input_path.write_bytes(uploaded.getvalue())
    input_type = _detect_input_type(input_path)
    is_image_input = input_type == "Image"

    classification = None
    if input_type == "PDF":
        classifier = PdfTypeClassifier()
        classification = classifier.classify(input_path)
        pdf_type = classification.pdf_type
        page_count = classification.page_count
        classification_confidence = classification.confidence
        classification_reasoning = classification.reasoning
        image_heavy_pages = classification.image_heavy_pages
        text_pages = classification.text_pages
        avg_text_density = classification.avg_text_density
        avg_image_ratio = classification.avg_image_ratio
    else:
        pdf_type = "image"
        page_count = 1
        classification_confidence = 1.0
        classification_reasoning = "Image input detected; route to OCR-capable extractors."
        image_heavy_pages = 1
        text_pages = 0
        avg_text_density = 0.0
        avg_image_ratio = 1.0

    recs = RECOMMENDATIONS.get(pdf_type, [])
    rec_text = ", ".join(recs)
    st.info(
        f"`{uploaded.name}` detected: {input_type}. "
        f"Classification: {pdf_type.title()} "
        f"(confidence {classification_confidence:.2f}). "
        f"Recommended: {rec_text}"
    )
    if "PaddleOCR" in selected_extractors:
        st.caption(
            f"`{uploaded.name}` PaddleOCR Language Mode: "
            f"{_paddleocr_language_label(paddleocr_language_mode)} "
            f"(`{paddleocr_language_mode}`)"
        )

    per_extractor_results: dict[str, list[Any]] = {}
    per_extractor_payloads: dict[str, dict[str, object]] = {}
    per_extractor_markdown: dict[str, str] = {}
    per_extractor_paths: dict[str, dict[str, str]] = {}
    per_extractor_text: dict[str, str] = {}
    comparison_rows: list[dict[str, object]] = []
    warnings: list[str] = []
    total_extractors = max(1, len(selected_extractors))

    for idx, extractor_name in enumerate(selected_extractors, start=1):
        progress_step = progress_offset + (idx - 1)
        progress_bar.progress(
            min(1.0, progress_step / progress_total),
            text=f"Running {extractor_name} on {uploaded.name} ({idx}/{total_extractors})...",
        )
        run_status.write(
            f"Started `{extractor_name}` on `{uploaded.name}` ({idx}/{total_extractors})."
        )
        start = time.perf_counter()
        extractor_slug = _extractor_slug(extractor_name)
        extractor_output_dir = output_root_dir / extractor_slug / input_path.stem
        extractor_output_dir.mkdir(parents=True, exist_ok=True)

        try:
            capabilities = EXTRACTOR_CAPABILITIES[extractor_name]
            if is_image_input and not capabilities["supports_image"]:
                results = _build_unsupported_image_result(extractor_name, input_path)
            else:
                extractor = _create_extractor(extractor_name, paddleocr_language_mode)
                if extractor_name == "OpenDataLoader":
                    hybrid_url = _resolve_opendataloader_hybrid_url(
                        opendataloader_mode=opendataloader_mode,
                        pdf_type=pdf_type,
                        run_status=run_status,
                        document_name=uploaded.name,
                    )
                    results = extractor.extract(
                        pdf_path=input_path,
                        output_dir=extractor_output_dir,
                        hybrid_url=hybrid_url,
                    )
                else:
                    results = extractor.extract(pdf_path=input_path)
            elapsed = time.perf_counter() - start

            payload = UnifiedOutputParser().to_json_payload(results)

            md_source = extractor_output_dir / f"{input_path.stem}.md"
            if extractor_name == "OpenDataLoader" and input_type == "PDF" and md_source.exists():
                markdown_text = _read_text_safely(md_source)
            else:
                markdown_text = _build_markdown_from_results(results, extractor_name)

            has_markdown_images = bool(re.search(r"!\[[^\]]*\]\([^)]+\)", markdown_text))
            if input_type == "PDF" and pdf_type == "scanned" and not has_markdown_images:
                image_section = _build_scanned_page_image_markdown(
                    pdf_path=input_path,
                    markdown_root_dir=output_markdown_dir,
                    extractor_slug=extractor_slug,
                )
                if image_section:
                    markdown_text = f"{markdown_text.rstrip()}\n\n{image_section}\n"

            json_output, md_output = _save_outputs(
                json_payload=payload,
                markdown_text=markdown_text,
                output_dir=extractor_output_dir,
            )

            all_text = "\n\n".join(result.extracted_text for result in results)
            no_text_output = not all_text.strip()
            extracted_result_count = len(results)
            processed_page_count = page_count if extracted_result_count > 0 else 0
            ocr_required_pages = sum(
                1
                for result in results
                if result.metadata and result.metadata.extra.get("ocr_required") is True
            )
            ocr_supported = bool(capabilities["ocr_supported"])
            char_count = len(all_text)
            word_count = len(all_text.split())
            bbox_count = sum(len(result.bounding_boxes) for result in results)
            status = _get_result_status(results)
            if status == "ok":
                status = "success"
            elif not status:
                status = "success" if not no_text_output else "empty_text_output"
            if pdf_type == "scanned" and no_text_output and status == "empty_text_output":
                status = "limited_for_scanned_pdf"
            if status == "unsupported_for_image_input":
                processed_page_count = 0
            if status != "success":
                warnings.append(f"{uploaded.name} / {extractor_name}: {status.replace('_', ' ')}")

            per_extractor_results[extractor_name] = results
            per_extractor_payloads[extractor_name] = payload
            per_extractor_markdown[extractor_name] = markdown_text
            per_extractor_paths[extractor_name] = {
                "json": str(json_output),
                "markdown": str(md_output),
            }
            per_extractor_text[extractor_name] = all_text
            comparison_rows.append(
                {
                    "extractor": extractor_name,
                    "latency_seconds": round(elapsed, 3),
                    "total_pages": page_count,
                    "processed_pages": processed_page_count,
                    "text_length": len(all_text),
                    "markdown_length": len(markdown_text),
                    "ocr_supported": ocr_supported,
                    "ocr_required_pages": ocr_required_pages,
                    "status": status,
                    "pdf_type": pdf_type,
                    "char_count": char_count,
                    "word_count": word_count,
                    "bbox_count": bbox_count,
                    "markdown_support": bool(capabilities["markdown_support"]),
                    "layout_preservation_support": bool(
                        capabilities["layout_preservation_support"]
                    ),
                    "error_message": "",
                }
            )
            run_status.write(
                f"Finished `{extractor_name}` on `{uploaded.name}` in {elapsed:.2f}s "
                f"(status: {status}, "
                f"pages: {processed_page_count}/{page_count}, "
                f"text length: {len(all_text)})."
            )
        except Exception as exc:
            capabilities = EXTRACTOR_CAPABILITIES[extractor_name]
            comparison_rows.append(
                {
                    "extractor": extractor_name,
                    "latency_seconds": round(time.perf_counter() - start, 3),
                    "total_pages": page_count,
                    "processed_pages": 0,
                    "text_length": 0,
                    "markdown_length": 0,
                    "ocr_supported": False,
                    "ocr_required_pages": 0,
                    "status": "failed",
                    "pdf_type": pdf_type,
                    "char_count": 0,
                    "word_count": 0,
                    "bbox_count": 0,
                    "markdown_support": bool(capabilities["markdown_support"]),
                    "layout_preservation_support": bool(
                        capabilities["layout_preservation_support"]
                    ),
                    "error_message": str(exc),
                }
            )
            warnings.append(f"{uploaded.name} / {extractor_name}: failed ({exc})")
            run_status.write(f"`{extractor_name}` on `{uploaded.name}` failed: {exc}")

    observations, recommendation = _build_comparison_observations(comparison_rows, classification)
    meta = {
        "file_name": uploaded.name,
        "file_size_kb": round(len(uploaded.getvalue()) / 1024, 2),
        "input_type": input_type,
        "total_pdf_pages": page_count,
        "image_heavy_pages": image_heavy_pages,
        "ocr_image_only_pages": max(0, page_count - text_pages),
        "pdf_type": pdf_type,
        "classification_confidence": classification_confidence,
        "classification_reasoning": classification_reasoning,
        "avg_text_density": avg_text_density,
        "avg_image_ratio": avg_image_ratio,
        "text_pages": text_pages,
        "selected_extractors": selected_extractors,
    }

    return {
        "file_name": uploaded.name,
        "per_extractor_results": per_extractor_results,
        "per_extractor_payloads": per_extractor_payloads,
        "per_extractor_markdown": per_extractor_markdown,
        "per_extractor_paths": per_extractor_paths,
        "per_extractor_text": per_extractor_text,
        "comparison_rows": comparison_rows,
        "meta": meta,
        "observations": observations,
        "recommendation": recommendation,
        "classification": classification,
        "warnings": warnings,
    }


def _render_extractor_result_tabs(
    extractor_results: dict[str, list[Any]],
    paddleocr_language_mode: str,
    project_root: Path,
) -> None:
    """Render the per-extractor Text/Markdown/JSON/Metadata tabs."""
    if not extractor_results:
        return

    extractor_tabs = st.tabs(list(extractor_results.keys()))
    for index, extractor_name in enumerate(extractor_results.keys()):
        with extractor_tabs[index]:
            inner_tabs = st.tabs(["Text", "Markdown", "JSON", "Metadata"])

            with inner_tabs[0]:
                text_value = st.session_state.last_text.get(extractor_name, "")
                st.text_area(
                    f"Extracted Text ({extractor_name})",
                    value=text_value,
                    height=320,
                )

            with inner_tabs[1]:
                markdown_value = st.session_state.last_markdown.get(extractor_name, "")
                markdown_for_view = markdown_value
                markdown_without_images = re.sub(
                    r"!\[[^\]]*\]\([^)]+\)",
                    "",
                    markdown_for_view,
                )
                st.markdown(markdown_without_images)

                md_output_path = st.session_state.last_paths.get(
                    extractor_name,
                    {},
                ).get("markdown", "")
                if md_output_path:
                    md_base_dir = Path(md_output_path).resolve().parent
                    image_paths = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown_for_view)
                    rendered: set[str] = set()
                    for rel_path in image_paths:
                        cleaned = rel_path.strip().strip("<>").strip().strip("\"'")
                        if cleaned.startswith(("http://", "https://", "data:")):
                            continue
                        candidates = [
                            (md_base_dir / cleaned).resolve(),
                            (md_base_dir.parent / cleaned).resolve(),
                            (project_root / cleaned).resolve(),
                            (project_root / "outputs" / cleaned).resolve(),
                            (project_root / "outputs" / "markdown" / cleaned).resolve(),
                        ]
                        for resolved in candidates:
                            key = str(resolved)
                            if key in rendered:
                                break
                            if resolved.exists():
                                st.image(str(resolved), caption=resolved.name, width=900)
                                rendered.add(key)
                                break

            with inner_tabs[2]:
                payload = st.session_state.last_payload.get(extractor_name)
                if payload is None:
                    st.info("JSON output will appear here after extraction.")
                else:
                    st.json(payload)

            with inner_tabs[3]:
                st.markdown('<div class="meta-card">', unsafe_allow_html=True)
                if extractor_name == "PaddleOCR":
                    ocr_metadata = None
                    if extractor_results.get(extractor_name):
                        ocr_metadata = extractor_results[extractor_name][0].metadata
                    ocr_mode = (
                        str(ocr_metadata.extra.get("ocr_language_mode"))
                        if ocr_metadata is not None
                        else paddleocr_language_mode
                    )
                    st.write(
                        "**Language Mode:** "
                        f"{_paddleocr_language_label(str(ocr_mode))} "
                        f"(`{ocr_mode}`)"
                    )
                    if ocr_metadata is not None:
                        metadata_extra = ocr_metadata.extra
                        st.write(f"**OCR Model:** {metadata_extra.get('ocr_model_name', '')}")
                        st.write(f"**OCR Language:** {metadata_extra.get('ocr_language', '')}")
                st.write(
                    f"**JSON Output:** "
                    f"`{st.session_state.last_paths.get(extractor_name, {}).get('json', '')}`"
                )
                st.write(
                    f"**Markdown Output:** "
                    f"`"
                    f"{st.session_state.last_paths.get(extractor_name, {}).get('markdown', '')}"
                    f"`"
                )
                st.markdown("</div>", unsafe_allow_html=True)


def _build_rvl_cdip_extractors(
    selected_extractors: list[str], project_root: Path
) -> dict[str, Any]:
    """Instantiate the selected RVL-CDIP extractors in canonical order."""
    extractors: dict[str, Any] = {}
    for name in RVL_CDIP_EXTRACTOR_ORDER:
        if name not in selected_extractors:
            continue
        if name == "PyMuPDF":
            extractors[name] = PymupdfExtractor()
        elif name == "OpenDataLoader":
            extractors[name] = OpendataloaderExtractor()
        elif name == "PaddleOCR":
            extractors[name] = PaddleocrExtractor()
        elif name == "Docling":
            docling_cls = import_module(
                "pdf_extraction_benchmark.extractors.docling.extractor"
            ).DoclingExtractor
            extractors[name] = docling_cls(output_root=project_root)
        elif name == "Tesseract":
            extractors[name] = TesseractExtractor()
    return extractors


def _build_rvl_cdip_extractor_comparison_df(summary: RvlCdipBenchmarkSummary) -> pd.DataFrame:
    """Build the extractor comparison table (success rate, latency, char/word/bbox counts)."""
    rows = []
    for extractor_summary in summary.extractor_summaries.values():
        rows.append(
            {
                "Extractor": extractor_summary.extractor,
                "Success Rate": extractor_summary.success_rate,
                "Avg Latency (ms)": extractor_summary.latency_ms.mean,
                "Avg Char Count": extractor_summary.char_count.mean,
                "Avg Word Count": extractor_summary.word_count.mean,
                "Avg Layout Regions": extractor_summary.bbox_count.mean,
            }
        )
    return pd.DataFrame(rows)


def _build_rvl_cdip_category_analysis(
    summary: RvlCdipBenchmarkSummary,
) -> tuple[pd.DataFrame, list[str]]:
    """Build the per-category best/worst extractor table and low-yield category list."""
    rows = []
    low_yield_categories: list[str] = []
    for category_summary in summary.category_summaries.values():
        word_counts = category_summary.extractor_word_count
        if not word_counts:
            continue
        best_extractor, best_words = max(word_counts.items(), key=lambda item: item[1])
        worst_extractor, worst_words = min(word_counts.items(), key=lambda item: item[1])
        rows.append(
            {
                "Category": category_summary.category,
                "Documents": category_summary.documents,
                "Best Extractor": best_extractor,
                "Best Avg Words": round(best_words, 1),
                "Worst Extractor": worst_extractor,
                "Worst Avg Words": round(worst_words, 1),
            }
        )
        if best_words < RVL_CDIP_LOW_YIELD_WORD_THRESHOLD:
            low_yield_categories.append(category_summary.category)
    return pd.DataFrame(rows), low_yield_categories


def _build_rvl_cdip_recommendations(summary: RvlCdipBenchmarkSummary) -> list[str]:
    """Derive recommendations from the actual extractor summaries.

    Extractors that ran without raising but extracted zero text on average
    produced no usable output, so they are excluded from the "Most
    reliable"/"Fastest"/yield-based picks (otherwise a fast no-op extractor
    like PyMuPDF on scanned PDFs would win by default) and called out
    separately as "No text extracted".
    """
    recommendations: list[str] = []
    summaries = list(summary.extractor_summaries.values())
    if not summaries:
        return recommendations

    yielding = [s for s in summaries if s.word_count.mean > 0]
    empty = [s for s in summaries if s.word_count.mean == 0]

    if empty:
        recommendations.append(
            "**No text extracted:** "
            + ", ".join(s.extractor for s in empty)
            + " (excluded from the picks below, despite a nonzero success rate)"
        )

    pool = yielding or summaries

    most_reliable = max(pool, key=lambda s: (s.success_rate, s.word_count.mean))
    recommendations.append(
        f"**Most reliable:** {most_reliable.extractor} "
        f"({most_reliable.success_rate * 100:.1f}% success rate, "
        f"{most_reliable.word_count.mean:.1f} avg words/doc)"
    )

    fastest = min(pool, key=lambda s: s.latency_ms.mean)
    recommendations.append(
        f"**Fastest:** {fastest.extractor} ({fastest.latency_ms.mean:.2f} ms avg)"
    )

    if yielding:
        best_yield = max(yielding, key=lambda s: s.word_count.mean)
        recommendations.append(
            f"**Highest text yield (best for scanned/OCR):** {best_yield.extractor} "
            f"({best_yield.word_count.mean:.1f} avg words/doc)"
        )

        def _yield_per_second(s: Any) -> float:
            latency_s = max(s.latency_ms.mean / 1000.0, 1e-6)
            return s.word_count.mean / latency_s

        best_tradeoff = max(yielding, key=_yield_per_second)
        recommendations.append(
            f"**Best speed/yield tradeoff:** {best_tradeoff.extractor} "
            f"({_yield_per_second(best_tradeoff):.1f} words/sec)"
        )
    else:
        recommendations.append(
            "No extractor produced extractable text for the selected documents "
            "(all zero-text) - consider enabling an OCR-capable extractor."
        )

    return recommendations


def _render_rvl_cdip_results(summary: RvlCdipBenchmarkSummary) -> None:
    """Render summary metrics, extractor comparison, category analysis, and recommendations."""
    st.markdown("#### Summary")
    total_evaluated = sum(s.documents_evaluated for s in summary.extractor_summaries.values())
    total_ok = sum(s.documents_ok for s in summary.extractor_summaries.values())
    overall_success_rate = (total_ok / total_evaluated) if total_evaluated else 0.0
    avg_latency = (
        sum(r.latency_ms for r in summary.documents) / len(summary.documents)
        if summary.documents
        else 0.0
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documents Processed", str(summary.total_documents))
    c2.metric("Categories Processed", str(len(summary.categories)))
    c3.metric("Overall Success Rate", f"{overall_success_rate * 100:.1f}%")
    c4.metric("Avg Extraction Time", f"{avg_latency:.1f} ms")

    st.markdown("#### Extractor Comparison")
    comparison_df = _build_rvl_cdip_extractor_comparison_df(summary)
    st.dataframe(comparison_df, width="stretch")

    if not comparison_df.empty:
        chart_df = comparison_df.set_index("Extractor")
        st.caption("Avg Latency (ms)")
        st.bar_chart(chart_df[["Avg Latency (ms)"]])
        st.caption("Avg Char & Word Count")
        st.bar_chart(chart_df[["Avg Char Count", "Avg Word Count"]])
        st.caption("Avg Layout Regions")
        st.bar_chart(chart_df[["Avg Layout Regions"]])

    st.markdown("#### Category Analysis")
    category_df, low_yield_categories = _build_rvl_cdip_category_analysis(summary)
    st.dataframe(category_df, width="stretch")
    if low_yield_categories:
        st.warning(
            "Categories with unusually low text extraction (best extractor averages "
            f"< {RVL_CDIP_LOW_YIELD_WORD_THRESHOLD:.0f} words): "
            f"{', '.join(low_yield_categories)}"
        )

    st.markdown("#### Recommendations")
    recommendations = _build_rvl_cdip_recommendations(summary)
    if recommendations:
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        for note in recommendations:
            st.write(f"- {note}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.caption(f"Full results written to `{summary.output_dir}`")


def _render_rvl_cdip_benchmark_tab(project_root: Path) -> None:
    """Render the RVL-CDIP Benchmark tab: controls, execution, and results."""
    st.markdown("### RVL-CDIP Benchmark")
    st.caption(
        "Run the category-based RVL-CDIP extraction robustness benchmark using the "
        "existing RvlCdipBenchmarkPipeline."
    )

    dataset_dir = project_root / "data" / "raw" / "rvl_cdip"
    if not dataset_dir.exists():
        st.warning(f"RVL-CDIP dataset not found at `{dataset_dir}`.")
        return

    categories = sorted(path.name for path in dataset_dir.iterdir() if path.is_dir())
    if not categories:
        st.warning(f"No category folders found in `{dataset_dir}`.")
        return

    if "rvl_cdip_summary" not in st.session_state:
        st.session_state.rvl_cdip_summary = None

    select_all = st.checkbox("Select all categories", value=True, key="rvl_cdip_select_all")
    if select_all:
        selected_categories = categories
        st.multiselect(
            "Categories",
            options=categories,
            default=categories,
            disabled=True,
            key="rvl_cdip_categories_all",
            help="Uncheck 'Select all categories' to choose individual categories.",
        )
    else:
        selected_categories = st.multiselect(
            "Categories",
            options=categories,
            default=categories,
            key="rvl_cdip_categories",
        )

    col1, col2 = st.columns(2)
    with col1:
        sample_size = st.selectbox(
            "Sample size per category",
            options=RVL_CDIP_SAMPLE_SIZE_OPTIONS,
            index=1,
            key="rvl_cdip_sample_size",
        )
    with col2:
        selected_extractors = st.multiselect(
            "Extractors",
            options=RVL_CDIP_EXTRACTOR_ORDER,
            default=[],
            key="rvl_cdip_extractors",
        )

    run_clicked = st.button(
        "Run RVL-CDIP Benchmark", type="primary", key="rvl_cdip_run", use_container_width=True
    )

    if run_clicked:
        if not selected_categories:
            st.warning("Please select at least one category.")
        elif not selected_extractors:
            st.warning("Please select at least one extractor.")
        else:
            run_status = st.status("Running RVL-CDIP benchmark...", expanded=True)
            progress_bar = st.progress(0.0, text="Initializing benchmark...")
            try:
                extractors = _build_rvl_cdip_extractors(selected_extractors, project_root)
                run_status.write(
                    f"Evaluating {len(selected_categories)} categories x {sample_size} "
                    f"docs/category with extractors: {', '.join(extractors.keys())}"
                )

                def _on_progress(completed: int, total: int) -> None:
                    fraction = completed / total if total else 1.0
                    progress_bar.progress(
                        min(fraction, 1.0), text=f"Evaluated {completed}/{total} runs..."
                    )

                pipeline = RvlCdipBenchmarkPipeline(
                    dataset_dir=dataset_dir,
                    output_dir=project_root / "outputs" / "benchmark_results" / "rvl_cdip",
                    extractors=extractors,
                )
                summary = pipeline.run(
                    sample_size_per_category=int(sample_size),
                    categories=selected_categories,
                    progress_callback=_on_progress,
                )
                st.session_state.rvl_cdip_summary = summary
                progress_bar.progress(1.0, text="Benchmark run complete.")
                run_status.update(
                    label="RVL-CDIP benchmark completed successfully.",
                    state="complete",
                    expanded=False,
                )
            except Exception as exc:  # noqa: BLE001 - surface benchmark failures in the UI
                run_status.update(
                    label=f"RVL-CDIP benchmark failed: {exc}",
                    state="error",
                    expanded=True,
                )
                st.error(f"Benchmark run failed: {exc}")

    if st.session_state.rvl_cdip_summary is not None:
        _render_rvl_cdip_results(st.session_state.rvl_cdip_summary)


def run() -> None:
    """Render and run the streamlined extraction dashboard."""
    st.set_page_config(page_title=APP_NAME, layout="wide")
    _inject_styles()

    project_root = Path(__file__).resolve().parents[3]
    output_root_dir = project_root / "outputs"
    output_markdown_dir = output_root_dir / "markdown"
    output_logs_dir = project_root / "outputs" / "logs"
    output_root_dir.mkdir(parents=True, exist_ok=True)
    output_markdown_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(output_logs_dir)

    with st.sidebar:
        st.header("Extraction")
        uploaded_files = st.file_uploader(
            "Upload Document(s)",
            type=SUPPORTED_UPLOAD_TYPES,
            accept_multiple_files=True,
        )
        selected_extractors = st.multiselect(
            "Extractors",
            options=list(EXTRACTOR_OPTIONS.keys()),
            default=[],
        )
        with st.expander("Advanced Settings"):
            paddleocr_language_label = st.selectbox(
                "PaddleOCR Language",
                options=list(PADDLEOCR_LANGUAGE_OPTIONS.keys()),
                index=0,
                help="Choose English or multilingual OCR for PaddleOCR runs.",
            )
            opendataloader_mode_label = st.selectbox(
                "OpenDataLoader Mode",
                options=list(OPENDATALOADER_MODE_OPTIONS.keys()),
                index=0,
                help=(
                    f"{OPENDATALOADER_MODE_DESCRIPTIONS['auto']}\n\n"
                    f"{OPENDATALOADER_MODE_DESCRIPTIONS['standard']}\n\n"
                    f"{OPENDATALOADER_MODE_DESCRIPTIONS['hybrid']}"
                ),
            )
        paddleocr_language_mode = PADDLEOCR_LANGUAGE_OPTIONS[paddleocr_language_label]
        opendataloader_mode = OPENDATALOADER_MODE_OPTIONS[opendataloader_mode_label]
        run_clicked = st.button(
            "Run Extraction",
            type="primary",
            use_container_width=True,
            disabled=not selected_extractors,
            help=None if selected_extractors else "Select at least one extractor first.",
        )

    st.title(APP_NAME)
    st.markdown(f'<div class="subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)

    if "last_results" not in st.session_state:
        st.session_state.documents = []
        st.session_state.last_results = {}
        st.session_state.last_payload = {}
        st.session_state.last_markdown = {}
        st.session_state.last_meta = {}
        st.session_state.last_paths = {}
        st.session_state.last_text = {}
        st.session_state.comparison_rows = []
        st.session_state.observations = []
        st.session_state.recommendation = {}
        st.session_state.last_classification = None

    if run_clicked:
        if not uploaded_files:
            st.warning("Please upload at least one document before running extraction.")
        elif not selected_extractors:
            st.warning("Please select at least one extractor.")
        else:
            run_status = st.status("Running extraction...", expanded=True)
            progress_bar = st.progress(0.0, text="Initializing extraction...")
            total_extractors = max(1, len(selected_extractors))
            progress_total = max(1, len(uploaded_files) * total_extractors)

            documents: list[dict[str, Any]] = []
            all_warnings: list[str] = []

            for doc_idx, uploaded in enumerate(uploaded_files):
                run_status.write(
                    f"Processing document `{uploaded.name}` "
                    f"({doc_idx + 1}/{len(uploaded_files)})..."
                )
                try:
                    document_state = _process_document(
                        uploaded=uploaded,
                        selected_extractors=selected_extractors,
                        paddleocr_language_mode=paddleocr_language_mode,
                        opendataloader_mode=opendataloader_mode,
                        project_root=project_root,
                        output_root_dir=output_root_dir,
                        output_markdown_dir=output_markdown_dir,
                        run_status=run_status,
                        progress_bar=progress_bar,
                        progress_offset=doc_idx * total_extractors,
                        progress_total=progress_total,
                    )
                except Exception as exc:
                    failure_message = f"{uploaded.name}: failed ({exc})"
                    run_status.write(failure_message)
                    document_state = {
                        "file_name": uploaded.name,
                        "per_extractor_results": {},
                        "per_extractor_payloads": {},
                        "per_extractor_markdown": {},
                        "per_extractor_paths": {},
                        "per_extractor_text": {},
                        "comparison_rows": [
                            {
                                "extractor": extractor_name,
                                "latency_seconds": 0.0,
                                "total_pages": 0,
                                "processed_pages": 0,
                                "text_length": 0,
                                "markdown_length": 0,
                                "ocr_supported": False,
                                "ocr_required_pages": 0,
                                "status": "failed",
                                "pdf_type": "unknown",
                                "char_count": 0,
                                "word_count": 0,
                                "bbox_count": 0,
                                "markdown_support": bool(
                                    EXTRACTOR_CAPABILITIES[extractor_name]["markdown_support"]
                                ),
                                "layout_preservation_support": bool(
                                    EXTRACTOR_CAPABILITIES[extractor_name][
                                        "layout_preservation_support"
                                    ]
                                ),
                                "error_message": str(exc),
                            }
                            for extractor_name in selected_extractors
                        ],
                        "meta": {
                            "file_name": uploaded.name,
                            "selected_extractors": selected_extractors,
                        },
                        "observations": [],
                        "recommendation": {},
                        "classification": None,
                        "warnings": [failure_message],
                    }

                documents.append(document_state)
                all_warnings.extend(document_state["warnings"])

            st.session_state.documents = documents

            if documents:
                doc = documents[0]
                st.session_state.last_results = doc["per_extractor_results"]
                st.session_state.last_payload = doc["per_extractor_payloads"]
                st.session_state.last_markdown = doc["per_extractor_markdown"]
                st.session_state.last_paths = doc["per_extractor_paths"]
                st.session_state.last_text = doc["per_extractor_text"]
                st.session_state.comparison_rows = doc["comparison_rows"]
                st.session_state.observations = doc["observations"]
                st.session_state.recommendation = doc["recommendation"]
                st.session_state.last_classification = doc["classification"]
                st.session_state.last_meta = doc["meta"]
            else:
                st.session_state.last_results = {}
                st.session_state.last_payload = {}
                st.session_state.last_markdown = {}
                st.session_state.last_paths = {}
                st.session_state.last_text = {}
                st.session_state.comparison_rows = []
                st.session_state.observations = []
                st.session_state.recommendation = {}
                st.session_state.last_classification = None
                st.session_state.last_meta = {}

            if all_warnings:
                for warning in all_warnings:
                    st.warning(warning)
                run_status.update(
                    label="Extraction completed with warnings.",
                    state="error",
                    expanded=True,
                )
            else:
                st.success("Extraction completed for all selected extractors.")
                run_status.update(
                    label="Extraction completed successfully.",
                    state="complete",
                    expanded=False,
                )
            progress_bar.progress(1.0, text="Extraction run complete.")

    (
        overview_tab,
        benchmarking_tab,
        native_vs_scanned_tab,
        rvl_cdip_tab,
        extractor_tab,
        advanced_tab,
        visualizations_tab,
    ) = st.tabs(
        [
            "Overview",
            "Benchmarking",
            "By Document Type",
            "RVL-CDIP Benchmark",
            "Results",
            "Advanced Features",
            "Visualizations",
        ]
    )

    with overview_tab:
        if not st.session_state.last_meta:
            st.info("Upload a document and run extraction to see results here.")
        if st.session_state.last_meta:
            _render_document_summary(st.session_state.last_meta)
            _render_overview_cards(st.session_state.last_meta, st.session_state.comparison_rows)

        if st.session_state.comparison_rows:
            st.markdown("### Comparison Overview")
            display_df = _format_comparison_rows(st.session_state.comparison_rows)
            st.dataframe(display_df, width="stretch")

        if st.session_state.observations:
            st.markdown("### Key Findings")
            st.markdown('<div class="summary-card">', unsafe_allow_html=True)
            for note in st.session_state.observations:
                st.write(f"- {note}")
            st.markdown("</div>", unsafe_allow_html=True)
        if st.session_state.recommendation:
            _render_recommendation_card(st.session_state.recommendation)

        if st.session_state.comparison_rows:
            _render_comparison_analysis(st.session_state.comparison_rows)

    with benchmarking_tab:
        if not st.session_state.documents:
            st.info("Upload a document and run extraction to see results here.")
        if st.session_state.documents:
            report_rows = build_multi_document_report_rows(
                [(doc["file_name"], doc["comparison_rows"]) for doc in st.session_state.documents]
            )
            _render_document_benchmark_results(report_rows)
            _render_aggregate_summary(report_rows)
            if len(st.session_state.documents) == 1:
                file_stem = (
                    Path(st.session_state.documents[0]["file_name"]).stem or "benchmark_report"
                )
            else:
                file_stem = "multi_document_benchmark_report"
            _render_export_controls(report_rows, file_stem)

    with native_vs_scanned_tab:
        _render_native_vs_scanned_analysis(st.session_state.documents)

    with rvl_cdip_tab:
        _render_rvl_cdip_benchmark_tab(project_root)

    with extractor_tab:
        if not st.session_state.last_results:
            st.info("Upload a document and run extraction to see results here.")
        _render_extractor_result_tabs(
            st.session_state.last_results, paddleocr_language_mode, project_root
        )

    with advanced_tab:
        if not st.session_state.last_results:
            st.info("Upload a document and run extraction to see results here.")
        if st.session_state.last_results:
            _render_advanced_document_features(
                st.session_state.last_results, st.session_state.last_markdown
            )

    with visualizations_tab:
        if not st.session_state.documents:
            st.info("Upload a document and run extraction to see results here.")
        if st.session_state.documents:
            _render_bounding_box_visualization(st.session_state.documents, project_root)


if __name__ == "__main__":
    run()
