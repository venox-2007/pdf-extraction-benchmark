# FUNSD Entity Evaluation Report

## Overview

- Dataset size: 50 documents
- Documents evaluated: 50
- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\datasets\FUNSD`

## Average Metrics

| Metric | Mean | Median | Min | Max | Std Dev |
| --- | ---: | ---: | ---: | ---: | ---: |
| Entity Precision | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| Entity Recall | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| Entity F1 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| CER | 0.484543 | 0.501809 | 0.146280 | 0.798742 | 0.167136 |
| WER | 0.688375 | 0.719074 | 0.279661 | 1.000000 | 0.167927 |

## CER / WER Comparison

- Correlation between CER and entity F1: 0.000
- Correlation between WER and entity F1: 0.000
- Entity-level metrics better reflect question-answer extraction quality, while CER/WER remain sensitive to reading order and form layout.

## Documents Where CER/WER Look Worse Than Entity Extraction

| Document | CER | WER | Entity F1 | Note |
| --- | ---: | ---: | ---: | --- |
| 86236474_6476 | 0.146280 | 0.279661 | 0.000000 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82250337_0338 | 0.192192 | 0.429907 | 0.000000 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 87125460 | 0.232877 | 0.402778 | 0.000000 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82092117 | 0.240892 | 0.470852 | 0.000000 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82573104 | 0.241594 | 0.503704 | 0.000000 | Entity extraction stayed strong even though document-level text was reordered or noisy. |

## Interpretation

- A strong entity score means the benchmark recovered the question-answer relationship even if the flattened document text was reordered.
- This makes entity precision/recall/F1 a better stakeholder-facing measure for FUNSD than document-level CER/WER alone.
