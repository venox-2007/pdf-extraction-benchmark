# Final FUNSD Benchmark — Curated 20-Document Corpus

Dataset: `data/final_benchmark/funsd/` (20 documents)
Extractor order: PyMuPDF -> OpenDataLoader -> Tesseract -> PaddleOCR -> Docling
Total runtime: 331.1s

| Extractor | Success | CER | WER | Token F1 | Avg latency (ms) | Avg words | Avg markdown len |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| PyMuPDF | 20/20 | 1.0000 | 1.0000 | 0.0000 | 40.2 | 0.0 | 0.0 |
| OpenDataLoader | 20/20 | 1.0000 | 1.0000 | 0.0000 | 740.2 | 0.0 | 47.5 |
| Tesseract | 20/20 | 0.4115 | 0.6120 | 0.6039 | 453.3 | 121.1 | 0.0 |
| PaddleOCR | 20/20 | 0.4181 | 0.6100 | 0.6570 | 3444.9 | 109.3 | 0.0 |
| Docling | 20/20 | 0.4722 | 0.7857 | 0.4349 | 11255.4 | 80.6 | 1038.3 |

## Per-extractor runtime

- **PyMuPDF**: 0.8s total, 0 failed
- **OpenDataLoader**: 15.0s total, 0 failed
- **Tesseract**: 12.1s total, 0 failed
- **PaddleOCR**: 72.7s total, 0 failed
- **Docling**: 227.6s total, 0 failed
