"""Coverage tests for modules with low automated coverage."""

from __future__ import annotations

from pathlib import Path

import pytest


# ── logger ────────────────────────────────────────────────────────────────────

class TestLogger:
    def test_get_logger_returns_logger(self) -> None:
        from pdf_extraction_benchmark.utils.logger import get_logger
        logger = get_logger("test.module")
        assert logger is not None
        assert logger.name == "test.module"

    def test_get_logger_same_name_returns_same_instance(self) -> None:
        from pdf_extraction_benchmark.utils.logger import get_logger
        a = get_logger("shared")
        b = get_logger("shared")
        assert a is b

    def test_logger_has_info_method(self) -> None:
        from pdf_extraction_benchmark.utils.logger import get_logger
        logger = get_logger("test.info")
        assert callable(logger.info)

    def test_logger_has_warning_method(self) -> None:
        from pdf_extraction_benchmark.utils.logger import get_logger
        logger = get_logger("test.warning")
        assert callable(logger.warning)

    def test_logger_info_does_not_raise(self) -> None:
        from pdf_extraction_benchmark.utils.logger import get_logger
        logger = get_logger("test.noop")
        logger.info("test message %s", "arg")  # should not raise


# ── ExtractionResult / BoundingBox / ExtractedTable models ───────────────────

class TestExtractionModels:
    def test_bounding_box_fields(self) -> None:
        from pdf_extraction_benchmark.models.extraction_result import BoundingBox
        bb = BoundingBox(x0=10.0, y0=20.0, x1=110.0, y1=70.0)
        assert bb.x0 == 10.0
        assert bb.y0 == 20.0
        assert bb.x1 == 110.0
        assert bb.y1 == 70.0

    def test_extracted_table_default_empty(self) -> None:
        from pdf_extraction_benchmark.models.extraction_result import ExtractedTable
        tbl = ExtractedTable(table_id="t1")
        assert tbl.cells == []

    def test_extraction_result_minimal(self) -> None:
        from pdf_extraction_benchmark.models.extraction_result import ExtractionResult
        result = ExtractionResult(
            tool_name="test",
            page_number=1,
            extracted_text="Hello world",
            tables=[],
            bounding_boxes=[],
            confidence_scores=[0.95],
            metadata={},
        )
        assert result.page_number == 1
        assert result.extracted_text == "Hello world"

    def test_extraction_result_empty_text(self) -> None:
        from pdf_extraction_benchmark.models.extraction_result import ExtractionResult
        result = ExtractionResult(
            tool_name="test",
            page_number=2,
            extracted_text="",
            tables=[],
            bounding_boxes=[],
            confidence_scores=[],
            metadata={},
        )
        assert result.extracted_text == ""
        assert result.page_number == 2

    def test_extraction_result_with_table(self) -> None:
        from pdf_extraction_benchmark.models.extraction_result import ExtractedTable, ExtractionResult
        tbl = ExtractedTable(table_id="t1")
        result = ExtractionResult(
            tool_name="test",
            page_number=1,
            extracted_text="",
            tables=[tbl],
            bounding_boxes=[],
            confidence_scores=[],
            metadata={},
        )
        assert len(result.tables) == 1
        assert result.tables[0].table_id == "t1"

    def test_bounding_box_in_result(self) -> None:
        from pdf_extraction_benchmark.models.extraction_result import BoundingBox, ExtractionResult
        bb = BoundingBox(x0=0.0, y0=0.0, x1=100.0, y1=50.0)
        result = ExtractionResult(
            tool_name="test",
            page_number=1,
            extracted_text="word",
            tables=[],
            bounding_boxes=[bb],
            confidence_scores=[0.9],
            metadata={},
        )
        assert len(result.bounding_boxes) == 1


# ── BaseExtractor interface ───────────────────────────────────────────────────

class TestBaseExtractor:
    def test_base_extractor_is_abstract(self) -> None:
        from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor
        with pytest.raises(TypeError):
            BaseExtractor()  # type: ignore[abstract]

    def test_concrete_subclass_can_be_instantiated(self) -> None:
        from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor
        from pdf_extraction_benchmark.models.extraction_result import ExtractionResult

        class ConcreteExtractor(BaseExtractor):
            def extract(self, pdf_path: Path) -> list[ExtractionResult]:
                return []

        obj = ConcreteExtractor()
        assert isinstance(obj, BaseExtractor)
        assert obj.extract(Path("x.pdf")) == []


# ── UnifiedOutputParser ───────────────────────────────────────────────────────

class TestUnifiedOutputParser:
    def test_parser_importable(self) -> None:
        from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser
        assert UnifiedOutputParser is not None

    def test_parser_instantiates(self) -> None:
        from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser
        p = UnifiedOutputParser()
        assert p is not None


# ── reports.aggregation ───────────────────────────────────────────────────────

class TestAggregation:
    def test_compute_aggregate_summary_importable(self) -> None:
        from pdf_extraction_benchmark.reports.aggregation import compute_aggregate_summary
        assert callable(compute_aggregate_summary)

    def test_build_report_rows_importable(self) -> None:
        from pdf_extraction_benchmark.reports.aggregation import build_report_rows
        assert callable(build_report_rows)

    def test_empty_aggregate_summary_constant(self) -> None:
        from pdf_extraction_benchmark.reports.aggregation import EMPTY_AGGREGATE_SUMMARY
        assert isinstance(EMPTY_AGGREGATE_SUMMARY, dict)

    def test_compute_per_extractor_summary_callable(self) -> None:
        from pdf_extraction_benchmark.reports.aggregation import compute_per_extractor_summary
        assert callable(compute_per_extractor_summary)


