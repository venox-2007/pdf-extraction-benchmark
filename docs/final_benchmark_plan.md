# Final Benchmark Selection Plan

Exact document IDs, selection rationale, and validation notes for the
60-document corpus at `data/final_benchmark/`. The manifest at
`data/final_benchmark/manifest.csv` is generated from these selections and is
the authoritative runtime reference.

---

## 1. FUNSD (20 documents)

**Source:** `datasets/FUNSD/images/` + `datasets/FUNSD/annotations/`
**Available:** 50 test documents
**Selected:** 20
**Selection method:** Stride-2 over sorted filenames — every other file
(indices 0, 2, 4 … 38 of the 50-item sorted list). Gives a systematic 40 %
sample with no manual curation bias.

### Selected document IDs

| # | Document ID | Image path | Annotation path |
|---|---|---|---|
| 1 | 82092117 | datasets/FUNSD/images/82092117.png | datasets/FUNSD/annotations/82092117.json |
| 2 | 82250337_0338 | datasets/FUNSD/images/82250337_0338.png | datasets/FUNSD/annotations/82250337_0338.json |
| 3 | 82252956_2958 | datasets/FUNSD/images/82252956_2958.png | datasets/FUNSD/annotations/82252956_2958.json |
| 4 | 82253245_3247 | datasets/FUNSD/images/82253245_3247.png | datasets/FUNSD/annotations/82253245_3247.json |
| 5 | 82254765 | datasets/FUNSD/images/82254765.png | datasets/FUNSD/annotations/82254765.json |
| 6 | 82504862 | datasets/FUNSD/images/82504862.png | datasets/FUNSD/annotations/82504862.json |
| 7 | 82573104 | datasets/FUNSD/images/82573104.png | datasets/FUNSD/annotations/82573104.json |
| 8 | 83443897 | datasets/FUNSD/images/83443897.png | datasets/FUNSD/annotations/83443897.json |
| 9 | 83573282 | datasets/FUNSD/images/83573282.png | datasets/FUNSD/annotations/83573282.json |
| 10 | 83624198 | datasets/FUNSD/images/83624198.png | datasets/FUNSD/annotations/83624198.json |
| 11 | 83641919_1921 | datasets/FUNSD/images/83641919_1921.png | datasets/FUNSD/annotations/83641919_1921.json |
| 12 | 83823750 | datasets/FUNSD/images/83823750.png | datasets/FUNSD/annotations/83823750.json |
| 13 | 85201976 | datasets/FUNSD/images/85201976.png | datasets/FUNSD/annotations/85201976.json |
| 14 | 85540866 | datasets/FUNSD/images/85540866.png | datasets/FUNSD/annotations/85540866.json |
| 15 | 86075409_5410 | datasets/FUNSD/images/86075409_5410.png | datasets/FUNSD/annotations/86075409_5410.json |
| 16 | 86220490 | datasets/FUNSD/images/86220490.png | datasets/FUNSD/annotations/86220490.json |
| 17 | 86236474_6476 | datasets/FUNSD/images/86236474_6476.png | datasets/FUNSD/annotations/86236474_6476.json |
| 18 | 86263525 | datasets/FUNSD/images/86263525.png | datasets/FUNSD/annotations/86263525.json |
| 19 | 87086073 | datasets/FUNSD/images/87086073.png | datasets/FUNSD/annotations/87086073.json |
| 20 | 87125460 | datasets/FUNSD/images/87125460.png | datasets/FUNSD/annotations/87125460.json |

### Ground truth format
FUNSD JSON annotations contain a list of form blocks, each with a `label`
(header/question/answer/other), bounding box, and `words` list (word text +
box). CER/WER is computed by concatenating all word texts per document.

---

## 2. RVL-CDIP (20 documents)

**Source:** `data/raw/rvl_cdip/<category>/originals/`
**Available:** 16 categories × 10 documents = 160 total
**Selected:** 20 (10 categories × 2 documents each)
**Selection method:** Choose 10 categories covering every major layout
archetype; within each category select document index 01 (first) and 06
(mid-range) for intra-category diversity.

### Selected categories and document IDs

