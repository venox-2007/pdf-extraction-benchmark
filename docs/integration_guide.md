# Integration Guide

How to embed the PDF extraction pipeline into a production Python service.

---

## Overview

The project exposes a single abstract interface (`BaseExtractor`) with five
concrete implementations. A classifier detects document type and routes to the
appropriate extractor. All results use a shared schema (`ExtractionResult`) so
downstream code is extractor-agnostic.

```
Input PDF
    │
    ▼
PdfTypeClassifier          ← classifies as native / scanned / hybrid
    │
    ├── native ────────────► PyMuPDF   (fast, text-layer)
    │                  or   OpenDataLoader (structured + tables)
    │
    └── scanned / hybrid ──► PaddleOCR (accuracy-priority OCR)
                        or   Tesseract  (speed-priority OCR)
                        or   Docling    (table-heavy scanned docs)
    │
    ▼
ExtractionResult[]          ← unified page-level schema
    │
    ▼
Your application logic
```

---

## Installation

```bash
# Clone / install the package
pip install -e .

# Optional: install dev tools
pip install -e .[dev]

# System requirements
# Java 11+ on PATH (OpenDataLoader)
# Tesseract binary (Tesseract extractor)
#   Windows: winget install --id UB-Mannheim.TesseractOCR -e
#   macOS:   brew install tesseract
#   Linux:   sudo apt-get install tesseract-ocr
```

---

## Core API

### 1. Classify a document

```python
from pathlib import Path
from pdf_extraction_benchmark.classifiers.pdf_type_classifier import PdfTypeClassifier

classifier = PdfTypeClassifier()
result = classifier.classify(Path("invoice.pdf"))

print(result.pdf_type)    # "native" | "scanned" | "hybrid"
print(result.confidence)  # 0.0–1.0
print(result.reasoning)   # human-readable explanation
```

### 2. Extract from a single PDF

```python
from pathlib import Path
from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor
from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor

# Native PDF
extractor = PymupdfExtractor()
results = extractor.extract(Path("native_report.pdf"))

for page in results:
    print(f"Page {page.page_number}: {len(page.extracted_text)} chars")
    print(page.extracted_text[:200])

# Scanned PDF
extractor = PaddleocrExtractor(language_mode="english")
results = extractor.extract(Path("scanned_invoice.pdf"))

for page in results:
    print(f"Confidence: {page.metadata.extra.get('average_confidence'):.2f}")
    print(f"Bounding boxes: {len(page.bounding_boxes)}")
```

### 3. Use the classifier to route automatically

```python
from pathlib import Path
from pdf_extraction_benchmark.classifiers.pdf_type_classifier import PdfTypeClassifier
from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor

classifier = PdfTypeClassifier()
native_extractor = PymupdfExtractor()
ocr_extractor = PaddleocrExtractor()

def extract(pdf_path: Path):
    doc_type = classifier.classify(pdf_path).pdf_type
    if doc_type == "native":
        return native_extractor.extract(pdf_path)
    else:  # scanned or hybrid
        return ocr_extractor.extract(pdf_path)
```

---

## Output Schema

Every extractor returns `list[ExtractionResult]` — one item per page.

```python
from pdf_extraction_benchmark.models.extraction_result import (
    ExtractionResult,
    BoundingBox,
    ExtractedTable,
    TableCell,
    ExtractionMetadata,
)

# ExtractionResult fields:
result.tool_name          # str — extractor name
result.page_number        # int — 1-indexed
result.extracted_text     # str — full page text
result.tables             # list[ExtractedTable]
result.bounding_boxes     # list[BoundingBox]  (word-level for OCR extractors)
result.confidence_scores  # list[float]        (0.0–1.0, OCR extractors only)
result.metadata           # ExtractionMetadata

# ExtractionMetadata fields:
result.metadata.source_file   # str
result.metadata.latency_ms    # float | None
result.metadata.extra         # dict — tool-specific (status, ocr_used, versions, etc.)

# BoundingBox fields:
bbox.x0, bbox.y0, bbox.x1, bbox.y1  # pixel coordinates (origin: top-left)
# Note: OCR extractors (PaddleOCR, Tesseract) produce boxes in 144-dpi space.
# PyMuPDF and Docling use 72-dpi (PDF point) space.

# ExtractedTable fields:
table.table_id            # str
table.bbox                # BoundingBox | None
table.cells               # list[TableCell]
cell.row, cell.col        # int (0-indexed)
cell.text                 # str
cell.bbox                 # BoundingBox | None
```

### Serialize to JSON

```python
import json
from dataclasses import asdict

# Single page
json.dumps(asdict(results[0]))

# All pages
json.dumps([asdict(r) for r in results])
```

### Check extraction status

```python
for page in results:
    status = page.metadata.extra.get("status", "unknown")
    if status == "ok":
        process(page.extracted_text)
    elif status == "no_text_detected":
        log.warning(f"Page {page.page_number}: no text extracted")
    elif status == "ocr_runtime_error":
        log.error(f"Page {page.page_number}: {page.metadata.extra.get('error')}")
```

