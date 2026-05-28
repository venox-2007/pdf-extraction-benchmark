"""Minimal professional Streamlit app for PDF extraction benchmarking."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import fitz
import streamlit as st

# Ensure local src package imports resolve when launching Streamlit directly.
SRC_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pdf_extraction_benchmark.classifiers.pdf_type_classifier import PdfTypeClassifier  # noqa: E402
from pdf_extraction_benchmark.extractors.opendataloader.extractor import (  # noqa: E402
    OpendataloaderExtractor,
)
from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor  # noqa: E402
from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser  # noqa: E402
from pdf_extraction_benchmark.utils.logger import configure_logging  # noqa: E402

APP_NAME = "DocuVision AI"
APP_SUBTITLE = "Clean PDF intelligence with multiple extraction backends"

RECOMMENDATIONS = {
    "native": ["OpenDataLoader", "PyMuPDF", "Marker"],
    "scanned": ["PaddleOCR", "Surya", "Tesseract (future)"],
    "mixed": ["OpenDataLoader + OCR fallback", "Surya", "PaddleOCR"],
}

EXTRACTOR_OPTIONS = {
    "OpenDataLoader": OpendataloaderExtractor,
    "PyMuPDF": PymupdfExtractor,
}


def _extractor_slug(extractor_name: str) -> str:
    """Convert extractor display name into output folder slug."""
    return extractor_name.lower().replace(" ", "")


def _inject_styles() -> None:
    """Apply lightweight styling for clean spacing and typography."""
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.4rem;
                padding-bottom: 2rem;
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


def _build_comparison_observations(rows: list[dict[str, object]]) -> list[str]:
    """Generate lightweight heuristic comparison notes."""
    notes: list[str] = []
    if len(rows) < 2:
        return notes

    fastest = min(rows, key=lambda row: float(row["latency_seconds"]))
    slowest = max(rows, key=lambda row: float(row["latency_seconds"]))
    if float(slowest["latency_seconds"]) > 0:
        ratio = float(fastest["latency_seconds"]) / float(slowest["latency_seconds"])
        if ratio <= 0.7:
            notes.append(f"{fastest['extractor']} extraction completed significantly faster.")

    rich_format = max(rows, key=lambda row: int(row["markdown_length"]))
    lean_text = max(rows, key=lambda row: int(row["text_length"]))
    if rich_format["extractor"] != lean_text["extractor"]:
        notes.append(f"{rich_format['extractor']} preserved richer markdown formatting.")

    for row in rows:
        if row["ocr_supported"] is False and row["ocr_required_pages"] > 0:
            notes.append(f"{row['extractor']} detected low OCR capability on scan-like pages.")
    return notes


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
        uploaded = st.file_uploader("Upload PDF", type=["pdf"])
        selected_extractors = st.multiselect(
            "Extractors",
            options=list(EXTRACTOR_OPTIONS.keys()),
            default=["OpenDataLoader", "PyMuPDF"],
        )
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
        st.session_state.last_classification = None

    if run_clicked:
        if uploaded is None:
            st.warning("Please upload a PDF before running extraction.")
        elif not selected_extractors:
            st.warning("Please select at least one extractor.")
        else:
            input_dir = project_root / "data" / "processed"
            input_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = input_dir / uploaded.name
            pdf_path.write_bytes(uploaded.getvalue())

            classifier = PdfTypeClassifier()
            classification = classifier.classify(pdf_path)
            st.session_state.last_classification = classification

            recs = RECOMMENDATIONS.get(classification.pdf_type, [])
            rec_text = ", ".join(recs)
            if classification.pdf_type == "scanned":
                st.warning(
                    f"Detected: Scanned PDF (confidence {classification.confidence:.2f}). "
                    f"OCR extractor recommended: {rec_text}"
                )
            else:
                st.info(
                    f"Detected: {classification.pdf_type.title()} PDF "
                    f"(confidence {classification.confidence:.2f}). "
                    f"Recommended extractors: {rec_text}"
                )

            per_extractor_results: dict[str, list[Any]] = {}
            per_extractor_payloads: dict[str, dict[str, object]] = {}
            per_extractor_markdown: dict[str, str] = {}
            per_extractor_paths: dict[str, dict[str, str]] = {}
            per_extractor_text: dict[str, str] = {}
            comparison_rows: list[dict[str, object]] = []
            warnings: list[str] = []

            for extractor_name in selected_extractors:
                start = time.perf_counter()
                extractor_slug = _extractor_slug(extractor_name)
                extractor_output_dir = output_root_dir / extractor_slug / pdf_path.stem
                extractor_output_dir.mkdir(parents=True, exist_ok=True)

                try:
                    extractor_cls = EXTRACTOR_OPTIONS[extractor_name]
                    extractor = extractor_cls()
                    if extractor_name == "OpenDataLoader":
                        results = extractor.extract(
                            pdf_path=pdf_path,
                            output_dir=extractor_output_dir,
                        )
                    else:
                        results = extractor.extract(pdf_path=pdf_path)
                    elapsed = time.perf_counter() - start

                    payload = UnifiedOutputParser().to_json_payload(results)

                    md_source = extractor_output_dir / f"{pdf_path.stem}.md"
                    if extractor_name == "OpenDataLoader" and md_source.exists():
                        markdown_text = _read_text_safely(md_source)
                    else:
                        markdown_text = "\n\n".join(result.extracted_text for result in results)

                    if classification.pdf_type == "scanned":
                        image_section = _build_scanned_page_image_markdown(
                            pdf_path=pdf_path,
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
                    processed_page_count = (
                        classification.page_count if extracted_result_count > 0 else 0
                    )
                    ocr_required_pages = sum(
                        1
                        for result in results
                        if result.metadata and result.metadata.extra.get("ocr_required") is True
                    )
                    ocr_supported = any(
                        result.metadata and result.metadata.extra.get("ocr_supported") is not False
                        for result in results
                    )
                    status = "success" if not no_text_output else "empty_text_output"
                    if classification.pdf_type == "scanned" and no_text_output:
                        status = "limited_for_scanned_pdf"
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
                            "total_pages": classification.page_count,
                            "processed_pages": processed_page_count,
                            "text_length": len(all_text),
                            "markdown_length": len(markdown_text),
                            "ocr_supported": ocr_supported,
                            "ocr_required_pages": ocr_required_pages,
                            "status": status,
                            "pdf_type": classification.pdf_type,
                        }
                    )
                except Exception as exc:
                    comparison_rows.append(
                        {
                            "extractor": extractor_name,
                            "latency_seconds": round(time.perf_counter() - start, 3),
                            "total_pages": classification.page_count,
                            "processed_pages": 0,
                            "text_length": 0,
                            "markdown_length": 0,
                            "ocr_supported": False,
                            "ocr_required_pages": 0,
                            "status": "failed",
                            "pdf_type": classification.pdf_type,
                        }
                    )
                    warnings.append(f"{extractor_name}: failed ({exc})")

            st.session_state.last_results = per_extractor_results
            st.session_state.last_payload = per_extractor_payloads
            st.session_state.last_markdown = per_extractor_markdown
            st.session_state.last_paths = per_extractor_paths
            st.session_state.last_text = per_extractor_text
            st.session_state.comparison_rows = comparison_rows
            st.session_state.observations = _build_comparison_observations(comparison_rows)
            st.session_state.last_meta = {
                "file_name": uploaded.name,
                "file_size_kb": round(len(uploaded.getvalue()) / 1024, 2),
                "total_pdf_pages": classification.page_count,
                "image_heavy_pages": classification.image_heavy_pages,
                "ocr_image_only_pages": max(
                    0,
                    classification.page_count - classification.text_pages,
                ),
                "pdf_type": classification.pdf_type,
                "classification_confidence": classification.confidence,
                "classification_reason": classification.reason,
                "selected_extractors": selected_extractors,
            }

            if warnings:
                for warning in warnings:
                    st.warning(warning)
            else:
                st.success("Extraction completed for all selected extractors.")

    if st.session_state.comparison_rows:
        st.markdown("### Comparison Overview")
        st.dataframe(st.session_state.comparison_rows, use_container_width=True)

    if st.session_state.observations:
        st.markdown("### Benchmark Notes")
        for note in st.session_state.observations:
            st.write(f"- {note}")

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
                    markdown_for_view = markdown_value[:15000]
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
                    st.write(
                        "**Classifier Confidence:** "
                        f"{st.session_state.last_meta.get('classification_confidence', 0.0):.2f}"
                    )
                    st.write(
                        f"**Classifier Reason:** "
                        f"{st.session_state.last_meta.get('classification_reason', '')}"
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
