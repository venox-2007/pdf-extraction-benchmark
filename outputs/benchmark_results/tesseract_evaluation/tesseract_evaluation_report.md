# Tesseract Comprehensive Evaluation Report

Goal: verify whether Tesseract genuinely outperforms PaddleOCR and Docling,
looking beyond extraction speed and word counts to OCR accuracy (CER/WER) and
output quality.

## Datasets and methodology

- **FUNSD** (`datasets/FUNSD`, 50 scanned form images with ground-truth text):
  used for **accuracy** (CER, WER, token precision/recall/F1, token overlap
  accuracy) via `FunsdBenchmarkPipeline`.
  - Tesseract: full 50-document run (`outputs/benchmark_results/funsd_tesseract/`,
    via `scripts/run_tesseract_funsd_benchmark.py`).
  - PaddleOCR: existing full 50-document run (`outputs/benchmark_results/funsd/`).
  - Docling: existing 5-document run (`outputs/benchmark_results/docling/funsd_summary.json`).
    Docling's FUNSD run only covers the first 5 documents
    (`82092117`, `82200067_0069`, `82250337_0338`, `82251504`, `82252956_2958`),
    so a matching 5-document subset of Tesseract/PaddleOCR is reported alongside
    the full 50-document numbers for a fair three-way comparison.
- **RVL-CDIP** (`data/raw/rvl_cdip`, 16 categories x 2 documents = 32 native/scanned
  PDFs): used for **extraction metrics** (latency, character/word/bbox counts,
  success rate) via `RvlCdipBenchmarkPipeline`
  (`outputs/benchmark_results/rvl_cdip_tesseract_comparison/`, from the prior
  Tesseract integration run).
- **Qualitative review**: Tesseract, PaddleOCR, and Docling were run directly on
  one representative document from each of `invoice`, `form`, `resume`,
  `handwritten`, and `specification`
  (`outputs/benchmark_results/tesseract_evaluation/qualitative_samples.json`).

FUNSD has no Tesseract/Docling overlap beyond 5 documents, so FUNSD accuracy
numbers should be read as directional rather than a large-sample guarantee.
RVL-CDIP has no ground-truth transcriptions, so it can only support extraction
volume/latency/success-rate comparisons, not CER/WER.

---

## 1. Accuracy Analysis (FUNSD, vs. ground truth)

### Full FUNSD set (Tesseract and PaddleOCR, n=50)

| Extractor | CER | WER | Token Precision | Token Recall | Token F1 | Token Overlap Acc. | Success Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Tesseract | 0.4845 | 0.6884 | 0.6025 | 0.5058 | 0.5447 | 0.3881 | 100% (50/50) |
| PaddleOCR | 0.4430 | 0.6465 | 0.7096 | 0.5680 | 0.6284 | 0.4750 | 100% (50/50) |

### Matching 5-document subset (same docs as Docling's FUNSD run)

| Extractor | CER | WER | Token F1 | Success Rate |
| --- | ---: | ---: | ---: | ---: |
| Tesseract | 0.4568 | 0.6271 | 0.5483 | 100% (5/5) |
| PaddleOCR | 0.3436 | 0.5849 | 0.6195 | 100% (5/5) |
| Docling | 0.4166 | 0.7358 | 0.4398 | 100% (5/5) |

**Findings:**

- On FUNSD, **PaddleOCR has the lowest CER and WER and the highest token
  precision/recall/F1** of the three engines, both over the full 50-document
  set and the 5-document subset shared with Docling.
- **Tesseract has a higher CER and WER than PaddleOCR** (CER +0.041, WER +0.042
  over 50 docs; CER +0.113, WER +0.042 over the 5-doc subset). It recognizes
  more raw characters/words (see Section 2) but a larger share of them are
  wrong, consistent with FUNSD being scanned, low-resolution forms where
  PaddleOCR's detector+recognizer pipeline is more robust than Tesseract's
  default LSTM engine at default settings.
- Docling has the lowest CER on the 5-doc subset but the **worst WER and token
  F1** of the three — it tends to merge/duplicate text blocks (see Section 3),
  which lowers word-level accuracy even when individual characters are often
  correct.
- All three extractors achieved a **100% success rate** (no runtime failures)
  across both datasets.

---

## 2. Extraction Metrics (RVL-CDIP, n=32 documents, 16 categories)

| Extractor | Success Rate | Mean Latency | Mean Chars | Mean Words | Mean BBoxes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Tesseract | 100% (32/32) | 1,265.50 ms | 850.72 | 149.75 | 149.75 |
| PaddleOCR | 100% (32/32) | 8,735.14 ms | 776.22 | 117.72 | 40.25 |
| Docling | 100% (32/32) | 32,295.17 ms | 803.91 | 102.50 | 29.78 |

