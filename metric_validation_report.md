# Comparison Analysis — Metric Validation Report

This report audits every metric shown in the Streamlit "Comparison Analysis" section
(`src/pdf_extraction_benchmark/ui/app.py`) for the four active extractors:
**PyMuPDF**, **PaddleOCR**, **Docling**, **OpenDataLoader**.

For each metric: the exact code path, source field(s), whether it reflects real
extractor output, correctness, assumptions/approximations, and demo risk.

All line references are to `src/pdf_extraction_benchmark/ui/app.py` unless another
file is named.

---

## 1. Extraction Time

**Code path:** `start = time.perf_counter()` before `extractor.extract(...)`,
`elapsed = time.perf_counter() - start` after (app.py extraction loop, ~line 632/650).
Stored as `comparison_rows[...]["latency_seconds"]`.

| Extractor | Real or placeholder | Notes |
|---|---|---|
| PyMuPDF | Real | Pure in-process parsing time. |
| PaddleOCR | Real | Includes page rasterization (`fitz` render to image) + OCR inference. |
| Docling | Real | Includes model inference **and** `_save_outputs()` writing `result.json`/`result.md` to disk inside `extract()`. |
| OpenDataLoader | Real | Includes a subprocess/JVM call (`opendataloader_pdf.convert`) plus reading back JSON from disk. |

**Assumptions / approximations:**
- All four are real wall-clock measurements, but **not apples-to-apples**: Docling and
  OpenDataLoader times include their own disk I/O (and for OpenDataLoader, JVM
  startup), while PyMuPDF and PaddleOCR are measured purely in-process. This can make
  Docling/OpenDataLoader look slower than their "pure extraction" cost.
- First-run model downloads (Docling, PaddleOCR) are not excluded — a cold cache run
  could massively inflate `latency_seconds` for those tools.

**Demo risk:** Low-to-medium. The numbers are real, but a side-by-side "fastest
extractor" claim can be unfair because of the I/O asymmetry above. Worth a caption.

---

## 2. Character Count

**Code path:**
```python
all_text = "\n\n".join(result.extracted_text for result in results)
char_count = len(all_text)
```
(app.py extraction loop)

| Extractor | Real or placeholder | Source field |
|---|---|---|
| PyMuPDF | Real | `page.get_text("text", sort=True)` per page |
| PaddleOCR | Real | OCR-recognized text lines joined per page |
| Docling | Real | Normalized text items (`document.export_to_dict()["texts"]`) |
| OpenDataLoader | Real | `content` strings from each "kid" block (kids-schema JSON) |

**Correctness:** Correct — straightforward `len()` of concatenated extracted text.

**Assumptions:** None significant. For PaddleOCR, this reflects whatever the OCR
engine recognized, including misreads — i.e. it measures *output volume*, not
*output correctness*.

**Demo risk:** Low.

---

## 3. Word Count

**Code path:** `word_count = len(all_text.split())` (same `all_text` as above).

**Source field:** Same as Character Count.

**Correctness:** Correct as a whitespace-token count.

