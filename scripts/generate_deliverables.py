"""Generate comparison_matrix.csv and all benchmark charts for the final deliverables."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "docs" / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

RESULTS = ROOT / "outputs" / "benchmark_results"

# ── colour palette (one per tool, consistent across all charts) ───────────────
TOOLS = ["PyMuPDF", "OpenDataLoader", "PaddleOCR", "Tesseract", "Docling"]
COLORS = {
    "PyMuPDF": "#4C72B0",
    "OpenDataLoader": "#DD8452",
    "PaddleOCR": "#55A868",
    "Tesseract": "#C44E52",
    "Docling": "#8172B3",
}

STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "#F8F8F8",
    "axes.grid": True,
    "grid.color": "white",
    "grid.linewidth": 1.2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.family": "DejaVu Sans",
    "axes.titlesize": 13,
    "axes.labelsize": 11,
}
plt.rcParams.update(STYLE)


def savefig(name: str) -> None:
    path = CHARTS / name
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  saved {path.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. COMPARISON MATRIX CSV
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== 1. Comparison Matrix CSV ===")

criteria = [
    ("Accuracy",            0.30),
    ("Table Extraction",    0.20),
    ("Latency",             0.20),
    ("Cost",                0.15),
    ("Handwriting",         0.05),
    ("Layout Preservation", 0.05),
    ("Ease of Integration", 0.05),
]

# Scores taken directly from comparison_matrix.md (updated with 50-doc Docling data)
scores: dict[str, list[int]] = {
    "PyMuPDF":        [7, 1, 10, 10, 1, 5, 9],
    "OpenDataLoader": [7, 7,  9,  8, 2, 8, 5],
    "PaddleOCR":      [8, 1,  5,  8, 3, 4, 7],
    "Docling":        [6, 9,  2,  8, 2, 9, 6],
    "Tesseract":      [7, 1,  8,  9, 2, 4, 8],
}

csv_lines = ["Tool," + ",".join(c for c, _ in criteria) + ",Weighted Total"]
for tool in TOOLS:
    s = scores[tool]
    weighted = sum(sc * w for sc, (_, w) in zip(s, criteria, strict=True))
    row = f"{tool}," + ",".join(str(x) for x in s) + f",{weighted:.2f}"
    csv_lines.append(row)

csv_path = ROOT / "docs" / "comparison_matrix.csv"
csv_path.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")
print("  saved docs/comparison_matrix.csv")


# ─────────────────────────────────────────────────────────────────────────────
# 2. FUNSD ACCURACY CHARTS
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== 2. FUNSD Accuracy Charts ===")

# Load FUNSD data
with open(RESULTS / "funsd" / "funsd_summary.json") as f:
    paddle_funsd = json.load(f)
with open(RESULTS / "funsd_tesseract" / "funsd_summary.json") as f:
    tess_funsd = json.load(f)
with open(RESULTS / "docling_funsd50" / "funsd_summary.json") as f:
    docling_funsd = json.load(f)

funsd_tools = ["PaddleOCR", "Tesseract", "Docling"]
funsd_colors = [COLORS[t] for t in funsd_tools]

_srcs = [paddle_funsd, tess_funsd, docling_funsd]
cer   = [s["average_cer"] for s in _srcs]
wer   = [s["average_wer"] for s in _srcs]
tf1   = [s["average_token_f1"] for s in _srcs]
tprec = [s["average_token_precision"] for s in _srcs]
trec  = [s["average_token_recall"] for s in _srcs]
docs  = [s["evaluated_documents"] for s in _srcs]

x = np.arange(len(funsd_tools))
w = 0.5


# Chart 2a — FUNSD CER (bar, lower is better)
fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.bar(x, cer, width=w, color=funsd_colors, zorder=3)
ax.set_xticks(x)
ax.set_xticklabels([f"{t}\n(n={d})" for t, d in zip(funsd_tools, docs, strict=True)])
ax.set_ylabel("Character Error Rate (CER)")
ax.set_title("FUNSD — Character Error Rate (lower is better)")
ax.set_ylim(0, max(cer) * 1.35)
for bar, val in zip(bars, cer, strict=True):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.008,
            f"{val:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.axhline(min(cer), color="grey", linestyle="--", linewidth=0.8, alpha=0.6)
savefig("funsd_cer.png")


# Chart 2b — FUNSD WER
fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.bar(x, wer, width=w, color=funsd_colors, zorder=3)
ax.set_xticks(x)
ax.set_xticklabels([f"{t}\n(n={d})" for t, d in zip(funsd_tools, docs, strict=True)])
ax.set_ylabel("Word Error Rate (WER)")
ax.set_title("FUNSD — Word Error Rate (lower is better)")
ax.set_ylim(0, max(wer) * 1.30)
for bar, val in zip(bars, wer, strict=True):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
            f"{val:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
savefig("funsd_wer.png")


# Chart 2c — FUNSD Token F1 / Precision / Recall (grouped)
fig, ax = plt.subplots(figsize=(9, 5))
gw = 0.22
offsets = [-gw, 0, gw]
labels = ["Token Precision", "Token Recall", "Token F1"]
data_sets = [tprec, trec, tf1]
grp_colors = ["#5B9BD5", "#ED7D31", "#70AD47"]

for i, (vals, label, col) in enumerate(zip(data_sets, labels, grp_colors, strict=True)):
    xpos = x + offsets[i]
    bars = ax.bar(xpos, vals, width=gw, label=label, color=col, zorder=3)
    for bar, val in zip(bars, vals, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.008,
                f"{val:.3f}", ha="center", va="bottom", fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels([f"{t}\n(n={d})" for t, d in zip(funsd_tools, docs, strict=True)])
ax.set_ylabel("Score")
ax.set_title("FUNSD — Token Precision, Recall, F1 (higher is better)")
ax.set_ylim(0, 1.0)
ax.legend(loc="upper right")
savefig("funsd_token_f1.png")


# Chart 2d — Combined accuracy summary (CER + Token F1 side by side)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
fig.suptitle("FUNSD Accuracy Summary — 50 documents per tool", fontsize=13, fontweight="bold")

bars1 = ax1.bar(x, cer, width=w, color=funsd_colors, zorder=3)
ax1.set_xticks(x)
ax1.set_xticklabels(funsd_tools)
ax1.set_title("CER ↓  (lower is better)")
ax1.set_ylim(0, 0.70)
for bar, val in zip(bars1, cer, strict=True):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.008,
             f"{val:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

bars2 = ax2.bar(x, tf1, width=w, color=funsd_colors, zorder=3)
ax2.set_xticks(x)
ax2.set_xticklabels(funsd_tools)
ax2.set_title("Token F1 ↑  (higher is better)")
ax2.set_ylim(0, 1.0)
for bar, val in zip(bars2, tf1, strict=True):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.008,
             f"{val:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

plt.tight_layout()
savefig("funsd_accuracy_summary.png")


# ─────────────────────────────────────────────────────────────────────────────
# 3. RVL-CDIP LATENCY CHART
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== 3. RVL-CDIP Latency Charts ===")

# Combine sample48 (PyMuPDF, OpenDataLoader, PaddleOCR, Docling)
# with tesseract_comparison (Tesseract) for a complete 5-tool picture
with open(RESULTS / "rvl_cdip_sample48" / "rvl_cdip_summary.json") as f:
    s48 = json.load(f)
with open(RESULTS / "rvl_cdip_tesseract_comparison" / "rvl_cdip_summary.json") as f:
    stess = json.load(f)

latency_ms = {
    "PyMuPDF":        s48["extractor_summaries"]["PyMuPDF"]["latency_ms"]["mean"],
    "OpenDataLoader": s48["extractor_summaries"]["OpenDataLoader"]["latency_ms"]["mean"],
    "PaddleOCR":      s48["extractor_summaries"]["PaddleOCR"]["latency_ms"]["mean"],
    "Docling":        s48["extractor_summaries"]["Docling"]["latency_ms"]["mean"],
    "Tesseract":      stess["extractor_summaries"]["Tesseract"]["latency_ms"]["mean"],
}

lat_tools = list(latency_ms.keys())
lat_vals  = [latency_ms[t] for t in lat_tools]
lat_colors = [COLORS[t] for t in lat_tools]
xi = np.arange(len(lat_tools))

# Chart 3a — Latency (log scale)
fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(xi, lat_vals, color=lat_colors, zorder=3)
ax.set_yscale("log")
ax.set_xticks(xi)
ax.set_xticklabels(lat_tools)
ax.set_ylabel("Mean latency per document (ms, log scale)")
ax.set_title("RVL-CDIP — Mean Extraction Latency per Document")
for bar, val in zip(bars, lat_vals, strict=True):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.15,
            f"{val:,.0f} ms", ha="center", va="bottom", fontsize=9, fontweight="bold")
ax.set_ylim(1, max(lat_vals) * 8)
savefig("rvlcdip_latency_log.png")

# Chart 3b — Latency (linear, OCR tools only for readability)
ocr_tools  = ["Tesseract", "PaddleOCR", "Docling"]
ocr_vals   = [latency_ms[t] for t in ocr_tools]
ocr_colors = [COLORS[t] for t in ocr_tools]
xi2 = np.arange(len(ocr_tools))

fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.bar(xi2, ocr_vals, color=ocr_colors, zorder=3)
ax.set_xticks(xi2)
ax.set_xticklabels(ocr_tools)
ax.set_ylabel("Mean latency per document (ms)")
ax.set_title("RVL-CDIP — OCR Tool Latency Comparison (linear scale)")
for bar, val in zip(bars, ocr_vals, strict=True):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 200,
            f"{val:,.0f} ms", ha="center", va="bottom", fontsize=10, fontweight="bold")
savefig("rvlcdip_latency_ocr.png")


# ─────────────────────────────────────────────────────────────────────────────
# 4. RVL-CDIP WORD COUNT CHART
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== 4. RVL-CDIP Word Count Chart ===")

word_count = {
    "PyMuPDF":        s48["extractor_summaries"]["PyMuPDF"]["word_count"]["mean"],
    "OpenDataLoader": s48["extractor_summaries"]["OpenDataLoader"]["word_count"]["mean"],
    "PaddleOCR":      s48["extractor_summaries"]["PaddleOCR"]["word_count"]["mean"],
    "Docling":        s48["extractor_summaries"]["Docling"]["word_count"]["mean"],
    "Tesseract":      stess["extractor_summaries"]["Tesseract"]["word_count"]["mean"],
}

wc_vals   = [word_count[t] for t in TOOLS]
wc_colors = [COLORS[t] for t in TOOLS]
xi3 = np.arange(len(TOOLS))

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(xi3, wc_vals, color=wc_colors, zorder=3)
ax.set_xticks(xi3)
ax.set_xticklabels(TOOLS)
ax.set_ylabel("Mean words extracted per document")
ax.set_title(
    "RVL-CDIP — Mean Word Count per Document\n"
    "(scanned images; native-PDF tools return 0 — no OCR)"
)
for bar, val in zip(bars, wc_vals, strict=True):
    lbl = f"{val:.0f}" if val > 0 else "0\n(no OCR)"
    ax.text(bar.get_x() + bar.get_width() / 2,
            max(bar.get_height(), 5) + 2,
            lbl, ha="center", va="bottom", fontsize=9, fontweight="bold")
savefig("rvlcdip_word_count.png")


# ─────────────────────────────────────────────────────────────────────────────
# 5. COST ANALYSIS CHART
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== 5. Cost Analysis Chart ===")

volumes = [10_000, 100_000, 1_000_000, 10_000_000]
vol_labels = ["10K", "100K", "1M", "10M"]

# Cost per page ($/page) from cost_analysis.md derivations
cpp = {
    "Textract\n(Analyze Doc)": 0.0150,
    "PyMuPDF":                 0.0000021,
    "Tesseract":               0.0000073,
    "OpenDataLoader":          0.0000345,
    "PaddleOCR (CPU)":         0.0000404,
    "Docling (CPU)":           0.0003664,
    "Mixed Pipeline":          0.0000337,
}

cost_labels = list(cpp.keys())
cost_colors_map = {
    "Textract\n(Analyze Doc)": "#E15759",
    "PyMuPDF":                 COLORS["PyMuPDF"],
    "Tesseract":               COLORS["Tesseract"],
    "OpenDataLoader":          COLORS["OpenDataLoader"],
    "PaddleOCR (CPU)":         COLORS["PaddleOCR"],
    "Docling (CPU)":           COLORS["Docling"],
    "Mixed Pipeline":          "#59A14F",
}

# Chart 5a — Monthly cost at 1M pages (bar)
monthly_at_1m = {label: rate * 1_000_000 for label, rate in cpp.items()}
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(range(len(cost_labels)),
              [monthly_at_1m[lbl] for lbl in cost_labels],
              color=[cost_colors_map[lbl] for lbl in cost_labels],
              zorder=3)
ax.set_yscale("log")
ax.set_xticks(range(len(cost_labels)))
ax.set_xticklabels(cost_labels, fontsize=9)
ax.set_ylabel("Monthly cost at 1M pages (USD, log scale)")
ax.set_title("Cost Comparison at 1,000,000 Pages/Month")
for bar, lbl in zip(bars, cost_labels, strict=True):
    val = monthly_at_1m[lbl]
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.4,
            f"${val:,.0f}" if val >= 1 else f"${val:.2f}",
            ha="center", va="bottom", fontsize=8, fontweight="bold")
savefig("cost_at_1m_pages.png")

# Chart 5b — Cost scaling across all 4 volumes (line chart)
fig, ax = plt.subplots(figsize=(10, 6))
for lbl, rate in cpp.items():
    monthly = [rate * v for v in volumes]
    ls = "--" if "Textract" in lbl else "-"
    lw = 2.5 if "Textract" in lbl or "Mixed" in lbl else 1.5
    ax.plot(vol_labels, monthly,
            marker="o", label=lbl,
            color=cost_colors_map[lbl],
            linestyle=ls, linewidth=lw)

ax.set_yscale("log")
ax.set_ylabel("Monthly cost (USD, log scale)")
ax.set_xlabel("Monthly page volume")
ax.set_title("Self-Hosted vs Textract Cost Scaling")
ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
    lambda val, _: f"${val:,.0f}" if val >= 1 else f"${val:.4f}"
))
savefig("cost_scaling.png")


# ─────────────────────────────────────────────────────────────────────────────
# 6. WEIGHTED SCORES CHART
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== 6. Weighted Scores Chart ===")

weighted = {
    "PyMuPDF":        6.55,
    "OpenDataLoader": 7.25,
    "PaddleOCR":      5.50,
    "Docling":        6.05,
    "Tesseract":      5.95,
}

sorted_tools  = sorted(weighted, key=weighted.get, reverse=True)
sorted_scores = [weighted[t] for t in sorted_tools]
sorted_colors = [COLORS[t] for t in sorted_tools]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.barh(sorted_tools, sorted_scores, color=sorted_colors, zorder=3)
ax.set_xlim(0, 10)
ax.set_xlabel("Weighted score (out of 10)")
ax.set_title(
    "Final Weighted Scores\n"
    "(Accuracy 30%, Tables 20%, Latency 20%, Cost 15%, Other 15%)"
)
ax.invert_yaxis()
for bar, val in zip(bars, sorted_scores, strict=True):
    ax.text(val + 0.1, bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}", va="center", fontsize=11, fontweight="bold")
ax.axvline(6.0, color="grey", linestyle="--", linewidth=0.8, alpha=0.7)
savefig("weighted_scores.png")


# Chart 6b — radar/spider chart for all 5 tools
criteria_short = [
    "Accuracy", "Tables", "Latency", "Cost", "Handwriting", "Layout", "Integration",
]
N = len(criteria_short)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"polar": True})
for tool in TOOLS:
    vals = scores[tool] + [scores[tool][0]]
    ax.plot(angles, vals, "o-", linewidth=1.8, label=tool, color=COLORS[tool])
    ax.fill(angles, vals, alpha=0.08, color=COLORS[tool])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(criteria_short, size=10)
ax.set_ylim(0, 10)
ax.set_yticks([2, 4, 6, 8, 10])
ax.set_yticklabels(["2", "4", "6", "8", "10"], size=8)
ax.set_title("Tool Comparison — Radar Chart\n(all 7 criteria, score 1–10)", pad=20, size=13)
ax.legend(loc="lower right", bbox_to_anchor=(1.3, -0.1))
savefig("radar_scores.png")


print("\nAll deliverables generated:")
for p in sorted(CHARTS.iterdir()):
    print(f"  {p.name}")
print("  docs/comparison_matrix.csv")
