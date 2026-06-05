# FUNSD Entity Evaluation Report

## Overview

- Dataset size: 50 documents
- Documents evaluated: 50
- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\datasets\FUNSD`

## Average Metrics

| Metric | Mean | Median | Min | Max | Std Dev |
| --- | ---: | ---: | ---: | ---: | ---: |
| Entity Precision | 0.039408 | 0.034648 | 0.000000 | 0.120690 | 0.030444 |
| Entity Recall | 0.206925 | 0.179144 | 0.000000 | 0.666667 | 0.165285 |
| Entity F1 | 0.063644 | 0.060606 | 0.000000 | 0.181818 | 0.047951 |
| CER | 0.442993 | 0.457783 | 0.175676 | 0.786036 | 0.157219 |
| WER | 0.646521 | 0.644276 | 0.338983 | 0.960526 | 0.162781 |

## CER / WER Comparison

- Correlation between CER and entity F1: 0.060
- Correlation between WER and entity F1: 0.008
- Entity-level metrics better reflect question-answer extraction quality, while CER/WER remain sensitive to reading order and form layout.

## Documents Where CER/WER Look Worse Than Entity Extraction

| Document | CER | WER | Entity F1 | Note |
| --- | ---: | ---: | ---: | --- |
| 87125460 | 0.228311 | 0.402778 | 0.156863 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82250337_0338 | 0.175676 | 0.415888 | 0.103093 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 86236474_6476 | 0.208071 | 0.338983 | 0.083333 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82251504 | 0.203160 | 0.481982 | 0.068182 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82253058_3059 | 0.239766 | 0.449198 | 0.102564 | Entity extraction stayed strong even though document-level text was reordered or noisy. |

## Interpretation

- A strong entity score means the benchmark recovered the question-answer relationship even if the flattened document text was reordered.
- This makes entity precision/recall/F1 a better stakeholder-facing measure for FUNSD than document-level CER/WER alone.
