"""Professional Streamlit dashboard for document extraction benchmarking."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import streamlit as st

from pdf_extraction_benchmark.extractors.opendataloader.extractor import OpendataloaderExtractor
from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser
from pdf_extraction_benchmark.utils.logger import configure_logging

APP_NAME = "DocuVision AI"
APP_SUBTITLE = "PDF Intelligence Platform"
APP_VERSION = "v0.2.0"


def _inject_styles() -> None:
    """Inject lightweight CSS for enterprise-style dashboard polish."""
    st.markdown(
        """
        <style>
            .app-header {
                padding: 1rem 1.2rem;
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 14px;
                background: linear-gradient(135deg, rgba(37,99,235,0.18), rgba(15,23,42,0.45));
                margin-bottom: 1rem;
            }
            .subtitle {
                color: #cbd5e1;
                font-size: 0.95rem;
            }
            .status-badge {
                display: inline-block;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.78rem;
                border: 1px solid rgba(148,163,184,0.35);
                background: rgba(15,23,42,0.65);
                color: #e2e8f0;
            }
            .panel {
                padding: 0.9rem;
                border-radius: 12px;
                border: 1px solid rgba(148,163,184,0.25);
                background: rgba(15,23,42,0.35);
            }
            .footer {
                margin-top: 1.2rem;
                padding-top: 0.8rem;
                border-top: 1px solid rgba(148,163,184,0.25);
                color: #94a3b8;
                font-size: 0.85rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header(active_extractor: str, status: str) -> None:
    """Render top-level dashboard branding and status."""
    st.markdown(
        f"""
        <div class="app-header">
            <h1 style="margin:0;">{APP_NAME}</h1>
            <div class="subtitle">{APP_SUBTITLE}</div>
            <div style="margin-top:0.5rem; display:flex; gap:0.5rem; align-items:center; flex-wrap:wrap;">
                <span class="status-badge">Status: {status}</span>
                <span class="status-badge">Active Extractor: {active_extractor}</span>
                <span class="status-badge">Version: {APP_VERSION}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> tuple[Any, str, str, bool]:
    """Render left control sidebar and return selected inputs."""
    with st.sidebar:
        st.header("Extraction Control")
        uploaded = st.file_uploader("Upload PDF", type=["pdf"])
        extractor_name = st.selectbox("Extractor", options=["OpenDataLoader"])
        st.selectbox("Output Mode", options=["Markdown + JSON"], index=0)
        benchmark_mode = st.selectbox("Benchmark Mode", options=["Quick Scan", "Full Benchmark (Coming Soon)"])

        st.divider()
        st.subheader("Supported Tools")
        st.caption("OpenDataLoader (active)")
        st.caption("Textract, PyMuPDF, PaddleOCR (planned)")

        st.divider()
        run_clicked = st.button("Run Extraction", type="primary", use_container_width=True)

    return uploaded, extractor_name, benchmark_mode, run_clicked


def _render_pdf_panel(uploaded_file: Any) -> None:
    """Show uploaded file metadata and preview placeholder."""
    st.markdown("### PDF Preview")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    if uploaded_file is None:
        st.info("No PDF uploaded yet. Upload a file from the sidebar to begin extraction.")
    else:
        size_kb = len(uploaded_file.getvalue()) / 1024
        st.write(f"**Filename:** {uploaded_file.name}")
        st.write(f"**File size:** {size_kb:.2f} KB")
        st.caption("First-page visual preview is optional and can be enabled in a later iteration.")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_metrics(
    page_count: int,
    extraction_time_s: float,
    extractor_name: str,
    tables_detected: int,
    status: str,
) -> None:
    """Render key extraction metrics as cards."""
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Pages", str(page_count))
    col2.metric("Time", f"{extraction_time_s:.2f}s")
    col3.metric("Extractor", extractor_name)
    col4.metric("Tables", str(tables_detected))
    col5.metric("Status", status)


def _save_outputs(
    json_payload: dict[str, object],
    markdown_text: str,
    pdf_stem: str,
    output_json_dir: Path,
    output_md_dir: Path,
) -> tuple[Path, Path]:
    """Persist JSON and Markdown extraction outputs."""
    json_output = output_json_dir / f"{pdf_stem}.json"
    md_output = output_md_dir / f"{pdf_stem}.md"
    json_output.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    md_output.write_text(markdown_text, encoding="utf-8")
    return json_output, md_output


def run() -> None:
    """Render and run the professional extraction dashboard."""
    st.set_page_config(page_title=APP_NAME, layout="wide")
    _inject_styles()

    project_root = Path(__file__).resolve().parents[3]
    output_json_dir = project_root / "outputs" / "json"
    output_md_dir = project_root / "outputs" / "markdown"
    output_logs_dir = project_root / "outputs" / "logs"
    output_json_dir.mkdir(parents=True, exist_ok=True)
    output_md_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(output_logs_dir)

    uploaded, extractor_name, benchmark_mode, run_clicked = _render_sidebar()

    status = "Ready"
    _render_header(active_extractor=extractor_name, status=status)

    metrics_container = st.container()
    col_left, col_right = st.columns([1.1, 1.9], gap="large")

    with col_left:
        _render_pdf_panel(uploaded)

    with col_right:
        st.markdown("### Extraction Workspace")
        st.caption(f"Benchmark Mode: {benchmark_mode}")

        if run_clicked:
            if uploaded is None:
                st.warning("Please upload a PDF from the sidebar before running extraction.")
            else:
                input_dir = project_root / "data" / "processed"
                input_dir.mkdir(parents=True, exist_ok=True)
                pdf_path = input_dir / uploaded.name
                pdf_path.write_bytes(uploaded.getvalue())

                start = time.perf_counter()
                try:
                    extractor = OpendataloaderExtractor()
                    results = extractor.extract(pdf_path=pdf_path, output_dir=project_root / "outputs")
                    elapsed = time.perf_counter() - start

                    parser = UnifiedOutputParser()
                    payload = parser.to_json_payload(results)

                    markdown_file = project_root / "outputs" / f"{pdf_path.stem}.md"
                    if markdown_file.exists():
                        markdown_text = markdown_file.read_text(encoding="utf-8")
                    else:
                        markdown_text = "\n\n".join(result.extracted_text for result in results)

                    json_output, md_output = _save_outputs(
                        json_payload=payload,
                        markdown_text=markdown_text,
                        pdf_stem=pdf_path.stem,
                        output_json_dir=output_json_dir,
                        output_md_dir=output_md_dir,
                    )

                    table_count = sum(len(result.tables) for result in results)
                    with metrics_container:
                        _render_metrics(
                            page_count=len(results),
                            extraction_time_s=elapsed,
                            extractor_name=extractor_name,
                            tables_detected=table_count,
                            status="Success",
                        )

                    st.success("Extraction completed successfully.")

                    tabs = st.tabs(["Extracted Text", "Markdown", "JSON", "Metadata", "Logs"])
                    all_text = "\n\n".join(result.extracted_text for result in results)

                    with tabs[0]:
                        st.text_area("Text", value=all_text, height=320)

                    with tabs[1]:
                        st.code(markdown_text[:15000], language="markdown")

                    with tabs[2]:
                        st.json(payload)

                    with tabs[3]:
                        st.json([result.metadata.extra if result.metadata else {} for result in results])

                    with tabs[4]:
                        st.write("Output files")
                        st.code(str(json_output))
                        st.code(str(md_output))
                        st.caption("Latest log file: outputs/logs/benchmark.log")

                    st.markdown("### Extraction Summary")
                    st.markdown('<div class="panel">', unsafe_allow_html=True)
                    st.write(f"Processed **{uploaded.name}** using **{extractor_name}**.")
                    st.write(f"Generated {len(results)} page-level records and saved dashboard outputs.")
                    st.markdown("</div>", unsafe_allow_html=True)

                except Exception as exc:
                    elapsed = time.perf_counter() - start
                    with metrics_container:
                        _render_metrics(
                            page_count=0,
                            extraction_time_s=elapsed,
                            extractor_name=extractor_name,
                            tables_detected=0,
                            status="Failed",
                        )
                    st.error(f"Extraction failed: {exc}")
        else:
            with metrics_container:
                _render_metrics(
                    page_count=0,
                    extraction_time_s=0.0,
                    extractor_name=extractor_name,
                    tables_detected=0,
                    status="Idle",
                )
            st.info("Upload a PDF and click 'Run Extraction' to populate results.")

    st.markdown(
        f'<div class="footer">{APP_NAME} • {APP_SUBTITLE} • {APP_VERSION} • Active Extractor: {extractor_name}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    run()
