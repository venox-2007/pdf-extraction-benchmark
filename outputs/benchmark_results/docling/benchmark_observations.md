# Docling FUNSD Benchmark Report

## Overview

- Dataset size: 5 documents
- Evaluated documents: 5
- Output directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\outputs\benchmark_results\docling`

## Runtime Notes

- Docling runs as a local PDF conversion pipeline and preserves reading order, page structure, and tables when the source contains them.
- On Windows, the Hugging Face cache needs symlink support disabled or Developer Mode/admin privileges enabled.
- FUNSD images are converted to temporary PDFs before conversion so Docling can process them with its PDF pipeline.

## Detailed Findings


## Dataset

- Dataset size: 5 documents
- Documents evaluated: 5
- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\datasets\FUNSD`

## Average Metrics

| Metric | Mean | Median | Min | Max | Std Dev |
| --- | ---: | ---: | ---: | ---: | ---: |
| CER | 0.416583 | 0.360595 | 0.173423 | 0.649102 | 0.193115 |
| WER | 0.735836 | 0.770270 | 0.443925 | 0.880240 | 0.158024 |
| Token Precision | 0.620458 | 0.579832 | 0.560345 | 0.760000 | 0.075844 |
| Token Recall | 0.349229 | 0.300885 | 0.221557 | 0.621495 | 0.139668 |
| Token F1 | 0.439833 | 0.403509 | 0.317597 | 0.683805 | 0.126289 |
| Token Overlap Accuracy | 0.291345 | 0.252747 | 0.188776 | 0.519531 | 0.116666 |

## Distributions

- CER chart: `outputs\charts\docling\cer_distribution.png`
- WER chart: `outputs\charts\docling\wer_distribution.png`
- F1 chart: `outputs\charts\docling\f1_distribution.png`

## Best 10 Documents

| Rank | Document | CER | WER | Token F1 | Primary Failure Mode |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | 82250337_0338 | 0.173423 | 0.443925 | 0.683805 | Numeric errors |
| 2 | 82251504 | 0.265613 | 0.770270 | 0.384615 | Missing text |
| 3 | 82092117 | 0.360595 | 0.717489 | 0.403509 | Missing text |
| 4 | 82252956_2958 | 0.634183 | 0.867257 | 0.409639 | Missing text |
| 5 | 82200067_0069 | 0.649102 | 0.880240 | 0.317597 | Missing text |

## Worst 10 Documents

| Rank | Document | CER | WER | Token F1 | Primary Failure Mode |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | 82200067_0069 | 0.649102 | 0.880240 | 0.317597 | Missing text |
| 2 | 82252956_2958 | 0.634183 | 0.867257 | 0.409639 | Missing text |
| 3 | 82092117 | 0.360595 | 0.717489 | 0.403509 | Missing text |
| 4 | 82251504 | 0.265613 | 0.770270 | 0.384615 | Missing text |
| 5 | 82250337_0338 | 0.173423 | 0.443925 | 0.683805 | Numeric errors |

## Failure Modes

| Failure mode | Documents |
| --- | ---: |
| Numeric errors | 5 |
| Missing text | 4 |
| Table-related errors | 4 |

## Recommendations

- Treat CER and WER as useful but not sufficient for FUNSD because they are sensitive to both OCR mistakes and document structure.
- Use token precision/recall/F1 to separate content capture from ordering noise.
- Inspect table-heavy or numeric-heavy documents separately because they show the largest layout and digit-related drift.
- Use the distribution charts to flag documents that sit far outside the cluster as likely preprocessing or extraction failures.

## Notes

- The CSV now includes CER, WER, token precision, token recall, token F1, and order-insensitive token overlap accuracy for every document.
- Failure categories are heuristic and are intended for reporting, not as ground truth labels.
- The top and worst examples are ranked primarily by CER, with WER and token metrics included for context.