| # | Category | Document ID | Source path | Layout archetype |
|---|---|---|---|---|
| 1 | advertisement | advertisement_01 | data/raw/rvl_cdip/advertisement/originals/advertisement_01.tif | multi-column, mixed graphics |
| 2 | advertisement | advertisement_06 | data/raw/rvl_cdip/advertisement/originals/advertisement_06.tif | multi-column, mixed graphics |
| 3 | budget | budget_01 | data/raw/rvl_cdip/budget/originals/budget_01.tif | tabular / numeric |
| 4 | budget | budget_06 | data/raw/rvl_cdip/budget/originals/budget_06.tif | tabular / numeric |
| 5 | email | email_01 | data/raw/rvl_cdip/email/originals/email_01.tif | prose, header-body |
| 6 | email | email_06 | data/raw/rvl_cdip/email/originals/email_06.tif | prose, header-body |
| 7 | form | form_01 | data/raw/rvl_cdip/form/originals/form_01.tif | structured form fields |
| 8 | form | form_06 | data/raw/rvl_cdip/form/originals/form_06.tif | structured form fields |
| 9 | handwritten | handwritten_01 | data/raw/rvl_cdip/handwritten/originals/handwritten_01.tif | handwritten script |
| 10 | handwritten | handwritten_06 | data/raw/rvl_cdip/handwritten/originals/handwritten_06.tif | handwritten script |
| 11 | invoice | invoice_01 | data/raw/rvl_cdip/invoice/originals/invoice_01.tif | line-item table |
| 12 | invoice | invoice_06 | data/raw/rvl_cdip/invoice/originals/invoice_06.tif | line-item table |
| 13 | letter | letter_01 | data/raw/rvl_cdip/letter/originals/letter_01.tif | flowing prose |
| 14 | letter | letter_06 | data/raw/rvl_cdip/letter/originals/letter_06.tif | flowing prose |
| 15 | memo | memo_01 | data/raw/rvl_cdip/memo/originals/memo_01.tif | short-form prose |
| 16 | memo | memo_06 | data/raw/rvl_cdip/memo/originals/memo_06.tif | short-form prose |
| 17 | news_article | news_article_01 | data/raw/rvl_cdip/news_article/originals/news_article_01.tif | multi-column newspaper |
| 18 | news_article | news_article_06 | data/raw/rvl_cdip/news_article/originals/news_article_06.tif | multi-column newspaper |
| 19 | scientific_publication | scientific_publication_01 | data/raw/rvl_cdip/scientific_publication/originals/scientific_publication_01.tif | two-column academic |
| 20 | scientific_publication | scientific_publication_06 | data/raw/rvl_cdip/scientific_publication/originals/scientific_publication_06.tif | two-column academic |

**Excluded categories (6):** file_folder, presentation, questionnaire, resume,
scientific_report, specification — omitted to keep total at 20; adequately
represented by structurally similar selected categories.

### Ground truth note
No word-level OCR ground truth exists for RVL-CDIP. These documents are used
for latency, throughput, and qualitative layout benchmarking only.
`ground_truth_path` is empty in the manifest for all RVL-CDIP rows.

---

## 3. SROIE (20 documents)

**Source:** `data/final_benchmark/sroie/img/` + `data/final_benchmark/sroie/box/`
**Available:** 146 receipt images in the local test subset
**Selected:** 20
**Selection method:** Stride-7 (`⌊146/20⌋ = 7`) over sorted filenames,
taking the first 20 results. Produces a uniform sample across the 146 receipts
without alphabetic bias.

### Selected document IDs

