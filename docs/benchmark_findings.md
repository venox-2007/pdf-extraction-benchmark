# Benchmark Findings — Final Summary

This document summarises the key empirical findings from the evaluation. All items
listed as "next steps" in the original draft have been completed.

For full scored evidence, see [`comparison_matrix.md`](comparison_matrix.md).
For cost projections, see [`cost_analysis.md`](cost_analysis.md).
For integration patterns, see [`integration_guide.md`](integration_guide.md).

---

## What was found

**Native PDFs:** PyMuPDF (6 ms/doc) and OpenDataLoader (~730 ms/doc) extract text
directly from the PDF text layer. No OCR is needed; both achieve near-perfect
character fidelity on clean digital documents.

**Scanned PDFs:** Text extraction from image-based PDFs requires OCR. Three OCR
engines were evaluated and fully integrated:

| Tool | FUNSD CER ↓ | Mean latency (RVL-CDIP) |
|---|---|---|
| PaddleOCR | **0.443** (50 docs) | 8,735 ms |
| Tesseract | 0.485 (50 docs) | 1,265 ms |
| Docling | 0.500 (50 docs) | 32,295 ms |

Note: an earlier 5-document Docling sample showed CER 0.417, which suggested Docling was
the accuracy leader. The full 50-document run (CER 0.500) reversed this: Docling has the
worst character error rate among the three OCR tools. Its advantage is structured output
(tables, layout), not raw text accuracy.

**Routing matters:** PaddleOCR applied to a native 26-page PDF took 262 seconds.
Always classify documents first (`PdfTypeClassifier`) before routing to an OCR extractor.

**Tables:** Only Docling and OpenDataLoader produce structured table output
(row/column/cell). The other three tools return flat text with no table awareness.

**Handwriting:** None of the five evaluated tools handle handwritten text reliably.
Retain AWS Textract for handwriting use cases.

---

## Architecture decision

The final recommended pipeline is a two-path router:

1. `PdfTypeClassifier` classifies each document as `native`, `scanned`, or `hybrid`.
2. Native → **PyMuPDF** (speed) or **OpenDataLoader** (structured/tables).
3. Scanned → **PaddleOCR** (accuracy) or **Tesseract** (speed/triage).
4. Table-heavy documents → **Docling** (with a latency timeout guard).

This matches the architecture in the README and the integration guide.
