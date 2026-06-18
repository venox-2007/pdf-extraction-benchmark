"""OpenDataLoader extractor implementation."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import fitz
import opendataloader_pdf

from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor
from pdf_extraction_benchmark.models.extraction_result import (
    BoundingBox,
    ExtractedTable,
    ExtractionMetadata,
    ExtractionResult,
    TableCell,
)
from pdf_extraction_benchmark.utils.logger import get_logger

# Block types in the OpenDataLoader kids schema that carry text content.
# Structural/graphical types (image, figure, table, separator, line, background,
# artifact) are excluded so their bounding boxes are never emitted as text regions.
_TEXT_BLOCK_TYPES: frozenset[str] = frozenset(
    {
        "paragraph",
        "heading",
        "text",
        "list",
        "list item",
        "caption",
        "footnote",
        "header",
        "footer",
        "title",
        "subtitle",
        "toc",
        "reference",
        "quote",
        "code",
        "formula",
        "note",
    }
)


class OpendataloaderExtractor(BaseExtractor):
    """Extractor adapter for OpenDataLoader PDF."""

    tool_name = "opendataloader"

    def __init__(self) -> None:
        """Initialize extractor logger."""
        self.logger = get_logger(__name__)

    def extract(
        self,
        pdf_path: Path,
        output_dir: Path | None = None,
        hybrid_url: str | None = None,
    ) -> list[ExtractionResult]:
        """Extract page-level structured results from a PDF file.

        The OpenDataLoader converter writes `*.json` and `*.md` outputs to the selected
        output directory. This method parses JSON output and maps it into standardized
        `ExtractionResult` objects.

        When `hybrid_url` is provided, OpenDataLoader is run in hybrid mode,
        routing every page through the Docling/OCR backend at that URL
        (`hybrid_mode="full"`) so that scanned/image-only pages produce
        extracted text. Without it, OpenDataLoader runs in its default
        Java-only (no-OCR) mode.
        """
        pdf_path = pdf_path.resolve()
        if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
            raise FileNotFoundError(f"Invalid PDF path: {pdf_path}")

        target_output = (output_dir or pdf_path.parent).resolve()
        target_output.mkdir(parents=True, exist_ok=True)

        self.logger.info("Starting OpenDataLoader extraction for %s", pdf_path)

        convert_kwargs: dict[str, Any] = {
            "input_path": str(pdf_path),
            "output_dir": str(target_output),
            "format": "json,markdown",
        }
        if hybrid_url:
            convert_kwargs.update(
                hybrid="docling-fast",
                hybrid_url=hybrid_url,
                hybrid_mode="full",
                hybrid_fallback=True,
            )

        try:
            opendataloader_pdf.convert(**convert_kwargs)
        except Exception as exc:  # pragma: no cover - external runtime dependency
            self.logger.exception("OpenDataLoader extraction failed for %s", pdf_path)
            raise RuntimeError(f"OpenDataLoader extraction failed: {exc}") from exc

        json_file = target_output / f"{pdf_path.stem}.json"
        if not json_file.exists():
            raise FileNotFoundError(f"Expected JSON output not found: {json_file}")

        payload = json.loads(self._read_text_safely(json_file))
        results = self._map_json_to_results(pdf_path=pdf_path, payload=payload)

        self.logger.info("Extraction completed: %s pages from %s", len(results), pdf_path.name)
        return results

    def _map_json_to_results(
        self, pdf_path: Path, payload: dict[str, Any]
    ) -> list[ExtractionResult]:
        """Map OpenDataLoader JSON payload to standardized results."""
        if isinstance(payload, dict):
            kids = payload.get("kids")
            if isinstance(kids, list):
                return self._map_kids_to_results(pdf_path=pdf_path, payload=payload)

        pages = payload.get("pages", []) if isinstance(payload, dict) else []
        if not isinstance(pages, list):
            pages = []

        if not pages:
            return [
                ExtractionResult(
                    tool_name=self.tool_name,
                    page_number=1,
                    extracted_text="",
                    metadata=ExtractionMetadata(
                        source_file=pdf_path.name,
                        extra={"status": "empty_output"},
                    ),
                )
            ]

        results: list[ExtractionResult] = []
        for index, page in enumerate(pages, start=1):
            if not isinstance(page, dict):
                continue

            text = self._extract_text(page)
            tables = self._extract_tables(page)
            boxes = self._extract_bounding_boxes(page)

            result = ExtractionResult(
                tool_name=self.tool_name,
                page_number=int(page.get("page", index)),
                extracted_text=text,
                tables=tables,
                bounding_boxes=boxes,
                confidence_scores=[],
                metadata=ExtractionMetadata(
                    source_file=pdf_path.name,
                    extra={"status": "ok", "page_index": index},
                ),
            )
            results.append(result)

        return results or [
            ExtractionResult(
                tool_name=self.tool_name,
                page_number=1,
                extracted_text="",
                metadata=ExtractionMetadata(
                    source_file=pdf_path.name,
                    extra={"status": "no_mappable_pages"},
                ),
            )
        ]

    def _map_kids_to_results(
        self, pdf_path: Path, payload: dict[str, Any]
    ) -> list[ExtractionResult]:
        """Map OpenDataLoader `kids` block schema into page-level extraction results."""
        raw_kids = payload.get("kids", [])
        if not isinstance(raw_kids, list):
            raw_kids = []

        page_blocks: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for block in raw_kids:
            if not isinstance(block, dict):
                continue
            page_num = self._to_int(block.get("page number"))
            if page_num is None or page_num <= 0:
                continue
            page_blocks[page_num].append(block)

        if not page_blocks:
            return [
                ExtractionResult(
                    tool_name=self.tool_name,
                    page_number=1,
                    extracted_text="",
                    metadata=ExtractionMetadata(
                        source_file=pdf_path.name,
                        extra={"status": "empty_output"},
                    ),
                )
            ]

        total_pages = self._to_int(payload.get("number of pages"))
        ordered_pages = sorted(page_blocks.keys())
        if total_pages is not None and total_pages > 0:
            ordered_pages = sorted(set(ordered_pages) | set(range(1, total_pages + 1)))

        # ODL uses PDF bottom-left coordinates; fetch page heights so we can
        # convert to top-left screen coordinates (consistent with all other extractors).
        page_heights = self._get_page_heights(pdf_path)

        results: list[ExtractionResult] = []
        for page_num in ordered_pages:
            blocks = page_blocks.get(page_num, [])
            page_height = page_heights.get(page_num, 0.0)
            text_parts: list[str] = []
            boxes: list[BoundingBox] = []

            for block in self._collect_text_blocks(blocks):
                content = block.get("content")
                if not (isinstance(content, str) and content.strip()):
                    continue
                text_parts.append(content.strip())
                box = self._to_bbox(block.get("bounding box"))
                if box is not None:
                    if page_height > 0:
                        box = self._flip_y(box, page_height)
                    boxes.append(box)

            results.append(
                ExtractionResult(
                    tool_name=self.tool_name,
                    page_number=page_num,
                    extracted_text="\n\n".join(text_parts),
                    tables=[],
                    bounding_boxes=boxes,
                    confidence_scores=[],
                    metadata=ExtractionMetadata(
                        source_file=pdf_path.name,
                        extra={"status": "ok", "schema": "kids"},
                    ),
                )
            )

        return results

    def _collect_text_blocks(
        self, blocks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Recursively collect text-bearing leaf blocks from a kids/rows/cells tree.

        Top-level text blocks (paragraph, heading, etc.) are returned directly.
        Table blocks are not returned themselves but their cell children are
        recursed into, yielding tighter per-cell paragraph bboxes instead of
        the coarse table-level box.
        """
        text_blocks: list[dict[str, Any]] = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type", "")).lower()
            if block_type == "table":
                for row in block.get("rows", []):
                    if not isinstance(row, dict):
                        continue
                    for cell in row.get("cells", []):
                        if not isinstance(cell, dict):
                            continue
                        cell_kids = cell.get("kids", [])
                        if isinstance(cell_kids, list):
                            text_blocks.extend(self._collect_text_blocks(cell_kids))
            elif not block_type or block_type in _TEXT_BLOCK_TYPES:
                text_blocks.append(block)
        return text_blocks

    def _get_page_heights(self, pdf_path: Path) -> dict[int, float]:
        """Return PDF page heights in points, keyed by 1-based page number.

        Returns an empty dict if the file cannot be opened (e.g. in unit tests
        using mock paths), in which case the caller skips the y-flip.
        """
        try:
            heights: dict[int, float] = {}
            with fitz.open(str(pdf_path)) as doc:
                for i, page in enumerate(doc, start=1):
                    heights[i] = float(page.rect.height)
            return heights
        except Exception:
            return {}

    def _flip_y(self, box: BoundingBox, page_height: float) -> BoundingBox:
        """Convert a bottom-left PDF bbox to top-left screen coordinates."""
        return BoundingBox(
            x0=box.x0,
            y0=page_height - box.y1,
            x1=box.x1,
            y1=page_height - box.y0,
        )

    def _extract_text(self, page: dict[str, Any]) -> str:
        """Extract text using common OpenDataLoader page keys."""
        for key in ("text", "markdown", "content"):
            value = page.get(key)
            if isinstance(value, str) and value.strip():
                return value

        blocks = page.get("blocks")
        if isinstance(blocks, list):
            parts: list[str] = []
            for block in blocks:
                if isinstance(block, dict):
                    text = block.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append(text)
            return "\n".join(parts)

        return ""

    def _extract_tables(self, page: dict[str, Any]) -> list[ExtractedTable]:
        """Extract table placeholders from page payload."""
        raw_tables = page.get("tables", [])
        if not isinstance(raw_tables, list):
            return []

        tables: list[ExtractedTable] = []
        for i, table in enumerate(raw_tables, start=1):
            if not isinstance(table, dict):
                continue

            cells: list[TableCell] = []
            raw_cells = table.get("cells", [])
            if isinstance(raw_cells, list):
                for cell in raw_cells:
                    if not isinstance(cell, dict):
                        continue
                    cells.append(
                        TableCell(
                            row=int(cell.get("row", 0)),
                            col=int(cell.get("col", 0)),
                            text=str(cell.get("text", "")),
                            bbox=self._to_bbox(cell.get("bbox")),
                        )
                    )

            tables.append(
                ExtractedTable(
                    table_id=str(table.get("id", f"table_{i}")),
                    cells=cells,
                    bbox=self._to_bbox(table.get("bbox")),
                )
            )

        return tables

    def _extract_bounding_boxes(self, page: dict[str, Any]) -> list[BoundingBox]:
        """Extract top-level bounding boxes where available."""
        raw_boxes = page.get("bounding_boxes", [])
        if not isinstance(raw_boxes, list):
            return []

        boxes: list[BoundingBox] = []
        for raw_box in raw_boxes:
            box = self._to_bbox(raw_box)
            if box is not None:
                boxes.append(box)
        return boxes

    def _to_bbox(self, value: Any) -> BoundingBox | None:
        """Convert generic bbox payload to `BoundingBox` when possible."""
        if isinstance(value, dict):
            keys = ("x0", "y0", "x1", "y1")
            if all(k in value for k in keys):
                try:
                    return BoundingBox(
                        x0=float(value["x0"]),
                        y0=float(value["y0"]),
                        x1=float(value["x1"]),
                        y1=float(value["y1"]),
                    )
                except (TypeError, ValueError):
                    return None

        if isinstance(value, list) and len(value) == 4:
            try:
                x0, y0, x1, y1 = [float(v) for v in value]
                return BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1)
            except (TypeError, ValueError):
                return None

        return None

    def _to_int(self, value: Any) -> int | None:
        """Safely parse integer-like values."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _read_text_safely(self, path: Path) -> str:
        """Read text with fallback decoding for Windows-encoded outputs."""
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self.logger.warning("UTF-8 decode failed for %s; falling back to cp1252.", path)
            try:
                return path.read_text(encoding="cp1252")
            except UnicodeDecodeError:
                self.logger.warning("cp1252 decode failed for %s; falling back to latin-1.", path)
                return path.read_text(encoding="latin-1")
