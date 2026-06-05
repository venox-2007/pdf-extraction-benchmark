# Hindi Preprocessing OCR Summary

## Best-to-worst by confidence
- 1. Grayscale ? confidence 0.882, chars 116
- 2. 2x upscaled ? confidence 0.869, chars 126
- 3. 4x upscaled ? confidence 0.869, chars 117
- 4. Original ? confidence 0.866, chars 109
- 5. Thresholded black-white ? confidence 0.799, chars 101

## Interpretation
- Grayscale performed best on this sample, with the highest confidence and slightly denser text output.
- Upscaling did not materially improve recognition; it mostly increased fragmentation/noise.
- Thresholding reduced confidence and produced the most corrupted transcript.
- The main bottleneck remains Devanagari recognition quality, not text detection.

## Files
- Detailed comparison: `outputs\benchmark_results\paddleocr_preprocessing\hindi_preprocessing_comparison_report.md`
- `outputs\benchmark_results\paddleocr_preprocessing\original.jpeg`
- `outputs\benchmark_results\paddleocr_preprocessing\upscaled_2x.jpeg`
- `outputs\benchmark_results\paddleocr_preprocessing\upscaled_4x.jpeg`
- `outputs\benchmark_results\paddleocr_preprocessing\grayscale.jpeg`
- `outputs\benchmark_results\paddleocr_preprocessing\thresholded_bw.jpeg`