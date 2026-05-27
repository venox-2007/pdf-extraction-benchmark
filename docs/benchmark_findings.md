# Benchmark Findings (Initial)

## Scope

This document records early practical observations from the extraction demo while validating native and scanned PDF behavior.

## Key Findings

1. OpenDataLoader performs reasonably well on native PDFs.
2. For scanned PDFs, OCR text extraction is currently limited in this setup.
3. In scanned cases, output may contain embedded image references in Markdown with little or no extracted text.
4. Page count alignment between generated outputs and expected document pages is under active investigation.

## Product Implications

1. The app now classifies PDFs as `native`, `scanned`, or `mixed` before extraction.
2. The UI surfaces extractor recommendations based on detected PDF type.
3. When scanned PDFs are routed through OpenDataLoader and text is missing, the app marks the result as a limitation and shows a clear warning.

## Next Steps (Lightweight)

1. Add OCR-first extractor adapters (PaddleOCR, Surya) for scanned workflows.
2. Add simple side-by-side quality notes in the UI for extraction comparisons.
3. Track page-level extraction consistency as part of benchmark metadata.
