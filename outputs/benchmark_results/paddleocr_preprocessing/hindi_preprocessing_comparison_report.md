# Hindi Preprocessing OCR Comparison

Source image: `C:\Users\Yug\Downloads\hindi.jpeg`
Multilingual mode: `PaddleOCR(language_mode="multilingual")`

## Preprocessing variants
- `Original` ? `outputs\benchmark_results\paddleocr_preprocessing\original.jpeg`
- `2x upscaled` ? `outputs\benchmark_results\paddleocr_preprocessing\upscaled_2x.jpeg`
- `4x upscaled` ? `outputs\benchmark_results\paddleocr_preprocessing\upscaled_4x.jpeg`
- `Grayscale` ? `outputs\benchmark_results\paddleocr_preprocessing\grayscale.jpeg`
- `Thresholded black-white` ? `outputs\benchmark_results\paddleocr_preprocessing\thresholded_bw.jpeg`

## Results
| Variant | OCR text | Avg confidence | Character count | Recognition quality |
| --- | --- | ---: | ---: | --- |
| Original | हमारी ? िज़ंदगी ? में ? का ? आना ? Iie ? एक ? मकसद ? ? ? है ? कुछ ? ? ? आज़माएंगे ? H? ? 'Thleh/ ? कुछ ? हमारा ? इरतेमाल? | 0.866 | 109 | Good |
| 2x upscaled | हमारी ? िज़ंदगी ? ! ? Uslk? ? का ? li? ? I ? एक ? मकसद ? होता ? है, ? ९क ? ? ? I chlhei? ? क ? िसखाएंगे ? कुछ ? ? ?? | 0.869 | 126 | Good |
| 4x upscaled | ? ? िज़ंदगी ? में ? Uslk? ? का ? आना ? होता ? है, ? मकसद ? ? ? कुछ ? I calhi? ? K३ ? कुछ ? िसखाएंगे ? इरतेमाल ? कुछ ?? | 0.869 | 117 | Good |
| Grayscale | Ille? ? िज़ंदगी ? मैं ? का ? आना ? Iie ? एक ? मकसद ? ? ? ै, ? कुछ ? हमे ? आज़माएंगे ? H? ? िसखाएंगे ? कुछ ? हमारा ?? | 0.882 | 116 | Good |
| Thresholded black-white | हमारी ? ?! ? Lik ? का ? Ile. ? 1. ? पक ? मकसद ? ' ? हमे ? I- ? हमों ? ँसखाएंगी ? Ialht? ? W? ? करंग ? और ? e ? हम ? H ?? | 0.799 | 101 | Good |

## Notes
- Original and grayscale variants preserved the same OCR structure, so grayscale alone did not unlock better Devanagari decoding.
- 2x and 4x upscaling increased text size but also amplified recognition noise in this sample.
- Thresholding changed the visual contrast, but the recognizer still produced mostly garbled output rather than a clean transcription.
- The bottleneck appears to be recognition quality for this font/style, not text-region detection.

## Detailed OCR outputs
### Original
- Confidence: `0.866`
- Character count: `109`
- Recognition quality: `Good`
- OCR text:
```text
हमारी
िज़ंदगी
में
का
आना
Iie
एक
मकसद
?
है
कुछ
?
आज़माएंगे
H?
'Thleh/
कुछ
हमारा
इरतेमाल
और
H?
l
का
EPh
भी
Ilshpk
```

### 2x upscaled
- Confidence: `0.869`
- Character count: `126`
- Recognition quality: `Good`
- OCR text:
```text
हमारी
िज़ंदगी
!
Uslk?
का
li?
I
एक
मकसद
होता
है,
९क
?
I chlhei?
क
िसखाएंगे
कुछ
?
इरतेमाल
करेंगु
और
कुछ
H?
l?
का
मतलब
1५
बताएंग.ा
```

### 4x upscaled
- Confidence: `0.869`
- Character count: `117`
- Recognition quality: `Good`
- OCR text:
```text
?
िज़ंदगी
में
Uslk?
का
आना
होता
है,
मकसद
?
कुछ
I calhi?
K३
कुछ
िसखाएंगे
इरतेमाल
कुछ
IlH?
और
H?
l
कुछ
का
1५
बताएंगे
.!!
```

### Grayscale
- Confidence: `0.882`
- Character count: `116`
- Recognition quality: `Good`
- OCR text:
```text
Ille?
िज़ंदगी
मैं
का
आना
Iie
एक
मकसद
?
ै,
कुछ
हमे
आज़माएंगे
H?
िसखाएंगे
कुछ
हमारा
इरतेमाल
करेंगे
और
H?
l
का
भ
I'lchlpk
```

### Thresholded black-white
- Confidence: `0.799`
- Character count: `101`
- Recognition quality: `Good`
- OCR text:
```text
हमारी
?!
Lik
का
Ile.
1.
पक
मकसद
'
हमे
I-
हमों
ँसखाएंगी
Ialht?
W?
करंग
और
e
हम
H
कग
सहा
मतनय
भी
I'lrhE
```