---

## Embedding in a FastAPI Microservice

```python
# service.py
from fastapi import FastAPI, UploadFile, File
from pathlib import Path
import tempfile, json
from dataclasses import asdict

from pdf_extraction_benchmark.classifiers.pdf_type_classifier import PdfTypeClassifier
from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor
from pdf_extraction_benchmark.extractors.paddleocr.extractor import PaddleocrExtractor

app = FastAPI()

# Initialise once at startup — model loading is expensive
classifier = PdfTypeClassifier()
native_extractor = PymupdfExtractor()
ocr_extractor = PaddleocrExtractor()


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    import os

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        doc_type = classifier.classify(tmp_path).pdf_type
        extractor = native_extractor if doc_type == "native" else ocr_extractor
        results = extractor.extract(tmp_path)
    finally:
        os.unlink(tmp_path)  # always clean up the temp file

    return {
        "document_type": doc_type,
        "pages": [asdict(r) for r in results],
    }
```

Run with:

```bash
pip install fastapi uvicorn python-multipart
uvicorn service:app --host 0.0.0.0 --port 8000
```

---

## Batch Processing

```python
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pdf_extraction_benchmark.extractors.pymupdf.extractor import PymupdfExtractor

extractor = PymupdfExtractor()
pdf_paths = list(Path("data/").glob("**/*.pdf"))

# Sequential (safe, simple)
results = {p: extractor.extract(p) for p in pdf_paths}

# Parallel (PyMuPDF is thread-safe; PaddleOCR is not — use processes instead)
with ThreadPoolExecutor(max_workers=4) as pool:
    futures = {p: pool.submit(extractor.extract, p) for p in pdf_paths}
    results = {p: f.result() for p, f in futures.items()}
```

> **Thread safety:** PyMuPDF is thread-safe. PaddleOCR and Docling are **not**
> thread-safe — use `multiprocessing.Pool` or separate processes for parallel
> OCR. Tesseract (pytesseract) calls the system binary as a subprocess and is
> effectively process-safe.

---

## Extractor Reference

| Class | Import path | Init args | Notes |
| --- | --- | --- | --- |
| `PymupdfExtractor` | `extractors.pymupdf.extractor` | none | Fastest; native PDFs only |
| `OpenDataLoaderExtractor` | `extractors.opendataloader.extractor` | `hybrid_url=None` | Java required; pass `hybrid_url` for OCR mode |
| `PaddleocrExtractor` | `extractors.paddleocr.extractor` | `language_mode="english"` | `"english"` or `"multilingual"` (Devanagari) |
| `DoclingExtractor` | `extractors.docling.extractor` | `output_root=None` | Saves result.json/.md alongside extraction |
| `TesseractExtractor` | `extractors.tesseract.extractor` | none | Tesseract binary must be on PATH or in standard Windows install location |

---

## OpenDataLoader Hybrid Mode

To enable OCR for scanned documents via OpenDataLoader:

```python
import subprocess, time, requests
from pdf_extraction_benchmark.extractors.opendataloader.extractor import OpenDataLoaderExtractor
from pdf_extraction_benchmark.utils.opendataloader_hybrid import ensure_hybrid_server

# Start the Docling/rapidocr backend server
server = ensure_hybrid_server()  # returns None if server fails to start

if server:
    extractor = OpenDataLoaderExtractor(hybrid_url="http://127.0.0.1:5002")
else:
    extractor = OpenDataLoaderExtractor()  # text-layer only fallback
```

The hybrid server is a local FastAPI process wrapping Docling's OCR pipeline.
It starts in the background and health-checks on `/health`. First startup
downloads Docling OCR model weights if not cached (~500 MB).

---

## Error Handling

All extractors catch page-level exceptions internally and return an
`ExtractionResult` with `status = "ocr_runtime_error"` rather than raising.
Document-level failures (file not found, invalid format) raise `FileNotFoundError`.

```python
try:
    results = extractor.extract(pdf_path)
except FileNotFoundError as e:
    log.error(f"Input file missing: {e}")
    return

for page in results:
    if page.metadata.extra.get("status") == "ocr_runtime_error":
        log.warning(f"OCR failed on page {page.page_number}: "
                    f"{page.metadata.extra.get('error')}")
```

---

## Configuration Checklist

Before deploying:

- [ ] Java 11+ on PATH (if using OpenDataLoader)
- [ ] Tesseract binary installed (if using Tesseract extractor)
  - Windows default path `C:\Program Files\Tesseract-OCR\tesseract.exe` is
    auto-detected even if not on PATH
- [ ] First run of PaddleOCR/Docling will download model weights — ensure
  outbound internet access or pre-cache models in your image
- [ ] For GPU acceleration (PaddleOCR): install `paddlepaddle-gpu` instead of
  `paddlepaddle` and ensure CUDA drivers match
- [ ] Set `PYTHONPATH=src` if running scripts outside the installed package
