"""OpenDataLoader extractor implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


class OpendataloaderExtractor(BaseExtractor):
    """Extractor adapter for OpenDataLoader PDF."""

    tool_name = "opendataloader"

    def __init__(self) -> None:
        """Initialize extractor logger."""
        self.logger = get_logger(__name__)

    def extract(self, pdf_path: Path, output_dir: Path | None = None) -> list[ExtractionResult]:
        """Extract page-level structured results from a PDF file.

        The OpenDataLoader converter writes `*.json` and `*.md` outputs to the selected
        output directory. This method parses JSON output and maps it into standardized
        `ExtractionResult` objects.
        """
        pdf_path = pdf_path.resolve()
        if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
            raise FileNotFoundError(f"Invalid PDF path: {pdf_path}")

        target_output = (output_dir or pdf_path.parent).resolve()
        target_output.mkdir(parents=True, exist_ok=True)

        self.logger.info("Starting OpenDataLoader extraction for %s", pdf_path)

        try:
            opendataloader_pdf.convert(
                input_path=str(pdf_path),
                output_dir=str(target_output),
                format="json,markdown",
            )
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

    def _map_json_to_results(self, pdf_path: Path, payload: dict[str, Any]) -> list[ExtractionResult]:
        """Map OpenDataLoader JSON payload to standardized results."""
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
