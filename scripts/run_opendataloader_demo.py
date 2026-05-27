"""Run OpenDataLoader extraction demo from terminal."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pdf_extraction_benchmark.extractors.opendataloader.extractor import OpendataloaderExtractor
from pdf_extraction_benchmark.parsers.unified_output_parser import UnifiedOutputParser
from pdf_extraction_benchmark.utils.logger import configure_logging, get_logger


def _read_text_safely(path: Path) -> str:
    """Read text with robust encoding fallbacks."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="cp1252")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1")


def main() -> None:
    """Execute OpenDataLoader extraction for a single PDF path."""
    project_root = Path(__file__).resolve().parents[1]
    configure_logging(project_root / "outputs" / "logs")
    logger = get_logger(__name__)

    if len(sys.argv) < 2:
        print("Usage: python scripts/run_opendataloader_demo.py <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1]).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    extractor = OpendataloaderExtractor()
    results = extractor.extract(pdf_path=pdf_path, output_dir=project_root / "outputs")

    parser = UnifiedOutputParser()
    payload = parser.to_json_payload(results)

    json_out = project_root / "outputs" / "json" / f"{pdf_path.stem}.json"
    md_source = project_root / "outputs" / f"{pdf_path.stem}.md"
    md_out = project_root / "outputs" / "markdown" / f"{pdf_path.stem}.md"

    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    markdown_text = _read_text_safely(md_source) if md_source.exists() else "\n\n".join(
        result.extracted_text for result in results
    )
    md_out.write_text(markdown_text, encoding="utf-8")

    logger.info("Saved JSON output to %s", json_out)
    logger.info("Saved Markdown output to %s", md_out)

    print("OpenDataLoader Demo Summary")
    print(f"- Input PDF: {pdf_path}")
    print(f"- Pages extracted: {len(results)}")
    print(f"- JSON output: {json_out}")
    print(f"- Markdown output: {md_out}")


if __name__ == "__main__":
    main()
