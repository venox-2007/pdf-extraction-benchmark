# RVL-CDIP Benchmark Report

## Dataset

- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\data\raw\rvl_cdip`
- Categories: 16
- Total documents: 32

## Extractor Robustness

| Extractor | Evaluated | OK | Failed | Success Rate | Mean Latency (ms) | Mean Char Count | Mean Word Count | Mean BBox Count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Tesseract | 32 | 32 | 0 | 1.0000 | 1265.50 | 850.72 | 149.75 | 149.75 |
| PaddleOCR | 32 | 32 | 0 | 1.0000 | 8735.14 | 776.22 | 117.72 | 40.25 |
| Docling | 32 | 32 | 0 | 1.0000 | 32295.17 | 803.91 | 102.50 | 29.78 |

## Per-Category Success Rate

| Category | Documents | Tesseract | PaddleOCR | Docling |
| --- | ---: | ---: | ---: | ---: |
| advertisement | 2 | 1.00 | 1.00 | 1.00 |
| budget | 2 | 1.00 | 1.00 | 1.00 |
| email | 2 | 1.00 | 1.00 | 1.00 |
| file_folder | 2 | 1.00 | 1.00 | 1.00 |
| form | 2 | 1.00 | 1.00 | 1.00 |
| handwritten | 2 | 1.00 | 1.00 | 1.00 |
| invoice | 2 | 1.00 | 1.00 | 1.00 |
| letter | 2 | 1.00 | 1.00 | 1.00 |
| memo | 2 | 1.00 | 1.00 | 1.00 |
| news_article | 2 | 1.00 | 1.00 | 1.00 |
| presentation | 2 | 1.00 | 1.00 | 1.00 |
| questionnaire | 2 | 1.00 | 1.00 | 1.00 |
| resume | 2 | 1.00 | 1.00 | 1.00 |
| scientific_publication | 2 | 1.00 | 1.00 | 1.00 |
| scientific_report | 2 | 1.00 | 1.00 | 1.00 |
| specification | 2 | 1.00 | 1.00 | 1.00 |

## Notes

- RVL-CDIP provides category labels, not text-level ground truth, so this benchmark reports extraction robustness (success rate, latency, output volume) rather than CER/WER-style accuracy.
- OpenDataLoader runs in its default Java-only mode here (no hybrid OCR backend); scanned/image-only pages may yield low word counts without indicating a failure.