**Assumptions / approximations:**
- `str.split()` is whitespace-based. For CJK or Devanagari text without spaces
  (relevant to PaddleOCR's "Multilingual" mode), this undercounts "words" — a line of
  Hindi text with no spaces counts as one "word" even if it's a full sentence.

**Demo risk:** Low for English documents; misleading if a multilingual/CJK document is
used in the demo, since word counts would not be comparable across extractors in that
case.

---

## 4. CER (Character Error Rate)

**Code path:** `_attach_relative_error_rates()` (app.py), called after the extraction
loop. Uses `character_error_rate()` from
`src/pdf_extraction_benchmark/benchmarks/funsd/metrics.py` (Levenshtein-based).

**Source field:** `per_extractor_text[extractor_name]` (same `all_text` as Character
Count).

**Real or placeholder:** **Hybrid.** The Levenshtein computation itself is real, but
there is **no ground-truth transcript** for arbitrary uploaded documents. The
extractor that produced the **most characters** is selected as a *pseudo-reference*,
and every other extractor's CER is computed against that reference's text — not
against a verified correct transcript.

**Correctness:** The arithmetic is correct (`character_error_rate = Levenshtein /
len(reference)`), but the *meaning* is "edit distance vs. the longest output," not
"OCR accuracy."

**Assumptions / approximations:**
- The longest-text extractor is treated as ground truth. If that extractor's output is
  itself wrong (e.g., includes extra boilerplate or layout tags), every other tool's
  CER inherits that bias.
- By construction, the reference extractor always reports `cer = 0.0`.

**Demo risk: HIGH.** In `_build_best_per_category()`, "Lowest CER" is computed as
`min(cer_rows, key=lambda row: row["cer"])`. Because the reference extractor's CER is
*always* `0.0` by definition, **"Lowest CER" will always (or near-always) be the
pseudo-reference extractor itself** — this is tautological, not a quality signal. A
viewer could easily mistake this for "this tool is most accurate," when it actually
just means "this tool produced the most text and was used as the yardstick." A caption
explaining the pseudo-reference is shown in the UI, but the **"Best Tool Per Category"
card does not repeat this caveat next to the CER/WER entries**, so it's easy to miss.

---

## 5. WER (Word Error Rate)

**Code path:** Same function `_attach_relative_error_rates()`, using
`word_error_rate()` from `funsd/metrics.py` (whitespace-tokenized Levenshtein).

**Source field / real-or-placeholder / assumptions:** Identical situation to CER —
relative to the same pseudo-reference, same tautology for "Lowest WER" in the
Best-Tool card, same `0.0` for the reference extractor.

**Demo risk: HIGH** — same reasoning as CER. "Lowest WER" is structurally biased
toward the pseudo-reference extractor.

---

## 6. Bounding Box Count

**Code path:** `bbox_count = sum(len(result.bounding_boxes) for result in results)`
(app.py extraction loop).

| Extractor | Real or placeholder | Source field | Granularity |
|---|---|---|---|
| PyMuPDF | Real | `page.get_text("blocks", sort=True)` → one bbox per text **block** ([pymupdf/extractor.py:47-59](src/pdf_extraction_benchmark/extractors/pymupdf/extractor.py#L47-L59)) | Text blocks (paragraph-ish) |
| PaddleOCR | Real | OCR detection polygons → axis-aligned bbox per detected text **line** ([paddleocr/extractor.py:188-194](src/pdf_extraction_benchmark/extractors/paddleocr/extractor.py#L188-L194)) | OCR text lines |
| Docling | Real | `prov[0]["bbox"]` per text **item**, plus one bbox per detected **table** ([docling/extractor.py:137-154](src/pdf_extraction_benchmark/extractors/docling/extractor.py#L137-L154)) | Text items + table regions |
| OpenDataLoader | Real | `block["bounding box"]` per "kid" content block ([opendataloader/extractor.py:164-172](src/pdf_extraction_benchmark/extractors/opendataloader/extractor.py#L164-L172)) | Content blocks |

**Correctness:** Each count is a correct `len()` of real bounding boxes returned by
that tool.

**Assumptions / approximations:** **Not directly comparable across tools** — each
extractor defines a "bounding box" at a different granularity (block vs. line vs.
item/table vs. content block). A higher count does not mean "more thorough layout
detection"; it can simply mean the tool segments text more finely.

### Concrete example — `data/raw/native/native_1.pdf` (3 pages)

| Extractor | Bounding Box Count | Per-page breakdown |
|---|---|---|
| PyMuPDF | 7 | 3, 2, 2 |
| OpenDataLoader | 24 | 9, 9, 6 |
| Docling | 25 | 10, 9, 6 |

**Why these values:**
- **PyMuPDF = 7**: PyMuPDF's `get_text("blocks")` merges contiguous text into large
  paragraph-level blocks — `native_1.pdf` (a short sample PDF) collapses into only 2-3
  blocks per page.
- **OpenDataLoader (24) and Docling (25)**: both perform finer-grained layout
  segmentation (headings, paragraphs, list items treated as separate elements), so
  each page yields ~6-10 boxes instead of 2-3.

### Concrete example — `data/raw/scanned/scanned_5.pdf` (1 page, OCR'd by PaddleOCR)

| Extractor | Bounding Box Count |
|---|---|
| PaddleOCR | 79 |
| PyMuPDF | 0 (no text layer on a scanned page) |

**Why 79:** PaddleOCR's text-detection model found 79 distinct lines of text on the
single scanned page (a two-column form), each producing one bbox
(`metadata.extra["total_text_blocks"] == 79` confirms 1:1 with `bounding_boxes`).

**Demo risk:** Medium. The numbers are all real, but presenting them in one column
side-by-side invites a "more boxes = better layout detection" reading that isn't
accurate given the granularity differences. A caption noting "granularity differs per
tool" is recommended.

---

## 7. Table Count

**Code path:** `table_count = sum(len(result.tables) for result in results)`.

| Extractor | Real or placeholder | Detail |
|---|---|---|
| PyMuPDF | **Placeholder (always 0)** | `tables=[]` is hardcoded for every result ([pymupdf/extractor.py:79](src/pdf_extraction_benchmark/extractors/pymupdf/extractor.py#L79)) — PyMuPDF extractor performs no table detection. |
| PaddleOCR | **Placeholder (always 0)** | `tables=[]` is hardcoded for every result ([paddleocr/extractor.py:166,214,259,306](src/pdf_extraction_benchmark/extractors/paddleocr/extractor.py#L214)) — no table-structure model is used. |
| OpenDataLoader | **Placeholder (always 0) in practice** | `_extract_tables()` exists ([opendataloader/extractor.py:210-244](src/pdf_extraction_benchmark/extractors/opendataloader/extractor.py#L210-L244)) but is only reachable from `_map_json_to_results()` (the "pages"-schema branch). The actual JSON produced by the installed `opendataloader-pdf` version uses the **"kids" schema**, handled by `_map_kids_to_results()` ([opendataloader/extractor.py:127-189](src/pdf_extraction_benchmark/extractors/opendataloader/extractor.py#L127-L189)), which **never sets `tables`** — it always defaults to `tables=[]`. Verified against `outputs/.../native_1.json`, which has a top-level `"kids"` key and no `"pages"` key. |
| Docling | **Real** | `document.tables` (TableFormer model output) is mapped via `_build_table()` ([docling/extractor.py:147-154, 339-363](src/pdf_extraction_benchmark/extractors/docling/extractor.py#L339-L363)). |

### Concrete example — `data/raw/native/native_1.pdf`

All four extractors reported `table_count = 0` for this document, because
`native_1.pdf` (a short text/letter-style sample) contains no tables that Docling's
TableFormer detects, **and** PyMuPDF/PaddleOCR/OpenDataLoader cannot report tables at
all regardless of document content.

**Demo risk: HIGH.** "Table Count" is structurally a placeholder for 3 of 4
extractors — it can **never** be anything but 0 for PyMuPDF, PaddleOCR, and (with the
currently-installed OpenDataLoader output schema) OpenDataLoader. Only Docling's value
is meaningful. In `_build_best_per_category()`, "Most Tables Extracted" is `max(rows,
key=lambda row: row["table_count"])` — on a document with no tables, this resolves to
whichever extractor appears first with `table_count == 0` (effectively arbitrary), and
even on a document *with* tables, it will only ever credit Docling (or a 0-way tie).
This metric should either be removed for the other three extractors or clearly labeled
"Docling only — not supported by other extractors."

---

## 8. Image Count

**Code path:**
```python
image_count = sum(
    int(result.metadata.extra.get("image_count", 0)) if result.metadata else 0
    for result in results
)
if image_count == 0:
    image_count = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", markdown_text))
```

| Extractor | Real or placeholder | Detail |
|---|---|---|
| PyMuPDF | **Real** | `metadata.extra["image_count"] = len(page.get_images(full=True))` ([pymupdf/extractor.py:69,93](src/pdf_extraction_benchmark/extractors/pymupdf/extractor.py#L69)) — counts embedded image XObjects per page. |
| OpenDataLoader | **Real, but indirect** | No `image_count` in metadata → falls back to counting `![...](...)` references in OpenDataLoader's own generated markdown file. Reflects whatever images OpenDataLoader chose to embed in its markdown export. |
| Docling | **Real, but indirect** | Same fallback — counts `![...](...)` in `document.export_to_markdown()` output. |
| PaddleOCR | **Misleading (synthetic)** | PaddleOCR never sets `image_count`, and its markdown (`_build_markdown_from_results`) contains no image links from OCR itself. For **scanned PDFs**, `app.py` (`_build_scanned_page_image_markdown`, lines ~259-300) injects one `![...]()` link **per page** pointing to a rendered full-page PNG **for UI preview purposes**. The fallback regex then counts these synthetic preview images, so `image_count` for PaddleOCR on a scanned doc ≈ **page count**, not "images detected by PaddleOCR." |

### Concrete example — `data/raw/native/native_1.pdf`
All four extractors reported `image_count = 0`: PyMuPDF found 0 embedded XObjects
(confirmed via `page.get_images(full=True)` returning empty for all 3 pages), and the
generated markdown for OpenDataLoader/Docling contained no `![...]()` references
(`grep -c '!\[' result.md` → 0 for both).

**Demo risk: HIGH** for PaddleOCR on scanned documents. The number shown is **not**
"images found in the document" — it's "number of pages," because of the app's own
full-page-preview injection. Showing this next to PyMuPDF's genuinely-counted
`image_count` invites a false comparison (e.g., a 5-page scanned PDF would show
PaddleOCR `image_count = 5` vs. PyMuPDF `image_count = 0`, implying PaddleOCR "found 5
images" when really the app just rendered 5 page previews).

---

## 9. Markdown Support

**Code path:** Static lookup, `EXTRACTOR_CAPABILITIES[extractor_name]["markdown_support"]`
(app.py `EXTRACTOR_CAPABILITIES` dict, hardcoded constants).

| Extractor | Value | Basis |
|---|---|---|
| OpenDataLoader | `True` | Produces a native `.md` export (`opendataloader_pdf.convert(..., format="json,markdown")`). |
| PyMuPDF | `False` | No native markdown export; app builds plain joined text. |
| Docling | `True` | `document.export_to_markdown()` is a first-class Docling API. |
| PaddleOCR | `False` | No native markdown export; app builds plain joined text. |

**Real or placeholder:** **Static capability flag — not computed from the uploaded
document at all.** It is the same for every document, every run.

**Correctness:** Reasonably accurate as a description of each tool's *capabilities*,
but it is a hardcoded label, not a measurement.

**Demo risk:** Low-to-medium. Fine as a "capability reference" column, but it could be
misread as "this extractor produced markdown for *this* document" when it's really a
constant from a Python dict.

---

## 10. Layout Preservation Support

**Code path:** Static lookup,
`EXTRACTOR_CAPABILITIES[extractor_name]["layout_preservation_support"]` (same dict as
above).

| Extractor | Value | Basis (subjective) |
|---|---|---|
| OpenDataLoader | `True` | Structured block/heading layout in output. |
| PyMuPDF | `True` | Per-block bounding boxes preserve coordinate layout (`metadata.extra["layout_preservation"] = "basic"`). |
| Docling | `True` | Layout-aware model with reading order + tables (`"layout_preservation": "docling_markdown"`). |
| PaddleOCR | `False` | OCR text lines with bounding boxes but no structural/reading-order reconstruction (`"layout_preservation": "ocr_boxes"`). |

**Real or placeholder:** **Static capability flag**, identical across all documents —
same caveat as Markdown Support.

**Correctness:** This is a **judgment call**, not a measured property. PaddleOCR does
return per-line bounding boxes (`"layout_preservation": "ocr_boxes"` in its own
metadata), which arguably is *some* layout information — the `False` here reflects "no
structural reconstruction," a reasonable but debatable threshold.

In `_build_best_per_category()`, "Best Layout Preservation" is computed as:
```python
layout_rows = [row for row in successful_rows if row.get("layout_preservation_support")]
best["Best Layout Preservation"] = max(layout_rows, key=lambda row: row["char_count"])["extractor"]
```
i.e., among the three extractors statically flagged `True`, pick whichever produced
the most characters. This conflates "has layout preservation capability" (static) with
"produced more text" (dynamic, unrelated to layout quality).

**Demo risk:** Medium. Both the underlying flag and the "Best Layout Preservation"
derivation are approximations/judgment calls rather than measurements.

---

## Summary Table

| Metric | Valid | Approximate | Placeholder | Notes |
|---|---|---|---|---|
| Extraction Time | ✅ | ✅ | | Real wall-clock time, but Docling/OpenDataLoader include disk I/O the others don't — not perfectly apples-to-apples. |
| Character Count | ✅ | | | Real, correct `len()` of extracted text for all 4 extractors. |
| Word Count | ✅ | ✅ | | Real, but whitespace-based `.split()` undercounts for CJK/Devanagari (multilingual PaddleOCR mode). |
| CER | | ✅ | | Real Levenshtein computation, but **relative to a pseudo-reference** (longest-text extractor), not ground truth. Reference always shows `0.0`. |
| WER | | ✅ | | Same as CER — relative metric, not absolute accuracy. |
| Bounding Box Count | ✅ | ✅ | | All real, but each tool defines "bounding box" at a different granularity (block/line/item/content-block) — not directly comparable. |
| Table Count | | | ✅ (3 of 4) | Real only for **Docling**. PyMuPDF and PaddleOCR hardcode `tables=[]`; OpenDataLoader's table-extraction code path is dead given the actual "kids"-schema JSON output (always `tables=[]` in practice). |
| Image Count | | ✅ | ✅ (PaddleOCR/scanned) | Real for PyMuPDF (`page.get_images`). Indirect-but-real for OpenDataLoader/Docling (markdown image refs). For PaddleOCR on scanned docs, counts **synthetic full-page preview images injected by the app**, not extractor-detected images. |
| Markdown Support | ✅ | | ✅ | Accurate as a static capability label, but hardcoded — not computed per document. |
| Layout Preservation Support | | ✅ | ✅ | Hardcoded judgment-call flag; "Best Layout Preservation" derivation conflates this static flag with dynamic character count. |

### Metrics that should NOT be shown as-is during a demo

1. **CER / WER "Lowest" in the Best-Tool-Per-Category card** — structurally tautological
   (always favors the pseudo-reference extractor). Either remove these two entries from
   the Best-Tool card, or visibly label them "vs. pseudo-reference, not ground truth"
   directly on the card (not just in a caption above the table).
2. **Table Count for PyMuPDF, PaddleOCR, and OpenDataLoader** — always 0 by
   construction, regardless of document content. Either hide this column for those
   three extractors or annotate it "not supported."
3. **Image Count for PaddleOCR on scanned documents** — currently reports the number of
   synthetic page-preview images the app itself generated, which can be confused with
   "images detected in the document."

---

## GitHub

This report is a documentation-only addition (`metric_validation_report.md`); no
application code was changed during this audit. Committed and pushed to `main`.
