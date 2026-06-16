"""Hybrid PDF image extraction.

Strategy
--------
* **Scanned PDFs** — Approach A: enumerate image XObjects via
  ``page.get_images()`` and decode each raster directly.  One XObject per
  figure, lossless round-trip, exact bounding box.

* **Native / hybrid PDFs** — Approach B: detect non-text visual regions by
  combining image-XObject positions with clustered PDF drawing paths
  (``page.get_drawings()``), then render each discovered region with
  ``page.get_pixmap(clip=...)``.  This captures raster images *and* vector
  content (charts, diagrams, TikZ, SVG-derived paths) that ``get_images()``
  silently misses.

Public API
----------
``extract_and_save_images(pdf_path, output_dir, pdf_type)``
    Extract all visual content and return ``list[ExtractedImage]``.

``inject_image_markdown(page_results, images, project_outputs_dir)``
    Return full-document markdown string with image references injected
    after each page's extracted text in reading order.

``attach_images_to_results(page_results, images)``
    Populate ``ExtractionResult.images`` in-place, matching on page number.
"""

from __future__ import annotations

from pathlib import Path

import fitz

from pdf_extraction_benchmark.models.extraction_result import (
    BoundingBox,
    ExtractedImage,
    ExtractionResult,
)
from pdf_extraction_benchmark.utils.logger import get_logger

logger = get_logger(__name__)

# ── tuneable constants ────────────────────────────────────────────────────────
DPI: int = 150
MIN_AREA_PTS: float = 3600.0   # 60 × 60 pt ≈ 125 × 125 px at 150 DPI
MERGE_GAP_PTS: float = 8.0    # gap within which drawing elements are merged
MAX_PAGE_FRACTION: float = 0.90  # regions covering >90 % of page area are skipped
TEXT_COVERAGE_THRESHOLD: float = 0.60  # skip regions >60 % covered by text blocks


# ── public functions ──────────────────────────────────────────────────────────


