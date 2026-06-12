# PDF Extraction Tool Evaluation & Benchmarking

Beginner-friendly, src-based Python project for benchmarking PDF extraction and OCR tools.

## Runtime Requirements

- Python 3.11+
- Java 11+ on system PATH (required by OpenDataLoader)

Verify Java:

```bash
java -version
```

If Java is missing on Windows, install Eclipse Temurin JDK 11+ and reopen terminal.

## Setup

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install --upgrade pip
pip install -e .[dev]
pip install -r requirements.txt
```

## Run Streamlit UI

```bash
streamlit run src/pdf_extraction_benchmark/ui/app.py
```

## Run OpenDataLoader Demo Script

```bash
python scripts/run_opendataloader_demo.py data/raw/native/native_research_01.pdf
```

## Major directories

- `config/`: Tool configs, benchmark configs, dataset paths, environment placeholders.
- `data/`: Raw PDFs, processed outputs, and ground-truth references.
- `src/pdf_extraction_benchmark/`: Main package with modular architecture.
- `tests/`: Starter tests for extractors, benchmark pipeline, parser outputs.
- `outputs/`: JSON/Markdown/charts/logs/benchmark results.
- `scripts/`: Runnable benchmark and extraction scripts.

## Dataset Strategy (Native vs Scanned)

The dataset is intentionally organized around extraction strategy, not early document subcategories:

- `data/raw/native/`: text-based PDFs suited for direct parsing/extraction.
- `data/raw/scanned/`: image-based PDFs requiring OCR-oriented extractors.

Why this matters:

- Native PDFs -> direct extraction tools (OpenDataLoader, PyMuPDF, Marker)
- Scanned PDFs -> OCR-based extractors (PaddleOCR, Tesseract/future)

This keeps routing and benchmarking aligned with real-world document AI pipelines.

### OpenDataLoader extraction modes

OpenDataLoader operates in two modes depending on document type:

- **Native PDFs**: OpenDataLoader's standard (Java, text-layer) extraction pipeline.
- **Scanned/Image PDFs**: OpenDataLoader Hybrid Mode, which delegates OCR and layout
  analysis to a Docling-based backend (`docling-fast`) running with `rapidocr`.

Because of this, benchmark results for OpenDataLoader on scanned/image documents
reflect the Docling+rapidocr hybrid backend's accuracy and speed (including its
startup/inference cost), not an independent OCR engine. Native-PDF results are
unaffected and use OpenDataLoader's own pipeline.

Future-ready TODOs (not implemented yet):

- dataset metadata manifests
- benchmark tags and document categories
- quality labels (low quality, rotated, skewed)
- page-level rotation/skew annotations

## Milestone 1 scope

- Streamlit UI
- OpenDataLoader integration
- Basic extraction flow
- Visible JSON + Markdown outputs

## Git Workflow

### Pull latest changes

```bash
git pull origin main
```

### Push your updates

```bash
git status
git add .
git commit -m "type: short clear message"
git push
```

### Recommended commit style

- `feat: add opendataloader extractor`
- `fix: handle missing output json`
- `docs: update streamlit setup`
