# FUNSD Benchmark Report

## Dataset

- Dataset size: 50 documents
- Documents evaluated: 50
- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\datasets\FUNSD`

## Average Metrics

| Metric | Mean | Median | Min | Max | Std Dev |
| --- | ---: | ---: | ---: | ---: | ---: |
| CER | 0.442993 | 0.457783 | 0.175676 | 0.786036 | 0.157219 |
| WER | 0.646521 | 0.644276 | 0.338983 | 0.960526 | 0.162781 |
| Token Precision | 0.709623 | 0.758594 | 0.181818 | 0.917808 | 0.140718 |
| Token Recall | 0.567955 | 0.593499 | 0.078947 | 0.840000 | 0.159508 |
| Token F1 | 0.628433 | 0.669320 | 0.110092 | 0.875817 | 0.153323 |
| Token Overlap Accuracy | 0.475024 | 0.502992 | 0.058252 | 0.779070 | 0.152375 |

## Distributions

- CER chart: `outputs\charts\funsd\cer_distribution.png`
- WER chart: `outputs\charts\funsd\wer_distribution.png`
- F1 chart: `outputs\charts\funsd\f1_distribution.png`

## Best 10 Documents

| Rank | Document | CER | WER | Token F1 | Primary Failure Mode |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | 82250337_0338 | 0.175676 | 0.415888 | 0.743842 | Character substitutions |
| 2 | 85240939 | 0.198980 | 0.428571 | 0.676259 | Numeric errors |
| 3 | 82251504 | 0.203160 | 0.481982 | 0.658477 | Numeric errors |
| 4 | 86236474_6476 | 0.208071 | 0.338983 | 0.777778 | Character substitutions |
| 5 | 87125460 | 0.228311 | 0.402778 | 0.721805 | Numeric errors |
| 6 | 82253058_3059 | 0.239766 | 0.449198 | 0.719764 | Numeric errors |
| 7 | 85201976 | 0.242485 | 0.400000 | 0.875817 | Character substitutions |
| 8 | 87428306 | 0.252252 | 0.443850 | 0.672783 | Missing text |
| 9 | 82092117 | 0.270632 | 0.533632 | 0.597884 | Missing text |
| 10 | 82573104 | 0.272727 | 0.629630 | 0.569038 | Missing text |

## Worst 10 Documents

| Rank | Document | CER | WER | Token F1 | Primary Failure Mode |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | 82504862 | 0.786036 | 0.936508 | 0.621849 | Numeric errors |
| 2 | 82491256 | 0.775681 | 0.943662 | 0.640625 | Numeric errors |
| 3 | 87093315_87093318 | 0.756162 | 0.860825 | 0.745763 | Numeric errors |
| 4 | 86230203_0206 | 0.693548 | 0.912409 | 0.725191 | Numeric errors |
| 5 | 86075409_5410 | 0.681440 | 0.808000 | 0.629108 | Missing text |
| 6 | 86328049_8050 | 0.642478 | 0.884422 | 0.425150 | Missing text |
| 7 | 85540866 | 0.613065 | 0.680000 | 0.875000 | Character substitutions |
| 8 | 82200067_0069 | 0.608383 | 0.820359 | 0.398496 | Missing text |
| 9 | 83823750 | 0.576846 | 0.773006 | 0.377953 | Missing text |
| 10 | 82253362_3364 | 0.574013 | 0.828947 | 0.657143 | Numeric errors |

## Failure Modes

| Failure mode | Documents |
| --- | ---: |
| Numeric errors | 46 |
| Table-related errors | 39 |
| Missing text | 21 |
| Layout issues | 15 |
| Character substitutions | 10 |

## Recommendations

- Treat CER and WER as useful but not sufficient for FUNSD because they are sensitive to both OCR mistakes and document structure.
- Use token precision/recall/F1 to separate content capture from ordering noise.
- Inspect table-heavy or numeric-heavy documents separately because they show the largest layout and digit-related drift.
- Use the distribution charts to flag documents that sit far outside the cluster as likely preprocessing or extraction failures.

## Notes

- The CSV now includes CER, WER, token precision, token recall, token F1, and order-insensitive token overlap accuracy for every document.
- Failure categories are heuristic and are intended for reporting, not as ground truth labels.
- The top and worst examples are ranked primarily by CER, with WER and token metrics included for context.
