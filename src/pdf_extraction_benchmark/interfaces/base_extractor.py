"""Abstract interface for all extractor adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pdf_extraction_benchmark.models.extraction_result import ExtractionResult


class BaseExtractor(ABC):
    """Contract that all extraction tool adapters must implement."""

    tool_name: str

    @abstractmethod
    def extract(self, pdf_path: Path) -> list[ExtractionResult]:
        """Extract structured page-level results from a PDF."""
        raise NotImplementedError