| # | Document ID | Image path | Box path |
|---|---|---|---|
| 1 | X00016469620 | data/final_benchmark/sroie/img/X00016469620.jpg | data/final_benchmark/sroie/box/X00016469620.txt |
| 2 | X51005441402 | data/final_benchmark/sroie/img/X51005441402.jpg | data/final_benchmark/sroie/box/X51005441402.txt |
| 3 | X51005447848 | data/final_benchmark/sroie/img/X51005447848.jpg | data/final_benchmark/sroie/box/X51005447848.txt |
| 4 | X51005621482 | data/final_benchmark/sroie/img/X51005621482.jpg | data/final_benchmark/sroie/box/X51005621482.txt |
| 5 | X51005677331 | data/final_benchmark/sroie/img/X51005677331.jpg | data/final_benchmark/sroie/box/X51005677331.txt |
| 6 | X51005711445 | data/final_benchmark/sroie/img/X51005711445.jpg | data/final_benchmark/sroie/box/X51005711445.txt |
| 7 | X51005719895 | data/final_benchmark/sroie/img/X51005719895.jpg | data/final_benchmark/sroie/box/X51005719895.txt |
| 8 | X51005757290 | data/final_benchmark/sroie/img/X51005757290.jpg | data/final_benchmark/sroie/box/X51005757290.txt |
| 9 | X51005806719 | data/final_benchmark/sroie/img/X51005806719.jpg | data/final_benchmark/sroie/box/X51005806719.txt |
| 10 | X51006328345 | data/final_benchmark/sroie/img/X51006328345.jpg | data/final_benchmark/sroie/box/X51006328345.txt |
| 11 | X51006387971 | data/final_benchmark/sroie/img/X51006387971.jpg | data/final_benchmark/sroie/box/X51006387971.txt |
| 12 | X51006393376 | data/final_benchmark/sroie/img/X51006393376.jpg | data/final_benchmark/sroie/box/X51006393376.txt |
| 13 | X51006414633 | data/final_benchmark/sroie/img/X51006414633.jpg | data/final_benchmark/sroie/box/X51006414633.txt |
| 14 | X51006556827 | data/final_benchmark/sroie/img/X51006556827.jpg | data/final_benchmark/sroie/box/X51006556827.txt |
| 15 | X51006619509 | data/final_benchmark/sroie/img/X51006619509.jpg | data/final_benchmark/sroie/box/X51006619509.txt |
| 16 | X51006620192 | data/final_benchmark/sroie/img/X51006620192.jpg | data/final_benchmark/sroie/box/X51006620192.txt |
| 17 | X51007103692 | data/final_benchmark/sroie/img/X51007103692.jpg | data/final_benchmark/sroie/box/X51007103692.txt |
| 18 | X51007339112 | data/final_benchmark/sroie/img/X51007339112.jpg | data/final_benchmark/sroie/box/X51007339112.txt |
| 19 | X51007339650 | data/final_benchmark/sroie/img/X51007339650.jpg | data/final_benchmark/sroie/box/X51007339650.txt |
| 20 | X51008042787 | data/final_benchmark/sroie/img/X51008042787.jpg | data/final_benchmark/sroie/box/X51008042787.txt |

### Ground truth format
SROIE `.txt` box files contain one word per line in the format:
`x1,y1,x2,y2,x3,y3,x4,y4,word_text`
(quad bounding box + word). CER/WER is computed by reading word_text fields
in order per document.

Note: `entities/` files contain key-value labels (company, date, address,
total) and are excluded from OCR benchmarking.

---

## Validation

All 60 manifest entries have been validated on disk:

```
✓ 20 FUNSD image + annotation pairs present
✓ 20 RVL-CDIP TIF files present
✓ 20 SROIE image + box file pairs present
```

Re-validate at any time:

```bash
python -c "
import csv, os, sys
errors = []
with open('data/final_benchmark/manifest.csv') as f:
    for row in csv.DictReader(f):
        if not os.path.exists(row['source_path']):
            errors.append('MISSING: ' + row['source_path'])
        if row['ground_truth_path'] and not os.path.exists(row['ground_truth_path']):
            errors.append('MISSING GT: ' + row['ground_truth_path'])
print('Errors:', len(errors))
for e in errors: print(' ', e)
"
```

---

## Summary

| Sub-corpus | Source dir | Count | Selection method |
|---|---|---|---|
| funsd | `datasets/FUNSD/` | 20 | Stride-2 from 50 sorted files |
| rvl_cdip | `data/raw/rvl_cdip/` | 20 | 10 categories × 2 docs (indices 01, 06) |
| sroie | `data/final_benchmark/sroie/` | 20 | Stride-7 from 146 sorted files |
| **Total** | | **60** | |
