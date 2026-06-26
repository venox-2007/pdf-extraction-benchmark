# Docling vs PaddleOCR on FUNSD

## Average Comparison

- Docling average CER: 0.416583
- PaddleOCR average CER: 0.442993
- Docling average WER: 0.735836
- PaddleOCR average WER: 0.646521
- Docling average Token F1: 0.439833
- PaddleOCR average Token F1: 0.628433

## Reading Order and Structure

- Docling tends to preserve document flow as structured markdown, which helps reading order when text is grouped into blocks and sections.
- PaddleOCR typically emits flatter line-by-line text, which can be more sensitive to layout reordering but may be simpler on sparse scanned pages.
- Docling is better suited to table and form structure preservation when its layout model recognizes the regions correctly.

## Documents Where Docling Performs Better

| Document | Docling CER | Paddle CER | CER Δ | Docling Token F1 | Paddle Token F1 | F1 Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 82250337_0338 | 0.173423 | 0.175676 | 0.002252 | 0.683805 | 0.743842 | -0.060038 |
| 82200067_0069 | 0.649102 | 0.608383 | -0.040719 | 0.317597 | 0.398496 | -0.080900 |
| 82092117 | 0.360595 | 0.270632 | -0.089963 | 0.403509 | 0.597884 | -0.194375 |
| 82251504 | 0.265613 | 0.203160 | -0.062453 | 0.384615 | 0.658477 | -0.273861 |
| 82252956_2958 | 0.634183 | 0.460270 | -0.173913 | 0.409639 | 0.698565 | -0.288926 |

## Documents Where PaddleOCR Performs Better

| Document | Docling CER | Paddle CER | CER Δ | Docling Token F1 | Paddle Token F1 | F1 Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 82252956_2958 | 0.634183 | 0.460270 | -0.173913 | 0.409639 | 0.698565 | -0.288926 |
| 82251504 | 0.265613 | 0.203160 | -0.062453 | 0.384615 | 0.658477 | -0.273861 |
| 82092117 | 0.360595 | 0.270632 | -0.089963 | 0.403509 | 0.597884 | -0.194375 |
| 82200067_0069 | 0.649102 | 0.608383 | -0.040719 | 0.317597 | 0.398496 | -0.080900 |
| 82250337_0338 | 0.173423 | 0.175676 | 0.002252 | 0.683805 | 0.743842 | -0.060038 |

## Interpretation

- Docling is a stronger fit when structure preservation and markdown-like document reconstruction matter.
- PaddleOCR can remain competitive when the source is a simple scan and the main goal is raw text capture.
