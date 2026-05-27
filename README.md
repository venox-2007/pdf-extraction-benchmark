# PDF Extraction Tool Evaluation & Benchmarking

Production-ready, src-based Python scaffold for benchmarking PDF extraction and OCR tools.

## Major directories

- `config/`: Tool configs, benchmark configs, dataset paths, and environment config placeholders.
- `data/`: Raw PDFs, processed outputs, and ground-truth references.
- `src/pdf_extraction_benchmark/`: Main package with clean modular architecture.
- `tests/`: Sample tests for extractors, benchmark pipeline, and parser outputs.
- `outputs/`: Generated artifacts, logs, and benchmark result storage.
- `scripts/`: Runnable benchmark scripts.

## Architecture

- `interfaces/`: Abstract contracts (for example, `BaseExtractor`) for extensibility.
- `models/`: Shared schemas (`ExtractionResult`) used across extractors/parsers/benchmarks.
- `extractors/`: Tool adapters with a unified API.
- `classifiers/`: Document routing/classification modules.
- `parsers/`: Output normalization into unified JSON payloads.
- `benchmarks/`: Isolated benchmark dimensions and orchestrator pipeline.
- `utils/`: Cross-cutting helpers such as logging.

## Dev workflow

```bash
make setup
make lint
make format
make test
make run
```

## Notes

- Uses `pathlib` throughout starter modules.
- Configured for Python 3.11+, Ruff lint+format, and pytest discovery.
- Add new extraction tools by creating a package under `extractors/` implementing `BaseExtractor`.

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

Use short, clear commit messages. A simple format is:

- `feat: add pymupdf extractor parsing`
- `fix: handle empty OCR output`
- `docs: update benchmark usage`

If you are just starting, plain messages are also okay, for example:

- `Update parser output fields`
- `Add latency benchmark script`
