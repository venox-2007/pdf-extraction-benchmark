# Final Benchmark Corpus

## Purpose

A balanced 60-document evaluation corpus for end-to-end assessment of all five
extractor adapters (PyMuPDF, OpenDataLoader, PaddleOCR, Tesseract, Docling)
across three distinct document domains. This corpus is the canonical reference
set for the internship deliverable.

## Source Datasets

| Sub-corpus | Source | Document Type | Count |
|---|---|---|---|
| `funsd/` | FUNSD (Form Understanding in Noisy Scanned Documents) | Scanned form images | 20 |
| `rvl_cdip/` | RVL-CDIP (16-category document classification set) | Scanned document images/TIFs | 20 |
| `sroie/` | SROIE 2019 (ICDAR receipt OCR challenge, test split) | Scanned receipt images | 20 |

## Document Counts

- FUNSD: 20 of 50 available test documents
- RVL-CDIP: 20 of 160 available documents (16 categories × 10 each)
- SROIE: 20 of 347 available test receipts
- **Total: 60 documents**

## Selection Methodology

### FUNSD (20 / 50)
Every other document in alphabetical order (indices 0, 2, 4, … 38 of the 50
sorted filenames). This systematic stride-2 sample preserves the natural
diversity of the dataset without cherry-picking.

### RVL-CDIP (20 / 160)
Two documents selected from each of the 10 most structurally diverse
categories, choosing document index 01 and 06 (first and mid-point of the
10-document run) per category. The 10 selected categories span the full range
of layout complexity: advertisement, budget, email, form, handwritten, invoice,
letter, memo, news_article, and scientific_publication. The remaining 6
categories (file_folder, presentation, questionnaire, resume, scientific_report,
specification) are excluded to keep the total at 20 while still covering
prose, tabular, handwritten, and structured-form layouts.

### SROIE (20 / 347)
20 receipts sampled at a uniform stride of ~17 (every 17th file alphabetically)
from the ICDAR 2019 SROIE test split. The SROIE test set has no category
labels, so stride sampling is the fairest way to ensure geographic and vendor
diversity across the 347 receipts.

## Directory Structure

```
data/final_benchmark/
├── README.md          ← this file
├── funsd/             ← 20 FUNSD form images + JSON annotations (to be populated)
├── rvl_cdip/          ← 20 RVL-CDIP document images/TIFs (to be populated)
└── sroie/             ← 20 SROIE receipt images (to be populated)
```

Files are **not yet copied** into these directories. See
[`docs/final_benchmark_plan.md`](../../docs/final_benchmark_plan.md) for the
exact document IDs and copy commands.