def extract_and_save_images(
    pdf_path: Path,
    output_dir: Path,
    pdf_type: str,
    *,
    dpi: int = DPI,
    min_area_pts: float = MIN_AREA_PTS,
    merge_gap_pts: float = MERGE_GAP_PTS,
) -> list[ExtractedImage]:
    """Extract visual content from a PDF and save to *output_dir* as PNGs.

    Parameters
    ----------
    pdf_path:
        Path to the source PDF.
    output_dir:
        Directory where extracted PNG files are written.
    pdf_type:
        Classification from ``PdfTypeClassifier``: ``"scanned"``,
        ``"native"``, or ``"hybrid"``.
    dpi:
        Rasterisation resolution for Approach B renders.
    min_area_pts:
        Minimum region area in PDF points² for Approach B (filters hairlines
        and decorative borders).
    merge_gap_pts:
        Gap tolerance in points for merging adjacent drawing elements.

    Returns
    -------
    list[ExtractedImage]
        One entry per extracted figure, ordered by (page_number, image_index).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    if pdf_type == "scanned":
        return _extract_xobjects(pdf_path, output_dir, dpi=dpi)
    return _extract_visual_regions(
        pdf_path,
        output_dir,
        dpi=dpi,
        min_area_pts=min_area_pts,
        merge_gap_pts=merge_gap_pts,
    )


def inject_image_markdown(
    page_results: list[ExtractionResult],
    images: list[ExtractedImage],
    project_outputs_dir: Path,
) -> str:
    """Build full-document markdown with image references after each page's text.

    Images on each page are appended after that page's extracted text in
    ascending ``image_index`` order (approximate in-page ordering by figure
    position, exact across pages).

    Parameters
    ----------
    page_results:
        Per-page extraction results in page order.
    images:
        Images returned by :func:`extract_and_save_images`.
    project_outputs_dir:
        ``project_root / "outputs"`` — used to compute relative markdown paths
        that the Streamlit UI's image resolver can find.

    Returns
    -------
    str
        Full-document markdown string.
    """
    by_page: dict[int, list[ExtractedImage]] = {}
    for img in images:
        by_page.setdefault(img.page_number, []).append(img)

    parts: list[str] = []
    for result in page_results:
        text = result.extracted_text.strip()
        if text:
            parts.append(text)

        page_imgs = sorted(
            by_page.get(result.page_number, []),
            key=lambda i: i.image_index,
        )
        for img in page_imgs:
            rel = _rel_path(img.path, project_outputs_dir)
            alt = f"Figure p{img.page_number}_{img.image_index}"
            parts.append(f"![{alt}]({rel})")

    return "\n\n".join(parts)


def attach_images_to_results(
    page_results: list[ExtractionResult],
    images: list[ExtractedImage],
) -> None:
    """Populate ``ExtractionResult.images`` in-place from *images*.

    Matches images to page results by ``page_number``.  Safe to call
    multiple times (does not duplicate existing entries).
    """
    existing: set[tuple[int, int]] = set()
    for result in page_results:
        for img in result.images:
            existing.add((img.page_number, img.image_index))

    page_map: dict[int, ExtractionResult] = {r.page_number: r for r in page_results}
    for img in images:
        key = (img.page_number, img.image_index)
        if key not in existing:
            result = page_map.get(img.page_number)
            if result is not None:
                result.images.append(img)
                existing.add(key)


# ── Approach A: XObject extraction (scanned PDFs) ────────────────────────────


def _extract_xobjects(
    pdf_path: Path,
    output_dir: Path,
    dpi: int,
) -> list[ExtractedImage]:
    """Extract embedded raster image XObjects from a PDF (Approach A)."""
    results: list[ExtractedImage] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(len(doc)):
            page = doc.load_page(page_idx)
            page_number = page_idx + 1
            counter = 0
            for item in page.get_images(full=True):
                xref = item[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n > 4:  # CMYK or exotic colorspace → convert to RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    counter += 1
                    fname = f"figure_p{page_number}_{counter}.png"
                    out_path = output_dir / fname
                    pix.save(str(out_path))
                    bbox = _image_bbox(page, xref)
                    results.append(
                        ExtractedImage(
                            page_number=page_number,
                            image_index=counter,
                            path=str(out_path),
                            bbox=bbox,
                            width=pix.width,
                            height=pix.height,
                            strategy="xobject",
                        )
                    )
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "Could not extract xobject xref=%s on page %d of %s",
                        xref,
                        page_number,
                        pdf_path.name,
                    )
    return results


# ── Approach B: visual-region detection (native / hybrid PDFs) ───────────────


def _extract_visual_regions(
    pdf_path: Path,
    output_dir: Path,
    dpi: int,
    min_area_pts: float,
    merge_gap_pts: float,
) -> list[ExtractedImage]:
    """Detect and render non-text visual regions from a PDF (Approach B).

    Combines image-XObject positions with clustered PDF drawing paths so that
    both raster images and vector content (charts, diagrams, TikZ, SVG-derived
    paths) are captured.
    """
    results: list[ExtractedImage] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(len(doc)):
            page = doc.load_page(page_idx)
            page_number = page_idx + 1
            page_rect = page.rect
            page_area = page_rect.width * page_rect.height

            # ── candidate visual rectangles ───────────────────────────────────
            candidate_rects: list[fitz.Rect] = []

            # Source 1: image XObject positions (raster images embedded in PDF)
            for item in page.get_images(full=True):
                xref = item[0]
                try:
                    for r in page.get_image_rects(xref):
                        candidate_rects.append(fitz.Rect(r))
                except Exception:  # noqa: BLE001
                    pass

            # Source 2: PDF drawing operations (vector graphics)
            drawing_rects: list[fitz.Rect] = []
            for d in page.get_drawings():
                r = d.get("rect")
                if r is None:
                    continue
                fr = fitz.Rect(r)
                if fr.get_area() > 4.0:  # skip sub-pixel hairlines
                    drawing_rects.append(fr)

            if drawing_rects:
                for cluster in _merge_rects(drawing_rects, gap=merge_gap_pts):
                    # Discard elements thinner than 4 pt in either dimension
                    if cluster.height >= 4.0 and cluster.width >= 4.0:
                        candidate_rects.append(cluster)

            if not candidate_rects:
                continue

            # ── text-block positions (used to filter text-heavy regions) ──────
            text_rects: list[fitz.Rect] = [
                fitz.Rect(b["bbox"])
                for b in page.get_text("dict").get("blocks", [])
                if b.get("type") == 0
            ]

            # ── merge candidates, filter, render ─────────────────────────────
            merged = _merge_rects(candidate_rects, gap=merge_gap_pts)
            counter = 0
            for region in sorted(merged, key=lambda r: (r.y0, r.x0)):
                area = region.get_area()
                if area < min_area_pts:
                    continue
                if area > page_area * MAX_PAGE_FRACTION:
                    continue
                if _text_coverage(region, text_rects) > TEXT_COVERAGE_THRESHOLD:
                    continue

                clip = region & page_rect
                if clip.is_empty:
                    continue

                try:
                    pix = page.get_pixmap(clip=clip, dpi=dpi)
                    counter += 1
                    fname = f"figure_p{page_number}_{counter}.png"
                    out_path = output_dir / fname
                    pix.save(str(out_path))
                    bbox = BoundingBox(
                        x0=clip.x0, y0=clip.y0, x1=clip.x1, y1=clip.y1
                    )
                    results.append(
                        ExtractedImage(
                            page_number=page_number,
                            image_index=counter,
                            path=str(out_path),
                            bbox=bbox,
                            width=pix.width,
                            height=pix.height,
                            strategy="region",
                        )
                    )
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "Could not render visual region on page %d of %s",
                        page_number,
                        pdf_path.name,
                    )

    return results


# ── geometry helpers ──────────────────────────────────────────────────────────


def _merge_rects(rects: list[fitz.Rect], gap: float) -> list[fitz.Rect]:
    """Merge overlapping or near-adjacent rectangles with a *gap* tolerance.

    Iterates until no further merges are possible (union-find by repeated
    linear scan — adequate for typical figure counts per page).
    """
    if not rects:
        return []
    merged = list(rects)
    changed = True
    while changed:
        changed = False
        output: list[fitz.Rect] = []
        consumed = [False] * len(merged)
        for i, a in enumerate(merged):
            if consumed[i]:
                continue
            expanded = fitz.Rect(a.x0 - gap, a.y0 - gap, a.x1 + gap, a.y1 + gap)
            for j in range(i + 1, len(merged)):
                if consumed[j]:
                    continue
                if expanded.intersects(merged[j]):
                    a = a | merged[j]
                    expanded = fitz.Rect(
                        a.x0 - gap, a.y0 - gap, a.x1 + gap, a.y1 + gap
                    )
                    consumed[j] = True
                    changed = True
            output.append(a)
            consumed[i] = True
        merged = output
    return merged


def _text_coverage(region: fitz.Rect, text_rects: list[fitz.Rect]) -> float:
    """Return the fraction of *region* area covered by *text_rects*."""
    area = region.get_area()
    if area <= 0:
        return 1.0
    covered = sum((region & tr).get_area() for tr in text_rects)
    return covered / area


def _image_bbox(page: fitz.Page, xref: int) -> BoundingBox | None:
    """Return the first bounding box for image *xref* on *page*, or None."""
    try:
        rects = page.get_image_rects(xref)
        if rects:
            r = rects[0]
            return BoundingBox(x0=r.x0, y0=r.y0, x1=r.x1, y1=r.y1)
    except Exception:  # noqa: BLE001
        pass
    return None


def _rel_path(abs_path_str: str, project_outputs_dir: Path) -> str:
    """Return a posix path relative to *project_outputs_dir* for markdown.

    The Streamlit UI resolves image paths relative to
    ``project_root / "outputs"`` so paths of the form
    ``extracted_images/<stem>/figure_p1_1.png`` are found automatically.
    Falls back to the absolute path string when relativisation fails.
    """
    try:
        return Path(abs_path_str).relative_to(project_outputs_dir).as_posix()
    except ValueError:
        return abs_path_str
