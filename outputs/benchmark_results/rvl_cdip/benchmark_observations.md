# RVL-CDIP Benchmark Report

## Dataset

- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\data\raw\rvl_cdip`
- Categories: 16
- Total documents: 16

## Extractor Robustness

| Extractor | Evaluated | OK | Failed | Success Rate | Mean Latency (ms) | Mean Char Count | Mean Word Count | Mean BBox Count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PyMuPDF | 16 | 16 | 0 | 1.0000 | 6.38 | 0.00 | 0.00 | 0.00 |
| OpenDataLoader | 16 | 16 | 0 | 1.0000 | 729.56 | 0.00 | 0.00 | 1.00 |
| PaddleOCR | 16 | 16 | 0 | 1.0000 | 7314.81 | 699.62 | 107.00 | 34.12 |
| Docling | 16 | 16 | 0 | 1.0000 | 35617.93 | 726.12 | 95.75 | 25.19 |

## Per-Category Success Rate

| Category | Documents | PyMuPDF | OpenDataLoader | PaddleOCR | Docling |
| --- | ---: | ---: | ---: | ---: | ---: |
| advertisement | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| budget | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| email | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| file_folder | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| form | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| handwritten | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| invoice | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| letter | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| memo | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| news_article | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| presentation | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| questionnaire | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| resume | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| scientific_publication | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| scientific_report | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| specification | 1 | 1.00 | 1.00 | 1.00 | 1.00 |

## Notes

- RVL-CDIP provides category labels, not text-level ground truth, so this benchmark reports extraction robustness (success rate, latency, output volume) rather than CER/WER-style accuracy.
- OpenDataLoader runs in its default Java-only mode here (no hybrid OCR backend); scanned/image-only pages may yield low word counts without indicating a failure.
