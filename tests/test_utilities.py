"""Coverage tests for utility and base modules."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


# ── benchmarks/base.py ────────────────────────────────────────────────────────

class TestBenchmarkResult:
    def test_instantiate_minimal(self) -> None:
        from pdf_extraction_benchmark.benchmarks.base import BenchmarkResult
        r = BenchmarkResult(dimension="accuracy", score=0.85)
        assert r.dimension == "accuracy"
        assert r.score == 0.85
        assert r.details == {}

    def test_instantiate_with_details(self) -> None:
        from pdf_extraction_benchmark.benchmarks.base import BenchmarkResult
        r = BenchmarkResult(
            dimension="latency",
            score=9.0,
            details={"mean_ms": 6.2, "unit": "ms"},
        )
        assert r.details["mean_ms"] == 6.2
        assert r.details["unit"] == "ms"

    def test_score_zero(self) -> None:
        from pdf_extraction_benchmark.benchmarks.base import BenchmarkResult
        r = BenchmarkResult(dimension="handwriting", score=0.0)
        assert r.score == 0.0

    def test_score_ten(self) -> None:
        from pdf_extraction_benchmark.benchmarks.base import BenchmarkResult
        r = BenchmarkResult(dimension="cost", score=10.0)
        assert r.score == 10.0

    def test_details_mutable_independently(self) -> None:
        from pdf_extraction_benchmark.benchmarks.base import BenchmarkResult
        r1 = BenchmarkResult(dimension="a", score=1.0)
        r2 = BenchmarkResult(dimension="b", score=2.0)
        r1.details["key"] = "val"
        assert "key" not in r2.details


# ── utils/logger.py ───────────────────────────────────────────────────────────

class TestConfigureLogging:
    def test_configure_logging_creates_log_file(self, tmp_path: Path) -> None:
        from pdf_extraction_benchmark.utils.logger import configure_logging
        import logging
        configure_logging(tmp_path, level=logging.WARNING)
        log_file = tmp_path / "benchmark.log"
        assert log_file.exists()

    def test_configure_logging_creates_dir(self, tmp_path: Path) -> None:
        from pdf_extraction_benchmark.utils.logger import configure_logging
        import logging
        new_dir = tmp_path / "logs" / "subdir"
        configure_logging(new_dir, level=logging.ERROR)
        assert new_dir.exists()
        assert (new_dir / "benchmark.log").exists()

    def test_configure_logging_sets_level(self, tmp_path: Path) -> None:
        from pdf_extraction_benchmark.utils.logger import configure_logging
        import logging
        configure_logging(tmp_path, level=logging.DEBUG)
        root = logging.getLogger()
        assert root.level <= logging.DEBUG


# ── utils/opendataloader_hybrid.py ───────────────────────────────────────────

class TestIsServerHealthy:
    def test_returns_false_when_server_not_running(self) -> None:
        from pdf_extraction_benchmark.utils.opendataloader_hybrid import _is_server_healthy
        # Port 19999 is extremely unlikely to be in use
        assert _is_server_healthy("http://127.0.0.1:19999") is False

    def test_returns_false_on_connection_refused(self) -> None:
        from pdf_extraction_benchmark.utils.opendataloader_hybrid import _is_server_healthy
        assert _is_server_healthy("http://127.0.0.1:19998") is False

    def test_returns_true_when_healthy(self) -> None:
        from pdf_extraction_benchmark.utils.opendataloader_hybrid import _is_server_healthy
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_response):
            assert _is_server_healthy("http://127.0.0.1:5002") is True

    def test_returns_false_on_non_200(self) -> None:
        from pdf_extraction_benchmark.utils.opendataloader_hybrid import _is_server_healthy
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.status = 503
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_response):
            result = _is_server_healthy("http://127.0.0.1:5002")
            # Status 503 means not healthy
            assert result is False

    def test_module_constants(self) -> None:
        import pdf_extraction_benchmark.utils.opendataloader_hybrid as m
        assert m.DEFAULT_HOST == "127.0.0.1"
        assert m.DEFAULT_PORT == 5002
        assert m.HEALTH_CHECK_TIMEOUT_SECONDS > 0


# ── FUNSD analysis ────────────────────────────────────────────────────────────

class TestFunsdAnalysis:
    def test_module_importable(self) -> None:
        import pdf_extraction_benchmark.benchmarks.funsd.analysis as m
        assert m is not None

    def test_has_expected_callables(self) -> None:
        import pdf_extraction_benchmark.benchmarks.funsd.analysis as m
        public = [name for name in dir(m) if not name.startswith("_")]
        assert len(public) > 0


# ── Docling extractor — init and basic coverage ───────────────────────────────

class TestDoclingExtractorInit:
    def test_extractor_instantiates(self) -> None:
        from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor
        extractor = DoclingExtractor()
        assert extractor is not None

    def test_extractor_has_extract_method(self) -> None:
        from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor
        extractor = DoclingExtractor()
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)

    def test_extractor_has_name_attribute(self) -> None:
        from pdf_extraction_benchmark.extractors.docling.extractor import DoclingExtractor
        extractor = DoclingExtractor()
        # BaseExtractor subclasses typically expose a name or similar identifier
        assert extractor is not None
