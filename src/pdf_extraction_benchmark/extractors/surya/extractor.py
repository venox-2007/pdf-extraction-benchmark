"""Surya extractor adapter implementation."""

from __future__ import annotations

from pathlib import Path

from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor
from pdf_extraction_benchmark.models.extraction_result import ExtractionResult
from pdf_extraction_benchmark.utils.logger import get_logger

from .runtime import (
    build_extraction_results,
    run_document,
    save_document_outputs,
)


class SuryaExtractor(BaseExtractor):
    """Extractor adapter for Surya's layout-aware OCR backend."""

    tool_name = "surya"

    def __init__(
        self,
        backend: str | None = None,
        render_dpi: int = 192,
        output_root: Path | None = None,
    ) -> None:
        self.logger = get_logger(__name__)
        self.backend = backend
        self.render_dpi = render_dpi
        self.output_root = output_root

    def extract(self, pdf_path: Path) -> list[ExtractionResult]:
        """Extract page-level structured results from a PDF or supported image file."""
        pdf_path = pdf_path.resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"Input file not found: {pdf_path}")

        try:
            document = run_document(
                pdf_path,
                backend=self.backend,
                render_dpi=self.render_dpi,
            )
            results = build_extraction_results(document)
            save_document_outputs(document, results, project_root=self.output_root)
            return results
        except Exception as exc:  # pragma: no cover - backend/runtime variability
            self.logger.exception("Surya extraction failed for %s", pdf_path)
            raise RuntimeError(f"Surya extraction failed: {exc}") from exc
