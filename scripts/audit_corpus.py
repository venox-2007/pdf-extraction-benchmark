"""Corpus integrity audit for the final benchmark dataset."""
import csv
import json
import os
from collections import Counter

SEP = "=" * 60
issues = []


def ok(cond):
    return "OK" if cond else "FAIL"


# ── Load manifest ─────────────────────────────────────────────────────────────
with open("data/final_benchmark/manifest.csv") as f:
    rows = list(csv.DictReader(f))

# ── MANIFEST structural checks ────────────────────────────────────────────────
print(SEP)
print("MANIFEST CHECKS")
print(SEP)

total = len(rows)
print(f"  Total rows: {total}  [{ok(total == 60)}]")
if total != 60:
    issues.append(f"Manifest has {total} rows, expected 60")

for ds in ("funsd", "rvl_cdip", "sroie"):
    ids = [r["document_id"] for r in rows if r["dataset"] == ds]
    dups = [k for k, v in Counter(ids).items() if v > 1]
    print(f"  {ds} duplicates: {dups or 'none'}  [{ok(not dups)}]")
    if dups:
        issues.append(f"{ds} duplicate document_ids: {dups}")

ds_counts = Counter(r["dataset"] for r in rows)
expected_ds = {"funsd": 20, "rvl_cdip": 20, "sroie": 20}
print(f"  Dataset distribution: {dict(ds_counts)}  [{ok(ds_counts == Counter(expected_ds))}]")

for ds, expected_cat in (("funsd", {"form"}), ("sroie", {"receipt"})):
    cats = set(r["category"] for r in rows if r["dataset"] == ds)
    correct = cats == expected_cat
    print(f"  {ds} categories: {cats}  [{ok(correct)}]")
    if not correct:
        issues.append(f"{ds} unexpected categories: {cats}")

src_missing, gt_missing = [], []
for r in rows:
    if not os.path.exists(r["source_path"]):
        src_missing.append(r["source_path"])
    if r["ground_truth_path"] and not os.path.exists(r["ground_truth_path"]):
        gt_missing.append(r["ground_truth_path"])
print(f"  source_path missing: {len(src_missing)}  [{ok(not src_missing)}]")
print(f"  ground_truth_path missing: {len(gt_missing)}  [{ok(not gt_missing)}]")
for p in src_missing:
    issues.append(f"Missing source: {p}")
for p in gt_missing:
    issues.append(f"Missing GT: {p}")

# ── FUNSD checks ──────────────────────────────────────────────────────────────
print()
print(SEP)
print("FUNSD CHECKS (20 documents)")
print(SEP)

funsd_rows = [r for r in rows if r["dataset"] == "funsd"]
funsd_ok = 0
for r in funsd_rows:
    doc_id = r["document_id"]
    img_path = r["source_path"]
    ann_path = r["ground_truth_path"]

    img_stem = os.path.splitext(os.path.basename(img_path))[0]
    ann_stem = os.path.splitext(os.path.basename(ann_path))[0]
    stem_ok = img_stem == ann_stem == doc_id
    img_exists = os.path.exists(img_path)
    ann_exists = os.path.exists(ann_path)

    json_ok = False
    form_ok = False
    if ann_exists:
        try:
            data = json.load(open(ann_path, encoding="utf-8"))
            json_ok = True
            form_ok = len(data.get("form", [])) > 0
        except Exception as e:
            issues.append(f"FUNSD {doc_id}: JSON parse error: {e}")

    row_ok = img_exists and ann_exists and stem_ok and json_ok and form_ok
    if row_ok:
        funsd_ok += 1
    else:
        detail = []
        if not img_exists:
            detail.append("img missing")
        if not ann_exists:
            detail.append("ann missing")
        if not stem_ok:
            detail.append(f"stem mismatch img={img_stem} ann={ann_stem}")
        if not json_ok:
            detail.append("invalid JSON")
        if not form_ok:
            detail.append("empty form data")
        msg = f"FUNSD {doc_id}: {', '.join(detail)}"
        issues.append(msg)
        print(f"  [FAIL] {msg}")

print(f"  Verified: {funsd_ok}/20  [{ok(funsd_ok == 20)}]")

