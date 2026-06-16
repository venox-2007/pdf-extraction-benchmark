"""Unified extraction result schema used across tools."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class BoundingBox:
    """Represents a rectangular region in page coordinates."""

    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(slots=True)
class TableCell:
    """Represents one extracted table cell."""

    row: int
    col: int
    text: str
    bbox: BoundingBox | None = None


@dataclass(slots=True)
class ExtractedTable:
    """Represents one extracted table on a page."""

    table_id: str
    cells: list[TableCell] = field(default_factory=list)
    bbox: BoundingBox | None = None


@dataclass(slots=True)
class ExtractionMetadata:
    """Operational metadata for a page extraction result."""

    source_file: str
    latency_ms: float | None = None
    cost_usd: float | None = None
    extra: dict[str, str | float | int | bool] = field(default_factory=dict)


@dataclass(slots=True)
class ExtractedImage:
    """A figure, chart, or embedded image extracted from a PDF page."""

    page_number: int
    image_index: int
    path: str  # absolute path to saved PNG file (str for JSON serialisability)
    bbox: BoundingBox | None = None
    width: int = 0
    height: int = 0
    strategy: str = "region"  # "xobject" (scanned) | "region" (native/hybrid)


@dataclass(slots=True)
class ExtractionResult:
    """Unified page-level extraction payload."""

    tool_name: str
    page_number: int
    extracted_text: str
    tables: list[ExtractedTable] = field(default_factory=list)
    bounding_boxes: list[BoundingBox] = field(default_factory=list)
    confidence_scores: list[float] = field(default_factory=list)
    metadata: ExtractionMetadata | None = None
    images: list[ExtractedImage] = field(default_factory=list)
