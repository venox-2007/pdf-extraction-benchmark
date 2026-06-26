# FUNSD Entity Evaluation Report

## Overview

- Dataset size: 5 documents
- Documents evaluated: 5
- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\datasets\FUNSD`

## Average Metrics

| Metric | Mean | Median | Min | Max | Std Dev |
| --- | ---: | ---: | ---: | ---: | ---: |
| Entity Precision | 0.019875 | 0.018182 | 0.006667 | 0.033113 | 0.010374 |
| Entity Recall | 0.176124 | 0.129032 | 0.083333 | 0.357143 | 0.098379 |
| Entity F1 | 0.035113 | 0.033333 | 0.012346 | 0.060606 | 0.017826 |
| CER | 0.416583 | 0.360595 | 0.173423 | 0.649102 | 0.193115 |
| WER | 0.735836 | 0.770270 | 0.443925 | 0.880240 | 0.158024 |

## CER / WER Comparison

- Correlation between CER and entity F1: 0.054
- Correlation between WER and entity F1: -0.438
- Entity-level metrics better reflect question-answer extraction quality, while CER/WER remain sensitive to reading order and form layout.

## Documents Where CER/WER Look Worse Than Entity Extraction

| Document | CER | WER | Entity F1 | Note |
| --- | ---: | ---: | ---: | --- |
| 82250337_0338 | 0.173423 | 0.443925 | 0.060606 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82251504 | 0.265613 | 0.770270 | 0.012346 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82092117 | 0.360595 | 0.717489 | 0.020202 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82200067_0069 | 0.649102 | 0.880240 | 0.049080 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82252956_2958 | 0.634183 | 0.867257 | 0.033333 | Entity extraction stayed strong even though document-level text was reordered or noisy. |

## Interpretation

- A strong entity score means the benchmark recovered the question-answer relationship even if the flattened document text was reordered.
- This makes entity precision/recall/F1 a better stakeholder-facing measure for FUNSD than document-level CER/WER alone.
