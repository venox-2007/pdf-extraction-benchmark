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
python scripts/run_opendataloader_demo.py data/raw/native/sample_native_demo.pdf
```

## Major directories

- `config/`: Tool configs, benchmark configs, dataset paths, environment placeholders.
- `data/`: Raw PDFs, processed outputs, and ground-truth references.
- `src/pdf_extraction_benchmark/`: Main package with modular architecture.
- `tests/`: Starter tests for extractors, benchmark pipeline, parser outputs.
- `outputs/`: JSON/Markdown/charts/logs/benchmark results.
- `scripts/`: Runnable benchmark and extraction scripts.

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
