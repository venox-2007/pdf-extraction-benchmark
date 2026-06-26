# FUNSD Entity Evaluation Report

## Overview

- Dataset size: 50 documents
- Documents evaluated: 50
- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\datasets\FUNSD`

## Average Metrics

| Metric | Mean | Median | Min | Max | Std Dev |
| --- | ---: | ---: | ---: | ---: | ---: |
| Entity Precision | 0.018634 | 0.012881 | 0.000000 | 0.063291 | 0.016428 |
| Entity Recall | 0.197077 | 0.121324 | 0.000000 | 0.833333 | 0.209600 |
| Entity F1 | 0.032942 | 0.022506 | 0.000000 | 0.117647 | 0.028645 |
| CER | 0.499991 | 0.488567 | 0.173423 | 1.043956 | 0.197898 |
| WER | 0.765187 | 0.774966 | 0.387500 | 1.178571 | 0.150501 |

## CER / WER Comparison

- Correlation between CER and entity F1: -0.024
- Correlation between WER and entity F1: -0.130
- Entity-level metrics better reflect question-answer extraction quality, while CER/WER remain sensitive to reading order and form layout.

## Documents Where CER/WER Look Worse Than Entity Extraction

| Document | CER | WER | Entity F1 | Note |
| --- | ---: | ---: | ---: | --- |
| 82250337_0338 | 0.173423 | 0.443925 | 0.060606 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 86236474_6476 | 0.174023 | 0.864407 | 0.000000 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 85240939 | 0.205102 | 0.577922 | 0.018349 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 87428306 | 0.231532 | 0.545455 | 0.043165 | Entity extraction stayed strong even though document-level text was reordered or noisy. |
| 82573104 | 0.275218 | 0.718519 | 0.062500 | Entity extraction stayed strong even though document-level text was reordered or noisy. |

## Interpretation

- A strong entity score means the benchmark recovered the question-answer relationship even if the flattened document text was reordered.
- This makes entity precision/recall/F1 a better stakeholder-facing measure for FUNSD than document-level CER/WER alone.
