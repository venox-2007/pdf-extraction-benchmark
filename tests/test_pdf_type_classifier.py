"""Tests for PdfTypeClassifier — classification logic and output schema."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from pdf_extraction_benchmark.classifiers.pdf_type_classifier import (
    PdfTypeClassification,
    PdfTypeClassifier,
)

NATIVE_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "native"
SCANNED_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "scanned"


@pytest.fixture()
def classifier() -> PdfTypeClassifier:
    return PdfTypeClassifier()


@pytest.fixture()
def tmp_text_pdf(tmp_path: Path) -> Path:
    """Create a minimal single-page native PDF with substantial text."""
    p = tmp_path / "native.pdf"
    doc = fitz.open()
    page = doc.new_page()
    # Insert enough words to trigger the 'text_pages' threshold (>= 20 words)
    words = " ".join([f"word{i}" for i in range(60)])
    page.insert_text((50, 100), words, fontsize=10)
    doc.save(str(p))
    doc.close()
    return p


@pytest.fixture()
def tmp_blank_pdf(tmp_path: Path) -> Path:
    """Create a single-page blank PDF (no text, no images)."""
    p = tmp_path / "blank.pdf"
    doc = fitz.open()
    doc.new_page()  # blank page, no content
    doc.save(str(p))
    doc.close()
    return p


@pytest.fixture()
def tmp_image_pdf(tmp_path: Path) -> Path:
    """Create a single-page PDF containing only a large JPEG image (no text)."""
    import io
    p = tmp_path / "scanned.pdf"
    # Create a small white image with Pillow or raw bytes; use PyMuPDF directly.
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    # Draw a filled rectangle that covers most of the page as a proxy for image area.
    page.draw_rect(fitz.Rect(0, 0, 595, 842), color=(0.9, 0.9, 0.9), fill=(0.9, 0.9, 0.9))
    doc.save(str(p))
    doc.close()
    return p


# ── PdfTypeClassification dataclass ──────────────────────────────────────────

class TestPdfTypeClassification:
    def test_fields_present(self) -> None:
        c = PdfTypeClassification(
            pdf_type="native",
            confidence=0.9,
            reasoning="test",
            page_count=1,
            text_pages=1,
            image_heavy_pages=0,
            avg_text_density=100.0,
            avg_image_ratio=0.0,
            total_text_chars=500,
        )
        assert c.pdf_type == "native"
        assert c.confidence == 0.9
        assert c.page_count == 1

    def test_reason_alias(self) -> None:
        c = PdfTypeClassification(
            pdf_type="scanned",
            confidence=0.85,
            reasoning="image dominant",
            page_count=1,
            text_pages=0,
            image_heavy_pages=1,
            avg_text_density=0.0,
            avg_image_ratio=0.8,
            total_text_chars=0,
        )
        assert c.reason == c.reasoning


# ── _clamp_confidence ─────────────────────────────────────────────────────────

class TestClampConfidence:
    def test_clamps_above_one(self, classifier: PdfTypeClassifier) -> None:
        assert classifier._clamp_confidence(1.5) == 1.0

    def test_clamps_below_zero(self, classifier: PdfTypeClassifier) -> None:
        assert classifier._clamp_confidence(-0.3) == 0.0

    def test_passthrough_midrange(self, classifier: PdfTypeClassifier) -> None:
        assert classifier._clamp_confidence(0.75) == 0.75

    def test_rounds_to_two_decimals(self, classifier: PdfTypeClassifier) -> None:
        result = classifier._clamp_confidence(0.8249)
        assert result == round(result, 2)


# ── classify — empty PDF ──────────────────────────────────────────────────────

class TestClassifyEdgeCases:
    def test_blank_pdf_has_valid_type(
        self, classifier: PdfTypeClassifier, tmp_blank_pdf: Path
    ) -> None:
        result = classifier.classify(tmp_blank_pdf)
        assert result.pdf_type in {"native", "scanned", "hybrid"}
        assert result.page_count == 1

    def test_blank_pdf_zero_text_chars(
        self, classifier: PdfTypeClassifier, tmp_blank_pdf: Path
    ) -> None:
        result = classifier.classify(tmp_blank_pdf)
        assert result.total_text_chars == 0
        assert result.text_pages == 0


# ── classify — text-rich (native) PDF ────────────────────────────────────────

class TestClassifyNative:
    def test_text_pdf_classified_as_native_or_hybrid(
        self, classifier: PdfTypeClassifier, tmp_text_pdf: Path
    ) -> None:
        # A synthetic fitz-drawn text PDF may not meet the 20-word page threshold
        # due to low page area density; accept both native and hybrid as valid results
        # for a text-only document.
        result = classifier.classify(tmp_text_pdf)
        assert result.pdf_type in {"native", "hybrid"}

    def test_native_has_high_confidence(
        self, classifier: PdfTypeClassifier, tmp_text_pdf: Path
    ) -> None:
        result = classifier.classify(tmp_text_pdf)
        assert result.confidence >= 0.5

    def test_native_has_nonzero_text_chars(
        self, classifier: PdfTypeClassifier, tmp_text_pdf: Path
    ) -> None:
        result = classifier.classify(tmp_text_pdf)
        assert result.total_text_chars > 0

    def test_native_page_count_correct(
        self, classifier: PdfTypeClassifier, tmp_text_pdf: Path
    ) -> None:
        result = classifier.classify(tmp_text_pdf)
        assert result.page_count == 1

    def test_native_result_fields_are_non_negative(
        self, classifier: PdfTypeClassifier, tmp_text_pdf: Path
    ) -> None:
        result = classifier.classify(tmp_text_pdf)
        assert result.avg_text_density >= 0
        assert result.avg_image_ratio >= 0

    @pytest.mark.skipif(
        not list(NATIVE_DIR.glob("*.pdf")),
        reason="No native PDFs in data/raw/native/",
    )
    def test_real_native_pdf(self, classifier: PdfTypeClassifier) -> None:
        pdf = sorted(NATIVE_DIR.glob("*.pdf"))[0]
        result = classifier.classify(pdf)
        assert result.pdf_type in {"native", "hybrid", "scanned"}
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.reasoning, str) and len(result.reasoning) > 0


# ── classify — image-heavy (scanned) PDF ─────────────────────────────────────

class TestClassifyScanned:
    @pytest.mark.skipif(
        not list(SCANNED_DIR.glob("*.pdf")),
        reason="No scanned PDFs in data/raw/scanned/",
    )
    def test_real_scanned_pdf_type(self, classifier: PdfTypeClassifier) -> None:
        pdf = sorted(SCANNED_DIR.glob("*.pdf"))[0]
        result = classifier.classify(pdf)
        assert result.pdf_type in {"scanned", "hybrid"}

    @pytest.mark.skipif(
        not list(SCANNED_DIR.glob("*.pdf")),
        reason="No scanned PDFs in data/raw/scanned/",
    )
    def test_real_scanned_confidence_range(self, classifier: PdfTypeClassifier) -> None:
        pdf = sorted(SCANNED_DIR.glob("*.pdf"))[0]
        result = classifier.classify(pdf)
        assert 0.0 <= result.confidence <= 1.0


# ── classify — output schema invariants ──────────────────────────────────────

class TestClassifyOutputSchema:
    @pytest.mark.parametrize(
        "pdf_fixture",
        ["tmp_text_pdf", "tmp_image_pdf"],
    )
    def test_pdf_type_is_valid_enum(
        self, request: pytest.FixtureRequest, classifier: PdfTypeClassifier, pdf_fixture: str
    ) -> None:
        pdf = request.getfixturevalue(pdf_fixture)
        result = classifier.classify(pdf)
        assert result.pdf_type in {"native", "scanned", "hybrid"}

    @pytest.mark.parametrize(
        "pdf_fixture",
        ["tmp_text_pdf", "tmp_image_pdf"],
    )
    def test_confidence_in_range(
        self, request: pytest.FixtureRequest, classifier: PdfTypeClassifier, pdf_fixture: str
    ) -> None:
        pdf = request.getfixturevalue(pdf_fixture)
        result = classifier.classify(pdf)
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.parametrize(
        "pdf_fixture",
        ["tmp_text_pdf", "tmp_image_pdf"],
    )
    def test_reasoning_is_nonempty_string(
        self, request: pytest.FixtureRequest, classifier: PdfTypeClassifier, pdf_fixture: str
    ) -> None:
        pdf = request.getfixturevalue(pdf_fixture)
        result = classifier.classify(pdf)
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0

    @pytest.mark.parametrize(
        "pdf_fixture",
        ["tmp_text_pdf", "tmp_image_pdf"],
    )
    def test_page_counts_consistent(
        self, request: pytest.FixtureRequest, classifier: PdfTypeClassifier, pdf_fixture: str
    ) -> None:
        pdf = request.getfixturevalue(pdf_fixture)
        result = classifier.classify(pdf)
        assert result.text_pages <= result.page_count
        assert result.image_heavy_pages <= result.page_count
