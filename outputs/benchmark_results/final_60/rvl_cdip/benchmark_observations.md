# Final RVL-CDIP Benchmark — Curated 20-Document Corpus

- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\data\final_benchmark\rvl_cdip`
- Categories: 10
- Total documents: 20
- Extractor order: PyMuPDF -> OpenDataLoader -> Tesseract -> PaddleOCR -> Docling
- Total runtime: 317.7s

## Extractor Robustness

| Extractor | Evaluated | OK | Failed | Success Rate | Mean Latency (ms) | Mean Char Count | Mean Word Count | Mean BBox Count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PyMuPDF | 20 | 20 | 0 | 1.0000 | 22.94 | 0.00 | 0.00 | 0.00 |
| OpenDataLoader | 20 | 20 | 0 | 1.0000 | 663.18 | 0.00 | 0.00 | 0.00 |
| Tesseract | 20 | 20 | 0 | 1.0000 | 552.94 | 1130.70 | 191.90 | 191.90 |
| PaddleOCR | 20 | 20 | 0 | 1.0000 | 3388.45 | 1135.90 | 173.45 | 45.60 |
| Docling | 20 | 20 | 0 | 1.0000 | 11147.67 | 1211.10 | 159.35 | 25.85 |

## Per-Category Success Rate

| Category | Documents | PyMuPDF | OpenDataLoader | Tesseract | PaddleOCR | Docling |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| advertisement | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| budget | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| email | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| form | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| handwritten | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| invoice | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| letter | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| memo | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| news_article | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| scientific_publication | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Notes

- RVL-CDIP provides category labels, not text-level ground truth, so this benchmark reports extraction robustness (success rate, latency, output volume, bbox/layout count) rather than CER/WER-style accuracy, identical to the existing RVL-CDIP benchmark methodology.
- OpenDataLoader runs in its default Java-only mode (no hybrid OCR backend); scanned/image-only pages may yield zero/low word counts without indicating a failure.
- PyMuPDF and OpenDataLoader require PDF input; each `.tif` document is wrapped into a single-page PDF via fitz before extraction.