# ── reports.native_vs_scanned ─────────────────────────────────────────────────

class TestNativeVsScanned:
    def test_module_importable(self) -> None:
        import pdf_extraction_benchmark.reports.native_vs_scanned as m
        assert m is not None


# ── FUNSD benchmark metrics ───────────────────────────────────────────────────

class TestFunsdMetrics:
    def test_cer_identical_strings(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import character_error_rate
        assert character_error_rate("hello", "hello") == pytest.approx(0.0)

    def test_cer_completely_different(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import character_error_rate
        cer = character_error_rate("abc", "xyz")
        assert isinstance(cer, float)
        assert cer >= 0.0

    def test_cer_partial_match(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import character_error_rate
        cer = character_error_rate("hello world", "hello earth")
        assert 0.0 < cer < 1.5

    def test_wer_identical_strings(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import word_error_rate
        assert word_error_rate("hello world", "hello world") == pytest.approx(0.0)

    def test_wer_single_substitution(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import word_error_rate
        wer = word_error_rate("hello world", "hello earth")
        assert wer == pytest.approx(0.5)

    def test_wer_completely_different(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import word_error_rate
        wer = word_error_rate("a b c", "x y z")
        assert isinstance(wer, float)
        assert wer >= 0.0

    def test_token_f1_returns_float(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import token_f1
        result = token_f1(["a", "b", "c"], ["a", "b", "c"])
        assert isinstance(result, float)

    def test_token_f1_perfect_match(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import token_f1
        f1 = token_f1(["a", "b", "c"], ["a", "b", "c"])
        assert f1 == pytest.approx(1.0)

    def test_token_f1_no_overlap(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import token_f1
        f1 = token_f1(["x", "y"], ["a", "b"])
        assert f1 == pytest.approx(0.0)

    def test_token_f1_empty_hypothesis(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import token_f1
        f1 = token_f1(["a", "b"], [])
        assert f1 == pytest.approx(0.0)

    def test_token_f1_empty_reference(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import token_f1
        f1 = token_f1([], ["a", "b"])
        assert f1 == pytest.approx(0.0)

    def test_token_f1_partial_overlap(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.metrics import token_f1
        f1 = token_f1(["a", "b", "c"], ["a", "b", "x"])
        assert 0.0 < f1 < 1.0


# ── RVL-CDIP benchmark init ───────────────────────────────────────────────────

class TestRvlCdipBenchmark:
    def test_pipeline_init_no_args(self) -> None:
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
        pipeline = RvlCdipBenchmarkPipeline()
        assert pipeline is not None

    def test_pipeline_init_with_dirs(self, tmp_path: Path) -> None:
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
        pipeline = RvlCdipBenchmarkPipeline(
            dataset_dir=tmp_path,
            output_dir=tmp_path / "out",
            extractors={},
        )
        assert pipeline is not None

    def test_pipeline_has_run_method(self) -> None:
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
        pipeline = RvlCdipBenchmarkPipeline()
        assert hasattr(pipeline, "run")
        assert callable(pipeline.run)


# ── Docling benchmark init ────────────────────────────────────────────────────

class TestDoclingBenchmark:
    def test_pipeline_init_no_args(self) -> None:
        from pdf_extraction_benchmark.benchmarks.docling.benchmark import DoclingBenchmarkPipeline
        pipeline = DoclingBenchmarkPipeline()
        assert pipeline is not None

    def test_pipeline_init_with_dirs(self, tmp_path: Path) -> None:
        from pdf_extraction_benchmark.benchmarks.docling.benchmark import DoclingBenchmarkPipeline
        pipeline = DoclingBenchmarkPipeline(
            dataset_dir=tmp_path,
            output_dir=tmp_path / "out",
        )
        assert pipeline is not None

    def test_pipeline_has_run_method(self) -> None:
        from pdf_extraction_benchmark.benchmarks.docling.benchmark import DoclingBenchmarkPipeline
        pipeline = DoclingBenchmarkPipeline()
        assert hasattr(pipeline, "run")


# ── FUNSD benchmark pipeline ──────────────────────────────────────────────────

class TestFunsdBenchmarkPipeline:
    def test_pipeline_init_no_args(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline
        pipeline = FunsdBenchmarkPipeline()
        assert pipeline is not None

    def test_pipeline_init_with_ocr_runner(self, tmp_path: Path) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline

        def fake_ocr(path: Path) -> str:
            return "fake text"

        pipeline = FunsdBenchmarkPipeline(
            dataset_dir=tmp_path,
            output_dir=tmp_path / "out",
            ocr_runner=fake_ocr,
        )
        assert pipeline is not None

    def test_character_error_rate_static(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline
        cer = FunsdBenchmarkPipeline.character_error_rate("hello", "hello")
        assert cer == pytest.approx(0.0)

    def test_word_error_rate_static(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline
        wer = FunsdBenchmarkPipeline.word_error_rate("a b c", "a b c")
        assert wer == pytest.approx(0.0)

    def test_word_error_rate_mismatch(self) -> None:
        from pdf_extraction_benchmark.benchmarks.funsd.benchmark import FunsdBenchmarkPipeline
        wer = FunsdBenchmarkPipeline.word_error_rate("hello world", "hello earth")
        assert wer == pytest.approx(0.5)
