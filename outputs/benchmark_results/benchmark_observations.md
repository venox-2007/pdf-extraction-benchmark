# Benchmark Observations

- Fastest overall extractor (average latency): **PyMuPDF**.
- Best scanned-PDF text recovery (average text length): **PaddleOCR**.
- Best native-PDF text extraction (average text length): **PyMuPDF**.
- Most markdown-rich output (average markdown length): **PyMuPDF**.
- Table preservation note: only OpenDataLoader currently maps richer structural layout/table-style markdown in this project; PyMuPDF and PaddleOCR currently provide text-first output.
- Classification mismatches observed: **6** run rows.
- Non-success extraction runs observed: **4** out of 30.

## Anomalies
- Long runtime: PaddleOCR on native_1.pdf took 66.18s
- Long runtime: PaddleOCR on native_2.pdf took 262.85s
- Long runtime: PaddleOCR on native_3.pdf took 112.50s
- Empty output: OpenDataLoader on scanned_1.pdf produced zero text
- Empty output: PyMuPDF on scanned_1.pdf produced zero text
- Long runtime: PaddleOCR on scanned_2.pdf took 93.36s
- Long runtime: PaddleOCR on scanned_4.pdf took 31.10s
- Empty output: OpenDataLoader on scanned_5.pdf produced zero text
- Empty output: PyMuPDF on scanned_5.pdf produced zero text