**Findings:**

- Tesseract is **~7x faster than PaddleOCR** and **~25x faster than Docling**
  on mean latency, with the lowest latency variance (stddev 587 ms vs 7,306 ms
  for PaddleOCR and 36,548 ms for Docling — Docling has extreme outliers, e.g.
  207.9s on `specification_01.pdf`).
- Tesseract extracts the **most characters and words on average** and produces
  **far more bounding boxes** (word-level boxes vs. line/region-level boxes for
  PaddleOCR/Docling) — this drives its higher word/char counts and is not, by
  itself, evidence of higher accuracy (see Section 1).
- All three extractors have 100% success rate (no runtime errors), but each had
  at least one document where it returned **zero extracted text** despite
  `status=ok`: Tesseract on `questionnaire_01` and `scientific_publication_02`,
  PaddleOCR on `handwritten_02`, Docling on `budget_02`. These are "no text
  extracted" cases, not failures, but they affect per-extractor reliability on
  specific document types.

---

## 3. Qualitative Review

One representative document per category (`*_01.pdf`), first ~600 characters
of extracted text shown for each extractor. Full samples are in
`outputs/benchmark_results/tesseract_evaluation/qualitative_samples.json`.

### Invoice (`invoice_01.pdf`)

- **Tesseract** (1,070 chars): Recovers most of the invoice header and line
  items (`TED BATES`, `PRODUCTION BILL`, `BILL NUMBER P-09-0962`, vendor names,
  PO numbers), with scattered OCR noise (`fei YOu`, `Se DaTe OVE SEPZL/T9`).
  Reading order is mostly column-by-column.
- **PaddleOCR** (984 chars): Similar content recovery, slightly more
  character-level corruption in words (`TED BATESYORX/VERTISING`,
  `BILL NUBER P-09-0942PAGE`) and merges adjacent fields without spaces.
- **Docling** (1,358 chars): Recovers the same content but **duplicates the
  entire header block** (the same "TEDBATESYORX/AVERTICING ... PRINT PRUDN"
  text appears twice in the first 600 characters) — a layout-merge artifact on
  this scanned invoice.
- **Verdict**: All three are noisy on this scanned 1979 production-bill scan.
  Tesseract and PaddleOCR have comparable usable content; Docling's duplication
  inflates its character count without adding information.

### Form (`form_01.pdf`)

- **Tesseract** (412 chars): Captures the form title, field labels (`Name:`,
  `Date:`, `Code:`, evaluation criteria), but also picks up handwritten/marginal
  noise (`KE RE __`, `af 19/4`, garbled fragments).
- **PaddleOCR** (309 chars): Cleanest output — form labels and structure are
  recovered with minimal noise, and it is the most faithful to the printed
  template text (no stray handwriting fragments).
