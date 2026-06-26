# Final SROIE Benchmark — Curated 20-Document Corpus

Dataset: `data/final_benchmark/sroie/img/` (20 receipt images)
Ground truth: `data/final_benchmark/sroie/box/*.txt` (ICDAR box-transcription format)
Extractor order: PyMuPDF -> OpenDataLoader -> Tesseract -> PaddleOCR -> Docling
Total runtime: 416.9s

| Extractor | Success | CER | WER | Token F1 | Avg latency (ms) | Avg words | Avg markdown len |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| PyMuPDF | 20/20 | 1.0000 | 1.0000 | 0.0000 | 30.7 | 0.0 | 0.0 |
| OpenDataLoader | 20/20 | 1.0000 | 1.0000 | 0.0000 | 931.1 | 0.0 | 50.0 |
| Tesseract | 20/20 | 0.3846 | 0.6268 | 0.4972 | 723.1 | 115.5 | 0.0 |
| PaddleOCR | 20/20 | 0.3183 | 0.6502 | 0.4587 | 3037.5 | 89.3 | 0.0 |
| Docling | 20/20 | 0.4424 | 0.7175 | 0.3746 | 15794.3 | 65.6 | 1384.8 |

## Per-extractor runtime

- **PyMuPDF**: 0.6s total, 0 failed
- **OpenDataLoader**: 18.7s total, 0 failed
- **Tesseract**: 16.1s total, 0 failed
- **PaddleOCR**: 63.3s total, 0 failed
- **Docling**: 317.1s total, 0 failed

## Notes

- Ground truth is built by concatenating each receipt's box-transcription lines in file order, normalized identically to the FUNSD methodology (whitespace-collapsed, newline-joined).
- PyMuPDF and OpenDataLoader require PDF input; each `.jpg` receipt is wrapped into a single-page PDF via fitz before extraction. OpenDataLoader ran in its default Java-only mode (no hybrid OCR backend).
