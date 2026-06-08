"""Minimal professional Streamlit app for PDF extraction benchmarking."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import fitz
import pandas as pd
import streamlit as st

# Ensure local src package imports resolve when launching Streamlit directly.
SRC_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pdf_extraction_benchmark.classifiers.pdf_type_classifier import PdfTypeClassifier  # noqa: E402
from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.opendataloader.extractor import (  # noqa: E402
    OpendataloaderExtractor,
)
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor  # noqa: E402
from pdf_extraction_benchmark.extractors.surya.extractor import SuryaExtractor  # noqa: E402
from pdf_extraction_benchmark.models.extraction_result import (  # noqa: E402
    ExtractionMetadata,
    ExtractionResult,
)
from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser  # noqa: E402
from pdf_extraction_benchmark.utils.logger import configure_logging  # noqa: E402

APP_NAME = "DocuVision AI"
APP_SUBTITLE = "Clean PDF intelligence with multiple extraction backends"
SUPPORTED_UPLOAD_TYPES = ["pdf", "png", "jpg", "jpeg", "tif", "tiff"]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

RECOMMENDATIONS = {
    "native": ["OpenDataLoader", "PyMuPDF", "Marker"],
    "hybrid": ["PaddleOCR + PyMuPDF", "OpenDataLoader + OCR fallback"],
    "scanned": ["PaddleOCR", "Surya", "Docling"],
    "image": ["PaddleOCR"],
}

EXTRACTOR_OPTIONS = {
    "OpenDataLoader": OpendataloaderExtractor,
    "PyMuPDF": PymupdfExtractor,
    "Docling": DoclingExtractor,
    "PaddleOCR": PaddleocrExtractor,
    "Surya": SuryaExtractor,
}

EXTRACTOR_CAPABILITIES = {
    "OpenDataLoader": {"ocr_supported": False, "supports_pdf": True, "supports_image": False},
    "PyMuPDF": {"ocr_supported": False, "supports_pdf": True, "supports_image": False},
    "Docling": {"ocr_supported": True, "supports_pdf": True, "supports_image": False},
    "PaddleOCR": {"ocr_supported": True, "supports_pdf": True, "supports_image": True},
    "Surya": {"ocr_supported": True, "supports_pdf": True, "supports_image": True},
}

PADDLEOCR_LANGUAGE_OPTIONS = {
    "English": "english",
    "Multilingual (Hindi/Marathi/Devanagari)": "multilingual",
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
            f"{fastest_name} was fastest ({fastest_latency:.3f}s), "
            "but produced no usable text."
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
        str(row.get("extractor", ""))
        for row in rows
        if str(row.get("status", "")) == "failed"
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
            str(ocr_winner.get("extractor"))
            if ocr_winner
            else str(most_text.get("extractor"))
        )
        secondary = (
            str(fastest.get("extractor"))
            if str(fastest.get("extractor")) != primary
            else "-"
        )
        reason = (
            f"Scanned PDF detected. `{primary}` recovered the most usable text for this run."
            if primary != "-"
            else "Scanned PDF detected. OCR-capable extractor is recommended."
        )
    elif pdf_type == "image":
        primary = (
            str(ocr_winner.get("extractor"))
            if ocr_winner
            else str(most_text.get("extractor"))
        )
        secondary = (
            str(fastest.get("extractor"))
            if str(fastest.get("extractor")) != primary
            else "-"
        )
        reason = (
            f"Image input detected. `{primary}` recovered the most usable OCR text."
            if primary != "-"
            else "Image input detected. OCR-capable extraction is recommended."
        )
    elif pdf_type == "hybrid":
        primary = str(most_text.get("extractor"))
        secondary = (
            str(ocr_winner.get("extractor"))
            if ocr_winner
            else str(fastest.get("extractor"))
        )
        if secondary == primary:
            secondary = (
                str(fastest.get("extractor"))
                if str(fastest.get("extractor")) != primary
                else "-"
            )
        reason = (
            "Hybrid PDF detected with both text and image-heavy signals. "
            f"Use `{primary}` as primary and `{secondary}` as secondary for OCR recovery."
        )
    else:
        primary = str(most_text.get("extractor"))
        secondary = (
            str(fastest.get("extractor"))
            if str(fastest.get("extractor")) != primary
            else "-"
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
            f'{recommendation.get("reason", "-")}</div>'
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
            f'{meta.get("classification_confidence", 0.0) * 100:.0f}%</div>'
            f'<div style="margin-top:0.35rem"><b>Reason:</b> '
            f'{meta.get("classification_reasoning", "-")}</div>'
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
    selected = ", ".join(meta.get("selected_extractors", []))
    if comparison_rows:
        processed_pages = max(int(row.get("processed_pages", 0)) for row in comparison_rows)
        total_time = sum(float(row.get("latency_seconds", 0.0)) for row in comparison_rows)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pages", str(total_pages))
    c2.metric("Processed Pages", str(processed_pages))
    c3.metric("Extraction Time", f"{total_time:.2f}s")
    c4.metric("Selected Extractors", str(len(meta.get("selected_extractors", []))))
    st.caption(f"Extractors: {selected}")


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
    display_cols = [
        "extractor",
        "latency_seconds",
        "total_pages",
        "processed_pages",
        "text_length",
        "markdown_length",
        "ocr_required_pages",
        "status",
        "pdf_type",
    ]
    return df[display_cols]

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
        uploaded = st.file_uploader("Upload Document", type=SUPPORTED_UPLOAD_TYPES)
        selected_extractors = st.multiselect(
            "Extractors",
            options=list(EXTRACTOR_OPTIONS.keys()),
            default=["OpenDataLoader", "PyMuPDF", "PaddleOCR"],
        )
        paddleocr_language_label = st.selectbox(
            "PaddleOCR Language",
            options=list(PADDLEOCR_LANGUAGE_OPTIONS.keys()),
            index=0,
            help="Choose English or multilingual OCR for PaddleOCR runs.",
        )
        paddleocr_language_mode = PADDLEOCR_LANGUAGE_OPTIONS[paddleocr_language_label]
        run_clicked = st.button("Run Extraction", type="primary", use_container_width=True)

    st.title(APP_NAME)
    st.markdown(f'<div class="subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)

    if "last_results" not in st.session_state:
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
        if uploaded is None:
            st.warning("Please upload a document before running extraction.")
        elif not selected_extractors:
            st.warning("Please select at least one extractor.")
        else:
            run_status = st.status("Running extraction...", expanded=True)
            progress_bar = st.progress(0.0, text="Initializing extraction...")
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
            st.session_state.last_classification = classification

            recs = RECOMMENDATIONS.get(pdf_type, [])
            rec_text = ", ".join(recs)
            st.info(
                f"Input detected: {input_type}. "
                f"Classification: {pdf_type.title()} "
                f"(confidence {classification_confidence:.2f}). "
                f"Recommended: {rec_text}"
            )
            if "PaddleOCR" in selected_extractors:
                st.caption(
                    "PaddleOCR Language Mode: "
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
                progress_ratio = (idx - 1) / total_extractors
                progress_bar.progress(
                    progress_ratio,
                    text=f"Running {extractor_name} ({idx}/{total_extractors})...",
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
                            results = extractor.extract(
                                pdf_path=input_path,
                                output_dir=extractor_output_dir,
                            )
                        else:
                            results = extractor.extract(pdf_path=input_path)
                    elapsed = time.perf_counter() - start

                    payload = UnifiedOutputParser().to_json_payload(results)

                    md_source = extractor_output_dir / f"{input_path.stem}.md"
                    if (
                        extractor_name == "OpenDataLoader"
                        and input_type == "PDF"
                        and md_source.exists()
                    ):
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
                        warnings.append(f"{extractor_name}: {status.replace('_', ' ')}")

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
                        }
                    )
                    run_status.write(
                        f"Finished `{extractor_name}` in {elapsed:.2f}s "
                        f"(status: {status}, "
                        f"pages: {processed_page_count}/{page_count}, "
                        f"text length: {len(all_text)})."
                    )
                except Exception as exc:
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
                        }
                    )
                    warnings.append(f"{extractor_name}: failed ({exc})")
                    run_status.write(f"`{extractor_name}` failed: {exc}")

            st.session_state.last_results = per_extractor_results
            st.session_state.last_payload = per_extractor_payloads
            st.session_state.last_markdown = per_extractor_markdown
            st.session_state.last_paths = per_extractor_paths
            st.session_state.last_text = per_extractor_text
            st.session_state.comparison_rows = comparison_rows
            observations, recommendation = _build_comparison_observations(
                comparison_rows,
                st.session_state.last_classification,
            )
            st.session_state.observations = observations
            st.session_state.recommendation = recommendation
            st.session_state.last_meta = {
                "file_name": uploaded.name,
                "file_size_kb": round(len(uploaded.getvalue()) / 1024, 2),
                "input_type": input_type,
                "total_pdf_pages": page_count,
                "image_heavy_pages": image_heavy_pages,
                "ocr_image_only_pages": max(
                    0,
                    page_count - text_pages,
                ),
                "pdf_type": pdf_type,
                "classification_confidence": classification_confidence,
                "classification_reasoning": classification_reasoning,
                "avg_text_density": avg_text_density,
                "avg_image_ratio": avg_image_ratio,
                "text_pages": text_pages,
                "selected_extractors": selected_extractors,
            }

            if warnings:
                for warning in warnings:
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

    extractor_results = st.session_state.last_results
    if extractor_results:
        extractor_tabs = st.tabs(list(extractor_results.keys()))
        for index, extractor_name in enumerate(extractor_results.keys()):
            with extractor_tabs[index]:
                st.markdown(f"### {extractor_name}")
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
                    st.write(f"**File:** {st.session_state.last_meta.get('file_name', '')}")
                    st.write(f"**Size:** {st.session_state.last_meta.get('file_size_kb', 0)} KB")
                    st.write(
                        f"**Total PDF Pages:** "
                        f"{st.session_state.last_meta.get('total_pdf_pages', 0)}"
                    )
                    st.write(
                        f"**Detected Type:** "
                        f"{st.session_state.last_meta.get('pdf_type', 'unknown')}"
                    )
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
                            "**PaddleOCR Language Mode:** "
                            f"{_paddleocr_language_label(str(ocr_mode))} "
                            f"(`{ocr_mode}`)"
                        )
                        if ocr_metadata is not None:
                            metadata_extra = ocr_metadata.extra
                            st.write(
                                "**OCR Model:** "
                                f"{metadata_extra.get('ocr_model_name', '')}"
                            )
                            st.write(
                                "**OCR Language:** "
                                f"{metadata_extra.get('ocr_language', '')}"
                            )
                    if extractor_name == "Surya":
                        surya_metadata = None
                        if extractor_results.get(extractor_name):
                            surya_metadata = extractor_results[extractor_name][0].metadata
                        if surya_metadata is not None:
                            metadata_extra = surya_metadata.extra
                            st.write(
                                "**Surya Backend:** "
                                f"{metadata_extra.get('surya_backend', '')}"
                            )
                            st.write(
                                "**Surya Model:** "
                                f"{metadata_extra.get('surya_model_name', '')}"
                            )
                            st.write(
                                "**Layout Blocks:** "
                                f"{metadata_extra.get('surya_layout_block_count', 0)}"
                            )
                            st.write(
                                "**Average Confidence:** "
                                f"{metadata_extra.get('average_confidence', 0.0)}"
                            )
                    st.write(
                        "**Classifier Confidence:** "
                        f"{st.session_state.last_meta.get('classification_confidence', 0.0):.2f}"
                    )
                    st.write(
                        f"**Classifier Reason:** "
                        f"{st.session_state.last_meta.get('classification_reasoning', '')}"
                    )
                    st.write(
                        f"**Text-rich Pages:** {st.session_state.last_meta.get('text_pages', 0)} / "
                        f"{st.session_state.last_meta.get('total_pdf_pages', 0)}"
                    )
                    st.write(
                        f"**Avg Text Density:** "
                        f"{st.session_state.last_meta.get('avg_text_density', 0.0):.3f}"
                    )
                    st.write(
                        f"**Avg Image Ratio:** "
                        f"{st.session_state.last_meta.get('avg_image_ratio', 0.0):.3f}"
                    )
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


if __name__ == "__main__":
    run()
