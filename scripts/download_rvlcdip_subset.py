"""Prepare a 16-category x 10-document RVL-CDIP subset for the benchmark.

Reads cached .tif images from the Hugging Face hub snapshot for
vaclavpechtor/rvl_cdip-small-200 (already downloaded via `datasets`),
selects the first 10 documents per category (sorted by filename for
reproducibility), and writes:

  data/raw/rvl_cdip/<category>/originals/<category>_NN.tif  - original image
  data/raw/rvl_cdip/<category>/<category>_NN.pdf            - converted PDF

A summary report is written to data/raw/rvl_cdip/SUMMARY.md.
"""

from __future__ import annotations

import glob
import os
from pathlib import Path

from PIL import Image

CATEGORIES = [
    "advertisement",
    "budget",
    "email",
    "file_folder",
    "form",
    "handwritten",
    "invoice",
    "letter",
    "memo",
    "news_article",
    "presentation",
    "questionnaire",
    "resume",
    "scientific_publication",
    "scientific_report",
    "specification",
]

SAMPLES_PER_CATEGORY = 10

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = PROJECT_ROOT / "data" / "raw" / "rvl_cdip"

HF_CACHE_GLOB = os.path.expanduser(
    "~/.cache/huggingface/hub/datasets--vaclavpechtor--rvl_cdip-small-200/snapshots/*/train"
)


def find_snapshot_train_dir() -> Path:
    matches = glob.glob(HF_CACHE_GLOB)
    if not matches:
        raise FileNotFoundError(
            "Could not find the rvl_cdip-small-200 snapshot 'train' directory. "
            "Run `load_dataset('vaclavpechtor/rvl_cdip-small-200')` first."
        )
    return Path(matches[0])


def main() -> None:
    train_dir = find_snapshot_train_dir()
    report_rows: list[dict[str, object]] = []

    for category in CATEGORIES:
        category_dir = train_dir / category
        out_dir = OUTPUT_ROOT / category
        originals_dir = out_dir / "originals"
        out_dir.mkdir(parents=True, exist_ok=True)
        originals_dir.mkdir(parents=True, exist_ok=True)

        if not category_dir.is_dir():
            report_rows.append(
                {
                    "category": category,
                    "available": 0,
                    "extracted": 0,
                    "output_path": str(out_dir.relative_to(PROJECT_ROOT)),
                    "note": "category directory not found in snapshot",
                }
            )
            continue

        tif_files = sorted(category_dir.glob("*.tif"))
        selected = tif_files[:SAMPLES_PER_CATEGORY]

        for index, tif_path in enumerate(selected, start=1):
            name = f"{category}_{index:02d}"

            original_dest = originals_dir / f"{name}{tif_path.suffix}"
            original_dest.write_bytes(tif_path.read_bytes())

            pdf_dest = out_dir / f"{name}.pdf"
            with Image.open(tif_path) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(pdf_dest, "PDF")

        note = ""
        if len(selected) < SAMPLES_PER_CATEGORY:
            note = f"insufficient samples: only {len(selected)} available"

        report_rows.append(
            {
                "category": category,
                "available": len(tif_files),
                "extracted": len(selected),
                "output_path": str(out_dir.relative_to(PROJECT_ROOT)),
                "note": note,
            }
        )

    write_summary(report_rows)
    print_summary(report_rows)


def write_summary(rows: list[dict[str, object]]) -> None:
    total_extracted = sum(int(r["extracted"]) for r in rows)
    insufficient = [r for r in rows if r["note"]]

    lines = [
        "# RVL-CDIP Small 200 - Benchmark Subset Summary",
        "",
        "Source dataset: `vaclavpechtor/rvl_cdip-small-200` (Hugging Face)",
        f"Target per category: {SAMPLES_PER_CATEGORY}",
        f"Categories: {len(rows)}",
        f"Total documents extracted: {total_extracted}",
        "",
        "| Category | Available | Extracted | Output Path | Note |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['category']} | {r['available']} | {r['extracted']} | "
            f"{r['output_path']} | {r['note'] or '-'} |"
        )

    lines.append("")
    if insufficient:
        lines.append("## Categories with insufficient samples")
        for r in insufficient:
            lines.append(f"- {r['category']}: {r['note']}")
    else:
        lines.append("## Categories with insufficient samples")
        lines.append("None - all categories reached the target of "
                      f"{SAMPLES_PER_CATEGORY} documents.")

    summary_path = OUTPUT_ROOT / "SUMMARY.md"
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSummary written to {summary_path.relative_to(PROJECT_ROOT)}")


def print_summary(rows: list[dict[str, object]]) -> None:
    print(f"{'Category':<24} {'Available':>9} {'Extracted':>9}  Output Path")
    for r in rows:
        print(
            f"{r['category']:<24} {r['available']:>9} {r['extracted']:>9}  "
            f"{r['output_path']}"
            + (f"  [{r['note']}]" if r["note"] else "")
        )
    total = sum(int(r["extracted"]) for r in rows)
    print(f"\nTotal extracted: {total} / {len(rows) * SAMPLES_PER_CATEGORY}")


if __name__ == "__main__":
    main()
