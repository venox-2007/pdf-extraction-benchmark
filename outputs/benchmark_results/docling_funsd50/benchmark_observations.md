# Docling FUNSD Benchmark Report

## Overview

- Dataset size: 50 documents
- Evaluated documents: 50
- Output directory: `C:\Users\Yug\AppData\Local\Temp\outputs\benchmark_results\docling_funsd50`

## Runtime Notes

- Docling runs as a local PDF conversion pipeline and preserves reading order, page structure, and tables when the source contains them.
- On Windows, the Hugging Face cache needs symlink support disabled or Developer Mode/admin privileges enabled.
- FUNSD images are converted to temporary PDFs before conversion so Docling can process them with its PDF pipeline.

## Detailed Findings


## Dataset

- Dataset size: 50 documents
- Documents evaluated: 50
- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\datasets\FUNSD`

## Average Metrics

| Metric | Mean | Median | Min | Max | Std Dev |
| --- | ---: | ---: | ---: | ---: | ---: |
| CER | 0.499991 | 0.488567 | 0.173423 | 1.043956 | 0.197898 |
| WER | 0.765187 | 0.774966 | 0.387500 | 1.178571 | 0.150501 |
| Token Precision | 0.590354 | 0.614176 | 0.000000 | 0.915493 | 0.160913 |
| Token Recall | 0.393028 | 0.391996 | 0.000000 | 0.812500 | 0.165769 |
| Token F1 | 0.461212 | 0.469375 | 0.000000 | 0.860927 | 0.164135 |
| Token Overlap Accuracy | 0.314469 | 0.306686 | 0.000000 | 0.755814 | 0.140162 |

## Distributions

- CER chart: `outputs\charts\docling\cer_distribution.png`
- WER chart: `outputs\charts\docling\wer_distribution.png`
- F1 chart: `outputs\charts\docling\f1_distribution.png`

## Best 10 Documents

| Rank | Document | CER | WER | Token F1 | Primary Failure Mode |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | 82250337_0338 | 0.173423 | 0.443925 | 0.683805 | Numeric errors |
| 2 | 86236474_6476 | 0.174023 | 0.864407 | 0.208092 | Missing text |
| 3 | 85240939 | 0.205102 | 0.577922 | 0.554307 | Missing text |
| 4 | 85201976 | 0.230461 | 0.387500 | 0.860927 | Character substitutions |
| 5 | 87428306 | 0.231532 | 0.545455 | 0.596386 | Missing text |
| 6 | 82253058_3059 | 0.254804 | 0.631016 | 0.521452 | Missing text |
| 7 | 82251504 | 0.265613 | 0.770270 | 0.384615 | Missing text |
| 8 | 82573104 | 0.275218 | 0.718519 | 0.459459 | Missing text |
| 9 | 87125460 | 0.283105 | 0.583333 | 0.549618 | Missing text |
| 10 | 85629964 | 0.308917 | 0.670213 | 0.531646 | Missing text |

## Worst 10 Documents

| Rank | Document | CER | WER | Token F1 | Primary Failure Mode |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | 87086073 | 1.043956 | 1.178571 | 0.427586 | Numeric errors |
| 2 | 87147607 | 1.000000 | 1.000000 | 0.000000 | Missing text |
| 3 | 82504862 | 0.795045 | 0.920635 | 0.576271 | Missing text |
| 4 | 87093315_87093318 | 0.791373 | 0.912371 | 0.210526 | Missing text |
| 5 | 82491256 | 0.784067 | 0.915493 | 0.731343 | Numeric errors |
| 6 | 83823750 | 0.713573 | 0.932515 | 0.135922 | Missing text |
| 7 | 86328049_8050 | 0.707965 | 0.919598 | 0.482353 | Missing text |
| 8 | 86075409_5410 | 0.695291 | 0.840000 | 0.563636 | Missing text |
| 9 | 86244113 | 0.681818 | 1.000000 | 0.125000 | Missing text |
| 10 | 83641919_1921 | 0.661463 | 0.803828 | 0.490446 | Missing text |

## Failure Modes

| Failure mode | Documents |
| --- | ---: |
| Numeric errors | 47 |
| Missing text | 43 |
| Table-related errors | 38 |
| Layout issues | 3 |
| Character substitutions | 1 |

## Recommendations

- Treat CER and WER as useful but not sufficient for FUNSD because they are sensitive to both OCR mistakes and document structure.
- Use token precision/recall/F1 to separate content capture from ordering noise.
- Inspect table-heavy or numeric-heavy documents separately because they show the largest layout and digit-related drift.
- Use the distribution charts to flag documents that sit far outside the cluster as likely preprocessing or extraction failures.

## Notes

- The CSV now includes CER, WER, token precision, token recall, token F1, and order-insensitive token overlap accuracy for every document.
- Failure categories are heuristic and are intended for reporting, not as ground truth labels.
- The top and worst examples are ranked primarily by CER, with WER and token metrics included for context.