# ── SROIE checks ──────────────────────────────────────────────────────────────
print()
print(SEP)
print("SROIE CHECKS (20 documents)")
print(SEP)

sroie_rows = [r for r in rows if r["dataset"] == "sroie"]
sroie_ok = 0
for r in sroie_rows:
    doc_id = r["document_id"]
    img_path = r["source_path"]
    box_path = r["ground_truth_path"]
    ent_path = f"data/final_benchmark/sroie/entities/{doc_id}.txt"

    img_stem = os.path.splitext(os.path.basename(img_path))[0]
    box_stem = os.path.splitext(os.path.basename(box_path))[0]
    ent_stem = os.path.splitext(os.path.basename(ent_path))[0]
    stem_ok = img_stem == box_stem == ent_stem == doc_id

    img_exists = os.path.exists(img_path)
    box_exists = os.path.exists(box_path)
    ent_exists = os.path.exists(ent_path)
    box_nonempty = os.path.getsize(box_path) > 0 if box_exists else False
    ent_nonempty = os.path.getsize(ent_path) > 0 if ent_exists else False

    row_ok = img_exists and box_exists and ent_exists and stem_ok and box_nonempty and ent_nonempty
    if row_ok:
        sroie_ok += 1
    else:
        detail = []
        if not img_exists:
            detail.append("img missing")
        if not box_exists:
            detail.append("box missing")
        if not ent_exists:
            detail.append("entities missing")
        if not stem_ok:
            detail.append("stem mismatch")
        if not box_nonempty:
            detail.append("box empty")
        if not ent_nonempty:
            detail.append("entities empty")
        msg = f"SROIE {doc_id}: {', '.join(detail)}"
        issues.append(msg)
        print(f"  [FAIL] {msg}")

print(f"  Verified: {sroie_ok}/20  [{ok(sroie_ok == 20)}]")

# ── Orphan file check ─────────────────────────────────────────────────────────
print()
print(SEP)
print("ORPHAN FILE CHECKS")
print(SEP)

manifest_funsd = {r["document_id"] for r in rows if r["dataset"] == "funsd"}
manifest_sroie = {r["document_id"] for r in rows if r["dataset"] == "sroie"}

funsd_dir_stems = {os.path.splitext(f)[0] for f in os.listdir("data/final_benchmark/funsd")}
orphan_funsd = funsd_dir_stems - manifest_funsd
print(f"  FUNSD orphans:           {sorted(orphan_funsd) or 'none'}  [{ok(not orphan_funsd)}]")

sroie_img_stems = {os.path.splitext(f)[0] for f in os.listdir("data/final_benchmark/sroie/img")}
orphan_img = sroie_img_stems - manifest_sroie
print(f"  SROIE img orphans:       {sorted(orphan_img) or 'none'}  [{ok(not orphan_img)}]")

sroie_box_stems = {os.path.splitext(f)[0] for f in os.listdir("data/final_benchmark/sroie/box")}
orphan_box = sroie_box_stems - manifest_sroie
print(f"  SROIE box orphans:       {sorted(orphan_box) or 'none'}  [{ok(not orphan_box)}]")

ent_dir = "data/final_benchmark/sroie/entities"
sroie_ent_stems = {os.path.splitext(f)[0] for f in os.listdir(ent_dir)}
orphan_ent = sroie_ent_stems - manifest_sroie
print(f"  SROIE entities orphans:  {sorted(orphan_ent) or 'none'}  [{ok(not orphan_ent)}]")

if orphan_funsd or orphan_img or orphan_box or orphan_ent:
    issues.append("Orphan files found — see Orphan File Checks section above")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print(SEP)
print("SUMMARY")
print(SEP)
print(f"  FUNSD verified:   {funsd_ok}/20")
print(f"  SROIE verified:   {sroie_ok}/20")
print(f"  Total issues:     {len(issues)}")
if issues:
    print()
    print("ISSUES REQUIRING ATTENTION:")
    for i, iss in enumerate(issues, 1):
        print(f"  {i}. {iss}")
else:
    print()
    print("  Corpus integrity check PASSED. Benchmark-ready.")
