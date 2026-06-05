"""Tests for Surya extractor and benchmark integration."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from pdf_extraction_benchmark.benchmarks.surya.benchmark import SuryaBenchmarkPipeline
from pdf_extraction_benchmark.extractors.surya import runtime as surya_runtime
from pdf_extraction_benchmark.extractors.surya.extractor import SuryaExtractor
from pdf_extraction_benchmark.models.extraction_result import (
    BoundingBox,
    ExtractionMetadata,
    ExtractionResult,
)


def _fake_page_artifact() -> SimpleNamespace:
    layout_box = SimpleNamespace(label="Text", raw_label="text", position=0, count=120)
    layout_result = SimpleNamespace(bboxes=[layout_box], raw="{\"blocks\": []}", error=False)
    block = SimpleNamespace(
        polygon=[[10, 10], [100, 10], [100, 30], [10, 30]],
        confidence=0.93,
        html="<p>Hello Surya</p>",
        label="Text",
        raw_label="text",
        reading_order=0,
        skipped=False,
        error=False,
    )
    ocr_result = SimpleNamespace(blocks=[block], image_bbox=[0, 0, 200, 100])
    return SimpleNamespace(
        page_number=1,
        image=SimpleNamespace(size=(200, 100)),
        layout_result=layout_result,
        ocr_result=ocr_result,
        source_kind="image_frame",
    )


def test_surya_runtime_builds_results_and_writes_outputs(tmp_path: Path) -> None:
    """Surya runtime helpers should create schema-compatible outputs."""
    document = SimpleNamespace(
        source_path=tmp_path / "sample.png",
        backend="llamacpp",
        pages=[_fake_page_artifact()],
    )
    results = surya_runtime.build_extraction_results(document)

    assert len(results) == 1
    assert results[0].tool_name == "surya"
    assert results[0].extracted_text == "Hello Surya"
    assert len(results[0].bounding_boxes) == 1
    assert len(results[0].confidence_scores) == 1
    assert results[0].metadata is not None
    assert results[0].metadata.extra["surya_backend"] == "llamacpp"
    assert results[0].metadata.extra["surya_layout_block_count"] == 1

    json_path, md_path = surya_runtime.save_document_outputs(
        document,
        results,
        project_root=tmp_path,
    )
    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["total_pages"] == 1
    assert payload["document_metadata"]["backend"] == "llamacpp"


def test_surya_extractor_uses_runtime_helpers(tmp_path: Path, monkeypatch) -> None:
    """Extractor should delegate to the runtime helpers and persist outputs."""
    sample_path = tmp_path / "sample.png"
    sample_path.write_bytes(b"fake image bytes")
    fake_document = SimpleNamespace(
        source_path=sample_path,
        backend="llamacpp",
        pages=[_fake_page_artifact()],
    )
    fake_results = [
        ExtractionResult(
            tool_name="surya",
            page_number=1,
            extracted_text="Hello Surya",
            bounding_boxes=[BoundingBox(10, 10, 100, 30)],
            confidence_scores=[0.93],
            metadata=ExtractionMetadata(
                source_file="sample.png",
                extra={"status": "ok", "surya_backend": "llamacpp"},
            ),
        )
    ]
    called: dict[str, object] = {}

    monkeypatch.setattr(
        "pdf_extraction_benchmark.extractors.surya.extractor.run_document",
        lambda *_, **__: fake_document,
    )
    monkeypatch.setattr(
        "pdf_extraction_benchmark.extractors.surya.extractor.build_extraction_results",
        lambda document: fake_results,
    )
    monkeypatch.setattr(
        "pdf_extraction_benchmark.extractors.surya.extractor.save_document_outputs",
        lambda document, results, project_root=None: called.update(
            {
                "document": document,
                "results": results,
                "project_root": project_root,
            }
        ),
    )

    extractor = SuryaExtractor(output_root=tmp_path)
    results = extractor.extract(sample_path)

    assert results == fake_results
    assert called["project_root"] == tmp_path


def test_surya_benchmark_wrapper_writes_surya_named_outputs(tmp_path: Path, monkeypatch) -> None:
    """Surya benchmark wrapper should rename outputs and create comparison notes."""
    surya_output_dir = tmp_path / "outputs" / "benchmark_results" / "surya"
    funsd_output_dir = surya_output_dir
    comparison_dir = tmp_path / "outputs" / "benchmark_results" / "funsd"
    comparison_dir.mkdir(parents=True, exist_ok=True)
    (comparison_dir / "funsd_results.csv").write_text(
        "document_id,cer,wer,token_precision,token_recall,token_f1,token_overlap_accuracy\n"
        "doc1,0.8,0.7,0.5,0.4,0.45,0.55\n",
        encoding="utf-8",
    )

    class _DummySummary:
        total_documents = 1
        evaluated_documents = 1

    class _DummyPipeline:
        def __init__(self, *, output_dir: Path, **_: object) -> None:
            self.output_dir = output_dir

        def run(self, sample_size: int | None = None) -> _DummySummary:
            _ = sample_size
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / "funsd_results.csv").write_text(
                "document_id,cer,wer,token_precision,token_recall,token_f1,token_overlap_accuracy\n"
                "doc1,0.5,0.4,0.7,0.6,0.65,0.75\n",
                encoding="utf-8",
            )
            (self.output_dir / "funsd_summary.json").write_text(
                json.dumps({"total_documents": 1, "evaluated_documents": 1}),
                encoding="utf-8",
            )
            (self.output_dir / "benchmark_observations.md").write_text(
                "# FUNSD OCR Benchmark Report\n\nDetails.\n",
                encoding="utf-8",
            )
            return _DummySummary()

    monkeypatch.setattr(
        "pdf_extraction_benchmark.benchmarks.surya.benchmark.FunsdBenchmarkPipeline",
        _DummyPipeline,
    )

    pipeline = SuryaBenchmarkPipeline(
        output_dir=surya_output_dir,
        chart_dir=tmp_path / "outputs" / "charts" / "surya",
    )
    summary = pipeline.run()

    assert summary.total_documents == 1
    assert (funsd_output_dir / "benchmark_results.csv").exists()
    assert (funsd_output_dir / "benchmark_summary.json").exists()
    assert (funsd_output_dir / "benchmark_observations.md").exists()
    assert (funsd_output_dir / "surya_vs_paddleocr.md").exists()
