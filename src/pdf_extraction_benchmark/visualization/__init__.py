"""Bounding box visualization helpers."""

from pdf_extraction_benchmark.visualization.bbox_overlay import (
    DEFAULT_DPI,
    MAX_VISUALIZED_PAGES,
    build_page_visualizations,
    draw_bounding_boxes,
    get_extractor_color,
    get_extractor_source_dpi,
    has_bounding_boxes,
    render_page_image,
    scale_bounding_box,
)

__all__ = [
    "DEFAULT_DPI",
    "MAX_VISUALIZED_PAGES",
    "build_page_visualizations",
    "draw_bounding_boxes",
    "get_extractor_color",
    "get_extractor_source_dpi",
    "has_bounding_boxes",
    "render_page_image",
    "scale_bounding_box",
]
