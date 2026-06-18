# Final Benchmark Selection Plan

This document records the exact document IDs, rationale, and copy commands for
building the 60-document final benchmark corpus at `data/final_benchmark/`.

---

## 1. FUNSD (20 documents)

**Source:** `datasets/FUNSD/images/` + `datasets/FUNSD/annotations/`  
**Available:** 50 test documents  
**Selection method:** Stride-2 — every other file in sorted order (indices 0, 2, 4 … 38)

### Selected document IDs (image basename, no extension)

| # | Document ID |
|---|---|
| 1 | 82092117 |
| 2 | 82250337_0338 |
| 3 | 82252956_2958 |
| 4 | 82253245_3247 |
| 5 | 82254765 |
| 6 | 82504862 |
| 7 | 82573104 |
| 8 | 83443897 |
| 9 | 83573282 |
| 10 | 83624198 |
| 11 | 83641919_1921 |
| 12 | 83823750 |
| 13 | 85201976 |
| 14 | 85540866 |
| 15 | 86075409_5410 |
| 16 | 86220490 |
| 17 | 86236474_6476 |
| 18 | 86263525 |
| 19 | 87086073 |
| 20 | 87125460 |

### Rationale
FUNSD has no sub-categories; all 50 documents are scanned noisy forms with
varying layouts. Stride sampling gives unbiased coverage across the full
dataset without manual curation. Both the `.png` image and the matching `.json`
annotation file should be copied for each ID (needed for CER/WER evaluation).

### Copy commands (run when ready to populate)
```bash
# Run from repo root
IDS=(82092117 82250337_0338 82252956_2958 82253245_3247 82254765
     82504862 82573104 83443897 83573282 83624198
     83641919_1921 83823750 85201976 85540866 86075409_5410
     86220490 86236474_6476 86263525 87086073 87125460)

for id in "${IDS[@]}"; do
    cp "datasets/FUNSD/images/${id}.png"        "data/final_benchmark/funsd/"
    cp "datasets/FUNSD/annotations/${id}.json"  "data/final_benchmark/funsd/"
done
```

---

## 2. RVL-CDIP (20 documents)

**Source:** `data/raw/rvl_cdip/<category>/originals/`  
**Available:** 16 categories × 10 documents = 160 total  
**Selection method:** 10 categories selected for layout diversity; 2 documents
per category (document index 01 and 06, i.e. the first and roughly the
mid-point of each category's 10-document run).

### Selected categories and document IDs

| Category | Doc 1 | Doc 2 | Layout type |
|---|---|---|---|
| advertisement | advertisement_01.tif | advertisement_06.tif | multi-column, mixed graphics |
| budget | budget_01.tif | budget_06.tif | tabular / numeric |
| email | email_01.tif | email_06.tif | prose, header-body structure |
| form | form_01.tif | form_06.tif | structured form fields |
| handwritten | handwritten_01.tif | handwritten_06.tif | handwritten script |
| invoice | invoice_01.tif | invoice_06.tif | line-item table |
| letter | letter_01.tif | letter_06.tif | flowing prose |
| memo | memo_01.tif | memo_06.tif | short-form prose |
| news_article | news_article_01.tif | news_article_06.tif | multi-column newspaper |
| scientific_publication | scientific_publication_01.tif | scientific_publication_06.tif | two-column academic |

**Excluded categories (6):** file_folder, presentation, questionnaire, resume,
scientific_report, specification — omitted solely to cap the total at 20; they
are adequately represented by the structurally similar selected categories.

### Rationale
The 10 selected categories cover every major layout archetype present in the
benchmark (tabular, handwritten, multi-column, structured form, prose). Using
both the first and the mid-range document per category avoids bias toward any
single document while keeping the per-category sample small.

### Copy commands (run when ready to populate)
```bash
CATS=(advertisement budget email form handwritten invoice letter memo news_article scientific_publication)

for cat in "${CATS[@]}"; do
    cp "data/raw/rvl_cdip/${cat}/originals/${cat}_01.tif" "data/final_benchmark/rvl_cdip/"
    cp "data/raw/rvl_cdip/${cat}/originals/${cat}_06.tif" "data/final_benchmark/rvl_cdip/"
done
```

---

## 3. SROIE (20 documents)

**Source:** ICDAR 2019 SROIE test split (not yet downloaded)  
**Available:** 347 receipt images in the test set  
**Selection method:** Uniform stride of 17 (⌊347/20⌋) over the sorted
filename list — yields 20 receipts evenly spread across the 347-file alphabet.

### Placeholder document IDs
SROIE files follow the pattern `XXXXXX.jpg` (6-digit receipt ID). The exact
IDs depend on the downloaded test-set listing. Once downloaded to
`datasets/SROIE/test/img/`, run the following to derive the list:

```python
import os
files = sorted(os.listdir("datasets/SROIE/test/img"))
selected = files[::17][:20]
print(selected)
```

### Download instructions
The SROIE 2019 test dataset is publicly available from the ICDAR 2019
challenge page and several Kaggle mirrors. Suggested download:

```bash
# Kaggle (requires kaggle CLI + account)
kaggle datasets download -d urbikn/sroie-datasetv2 -p datasets/SROIE --unzip
# Expected structure after unzip:
#   datasets/SROIE/test/img/     ← 347 receipt JPEGs
#   datasets/SROIE/test/box/     ← word bounding boxes
#   datasets/SROIE/test/entities/ ← key-value entity labels
```

### Copy commands (run after download)
```bash
python -c "
import os, shutil
files = sorted(os.listdir('datasets/SROIE/test/img'))
selected = files[::17][:20]
for f in selected:
    shutil.copy(f'datasets/SROIE/test/img/{f}', 'data/final_benchmark/sroie/')
print('Copied:', selected)
"
```

---

## Summary

| Sub-corpus | Source dir | Count | Selection |
|---|---|---|---|
| funsd | `datasets/FUNSD/` | 20 | Stride-2 from 50 sorted files |
| rvl_cdip | `data/raw/rvl_cdip/` | 20 | 10 categories × 2 docs (01, 06) |
| sroie | `datasets/SROIE/` (pending) | 20 | Stride-17 from 347 sorted files |
| **Total** | | **60** | |

Next step: download SROIE, then run the copy commands above to populate
`data/final_benchmark/`. After populating, run the benchmark pipeline against
this corpus for the final deliverable report.
