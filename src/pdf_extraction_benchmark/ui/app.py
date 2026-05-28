"""Minimal professional Streamlit app for OpenDataLoader extraction."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import streamlit as st

# Ensure local src package imports resolve when launching Streamlit directly.
SRC_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pdf_extraction_benchmark.classifiers.pdf_type_classifier import PdfTypeClassifier
from pdf_extraction_benchmark.extractors.opendataloader.extractor import OpendataloaderExtractor
from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser
from pdf_extraction_benchmark.utils.logger import configure_logging

APP_NAME = "DocuVision AI"
APP_SUBTITLE = "Clean PDF intelligence with OpenDataLoader"

RECOMMENDATIONS = {
    "native": ["OpenDataLoader", "PyMuPDF", "Marker"],
    "scanned": ["PaddleOCR", "Surya", "Tesseract (future)"],
    "mixed": ["OpenDataLoader + OCR fallback", "Surya", "PaddleOCR"],
}


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
    pdf_stem: str,
    output_json_dir: Path,
    output_md_dir: Path,
) -> tuple[Path, Path]:
    """Save unified JSON and markdown outputs."""
    json_output = output_json_dir / f"{pdf_stem}.json"
    md_output = output_md_dir / f"{pdf_stem}.md"
    json_output.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    md_output.write_text(markdown_text, encoding="utf-8")
    return json_output, md_output


def run() -> None:
    """Render and run the streamlined extraction dashboard."""
    st.set_page_config(page_title=APP_NAME, layout="wide")
    _inject_styles()

    project_root = Path(__file__).resolve().parents[3]
    output_json_dir = project_root / "outputs" / "json"
    output_md_dir = project_root / "outputs" / "markdown"
    output_logs_dir = project_root / "outputs" / "logs"
    output_json_dir.mkdir(parents=True, exist_ok=True)
    output_md_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(output_logs_dir)

    with st.sidebar:
        st.header("Extraction")
        uploaded = st.file_uploader("Upload PDF", type=["pdf"])
        extractor_name = st.selectbox("Extractor", options=["OpenDataLoader"])
        run_clicked = st.button("Run Extraction", type="primary", use_container_width=True)

    st.title(APP_NAME)
    st.markdown(f'<div class="subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)

    if "last_results" not in st.session_state:
        st.session_state.last_results = None
        st.session_state.last_payload = None
        st.session_state.last_markdown = ""
        st.session_state.last_meta = {}
        st.session_state.last_paths = {}
        st.session_state.last_classification = None

    if run_clicked:
        if uploaded is None:
            st.warning("Please upload a PDF before running extraction.")
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

            start = time.perf_counter()
            try:
                extractor = OpendataloaderExtractor()
                results = extractor.extract(pdf_path=pdf_path, output_dir=project_root / "outputs")
                elapsed = time.perf_counter() - start

                parser = UnifiedOutputParser()
                payload = parser.to_json_payload(results)

                md_source = project_root / "outputs" / f"{pdf_path.stem}.md"
                if md_source.exists():
                    markdown_text = _read_text_safely(md_source)
                else:
                    markdown_text = "\n\n".join(result.extracted_text for result in results)

                json_output, md_output = _save_outputs(
                    json_payload=payload,
                    markdown_text=markdown_text,
                    pdf_stem=pdf_path.stem,
                    output_json_dir=output_json_dir,
                    output_md_dir=output_md_dir,
                )

                all_text = "\n\n".join(result.extracted_text for result in results)
                image_only_markdown = "![" in markdown_text and "](." in markdown_text
                no_text_output = not all_text.strip()
                extraction_state = "success"
                if classification.pdf_type == "scanned" and no_text_output and image_only_markdown:
                    extraction_state = "limited_for_scanned_pdf"
                elif no_text_output:
                    extraction_state = "empty_text_output"
                processed_page_numbers = {result.page_number for result in results}
                extracted_result_count = len(results)
                # OpenDataLoader may return fewer chunks than real PDF pages; use classifier page
                # analysis as the reliable source-of-truth for page-accounting metrics.
                processed_page_count = classification.page_count if extracted_result_count > 0 else 0
                textful_pages = classification.text_pages
                image_only_processed_pages = max(0, classification.page_count - textful_pages)

                st.session_state.last_results = results
                st.session_state.last_payload = payload
                st.session_state.last_markdown = markdown_text
                st.session_state.last_meta = {
                    "total_pdf_pages": classification.page_count,
                    "processed_pages": processed_page_count,
                    "extracted_result_count": extracted_result_count,
                    "image_heavy_pages": classification.image_heavy_pages,
                    "ocr_image_only_pages": image_only_processed_pages,
                    "time_s": elapsed,
                    "extractor": extractor_name,
                    "file_name": uploaded.name,
                    "file_size_kb": round(len(uploaded.getvalue()) / 1024, 2),
                    "pdf_type": classification.pdf_type,
                    "classification_confidence": classification.confidence,
                    "classification_reason": classification.reason,
                    "extraction_state": extraction_state,
                }
                st.session_state.last_paths = {"json": str(json_output), "markdown": str(md_output)}
                st.session_state.last_text = all_text

                if extraction_state == "limited_for_scanned_pdf":
                    st.warning(
                        "OpenDataLoader detected embedded images but no OCR text extraction. "
                        "Use an OCR-focused extractor for scanned PDFs."
                    )
                elif extraction_state == "empty_text_output":
                    st.warning(
                        "Extraction finished, but normalized text output is empty. "
                        "Please verify parser mapping for this PDF schema."
                    )
                else:
                    st.success("Extraction completed successfully.")
            except Exception as exc:
                st.error(f"Extraction failed: {exc}")

    meta = st.session_state.last_meta if st.session_state.last_meta else {
        "total_pdf_pages": 0,
        "processed_pages": 0,
        "ocr_image_only_pages": 0,
        "time_s": 0.0,
        "extractor": extractor_name,
        "pdf_type": "unknown",
        "classification_confidence": 0.0,
        "extraction_state": "idle",
    }

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total PDF Pages", str(meta["total_pdf_pages"]))
    m2.metric("Processed Pages", str(meta["processed_pages"]))
    m3.metric("OCR/Image-only Pages", str(meta["ocr_image_only_pages"]))
    m4.metric("Extraction Time", f"{meta['time_s']:.2f}s")
    m5.metric("PDF Type", str(meta["pdf_type"]).title())
    m6.metric("State", str(meta["extraction_state"]).replace("_", " ").title())

    tabs = st.tabs(["Text", "Markdown", "JSON"])

    with tabs[0]:
        text_value = st.session_state.get("last_text", "")
        st.text_area("Extracted Text", value=text_value, height=320)

    with tabs[1]:
        markdown_value = st.session_state.get("last_markdown", "")
        st.code(markdown_value[:15000], language="markdown")

    with tabs[2]:
        payload = st.session_state.get("last_payload")
        if payload is None:
            st.info("JSON output will appear here after extraction.")
        else:
            st.json(payload)

    if st.session_state.last_meta:
        st.markdown("### Metadata")
        st.markdown('<div class="meta-card">', unsafe_allow_html=True)
        st.write(f"**File:** {st.session_state.last_meta['file_name']}")
        st.write(f"**Size:** {st.session_state.last_meta['file_size_kb']} KB")
        st.write(f"**Total PDF Pages:** {st.session_state.last_meta['total_pdf_pages']}")
        st.write(f"**Processed Pages:** {st.session_state.last_meta['processed_pages']}")
        st.write(f"**Extracted Result Count:** {st.session_state.last_meta['extracted_result_count']}")
        st.write(f"**Image-heavy Pages (Classifier): {st.session_state.last_meta['image_heavy_pages']}")
        st.write(f"**OCR/Image-only Pages:** {st.session_state.last_meta['ocr_image_only_pages']}")
        st.write(f"**Detected Type:** {st.session_state.last_meta['pdf_type'].title()}")
        st.write(
            "**Classifier Confidence:** "
            f"{st.session_state.last_meta['classification_confidence']:.2f}"
        )
        st.write(f"**Classifier Reason:** {st.session_state.last_meta['classification_reason']}")
        recommendation = ", ".join(RECOMMENDATIONS.get(st.session_state.last_meta["pdf_type"], []))
        st.write(f"**Recommended Extractors:** {recommendation}")
        st.write(f"**Extraction State:** {st.session_state.last_meta['extraction_state']}")
        st.write(f"**JSON Output:** `{st.session_state.last_paths.get('json', '')}`")
        st.write(f"**Markdown Output:** `{st.session_state.last_paths.get('markdown', '')}`")
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    run()
