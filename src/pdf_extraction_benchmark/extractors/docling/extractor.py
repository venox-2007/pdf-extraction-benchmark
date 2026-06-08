"""Docling extractor adapter implementation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

try:  # pragma: no cover - runtime dependency ordering on Windows
    import torch  # noqa: F401
except Exception:  # pragma: no cover - best-effort preload for docling import
    torch = None  # type: ignore[assignment]

from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor
from pdf_extraction_benchmark.models.extraction_result import (
    BoundingBox,
    ExtractedTable,
    ExtractionMetadata,
    ExtractionResult,
    TableCell,
)
from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser
from pdf_extraction_benchmark.utils.logger import get_logger

try:  # pragma: no cover - optional runtime dependency
    from docling.document_converter import DocumentConverter
except ImportError:  # pragma: no cover - optional runtime dependency
    DocumentConverter = None  # type: ignore[assignment]

logger = get_logger(__name__)


def _safe_package_version(package_name: str) -> str:
    """Return a package version string or a stable fallback."""
    try:
        return package_version(package_name)
    except PackageNotFoundError:
        return "unknown"


@dataclass(slots=True)
class DoclingDocumentArtifact:
    """Raw Docling conversion outputs for one document."""

    source_path: Path
    document: Any
    exported: dict[str, Any]
    markdown: str


class DoclingExtractor(BaseExtractor):
    """Extractor adapter for Docling's structure-preserving PDF pipeline."""

    tool_name = "docling"

    def __init__(self, output_root: Path | None = None) -> None:
        self.logger = get_logger(__name__)
        if DocumentConverter is None:
            raise RuntimeError(
                "Docling is not installed. Install with: uv add docling"
            )
        self.output_root = output_root
        self._converter = DocumentConverter()

    def extract(self, pdf_path: Path) -> list[ExtractionResult]:
        """Extract page-wise text, layout, and table structure from a PDF."""
        pdf_path = pdf_path.resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"Input file not found: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise FileNotFoundError(f"Docling supports PDF input only: {pdf_path}")

        try:
            artifact = self._convert_document(pdf_path)
            results = self._build_page_results(artifact)
            self._save_outputs(artifact, results)
            return results
        except Exception as exc:  # pragma: no cover - backend/runtime variability
            self.logger.exception("Docling extraction failed for %s", pdf_path)
            raise RuntimeError(f"Docling extraction failed: {exc}") from exc

    def _convert_document(self, pdf_path: Path) -> DoclingDocumentArtifact:
        """Run Docling conversion and capture the raw document payload."""
        conversion = self._converter.convert(str(pdf_path))
        document = conversion.document
        exported = document.export_to_dict()
        markdown = document.export_to_markdown()
        return DoclingDocumentArtifact(
            source_path=pdf_path,
            document=document,
            exported=exported,
            markdown=markdown,
        )

    def _build_page_results(self, artifact: DoclingDocumentArtifact) -> list[ExtractionResult]:
        """Convert Docling pages into the unified extraction schema."""
        page_entries = artifact.exported.get("pages", {})
        text_items = artifact.exported.get("texts", [])
        table_items = getattr(artifact.document, "tables", []) or []
        page_numbers = sorted(
            {
                int(page_no)
                for page_no in page_entries.keys()
                if str(page_no).isdigit()
            }
        )
        if not page_numbers:
            page_numbers = [1]

        results: list[ExtractionResult] = []
        total_text_items = 0
        total_table_count = len(table_items)
        extraction_ts = datetime.now(UTC).isoformat()

        for page_number in page_numbers:
            page_size = page_entries.get(str(page_number), {}).get("size", {})
            page_height = float(page_size.get("height", 0.0) or 0.0)
            page_width = float(page_size.get("width", 0.0) or 0.0)

            page_text_items = [
                item
                for item in text_items
                if self._item_page_number(item) == page_number
            ]
            page_texts: list[str] = []
            page_boxes: list[BoundingBox] = []
            page_tables: list[ExtractedTable] = []

            for item in page_text_items:
                text = self._normalize_text(self._item_text(item))
                if not text:
                    continue
                bbox = self._item_bbox(item, page_height)
                if bbox is not None:
                    page_boxes.append(bbox)
                page_texts.append(text)
                total_text_items += 1

            for table_index, table in enumerate(table_items):
                if self._table_page_number(table) != page_number:
                    continue
                extracted_table = self._build_table(table, page_height, table_index)
                if extracted_table is not None:
                    page_tables.append(extracted_table)
                    if extracted_table.bbox is not None:
                        page_boxes.append(extracted_table.bbox)

            page_text = "\n".join(page_texts).strip()
            page_confidence: list[float] = []
            page_status = "ok" if page_text or page_tables else "no_text_detected"

            results.append(
                ExtractionResult(
                    tool_name=self.tool_name,
                    page_number=page_number,
                    extracted_text=page_text,
                    tables=page_tables,
                    bounding_boxes=page_boxes,
                    confidence_scores=page_confidence,
                    metadata=ExtractionMetadata(
                        source_file=artifact.source_path.name,
                        extra={
                            "status": page_status,
                            "extractor": self.tool_name,
                            "ocr_supported": True,
                            "ocr_used": True,
                            "ocr_required": True,
                            "layout_preservation": "docling_markdown",
                        "docling_version": _safe_package_version("docling"),
                        "docling_core_version": _safe_package_version(
                            "docling-core"
                        ),
                            "docling_text_item_count": len(page_text_items),
                            "docling_table_count": len(page_tables),
                            "docling_total_text_item_count": total_text_items,
                            "docling_total_table_count": total_table_count,
                            "docling_page_width": page_width,
                            "docling_page_height": page_height,
                            "extraction_timestamp": extraction_ts,
                            "total_page_count": len(page_numbers),
                            "document_markdown_length": len(artifact.markdown),
                        },
                    ),
                )
            )

        return results

    def _save_outputs(
        self,
        artifact: DoclingDocumentArtifact,
        results: list[ExtractionResult],
    ) -> None:
        """Persist result.json and result.md under outputs/docling/<document_name>/."""
        project_root = self.output_root or Path(__file__).resolve().parents[4]
        output_dir = project_root / "outputs" / "docling" / artifact.source_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)

        json_payload = UnifiedOutputParser().to_json_payload(results)
        json_payload["document_metadata"] = {
            "source_file": artifact.source_path.name,
            "page_count": len(results),
            "extractor": self.tool_name,
            "docling_version": _safe_package_version("docling"),
            "docling_core_version": _safe_package_version("docling-core"),
            "docling_markdown_length": len(artifact.markdown),
        }
        json_path = output_dir / "result.json"
        md_path = output_dir / "result.md"
        json_path.write_text(
            json.dumps(json_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        md_path.write_text(self._build_markdown_report(artifact, results), encoding="utf-8")

    def _build_markdown_report(
        self,
        artifact: DoclingDocumentArtifact,
        results: list[ExtractionResult],
    ) -> str:
        """Render a stakeholder-friendly extraction report."""
        lines = [
            "# Docling Extraction Report",
            "",
            f"- Source file: `{artifact.source_path.name}`",
            f"- Pages: {len(results)}",
            f"- Docling version: `{_safe_package_version('docling')}`",
            f"- Docling Core version: `{_safe_package_version('docling-core')}`",
            "",
            "## Document Markdown",
            "",
            artifact.markdown.strip() or "_No markdown produced._",
            "",
            "## Page Summary",
            "",
        ]
        for result in results:
            extra = result.metadata.extra if result.metadata else {}
            lines.extend(
                [
                    f"### Page {result.page_number}",
                    "",
                    f"- Status: `{extra.get('status', '')}`",
                    f"- Text items: {extra.get('docling_text_item_count', 0)}",
                    f"- Tables: {extra.get('docling_table_count', 0)}",
                    f"- Bounding boxes: {len(result.bounding_boxes)}",
                    "",
                    "```text",
                    result.extracted_text or "",
                    "```",
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    def _item_page_number(self, item: dict[str, Any]) -> int | None:
        """Return the page number for an exported Docling item."""
        prov = item.get("prov", [])
        if not prov:
            return None
        first = prov[0]
        page_no = first.get("page_no")
        if isinstance(page_no, int):
            return page_no
        try:
            return int(page_no)
        except (TypeError, ValueError):
            return None

    def _table_page_number(self, table: Any) -> int | None:
        """Return the page number for a Docling table item."""
        prov = getattr(table, "prov", None) or []
        if not prov:
            return None
        first = prov[0]
        page_no = getattr(first, "page_no", None)
        if isinstance(page_no, int):
            return page_no
        try:
            return int(page_no)
        except (TypeError, ValueError):
            return None

    def _item_text(self, item: dict[str, Any]) -> str:
        """Extract text from a Docling export item."""
        text = item.get("text") or item.get("orig") or ""
        return str(text).strip()

    def _item_bbox(self, item: dict[str, Any], page_height: float) -> BoundingBox | None:
        """Convert a Docling provenance bbox into the unified schema."""
        prov = item.get("prov", [])
        if not prov:
            return None
        bbox = prov[0].get("bbox")
        return self._bbox_from_docling(bbox, page_height)

    def _table_bbox(self, table: Any, page_height: float) -> BoundingBox | None:
        """Convert a Docling table provenance bbox into the unified schema."""
        prov = getattr(table, "prov", None) or []
        if not prov:
            return None
        bbox = getattr(prov[0], "bbox", None)
        return self._bbox_from_docling(bbox, page_height)

    def _bbox_from_docling(self, bbox: Any, page_height: float) -> BoundingBox | None:
        """Convert a Docling bottom-left bbox into top-left page coordinates."""
        if bbox is None:
            return None
        try:
            if isinstance(bbox, dict):
                left = float(bbox["l"])
                top = float(bbox["t"])
                right = float(bbox["r"])
                bottom = float(bbox["b"])
            else:
                left = float(bbox.l)
                top = float(bbox.t)
                right = float(bbox.r)
                bottom = float(bbox.b)
        except (TypeError, ValueError, AttributeError, KeyError):
            return None
        if page_height <= 0:
            return None
        return BoundingBox(
            x0=left,
            y0=page_height - top,
            x1=right,
            y1=page_height - bottom,
        )

    def _build_table(
        self,
        table: Any,
        page_height: float,
        table_index: int,
    ) -> ExtractedTable | None:
        """Convert a Docling table into the unified table schema."""
        cells: list[TableCell] = []
        data = getattr(table, "data", None)
        if data is None:
            return None

        for cell in getattr(data, "table_cells", []) or []:
            text = self._normalize_text(getattr(cell, "text", ""))
            bbox = self._bbox_from_docling(getattr(cell, "bbox", None), page_height)
            row = int(getattr(cell, "start_row_offset_idx", 0) or 0)
            col = int(getattr(cell, "start_col_offset_idx", 0) or 0)
            cells.append(TableCell(row=row, col=col, text=text, bbox=bbox))

        if not cells:
            return None

        table_bbox = self._table_bbox(table, page_height)
        table_id = getattr(table, "self_ref", None) or f"table_{table_index + 1}"
        return ExtractedTable(table_id=str(table_id), cells=cells, bbox=table_bbox)

    def _normalize_text(self, value: str) -> str:
        """Normalize whitespace in extracted text."""
        return " ".join(str(value).split()).strip()
