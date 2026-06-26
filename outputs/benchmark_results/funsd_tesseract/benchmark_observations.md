# FUNSD Benchmark Report

## Dataset

- Dataset size: 50 documents
- Documents evaluated: 50
- Dataset directory: `C:\Users\Yug\Documents\Internship\pdf-extraction-benchmark\datasets\FUNSD`

## Average Metrics

| Metric | Mean | Median | Min | Max | Std Dev |
| --- | ---: | ---: | ---: | ---: | ---: |
| CER | 0.484543 | 0.501809 | 0.146280 | 0.798742 | 0.167136 |
| WER | 0.688375 | 0.719074 | 0.279661 | 1.000000 | 0.167927 |
| Token Precision | 0.602450 | 0.602857 | 0.333333 | 0.869565 | 0.129905 |
| Token Recall | 0.505827 | 0.514430 | 0.193694 | 0.838983 | 0.158506 |
| Token F1 | 0.544655 | 0.547168 | 0.278638 | 0.833333 | 0.144645 |
| Token Overlap Accuracy | 0.388106 | 0.376628 | 0.161871 | 0.714286 | 0.140312 |

## Distributions

- CER chart: `outputs\charts\funsd\cer_distribution.png`
- WER chart: `outputs\charts\funsd\wer_distribution.png`
- F1 chart: `outputs\charts\funsd\f1_distribution.png`

## Best 10 Documents

| Rank | Document | CER | WER | Token F1 | Primary Failure Mode |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | 86236474_6476 | 0.146280 | 0.279661 | 0.828452 | Character substitutions |
| 2 | 82250337_0338 | 0.192192 | 0.429907 | 0.687805 | Numeric errors |
| 3 | 87125460 | 0.232877 | 0.402778 | 0.695035 | Numeric errors |
| 4 | 82092117 | 0.240892 | 0.470852 | 0.636580 | Numeric errors |
| 5 | 82573104 | 0.241594 | 0.503704 | 0.666667 | Numeric errors |
| 6 | 86263525 | 0.254054 | 0.444444 | 0.729412 | Numeric errors |
| 7 | 89856243 | 0.286965 | 0.501608 | 0.718954 | Character substitutions |
| 8 | 83443897 | 0.291488 | 0.574359 | 0.588889 | Missing text |
| 9 | 87428306 | 0.300000 | 0.454545 | 0.638037 | Missing text |
| 10 | 86220490 | 0.300905 | 0.453333 | 0.725926 | Numeric errors |

## Worst 10 Documents

| Rank | Document | CER | WER | Token F1 | Primary Failure Mode |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | 82491256 | 0.798742 | 0.943662 | 0.724638 | Character substitutions |
| 2 | 87528380 | 0.742721 | 0.834550 | 0.433387 | Missing text |
| 3 | 82251504 | 0.731377 | 0.878378 | 0.284768 | Missing text |
| 4 | 83641919_1921 | 0.727198 | 0.885167 | 0.278638 | Missing text |
| 5 | 82504862 | 0.720721 | 0.904762 | 0.619048 | Numeric errors |
| 6 | 86230203_0206 | 0.715881 | 1.000000 | 0.410448 | Missing text |
| 7 | 86075409_5410 | 0.707756 | 0.888000 | 0.413502 | Missing text |
| 8 | 87093315_87093318 | 0.691901 | 0.855670 | 0.507645 | Missing text |
| 9 | 82253362_3364 | 0.677632 | 0.855263 | 0.288889 | Missing text |
| 10 | 82200067_0069 | 0.668263 | 0.772455 | 0.459016 | Missing text |

## Failure Modes

| Failure mode | Documents |
| --- | ---: |
| Numeric errors | 47 |
| Table-related errors | 37 |
| Missing text | 30 |
| Character substitutions | 6 |
| Layout issues | 3 |

## Recommendations

- Treat CER and WER as useful but not sufficient for FUNSD because they are sensitive to both OCR mistakes and document structure.
- Use token precision/recall/F1 to separate content capture from ordering noise.
- Inspect table-heavy or numeric-heavy documents separately because they show the largest layout and digit-related drift.
- Use the distribution charts to flag documents that sit far outside the cluster as likely preprocessing or extraction failures.

## Notes

- The CSV now includes CER, WER, token precision, token recall, token F1, and order-insensitive token overlap accuracy for every document.
- Failure categories are heuristic and are intended for reporting, not as ground truth labels.
- The top and worst examples are ranked primarily by CER, with WER and token metrics included for context.
