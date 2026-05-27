"""Detect whether a PDF is native or scanned (placeholder)."""

from __future__ import annotations

from pathlib import Path


class NativeScannedClassifier:
    """Simple heuristic classifier placeholder for PDF type detection."""

    def classify(self, pdf_path: Path) -> str:
        """Return `native` or `scanned` based on filename hint."""
        name = pdf_path.name.lower()
        if "scan" in name or "scanned" in name:
            return "scanned"
        return "native"
