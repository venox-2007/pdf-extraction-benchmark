"""Tests for Streamlit PaddleOCR language mode wiring."""

from __future__ import annotations

from pdf_extraction_benchmark.ui import app


class _FakePaddleExtractor:
    """Capture the PaddleOCR init kwargs passed by the UI helper."""

    calls: list[dict[str, object]] = []

    def __init__(self, **kwargs: object) -> None:
        self.__class__.calls.append(dict(kwargs))


def test_paddleocr_language_label_round_trip() -> None:
    """The UI should render human-friendly labels for both modes."""
    assert app._paddleocr_language_label("english") == "English"
    assert app._paddleocr_language_label("multilingual") == (
        "Multilingual (Hindi/Marathi/Devanagari)"
    )


def test_create_extractor_passes_selected_paddleocr_mode(monkeypatch) -> None:
    """The Streamlit helper should forward the selected PaddleOCR mode."""
    monkeypatch.setitem(app.EXTRACTOR_OPTIONS, "PaddleOCR", _FakePaddleExtractor)

    english_extractor = app._create_extractor("PaddleOCR", "english")
    multilingual_extractor = app._create_extractor("PaddleOCR", "multilingual")

    assert isinstance(english_extractor, _FakePaddleExtractor)
    assert isinstance(multilingual_extractor, _FakePaddleExtractor)
    assert _FakePaddleExtractor.calls == [
        {"language_mode": "english"},
        {"language_mode": "multilingual"},
    ]
