#!/usr/bin/env python3
"""benchmark_error_analysis.py — classify every false positive and false negative
from the saved featured 3-pass run (gemini-3.1-flash-lite). Analysis only: it
reads predictions already on disk and makes NO API calls, changes NO scoring and
NO prompts.

Writes reports/false_positives.csv, reports/false_negatives.csv, and prints a
bucket summary that feeds reports/error_analysis.md.
"""
import csv
import json
import pathlib
import re
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402

FEATURED = "google/gemini-3.1-flash-lite"
REPORTS = L.BENCH / "reports"


def _grounded(rv, spec_l, spec_compact):
    if rv is None or str(rv).strip() == "":
        return False
    vs = str(rv).strip().lower()
    compact = re.sub(r"[^a-z0-9+]", "", vs)
    nums = re.findall(r"\d+\.?\d*", vs)
    toks = [t for t in re.findall(r"[a-z]+", vs) if len(t) > 2]
    return ((bool(compact) and compact in spec_compact)
            or (bool(nums) and all(re.search(r"(?<!\d)" + re.escape(n) + r"(?!\d)", spec_l) for n in nums))
            or (bool(toks) and all(t in spec_l for t in toks)))


def _featured_runs():
    dirs = sorted(d for d in (L.BENCH / "runs").glob("*")
                  if d.is_dir() and FEATURED.split("/")[-1] in d.name)
    out = []
    for d in dirs:
        sp = d / "summary.json"
        if sp.exists() and json.loads(sp.read_text(encoding="utf-8")).get("model") == FEATURED:
            preds = {}
            for line in (d / "predictions.jsonl").read_text(encoding="utf-8").splitlines():
                p = json.loads(line)
                preds[p["pair_id"]] = p
            out.append((d.name, preds))
    return out


def classify_fp(finding, pair_labels, is_clean_neg, spec_l, spec_compact, pair_findings):
    rv = finding.get("required_value")
    param = L.norm(finding.get("parameter"))
    if is_clean_neg:
        return "clean-negative false alert"
    if not _grounded(rv, spec_l, spec_compact):
        return "hallucinated requirement"
    # duplicate: another finding on this pair shares the parameter
    if sum(1 for f in pair_findings if L.norm(f.get("parameter")) == param) > 1:
        return "duplicate or over-broad finding"
    # parameter overlaps a positive label but the pair did not match it -> the
    # model found the right deviation; the mismatch is a scorer/label artifact
    pos = [lb for lb in pair_labels if lb["label_type"] in L.POSITIVE_LABEL_TYPES]
    over = [lb for lb in pos if L._param_overlap(lb, finding)]
    if over:
        if any(lb.get("difficulty") == "unit_conversion" for lb in over):
            return "unit representation mismatch (model correct, scorer/label strict)"
        return "wrong evidence span / weak benchmark label"
    # grounded, on a positive-bearing pair, no label parameter overlap -> a real
    # deviation the benchmark simply did not label
    return "missing benchmark label"


def classify_fn(label, ran, error_type):
    if not ran:
        if label.get("modality") == "image":
            return "image/vision unsupported"
        if error_type in ("image_pending", "vision_unavailable"):
            return "image/vision unsupported"
        return "transient provider error / parse issue"
    return {
        "direct_value": "direct value missed",
        "unit_conversion": "unit conversion missed",
        "derived_arithmetic": "derived arithmetic missed",
        "categorical_reasoning": "categorical reasoning missed",
        "domain_recall": "domain recall missed",
        "omission_detection": "omission missed",
        "table_or_layout": "table/layout missed",
        "scanned_or_image": "image/vision unsupported",
    }.get(label.get("difficulty"), "other missed")


def main() -> int:
    labels = L.load_labels()
    by_pair = L.group_labels_by_pair(labels)
    runs = _featured_runs()
    if not runs:
        print(f"no saved runs for {FEATURED}")
        return 1

    fp_rows, fn_rows = [], []
    fp_buckets, fn_buckets = Counter(), Counter()
    for run_name, preds in runs:
        for pid in sorted(by_pair):
            pls = by_pair[pid]
            pred = preds.get(pid, {})
            findings = pred.get("findings", [])
            ran = not pred.get("not_run", True)
            spec = (L.BENCH / "pairs" / pid / "owner_requirement.md").read_text(encoding="utf-8")
            spec_l = spec.lower()
            spec_compact = re.sub(r"[^a-z0-9+]", "", spec_l)
            is_clean_neg = {lb["label_type"] for lb in pls} == {"clean_negative"}
            pos = [lb for lb in pls if lb["label_type"] in L.POSITIVE_LABEL_TYPES]
            matched, unmatched = L._one_to_one(pos, findings, L.matches_semantic)
            # false positives
            for fi in unmatched:
                f = findings[fi]
                b = classify_fp(f, pls, is_clean_neg, spec_l, spec_compact, findings)
                fp_buckets[b] += 1
                fp_rows.append({"run": run_name, "pair_id": pid, "bucket": b,
                                "parameter": f.get("parameter"), "required_value": f.get("required_value"),
                                "provided_value": f.get("provided_value"), "severity": f.get("severity"),
                                "rationale": str(f.get("rationale", ""))[:160]})
            # false negatives (missed positive labels)
            for i, lb in enumerate(pos):
                if i not in matched:
                    b = classify_fn(lb, ran, pred.get("error_type"))
                    fn_buckets[b] += 1
                    fn_rows.append({"run": run_name, "pair_id": pid, "bucket": b,
                                    "label_id": lb.get("label_id"), "difficulty": lb.get("difficulty"),
                                    "parameter": lb.get("parameter"),
                                    "required_value": lb.get("required_value"),
                                    "submitted_value": lb.get("submitted_value"), "ran": ran})

    with (REPORTS / "false_positives.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fp_rows[0].keys()) if fp_rows else
                           ["run", "pair_id", "bucket"])
        w.writeheader()
        w.writerows(fp_rows)
    with (REPORTS / "false_negatives.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fn_rows[0].keys()) if fn_rows else
                           ["run", "pair_id", "bucket"])
        w.writeheader()
        w.writerows(fn_rows)

    print(f"runs analyzed: {[r[0] for r in runs]}")
    print(f"\nFALSE POSITIVES total (3 passes): {sum(fp_buckets.values())}")
    for b, n in fp_buckets.most_common():
        print(f"  {n:3d}  {b}")
    print(f"\nFALSE NEGATIVES total (3 passes): {sum(fn_buckets.values())}")
    for b, n in fn_buckets.most_common():
        print(f"  {n:3d}  {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