- **Docling** (408 chars): Recovers the same labels as PaddleOCR but
  **duplicates the entire field-label block** (the "Which Has More/Better...
  Remarks" section appears twice).
- **Verdict**: PaddleOCR produces the cleanest, least redundant output for this
  printed form; Tesseract picks up extra (noisy) handwritten annotations;
  Docling duplicates content again.

### Resume (`resume_01.pdf`)

- **Tesseract** (1,237 chars), **PaddleOCR** (1,222 chars), **Docling**
  (1,140 chars): all three produce **highly readable, near-identical
  transcriptions** of this clean, native-quality biography text ("ERNEST
  PEPPLES, SENIOR VICE PRESIDENT & GENERAL COUNSEL ..."). Differences are minor
  character substitutions (`l957` vs `1957`, `BsW` vs `Bsw`) and spacing.
- **Verdict**: On clean, high-quality scans/native text, all three extractors
  are roughly equivalent in quality; Tesseract's word-level bounding boxes are
  a bonus here at a fraction of the latency.

### Handwritten (`handwritten_01.pdf`)

- **Tesseract** (1,477 chars): Produces the most output but it is **mostly
  garbled** (`hith. dy. F. Golly pow Wafurol Dictecaba`) — recognizable words
  are sparse and surrounded by nonsense tokens.
- **PaddleOCR** (824 chars): Also garbled but slightly more coherent fragments
  ("NEDITED TRANSLATION", "Reseanrh councl") with fewer total characters.
- **Docling** (525 chars): Least output and similarly low-quality
  (`Fry20,1:78`, `Bensirs,`).
- **Verdict**: **None of the three are usable for handwritten text** — this is
  expected, as none of them are handwriting-recognition models. Tesseract's
  higher character count here is **noise volume, not accuracy** — it directly
  explains why Tesseract's RVL-CDIP "mean chars" looks favorable while its
  FUNSD CER/WER is worse than PaddleOCR's.

### Specification (`specification_01.pdf`)

- **Tesseract** (1,135 chars), **PaddleOCR** (1,044 chars), **Docling**
  (1,112 chars): all three recover the tabular spec sheet (`SAMPLE
  SPECIFICATIONS`, `A-096-145`, `VICEROY 84`, `Blend`, `Flue-Cured`, `Burley`)
  with comparable fidelity. Numeric/code fields (`31961`, `827`, `3.3-44`) are
  recovered inconsistently by all three (e.g. `1.344` vs `126` vs `3.3-44` for
  the same field), reflecting genuine table-layout difficulty rather than one
  engine being clearly better.
- **Verdict**: Roughly equivalent quality across all three for this tabular
  document; Tesseract is dramatically faster (1.3s vs ~15-208s for Docling on
  this specific document).

---

## 4. Recommendation Review

**Should Tesseract replace PaddleOCR as the recommended OCR engine?**

**No — not as a full replacement. Recommend Tesseract as the default/first-choice
OCR engine for speed-sensitive and bulk workflows, while keeping PaddleOCR as the
higher-accuracy option, especially for low-quality scans and forms.**

Rationale, by the four required dimensions:

- **Accuracy**: PaddleOCR has measurably lower CER/WER and higher token F1 on
  FUNSD (the only dataset with ground truth), both over the full 50-document
  set and the 5-document subset shared with Docling. Tesseract's higher
  character/word counts on RVL-CDIP do **not** translate into higher accuracy —
  the handwritten-document qualitative sample shows Tesseract's extra output is
  largely noise.
- **Speed**: Tesseract is dramatically faster (~7x PaddleOCR, ~25x Docling on
  RVL-CDIP) with much lower latency variance. This is Tesseract's clearest
  advantage and makes it well-suited for large-batch or latency-sensitive
  pipelines.
- **Reliability**: All three extractors hit 100% success rate on both datasets
  (no runtime errors). Each has isolated "no text extracted" documents
  (Tesseract: 2/32, PaddleOCR: 1/32, Docling: 1/32 on RVL-CDIP), so reliability
  is comparable.
- **Output quality**: On clean documents (resume) all three are comparable. On
  noisy/scanned documents (invoice, form), PaddleOCR's output is cleaner and
  less redundant; Docling repeatedly duplicates content blocks. Tesseract's
  word-level bounding boxes are the most granular of the three, which is useful
  for layout-sensitive downstream tasks.

**Practical recommendation**:

- Keep Tesseract as an available extractor (already integrated) and surface it
  as a **fast default** for scanned/image documents where latency matters or
  for first-pass triage.
- Keep **PaddleOCR as the recommended choice when accuracy is the priority**
  (e.g. forms, low-quality scans, anything feeding downstream NLP/entity
  extraction where CER/WER matters).
- Treat **Docling's OCR path as situational** — useful for layout/markdown/table
  structure on native or moderate-quality documents, but its FUNSD WER and its
  tendency to duplicate text blocks on scanned forms/invoices make it a weaker
  choice for raw OCR accuracy, and its latency (up to 208s on one document) is
  a liability for batch workloads.
- This is a **directional finding based on a 50-document FUNSD accuracy sample
  (5 documents for the Docling comparison) and a 32-document RVL-CDIP extraction
  sample** — sufficient to rule out "Tesseract is strictly better," but a larger
  FUNSD run for Docling would sharpen the three-way accuracy comparison.

---

## Artifacts

- `outputs/benchmark_results/funsd_tesseract/` — Tesseract FUNSD CER/WER/token
  metrics (50 docs)
- `outputs/benchmark_results/funsd/` — PaddleOCR FUNSD CER/WER/token metrics
  (50 docs, pre-existing)
- `outputs/benchmark_results/docling/funsd_summary.json` — Docling FUNSD
  CER/WER/token metrics (5 docs, pre-existing)
- `outputs/benchmark_results/rvl_cdip_tesseract_comparison/` — RVL-CDIP
  extraction metrics for Tesseract/PaddleOCR/Docling (32 docs, pre-existing)
- `outputs/benchmark_results/tesseract_evaluation/qualitative_samples.json` —
  raw extracted-text samples used in Section 3
