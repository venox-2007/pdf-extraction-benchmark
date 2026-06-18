"""Mocked tests for integration-heavy modules — no live services required.

Covers:
- OpendataloaderExtractor internal helper methods (no Java needed)
- RvlCdipBenchmarkPipeline internal methods (no dataset needed)
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

# ── OpendataloaderExtractor helper methods ────────────────────────────────────


class TestOpendataloaderExtractorHelpers:
    @pytest.fixture()
    def extractor(self):
        from pdf_extraction_benchmark.extractors.opendataloader.extractor import (
            OpendataloaderExtractor,
        )
        return OpendataloaderExtractor()

    # _to_int
    def test_to_int_integer(self, extractor) -> None:
        assert extractor._to_int(5) == 5

    def test_to_int_string(self, extractor) -> None:
        assert extractor._to_int("3") == 3

    def test_to_int_none(self, extractor) -> None:
        assert extractor._to_int(None) is None

    def test_to_int_float_string(self, extractor) -> None:
        assert extractor._to_int("not_a_number") is None

    # _to_bbox — dict form
    def test_to_bbox_dict_valid(self, extractor) -> None:
        bbox = extractor._to_bbox({"x0": 0.0, "y0": 1.0, "x1": 100.0, "y1": 200.0})
        assert bbox is not None
        assert bbox.x0 == 0.0
        assert bbox.y1 == 200.0

    def test_to_bbox_dict_missing_key(self, extractor) -> None:
        assert extractor._to_bbox({"x0": 0.0, "y0": 1.0}) is None

    def test_to_bbox_dict_bad_value(self, extractor) -> None:
        assert extractor._to_bbox({"x0": "bad", "y0": 1.0, "x1": 100.0, "y1": 200.0}) is None

    # _to_bbox — list form
    def test_to_bbox_list_valid(self, extractor) -> None:
        bbox = extractor._to_bbox([10.0, 20.0, 110.0, 220.0])
        assert bbox is not None
        assert bbox.x0 == 10.0

    def test_to_bbox_list_wrong_length(self, extractor) -> None:
        assert extractor._to_bbox([10.0, 20.0]) is None

    def test_to_bbox_list_bad_value(self, extractor) -> None:
        assert extractor._to_bbox([10.0, "bad", 110.0, 220.0]) is None

    def test_to_bbox_none(self, extractor) -> None:
        assert extractor._to_bbox(None) is None

    def test_to_bbox_other_type(self, extractor) -> None:
        assert extractor._to_bbox("bbox_string") is None

    # _extract_text
    def test_extract_text_text_key(self, extractor) -> None:
        page = {"text": "Hello world"}
        assert extractor._extract_text(page) == "Hello world"

    def test_extract_text_markdown_key(self, extractor) -> None:
        page = {"markdown": "# Header"}
        assert extractor._extract_text(page) == "# Header"

    def test_extract_text_content_key(self, extractor) -> None:
        page = {"content": "Some content"}
        assert extractor._extract_text(page) == "Some content"

    def test_extract_text_blocks(self, extractor) -> None:
        page = {"blocks": [{"text": "block one"}, {"text": "block two"}]}
        result = extractor._extract_text(page)
        assert "block one" in result
        assert "block two" in result

    def test_extract_text_empty(self, extractor) -> None:
        assert extractor._extract_text({}) == ""

    def test_extract_text_whitespace_skipped(self, extractor) -> None:
        page = {"text": "   "}
        assert extractor._extract_text(page) == ""

    # _extract_bounding_boxes
    def test_extract_bounding_boxes_valid(self, extractor) -> None:
        page = {"bounding_boxes": [{"x0": 0.0, "y0": 1.0, "x1": 100.0, "y1": 200.0}]}
        boxes = extractor._extract_bounding_boxes(page)
        assert len(boxes) == 1

    def test_extract_bounding_boxes_empty(self, extractor) -> None:
        assert extractor._extract_bounding_boxes({}) == []

    def test_extract_bounding_boxes_not_list(self, extractor) -> None:
        assert extractor._extract_bounding_boxes({"bounding_boxes": "bad"}) == []

    # _extract_tables
    def test_extract_tables_empty(self, extractor) -> None:
        assert extractor._extract_tables({}) == []

    def test_extract_tables_with_cells(self, extractor) -> None:
        page = {
            "tables": [
                {
                    "id": "t1",
                    "cells": [
                        {"row": 0, "col": 0, "text": "A"},
                        {"row": 0, "col": 1, "text": "B"},
                    ],
                }
            ]
        }
        tables = extractor._extract_tables(page)
        assert len(tables) == 1
        assert tables[0].table_id == "t1"
        assert len(tables[0].cells) == 2

    def test_extract_tables_not_list(self, extractor) -> None:
        assert extractor._extract_tables({"tables": "bad"}) == []

    def test_extract_tables_with_bbox(self, extractor) -> None:
        page = {
            "tables": [
                {
                    "id": "t2",
                    "bbox": {"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 50.0},
                    "cells": [],
                }
            ]
        }
        tables = extractor._extract_tables(page)
        assert tables[0].bbox is not None

    # _map_json_to_results — pages schema
    def test_map_json_pages_schema(self, extractor, tmp_path) -> None:
        pdf_path = tmp_path / "test.pdf"
        payload = {
            "pages": [
                {"page": 1, "text": "Page one content"},
                {"page": 2, "text": "Page two content"},
            ]
        }
        results = extractor._map_json_to_results(pdf_path=pdf_path, payload=payload)
        assert len(results) == 2
        assert results[0].page_number == 1
        assert "Page one" in results[0].extracted_text

    def test_map_json_empty_pages(self, extractor, tmp_path) -> None:
        pdf_path = tmp_path / "test.pdf"
        results = extractor._map_json_to_results(pdf_path=pdf_path, payload={"pages": []})
        assert len(results) == 1
        assert results[0].extracted_text == ""

    def test_map_json_no_pages_key(self, extractor, tmp_path) -> None:
        pdf_path = tmp_path / "test.pdf"
        results = extractor._map_json_to_results(pdf_path=pdf_path, payload={})
        assert len(results) == 1

    def test_map_json_pages_with_table(self, extractor, tmp_path) -> None:
        pdf_path = tmp_path / "test.pdf"
        payload = {
            "pages": [
                {
                    "page": 1,
                    "text": "text",
                    "tables": [{"id": "t1", "cells": []}],
                }
            ]
        }
        results = extractor._map_json_to_results(pdf_path=pdf_path, payload=payload)
        assert len(results[0].tables) == 1

    # _map_kids_to_results
    def test_map_kids_basic(self, extractor, tmp_path) -> None:
        pdf_path = tmp_path / "test.pdf"
        payload = {
            "number of pages": 2,
            "kids": [
                {"page number": 1, "content": "First page text"},
                {"page number": 2, "content": "Second page text"},
            ],
        }
        results = extractor._map_kids_to_results(pdf_path=pdf_path, payload=payload)
        assert len(results) == 2
        assert "First page text" in results[0].extracted_text

    def test_map_kids_empty(self, extractor, tmp_path) -> None:
        pdf_path = tmp_path / "test.pdf"
        results = extractor._map_kids_to_results(pdf_path=pdf_path, payload={"kids": []})
        assert len(results) == 1
        assert results[0].extracted_text == ""

    def test_map_kids_skips_invalid_page_number(self, extractor, tmp_path) -> None:
        pdf_path = tmp_path / "test.pdf"
        payload = {
            "kids": [
                {"page number": 0, "content": "Should be skipped"},
                {"page number": 1, "content": "Valid"},
            ]
        }
        results = extractor._map_kids_to_results(pdf_path=pdf_path, payload=payload)
        texts = [r.extracted_text for r in results]
        assert all("Should be skipped" not in t for t in texts)

    def test_map_kids_with_bounding_box(self, extractor, tmp_path) -> None:
        pdf_path = tmp_path / "test.pdf"
        payload = {
            "kids": [
                {
                    "page number": 1,
                    "content": "text",
                    "bounding box": {"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 50.0},
                }
            ]
        }
        results = extractor._map_kids_to_results(pdf_path=pdf_path, payload=payload)
        assert len(results[0].bounding_boxes) == 1

    def test_map_json_dispatches_to_kids(self, extractor, tmp_path) -> None:
        pdf_path = tmp_path / "test.pdf"
        payload = {
            "kids": [{"page number": 1, "content": "via kids"}],
        }
        results = extractor._map_json_to_results(pdf_path=pdf_path, payload=payload)
        assert any("via kids" in r.extracted_text for r in results)

    # _read_text_safely
    def test_read_text_safely_utf8(self, extractor, tmp_path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        assert extractor._read_text_safely(f) == "hello world"

    # extract() — mock opendataloader_pdf.convert
    def test_extract_invalid_path(self, extractor, tmp_path) -> None:
        with pytest.raises(FileNotFoundError):
            extractor.extract(tmp_path / "missing.pdf")

    def test_extract_non_pdf_extension(self, extractor, tmp_path) -> None:
        f = tmp_path / "file.txt"
        f.write_bytes(b"content")
        with pytest.raises(FileNotFoundError):
            extractor.extract(f)

    def test_extract_mocked_convert(self, extractor, tmp_path) -> None:
        """Test extract() with mocked opendataloader_pdf.convert — no Java needed."""
        import fitz
        pdf_path = tmp_path / "doc.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        payload = {"pages": [{"page": 1, "text": "Mocked extraction text"}]}
        json_file = tmp_path / "doc.json"
        json_file.write_text(json.dumps(payload), encoding="utf-8")

        with patch(
            "pdf_extraction_benchmark.extractors.opendataloader.extractor.opendataloader_pdf"
        ) as mock_odl:
            mock_odl.convert = MagicMock(return_value=None)
            results = extractor.extract(pdf_path, output_dir=tmp_path)

        assert len(results) == 1
        assert "Mocked extraction text" in results[0].extracted_text


# ── _statistics_for ───────────────────────────────────────────────────────────


class TestStatisticsFor:
    def test_empty_list(self) -> None:
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import _statistics_for
        s = _statistics_for([])
        assert s.mean == 0.0
        assert s.maximum == 0.0

    def test_single_value(self) -> None:
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import _statistics_for
        s = _statistics_for([5.0])
        assert s.mean == 5.0
        assert s.minimum == 5.0
        assert s.maximum == 5.0
        assert s.stddev == 0.0

    def test_multiple_values(self) -> None:
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import _statistics_for
        s = _statistics_for([1.0, 2.0, 3.0])
        assert s.mean == pytest.approx(2.0)
        assert s.minimum == 1.0
        assert s.maximum == 3.0


# ── RvlCdipBenchmarkPipeline internal methods ────────────────────────────────


class TestRvlCdipBenchmarkInternals:
    @pytest.fixture()
    def pipeline(self, tmp_path):
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
        return RvlCdipBenchmarkPipeline(
            dataset_dir=tmp_path / "data",
            output_dir=tmp_path / "out",
            extractors={},
        )

    @pytest.fixture()
    def minimal_summary(self, tmp_path):
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import (
            RvlCdipBenchmarkSummary,
            RvlCdipCategorySummary,
            RvlCdipExtractorSummary,
            _statistics_for,
        )
        ext_summary = RvlCdipExtractorSummary(
            extractor="MockExtractor",
            documents_evaluated=2,
            documents_ok=2,
            documents_failed=0,
            success_rate=1.0,
            latency_ms=_statistics_for([100.0, 200.0]),
            word_count=_statistics_for([50.0, 60.0]),
            char_count=_statistics_for([300.0, 360.0]),
            bbox_count=_statistics_for([5.0, 6.0]),
        )
        cat_summary = RvlCdipCategorySummary(
            category="invoice",
            documents=2,
            extractor_success_rate={"MockExtractor": 1.0},
            extractor_word_count={"MockExtractor": 55.0},
        )
        return RvlCdipBenchmarkSummary(
            dataset_dir=str(tmp_path / "data"),
            output_dir=str(tmp_path / "out"),
            categories=["invoice"],
            total_documents=2,
            extractor_summaries={"MockExtractor": ext_summary},
            category_summaries={"invoice": cat_summary},
            documents=[],
        )

    def test_extractor_table_nonempty(self, pipeline, minimal_summary) -> None:
        table = pipeline._extractor_table(minimal_summary.extractor_summaries)
        assert "MockExtractor" in table
        assert "|" in table

    def test_extractor_table_empty(self, pipeline) -> None:
        result = pipeline._extractor_table({})
        assert "No extractors" in result

    def test_category_table_nonempty(self, pipeline, minimal_summary) -> None:
        table = pipeline._category_table(
            minimal_summary.category_summaries,
            ["MockExtractor"],
        )
        assert "invoice" in table

    def test_category_table_empty(self, pipeline) -> None:
        result = pipeline._category_table({}, [])
        assert "No categories" in result

    def test_build_observations_markdown(self, pipeline, minimal_summary) -> None:
        md = pipeline._build_observations_markdown(minimal_summary)
        assert "RVL-CDIP Benchmark Report" in md
        assert "Extractor Robustness" in md

    def test_build_summary_with_results(self, tmp_path) -> None:
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import (
            RvlCdipBenchmarkPipeline,
            RvlCdipDocumentResult,
        )
        from pdf_extraction_benchmark.models.extraction_result import ExtractionResult

        class MockEx:
            def extract(self, path, **kwargs):
                return [
                    ExtractionResult(
                        tool_name="mock",
                        page_number=1,
                        extracted_text="hello world foo bar",
                        tables=[],
                        bounding_boxes=[],
                        confidence_scores=[],
                        metadata=None,
                    )
                ]

        pipeline = RvlCdipBenchmarkPipeline(
            dataset_dir=tmp_path / "data",
            output_dir=tmp_path / "out",
            extractors={"Mock": MockEx()},
        )

        doc = RvlCdipDocumentResult(
            category="invoice",
            document_id="inv_01",
            pdf_path=str(tmp_path / "inv_01.pdf"),
            extractor="Mock",
            status="ok",
            page_count=1,
            word_count=4,
            char_count=18,
            layout_region_count=0,
            latency_ms=50.0,
        )
        summary = pipeline._build_summary(
            documents=[("invoice", tmp_path / "inv_01.pdf")],
            results=[doc],
            categories=["invoice"],
        )
        assert summary.total_documents == 1
        assert "Mock" in summary.extractor_summaries
        assert summary.extractor_summaries["Mock"].documents_ok == 1

    def test_write_outputs(self, tmp_path, minimal_summary) -> None:
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import (
            RvlCdipBenchmarkPipeline,
            RvlCdipDocumentResult,
        )
        pipeline = RvlCdipBenchmarkPipeline(
            dataset_dir=tmp_path / "data",
            output_dir=tmp_path / "out",
            extractors={},
        )
        doc = RvlCdipDocumentResult(
            category="invoice",
            document_id="inv_01",
            pdf_path=str(tmp_path / "inv_01.pdf"),
            extractor="Mock",
            status="ok",
            page_count=1,
            word_count=5,
            char_count=25,
            layout_region_count=0,
            latency_ms=42.0,
        )
        pipeline._write_outputs([doc], minimal_summary)
        assert (tmp_path / "out" / "rvl_cdip_results.csv").exists()
        assert (tmp_path / "out" / "rvl_cdip_summary.json").exists()
        assert (tmp_path / "out" / "benchmark_observations.md").exists()

    def test_collect_documents_with_pdfs(self, tmp_path) -> None:
        import fitz

        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline

        cat_dir = tmp_path / "data" / "invoice"
        cat_dir.mkdir(parents=True)
        for name in ["doc1.pdf", "doc2.pdf"]:
            doc = fitz.open()
            doc.new_page()
            doc.save(str(cat_dir / name))
            doc.close()

        pipeline = RvlCdipBenchmarkPipeline(
            dataset_dir=tmp_path / "data",
            output_dir=tmp_path / "out",
            extractors={},
        )
        docs = pipeline._collect_documents(None, None)
        assert len(docs) == 2
        assert all(d[0] == "invoice" for d in docs)

    def test_collect_documents_missing_dir(self, tmp_path) -> None:
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
        pipeline = RvlCdipBenchmarkPipeline(
            dataset_dir=tmp_path / "missing",
            output_dir=tmp_path / "out",
            extractors={},
        )
        with pytest.raises(FileNotFoundError):
            pipeline._collect_documents(None)

    def test_collect_documents_empty_dir(self, tmp_path) -> None:
        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
        (tmp_path / "data").mkdir()
        pipeline = RvlCdipBenchmarkPipeline(
            dataset_dir=tmp_path / "data",
            output_dir=tmp_path / "out",
            extractors={},
        )
        with pytest.raises(FileNotFoundError):
            pipeline._collect_documents(None)

    def test_evaluate_document_success(self, tmp_path) -> None:
        import fitz

        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
        from pdf_extraction_benchmark.models.extraction_result import ExtractionResult

        class FakeExtractor:
            def extract(self, path, **kwargs):
                return [
                    ExtractionResult(
                        tool_name="fake",
                        page_number=1,
                        extracted_text="hello world",
                        tables=[],
                        bounding_boxes=[],
                        confidence_scores=[],
                        metadata=None,
                    )
                ]

        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        pipeline = RvlCdipBenchmarkPipeline(
            dataset_dir=tmp_path,
            output_dir=tmp_path / "out",
            extractors={"Fake": FakeExtractor()},
        )
        result = pipeline._evaluate_document("invoice", pdf_path, "Fake", FakeExtractor())
        assert result.status == "ok"
        assert result.word_count == 2
        assert result.category == "invoice"

    def test_evaluate_document_failure(self, tmp_path) -> None:
        import fitz

        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline

        class BrokenExtractor:
            def extract(self, path, **kwargs):
                raise RuntimeError("extractor failed")

        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        pipeline = RvlCdipBenchmarkPipeline(
            dataset_dir=tmp_path,
            output_dir=tmp_path / "out",
            extractors={},
        )
        result = pipeline._evaluate_document("invoice", pdf_path, "Broken", BrokenExtractor())
        assert result.status == "error"
        assert result.error is not None

    def test_run_end_to_end_mocked(self, tmp_path) -> None:
        """Full run() with a simple fake extractor and a tiny in-memory dataset."""
        import fitz

        from pdf_extraction_benchmark.benchmarks.rvl_cdip.benchmark import RvlCdipBenchmarkPipeline
        from pdf_extraction_benchmark.models.extraction_result import ExtractionResult

        class FakeExtractor:
            def extract(self, path, **kwargs):
                return [
                    ExtractionResult(
                        tool_name="fake",
                        page_number=1,
                        extracted_text="word1 word2",
                        tables=[],
                        bounding_boxes=[],
                        confidence_scores=[],
                        metadata=None,
                    )
                ]

        cat_dir = tmp_path / "data" / "memo"
        cat_dir.mkdir(parents=True)
        pdf_path = cat_dir / "memo_01.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        pipeline = RvlCdipBenchmarkPipeline(
            dataset_dir=tmp_path / "data",
            output_dir=tmp_path / "out",
            extractors={"Fake": FakeExtractor()},
        )
        summary = pipeline.run()
        assert summary.total_documents == 1
        assert "Fake" in summary.extractor_summaries
        assert (tmp_path / "out" / "rvl_cdip_summary.json").exists()


# ── _safe_package_version (Docling benchmark) ─────────────────────────────────


class TestSafePackageVersion:
    def test_known_package(self) -> None:
        from pdf_extraction_benchmark.benchmarks.docling.benchmark import _safe_package_version
        v = _safe_package_version("docling")
        assert isinstance(v, str)
        assert len(v) > 0

    def test_unknown_package(self) -> None:
        from pdf_extraction_benchmark.benchmarks.docling.benchmark import _safe_package_version
        assert _safe_package_version("this-package-does-not-exist-xyz") == "unknown"
