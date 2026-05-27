"""Streamlit app for PDF extraction demo with OpenDataLoader."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from pdf_extraction_benchmark.extractors.opendataloader.extractor import OpendataloaderExtractor
from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser
from pdf_extraction_benchmark.utils.logger import configure_logging


def run() -> None:
    """Render and run the Streamlit extraction UI."""
    project_root = Path(__file__).resolve().parents[3]
    output_json_dir = project_root / "outputs" / "json"
    output_md_dir = project_root / "outputs" / "markdown"
    output_logs_dir = project_root / "outputs" / "logs"
    output_json_dir.mkdir(parents=True, exist_ok=True)
    output_md_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(output_logs_dir)

    st.set_page_config(page_title="PDF Extraction Benchmark Demo", layout="wide")
    st.title("PDF Extraction Benchmark Demo")
    st.subheader("Milestone 1: Streamlit + OpenDataLoader end-to-end extraction")

    with st.sidebar:
        st.header("Project Overview")
        st.write("This demo extracts PDF content and saves JSON/Markdown outputs.")
        st.header("Supported Tools")
        st.write("- OpenDataLoader")
        st.header("Implementation Progress")
        st.write("- Streamlit UI: Done")
        st.write("- OpenDataLoader extractor: Done")
        st.write("- Benchmarking modules: Pending")

    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    extractor_name = st.selectbox("Extractor", options=["OpenDataLoader"])
    run_clicked = st.button("Run Extraction", type="primary")

    if run_clicked:
        if uploaded is None:
            st.warning("Please upload a PDF first.")
            return

        input_dir = project_root / "data" / "processed"
        input_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = input_dir / uploaded.name
        pdf_path.write_bytes(uploaded.getvalue())

        try:
            extractor = OpendataloaderExtractor()
            results = extractor.extract(pdf_path=pdf_path, output_dir=project_root / "outputs")

            parser = UnifiedOutputParser()
            payload = parser.to_json_payload(results)

            json_output = output_json_dir / f"{pdf_path.stem}.json"
            json_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            markdown_file = project_root / "outputs" / f"{pdf_path.stem}.md"
            if markdown_file.exists():
                markdown_text = markdown_file.read_text(encoding="utf-8")
            else:
                markdown_text = "\n\n".join(result.extracted_text for result in results)
            markdown_output = output_md_dir / f"{pdf_path.stem}.md"
            markdown_output.write_text(markdown_text, encoding="utf-8")

            st.success(f"Extraction complete using {extractor_name}.")
            st.write(f"Page count: {len(results)}")

            all_text = "\n\n".join(result.extracted_text for result in results)
            st.subheader("Extracted Text")
            st.text_area("Text Output", value=all_text, height=200)

            st.subheader("Markdown Preview")
            st.code(markdown_text[:5000], language="markdown")

            st.subheader("Extraction Metadata")
            st.json([result.metadata.extra if result.metadata else {} for result in results])

            st.subheader("Unified JSON Preview")
            st.json(payload)

            st.caption(f"Saved JSON: {json_output}")
            st.caption(f"Saved Markdown: {markdown_output}")

        except Exception as exc:
            st.error(f"Extraction failed: {exc}")


if __name__ == "__main__":
    run()
