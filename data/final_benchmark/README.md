# Final Benchmark Corpus

## Purpose

A balanced 60-document evaluation corpus for end-to-end assessment of all five
extractor adapters (PyMuPDF, OpenDataLoader, PaddleOCR, Tesseract, Docling)
across three distinct document domains. This corpus is the canonical reference
set for the internship deliverable.

The corpus is **manifest-driven**: document files are not copied into this
directory (except the SROIE receipts which are already here). The file
[`manifest.csv`](manifest.csv) is the single source of truth for paths and
ground-truth locations.

## Source Datasets

| Sub-corpus | Source | Document Type | Count |
|---|---|---|---|
| `funsd/` | FUNSD (Form Understanding in Noisy Scanned Documents) | Scanned form images (PNG) | 20 |
| `rvl_cdip/` | RVL-CDIP (16-category document classification set) | Scanned document images (TIF) | 20 |
| `sroie/` | SROIE 2019 (ICDAR receipt OCR challenge, local test subset) | Scanned receipt images (JPG) | 20 |

**Total: 60 documents**

## manifest.csv

Columns: `dataset`, `document_id`, `category`, `source_path`, `ground_truth_path`

- **FUNSD**: `source_path` → PNG image; `ground_truth_path` → JSON annotation
  (word-level bounding boxes + text labels)
- **RVL-CDIP**: `source_path` → TIF image; `ground_truth_path` → *(empty — no
  OCR ground truth available for RVL-CDIP; used for latency/throughput
  benchmarking only)*
- **SROIE**: `source_path` → JPG receipt image; `ground_truth_path` → `.txt`
  box file (word bounding boxes, one word per line)

## Document Counts by Dataset and Category

### FUNSD (20 / 50 available)

| Category | Count |
|---|---|
| form | 20 |

### RVL-CDIP (20 / 160 available — 10 categories × 2 docs each)

| Category | Count | Layout type |
|---|---|---|
| advertisement | 2 | multi-column, mixed graphics |
| budget | 2 | tabular / numeric |
| email | 2 | prose, header-body structure |
| form | 2 | structured form fields |
| handwritten | 2 | handwritten script |
| invoice | 2 | line-item table |
| letter | 2 | flowing prose |
| memo | 2 | short-form prose |
| news_article | 2 | multi-column newspaper |
| scientific_publication | 2 | two-column academic |

### SROIE (20 / 146 available)

| Category | Count |
|---|---|
| receipt | 20 |

## Selection Methodology

### FUNSD
Stride-2 sampling over all 50 sorted filenames (indices 0, 2, 4 … 38). This
gives a systematic, unbiased 40 % sample with no manual curation.

### RVL-CDIP
10 of the 16 available categories selected to cover every major layout
archetype (tabular, handwritten, multi-column, structured form, prose). Two
documents per category — indices 01 and 06 — to sample the start and mid-point
of each 10-document category run without bias.

### SROIE
146 receipt images are present locally (the available test subset). Stride-7
sampling (`⌊146/20⌋ = 7`) over the sorted filename list yields exactly 20
receipts spread uniformly across the alphabet of receipt IDs.

## Directory Structure

```
data/final_benchmark/
├── manifest.csv           ← canonical 60-row corpus manifest
├── README.md              ← this file
├── funsd/                 ← placeholder (files referenced via manifest source_path)
├── rvl_cdip/              ← placeholder (files referenced via manifest source_path)
└── sroie/
    ├── img/               ← 146 JPEG receipt images (20 selected in manifest)
    ├── box/               ← 146 word bounding-box .txt files
    └── entities/          ← key-value labels (not used in OCR benchmarking)
```

See [`docs/final_benchmark_plan.md`](../../docs/final_benchmark_plan.md) for
the complete selection rationale and exact document IDs.
