# Rejected / Deferred Tools

Three tools from the original evaluation list were not fully implemented.
This document records the investigation, the reason for rejection or deferral,
and the conclusion for each.

---

## 1. Marker

**Original brief:** "PDF to markdown with table support"
**Repository:** https://github.com/VikParuchuri/marker
**Status:** Stub only (`src/pdf_extraction_benchmark/extractors/marker/extractor.py`)

### Investigation

Marker is a PDF-to-Markdown converter that uses the Surya OCR engine (also by
VikParuchuri) plus layout detection models. It produces high-quality Markdown
output with heading detection, table rendering, and code block identification.

### Why rejected

1. **Dependency on Surya OCR.** Marker relies on Surya for OCR and layout
   detection. Surya requires PyTorch and CUDA-capable hardware for acceptable
   performance. CPU-only inference on Surya is 10–20× slower than Docling's
   ONNX-based pipeline. During evaluation, Surya could not be made to run
   reliably in this environment (see Surya section below).

2. **Coverage by Docling.** Docling (IBM) provides the same core value
   proposition — layout-aware extraction with structured Markdown output and
   table detection — without Surya as a dependency. Docling uses ONNX runtime
   (no GPU required), is installable from pip, and has already been benchmarked.
   Adding Marker would produce a highly correlated result to Docling without
   meaningfully expanding the comparison.

3. **Installation complexity.** `pip install marker-pdf` pulls in torch,
   torchvision, and ~2 GB of GPU model weights. On the evaluation machine
   (Windows, no discrete GPU), model inference was impractically slow.

### Conclusion

**Rejected.** Docling covers the same use case with lower installation complexity,
no GPU requirement, and comparable (or better, in the 5-doc FUNSD benchmark)
accuracy. If a GPU is available in the production environment, Marker is worth
re-evaluating as it may outperform Docling on markdown fidelity for complex
multi-column documents.

---

## 2. Surya OCR

**Original brief:** "Open-source OCR with table/layout detection"
**Repository:** https://github.com/VikParuchuri/surya
**Status:** Not implemented

### Investigation

Surya is a document OCR model suite that includes:
- Line-level text detection and recognition
- Layout analysis (reading order, regions)
- Table detection and recognition

It is the OCR backbone for Marker.

### Why rejected

1. **GPU requirement.** Surya's recognition model is a transformer-based
   sequence-to-sequence model that requires a GPU for practical use. The project
   evaluation machine has no discrete GPU. CPU inference on a 26-page test
   document took over 40 minutes — not viable for benchmarking.

2. **Installation failures.** `pip install surya-ocr` on Python 3.11 / Windows
   produced dependency conflicts with the existing environment (torch version
   clash with paddlepaddle's bundled torch) that could not be resolved without
   creating an isolated environment.

3. **Evaluated tools already cover the capability space.** Surya's OCR
   capability overlaps with PaddleOCR; its layout detection overlaps with
   Docling. Both of those alternatives were successfully installed and
   benchmarked.

### Conclusion

**Rejected for this evaluation.** Not usable without GPU. If a GPU instance is
available in production, Surya is worth evaluating as a potential unified
alternative to the PaddleOCR (OCR) + Docling (layout) combination.

---

## 3. Unstructured.io

**Original brief:** "Document parsing with layout detection"
**Repository:** https://github.com/Unstructured-IO/unstructured
**Package:** `unstructured[pdf]`
**Status:** Stub only (`src/pdf_extraction_benchmark/extractors/unstructured/extractor.py`)

### Investigation

A pre-implementation assessment was conducted (see chat history, June 2026).
Key findings:

- **API:** `partition_pdf()` returns a typed element list (Title, NarrativeText,
  Table, etc.) with optional bounding boxes and HTML table output.
- **Strategies:** `fast` (pdfminer.six, no OCR), `hi_res` (ONNX layout model +
  Tesseract), `ocr_only` (Tesseract only).
- **Current version:** 0.23.1 (June 2026).
- **Company direction:** Unstructured has explicitly stated the OSS library is a
  prototyping tool; production-quality features are being moved to the paid
  cloud API.

### Why rejected

**Hard dependency conflict — cannot be installed in the current environment.**

`unstructured >= 0.17` requires `numpy >= 2`. The project pins `numpy < 2`
because `paddlepaddle == 2.6.2` (PaddleOCR's runtime) enforces this constraint
at install time. The two packages cannot coexist in the same virtual environment:

```
pip install "unstructured[pdf]"
→ ERROR: Cannot install unstructured 0.23.1 because these package versions
  have conflicting dependencies:
    paddlepaddle 2.6.2 requires numpy<2
    unstructured 0.23.1 requires numpy>=2
```

The only resolution paths are:
1. Upgrade PaddleOCR to a version that supports numpy 2.x — no such version
   of `paddleocr == 2.7.3 / paddlepaddle == 2.6.2` exists.
2. Run Unstructured in an isolated subprocess — defeats the shared benchmark
   infrastructure and adds significant complexity.

**Even without the conflict, the benchmark value is limited:**
- `fast` strategy: equivalent to PyMuPDF (pdfminer.six text extraction, no
  bounding boxes, no tables). Already covered.
- `hi_res` strategy: adds ONNX layout detection and Tesseract OCR. This is a
  subset of what Docling already provides with a cleaner Python object model.
- Unique value (semantic element typing: Title vs NarrativeText vs Table) is
  not measured by the existing benchmark infrastructure (CER/WER, latency,
  char/word/bbox counts).
- The OSS library lags behind the cloud API on features; benchmarking the OSS
  version may misrepresent what a production integration would deliver.

### Conclusion

**Rejected due to unresolvable environment conflict.** The assessment is fully
documented. If PaddleOCR is replaced with a numpy-2-compatible OCR library in
the future, Unstructured.io `hi_res` strategy is the most straightforward next
tool to evaluate for the table-extraction use case alongside or instead of
Docling.

---

## 4. AWS Textract (Baseline)

**Original brief:** "Cloud API — Baseline (current solution)"
**Status:** Not implemented

### Why skipped

Explicitly excluded from evaluation per project stakeholder instruction. The
project goal is to identify open-source self-hosted alternatives that reduce
cost and latency versus Textract — not to re-benchmark Textract itself. Textract
pricing is used as the reference baseline in [`cost_analysis.md`](cost_analysis.md).

---

## Summary

| Tool | Decision | Primary Reason |
| --- | --- | --- |
| Marker | Rejected | Depends on Surya (GPU required); fully covered by Docling |
| Surya OCR | Rejected | GPU required; CPU inference impractical (~40 min/doc) |
| Unstructured.io | Rejected | `numpy<2` / `numpy>=2` conflict with PaddleOCR; OSS limitations |
| AWS Textract | Skipped | Excluded per stakeholder instruction; used as cost baseline only |
