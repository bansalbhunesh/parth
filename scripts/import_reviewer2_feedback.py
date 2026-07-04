#!/usr/bin/env python3
"""import_reviewer2_feedback.py — convert a filled reviewer_form.csv into
labels/reviewer_2.jsonl and print an agreement summary.

Never overwrites an existing non-empty reviewer_2.jsonl without first backing it
up. If the form has no filled verdicts yet, nothing is written.

  python scripts/import_reviewer2_feedback.py
  python scripts/import_reviewer2_feedback.py --form path/to/reviewer_form.csv
"""
import argparse
import csv
import json
import pathlib
import shutil
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402

DEFAULT_FORM = L.BENCH / "reviewer_packet" / "reviewer_form.csv"
OUT = L.BENCH / "labels" / "reviewer_2.jsonl"
VERDICTS = {"accept", "accept_with_minor_edit", "modify", "reject", "contested", "needs_more_evidence"}
AGREE = {"accept", "accept_with_minor_edit"}  # reviewer_1 accepted every label


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--form", default=str(DEFAULT_FORM))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    form, out = pathlib.Path(args.form), pathlib.Path(args.out)
    if not form.exists():
        print(f"form not found: {form}")
        return 1

    rows = list(csv.DictReader(form.open(encoding="utf-8")))
    total = len(rows)
    records, verdict_counts, unknown = [], Counter(), []
    for r in rows:
        v = (r.get("reviewer_verdict") or "").strip().lower()
        if not v:
            continue
        if v not in VERDICTS:
            unknown.append((r.get("label_id"), v))
            continue
        verdict_counts[v] += 1
        records.append({
            "label_id": r.get("label_id"), "reviewer": "reviewer_2", "verdict": v,
            "confidence": (r.get("reviewer_confidence") or "").strip().lower(),
            "evidence_sufficient": (r.get("evidence_sufficient_yes_no") or "").strip(),
            "severity_ok": (r.get("severity_ok_yes_no") or "").strip(),
            "difficulty_ok": (r.get("difficulty_ok_yes_no") or "").strip(),
            "commissioning_mapping_ok": (r.get("commissioning_mapping_ok_yes_no") or "").strip(),
            "suggested_correction": (r.get("suggested_correction") or "").strip(),
            "missing_related_label": (r.get("missing_related_label") or "").strip(),
            "notes": (r.get("reviewer_notes") or "").strip(),
            "review_status": "reviewed_two_person",
        })

    if unknown:
        print(f"[!] {len(unknown)} unknown verdict(s) ignored: {unknown[:5]}")
    if not records:
        print(f"No filled verdicts in {form.name} yet — nothing written. "
              f"(0/{total} labels reviewed.)")
        return 0

    # back up an existing non-empty output before writing
    if out.exists() and out.stat().st_size > 0:
        bak = out.with_suffix(f".jsonl.bak.{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        shutil.copyfile(out, bak)
        print(f"backed up existing {out.name} -> {bak.name}")
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")

    # agreement vs reviewer_1 (author accepted every label)
    r1 = {}
    r1_path = L.BENCH / "labels" / "reviewer_1.jsonl"
    if r1_path.exists():
        for line in r1_path.read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            r1[d["label_id"]] = d.get("verdict", "accept")
    both = [rec for rec in records if rec["label_id"] in r1]
    agree = sum(1 for rec in both
                if (rec["verdict"] in AGREE) == (r1[rec["label_id"]] in AGREE))
    coverage = 100.0 * len(records) / total if total else 0.0

    print(f"\nwrote {len(records)} reviewer_2 verdicts -> {out.relative_to(L.ROOT).as_posix()}")
    print(f"coverage: {len(records)}/{total} labels ({coverage:.0f}%)")
    print("verdicts:")
    for v in ("accept", "accept_with_minor_edit", "modify", "reject", "contested", "needs_more_evidence"):
        print(f"  {verdict_counts.get(v, 0):3d}  {v}")
    print(f"accepted: {verdict_counts['accept'] + verdict_counts['accept_with_minor_edit']} | "
          f"modified: {verdict_counts['modify']} | rejected: {verdict_counts['reject']} | "
          f"contested: {verdict_counts['contested']}")
    if both:
        print(f"agreement with reviewer_1 (label stands vs not): {agree}/{len(both)} "
              f"({100.0 * agree / len(both):.0f}%)")
    print("\nNext: review the disagreements, then follow labels/ADJUDICATION_PROTOCOL.md "
          "to populate adjudicated.jsonl and bump the benchmark version.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
