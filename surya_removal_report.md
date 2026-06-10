# Surya Removal Report

## Summary

Surya OCR has been completely removed from the PDF Extraction Benchmark project.
All Surya-related code, configuration, dependencies, tests, documentation
references, and generated outputs have been removed. The remaining four
extractors (OpenDataLoader, PyMuPDF, Docling, PaddleOCR) were verified to work
correctly both individually and together, and the full test suite passes.

## Changes Made

### 1. Imports

- Removed `from pdf_extraction_benchmark.benchmarks.surya.benchmark import SuryaBenchmarkPipeline`
  and the `"SuryaBenchmarkPipeline"` export from
  [`src/pdf_extraction_benchmark/benchmarks/__init__.py`](src/pdf_extraction_benchmark/benchmarks/__init__.py).
- Removed the lazy `import_module("pdf_extraction_benchmark.extractors.surya.extractor")`
  branch from `_create_extractor()` in
  [`src/pdf_extraction_benchmark/ui/app.py`](src/pdf_extraction_benchmark/ui/app.py).

### 2. Extractor Selection UI

In [`src/pdf_extraction_benchmark/ui/app.py`](src/pdf_extraction_benchmark/ui/app.py):

- Removed `"Surya": None` from `EXTRACTOR_OPTIONS`.
- Removed the `"Surya"` entry from `EXTRACTOR_CAPABILITIES`.
- Removed `"Surya"` from the `RECOMMENDATIONS["scanned"]` list (now
  `["PaddleOCR", "Docling"]`).
- Removed the Surya-specific result panel block (Surya backend, Surya model,
  layout block count, average confidence display).

### 3. Benchmark Wrappers

- Deleted [`src/pdf_extraction_benchmark/benchmarks/surya/`](src/pdf_extraction_benchmark/benchmarks/surya/)
  (`__init__.py`, `benchmark.py`).
- Deleted `outputs/benchmark_results/surya/` (including `surya_vs_paddleocr.md`).

### 4. Runtime Code

- Deleted [`src/pdf_extraction_benchmark/extractors/surya/`](src/pdf_extraction_benchmark/extractors/surya/)
  (`__init__.py`, `extractor.py`, `runtime.py`).
- Deleted `outputs/surya/` (generated extraction outputs).

### 5. Configuration Options

- No dedicated Surya config files existed under `config/`. The only
  Surya-specific runtime settings (`SURYA_GUIDED_LAYOUT`, `SURYA_MODEL_CHECKPOINT`,
  `TORCH_DEVICE_MODEL`, llama.cpp backend handling) lived inside
  `extractors/surya/runtime.py`, which has been deleted entirely.

### 6. Reports & Documentation

- [`README.md`](README.md): Updated the Native vs Scanned dataset strategy
  section to remove Surya from the list of OCR-based extractors
  (`PaddleOCR, Surya, Tesseract/future` -> `PaddleOCR, Tesseract/future`).
- [`docs/benchmark_findings.md`](docs/benchmark_findings.md): Updated the
  "Next Steps" section to remove Surya from the OCR-first extractor adapter
  list (`PaddleOCR, Surya` -> `PaddleOCR`).

### 7. Dependencies

- [`pyproject.toml`](pyproject.toml): Removed `"surya-ocr>=0.20.0"` from
  `dependencies`.
- [`uv.lock`](uv.lock): Regenerated via `uv lock`. This removed `surya-ocr`
  and its now-unused transitive dependencies (`distro`, `jiter`, `openai`,
  `platformdirs`).
- `requirements.txt`: Did not contain any Surya references (no change needed).
- Removed local Surya model/tooling artifacts that are not tracked by git:
  `tools/surya-models/` (GGUF model files) and `tools/surya-hindi.pdf`.

### 8. Tests

- Deleted [`tests/test_surya_extractor.py`](tests/test_surya_extractor.py).
- [`tests/test_ui_paddleocr_language_mode.py`](tests/test_ui_paddleocr_language_mode.py):
  Replaced `test_surya_option_is_exposed_in_ui` (which asserted Surya was
  exposed in the UI) with `test_docling_option_is_exposed_in_ui`, which
  asserts Docling is present and drops the Surya assertions.

## Verification

### Extractor smoke tests (via `streamlit.testing.v1.AppTest`)

Ran the Streamlit app and exercised the "Run Extraction" flow against
`data/raw/native/native_1.pdf`:

| Extractor      | Result | Notes |
|----------------|--------|-------|
| PyMuPDF        | PASS   | Instant, no errors |
| OpenDataLoader | PASS   | Java-based extraction completed, 3 pages |
| Docling        | PASS   | ~19s, layout/table/OCR pipeline completed |
| PaddleOCR      | PASS   | English mode, completed without error |
| All four together | PASS | "Extraction completed for all selected extractors.", no exceptions, no errors |

### Test suite

```
$ pytest -q
19 passed, 101 warnings in ~72s
```

No test failures. No remaining references to "surya" in `src/`, `tests/`,
`config/`, `docs/`, `README.md`, `pyproject.toml`, or `requirements.txt`
(verified via case-insensitive recursive search).

## Notes / Follow-ups

- `tools/llama/` (a llama.cpp Windows build, ~ used as the optional Surya
  llama.cpp inference backend) is still present locally and untracked by git.
  It was not removed because its exclusivity to Surya was not fully verified
  and it wasn't explicitly named in the removal scope — confirm with the user
  before deleting if it's no longer needed.
- The `datasets/` and `tools/` directories remain untracked/uncommitted as
  before; they were not part of this change.
