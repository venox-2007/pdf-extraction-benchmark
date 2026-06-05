# PaddleOCR Integration Update

## Before
- PaddleOCR was hard-coded to `lang="en"`.
- This routed OCR through the English recognition path only.
- Metadata did not include the active model name or language mode.

## After
- Added `language_mode="english"` and `language_mode="multilingual"` to `PaddleocrExtractor`.
- English mode keeps the English OCR path.
- Multilingual mode uses the Devanagari OCR path for English + Hindi/Marathi coverage.
- Metadata now records:
  - `ocr_model_name`
  - `ocr_detection_model_name`
  - `ocr_recognition_model_name`
  - `ocr_language_mode`
  - `ocr_language`
  - `ocr_version`

## Model Path
- Current installed `paddleocr==2.7.3` supports up to `PP-OCRv4`, so this repo uses the latest compatible multilingual setup.
- English mode resolves to:
  - `en_PP-OCRv3_det_infer`
  - `en_PP-OCRv4_rec_infer`
- Multilingual mode resolves to:
  - `Multilingual_PP-OCRv3_det_infer`
  - `devanagari_PP-OCRv4_rec_infer`

## Validation
- English smoke test returned clean text for an English sample:
  - `Invoice Total`
  - `Amount 1234.50`
  - `Hello World`
- Hindi/Marathi smoke test successfully routed through the multilingual model path.
- The synthetic Devanagari sample still came back noisy, which suggests the improvement is mainly in model coverage and routing rather than a guaranteed accuracy jump on every sample.

## Performance Notes
- English mode on the sample image ran in about `0.66s`.
- Multilingual mode on the Hindi sample ran in about `0.33s` after model download/caching.
- First-time multilingual use downloaded additional det/rec weights, so startup cost is higher even when steady-state inference is similar.

## Takeaway
- The extractor now supports a real English vs multilingual switch without changing benchmark logic.
- Metadata is richer and easier to audit.
- On this environment, the best compatible multilingual path is PP-OCRv4 Devanagari rather than PP-OCRv5.
