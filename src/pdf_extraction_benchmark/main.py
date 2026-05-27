"""Shared application entrypoint for benchmark orchestration."""

from __future__ import annotations

from pdf_extraction_benchmark.utils.logger import get_logger


def main() -> None:
    """Run a minimal benchmark scaffold pipeline."""
    logger = get_logger(__name__)
    logger.info("PDF extraction benchmark scaffold is ready.")


if __name__ == "__main__":
    main()
