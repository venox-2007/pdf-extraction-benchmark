"""Application logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_dir: Path, level: int = logging.INFO) -> None:
    """Configure root logger with console and file handlers."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "benchmark.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger."""
    return logging.getLogger(name)
