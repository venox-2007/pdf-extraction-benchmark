"""Shared benchmark scoring models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class BenchmarkResult:
    """Represents the score output of one benchmark dimension."""

    dimension: str
    score: float
    details: dict[str, str | float | int] = field(default_factory=dict)
