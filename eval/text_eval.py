"""Text-based eval — runs the regex extraction engine on raw markdown
spec/submittal files and scores against ground truth.

This breaks the circularity of the baseline eval (which compares
pre-extracted structured triples) by proving the analysis pipeline
independently discovers deviations from raw unstructured text.
"""

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from backend.analyze import _deterministic_compare
from eval.run_eval import score

DATA = pathlib.Path(__file__).parent.parent / "data"


def discover_projects():
    projects = {}

    corpus = DATA / "corpus"
    if (corpus / "ground_truth.json").exists():
        projects["meghdoot"] = corpus

    projects_dir = DATA / "projects"
    if projects_dir.exists():
        for p in sorted(projects_dir.iterdir()):
            if p.is_dir() and (p / "ground_truth.json").exists():
                projects[p.name] = p

    return projects


def extract_from_text(corpus_path: pathlib.Path):
    specs_dir = corpus_path / "specs"
    subs_dir = corpus_path / "submittals"
    findings = []

    for spec_path in sorted(specs_dir.glob("*.md")):
        sys_id = spec_path.stem
        sub_path = subs_dir / f"{sys_id}.md"
        if not sub_path.exists():
            continue
        spec_text = spec_path.read_text(encoding="utf-8")
        sub_text = sub_path.read_text(encoding="utf-8")
        devs = _deterministic_compare(spec_text, sub_text)
        for d in devs:
            d["system"] = sys_id
        findings.extend(devs)

    return findings


def run_text_eval():
    projects = discover_projects()
    results = {}

    for pid, path in projects.items():
        gt = json.loads((path / "ground_truth.json").read_text())
        gt_devs = gt["seeded_deviations"]
        proj_info = gt.get("project", {})

        t0 = time.time()
        findings = extract_from_text(path)
        elapsed = time.time() - t0

        s = score(findings, gt_devs)
        results[pid] = {
            "name": proj_info.get("name", pid),
            "tier": proj_info.get("tier", ""),
            "location": proj_info.get("location", ""),
            "capacity_mw": proj_info.get("capacity_mw", 0),
            "deviations": len(gt_devs),
            "findings": len(findings),
            "elapsed_s": round(elapsed, 3),
            "scores": s,
        }

    return results


def aggregate(results):
    total_gt = sum(r["deviations"] for r in results.values())
    total_tp = sum(len(r["scores"]["tp"]) for r in results.values())
    total_fp = sum(len(r["scores"]["fp"]) for r in results.values())
    total_fn = sum(len(r["scores"]["fn"]) for r in results.values())

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    return {
        "projects": len(results),
        "total_deviations": total_gt,
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "aggregate_precision": round(precision, 3),
        "aggregate_recall": round(recall, 3),
        "aggregate_f1": round(f1, 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    results = run_text_eval()
    agg = aggregate(results)

    if args.json:
        output = {
            "eval_type": "text-based (regex on raw markdown)",
            "aggregate": agg,
            "per_project": {
                pid: {
                    "name": r["name"],
                    "deviations": r["deviations"],
                    "findings": r["findings"],
                    "precision": r["scores"]["precision"],
                    "recall": r["scores"]["recall"],
                    "f1": r["scores"]["f1"],
                    "elapsed_s": r["elapsed_s"],
                }
                for pid, r in results.items()
            },
        }
        print(json.dumps(output, indent=2))
        return

    print(f"\n{'='*70}")
    print(f"  PRAMAAN TEXT-BASED EVAL — RAW MARKDOWN → REGEX EXTRACTION")
    print(f"  (Non-circular: proves pipeline discovers deviations from text)")
    print(f"{'='*70}")

    for pid, r in results.items():
        s = r["scores"]
        print(f"\n  {r['name']} ({r['tier']}, {r['location']})")
        print(f"    {r['capacity_mw']:>3d} MW | "
              f"GT: {r['deviations']:>2d} Found: {r['findings']:>2d} | "
              f"P={s['precision']:.3f} R={s['recall']:.3f} F1={s['f1']:.3f} | "
              f"{r['elapsed_s']:.3f}s")

    print(f"\n{'~'*70}")
    print(f"  AGGREGATE ACROSS {agg['projects']} PROJECTS")
    print(f"{'~'*70}")
    print(f"  Total ground-truth devs : {agg['total_deviations']}")
    print(f"  True positives          : {agg['total_tp']}")
    print(f"  False positives         : {agg['total_fp']}")
    print(f"  False negatives         : {agg['total_fn']}")
    print(f"  PRECISION               : {agg['aggregate_precision']:.3f}")
    print(f"  RECALL                  : {agg['aggregate_recall']:.3f}")
    print(f"  F1                      : {agg['aggregate_f1']:.3f}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
