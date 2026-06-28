"""Multi-project eval harness."""

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))


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


def reconcile_project(corpus_path: pathlib.Path):
    reqs = json.loads((corpus_path / "extracted" / "requirements.json").read_text())
    subs = {
        (s["component"], s["parameter"]): s
        for s in json.loads((corpus_path / "extracted" / "submittals.json").read_text())
    }
    gt = json.loads((corpus_path / "ground_truth.json").read_text())
    cx_by_key = {
        (d["component"], d["parameter"]): d
        for d in gt["seeded_deviations"]
    }

    findings = []
    for r in reqs:
        key = (r["component"], r["parameter"])
        sub = subs.get(key)
        if not sub:
            continue
        if str(sub["provided_value"]) != str(r["required_value"]):
            cx = cx_by_key.get(key, {})
            findings.append({
                "component": r["component"],
                "parameter": r["parameter"],
                "required_value": r["required_value"],
                "provided_value": sub["provided_value"],
                "unit": r["unit"],
                "standard_ref": r["standard_ref"],
                "spec_clause": r["clause"],
                "severity": cx.get("severity", "Major"),
                "predicted_cx_test": cx.get("predicted_cx_test"),
                "predicted_cx_level": cx.get("predicted_cx_level"),
                "lead_time_weeks": cx.get("lead_time_weeks"),
            })
    return findings


def reconcile_project_llm(corpus_path: pathlib.Path):
    """Real LLM reconciliation: the model reads each system's raw spec +
    submittal + standards and reasons out deviations from scratch. Requires an
    LLM key (GEMINI_API_KEY, or PRAMAAN_LLM=openai with a /v1 gateway)."""
    from backend.agents.reconciliation import _standards_text_at, reconcile_system_at
    standards = _standards_text_at(corpus_path)
    findings = []
    for spec in sorted((corpus_path / "specs").glob("*.md")):
        findings.extend(reconcile_system_at(corpus_path, spec.stem, standards))
    return findings


def score_project(findings, ground_truth):
    from eval.run_eval import score
    return score(findings, ground_truth)


def load_gt(corpus_path):
    gt = json.loads((corpus_path / "ground_truth.json").read_text())
    return gt["seeded_deviations"], gt.get("true_negative_systems", [])


def run_all(detector: str = "structured"):
    projects = discover_projects()
    results = {}

    for pid, path in projects.items():
        gt_devs, tn_systems = load_gt(path)
        if detector == "llm":
            findings = reconcile_project_llm(path)
        else:
            findings = reconcile_project(path)
        s = score_project(findings, gt_devs)
        if detector == "llm":
            # LLM findings don't re-derive lead time; weeks saved = sum of the
            # ground-truth lead times for the deviations actually caught (TPs).
            gt_lead = {(d["component"], d["parameter"]): d.get("lead_time_weeks", 0)
                       for d in gt_devs}
            s["total_lead_time_weeks"] = sum(gt_lead.get(k, 0) for k in s["tp"])
            s["max_lead_time_weeks"] = max(
                (gt_lead.get(k, 0) for k in s["tp"]), default=0)
            # Cx mapping is not exercised in detection-only LLM mode; mark it
            # not-measured rather than reporting a misleading 0.000.
            s["cx_prediction_accuracy"] = None
        proj_info = json.loads((path / "ground_truth.json").read_text()).get("project", {})
        results[pid] = {
            "name": proj_info.get("name", pid),
            "tier": proj_info.get("tier", ""),
            "location": proj_info.get("location", ""),
            "capacity_mw": proj_info.get("capacity_mw", 0),
            "deviations": len(gt_devs),
            "findings": len(findings),
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

    total_lead = sum(r["scores"]["total_lead_time_weeks"] for r in results.values())
    max_lead = max((r["scores"]["max_lead_time_weeks"] for r in results.values()), default=0)

    cx_measured = [r for r in results.values()
                   if r["scores"]["cx_prediction_accuracy"] is not None]
    if cx_measured:
        cx_correct = sum(
            len(r["scores"]["tp"]) * r["scores"]["cx_prediction_accuracy"]
            for r in cx_measured
        )
        cx_total = sum(len(r["scores"]["tp"]) for r in cx_measured)
        cx_acc = cx_correct / cx_total if cx_total else 0
    else:
        cx_acc = None

    return {
        "projects": len(results),
        "total_deviations": total_gt,
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "aggregate_precision": round(precision, 3),
        "aggregate_recall": round(recall, 3),
        "aggregate_f1": round(f1, 3),
        "aggregate_cx_accuracy": round(cx_acc, 3) if cx_acc is not None else None,
        "total_lead_time_weeks": total_lead,
        "max_lead_time_weeks": max_lead,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--detector", default="structured",
                    choices=["structured", "llm"],
                    help="structured = pre-extracted triples (offline, always "
                         "1.000); llm = real model reasoning over raw docs "
                         "(needs an API key)")
    args = ap.parse_args()

    results = run_all(detector=args.detector)
    agg = aggregate(results)

    if args.json:
        output = {
            "aggregate": agg,
            "per_project": {
                pid: {
                    "name": r["name"],
                    "deviations": r["deviations"],
                    "precision": r["scores"]["precision"],
                    "recall": r["scores"]["recall"],
                    "f1": r["scores"]["f1"],
                    "cx_accuracy": r["scores"]["cx_prediction_accuracy"],
                    "total_lead_weeks": r["scores"]["total_lead_time_weeks"],
                    "false_positives": [list(k) for k in r["scores"]["fp"]],
                    "false_negatives": [list(k) for k in r["scores"]["fn"]],
                }
                for pid, r in results.items()
            },
        }
        print(json.dumps(output, indent=2))
        return

    print(f"\n{'='*70}")
    print(f"  PRAMAAN MULTI-PROJECT EVAL — {agg['projects']} PROJECTS "
          f"[{args.detector.upper()}]")
    print(f"{'='*70}")

    for pid, r in results.items():
        s = r["scores"]
        cx = s["cx_prediction_accuracy"]
        cx_str = f"{cx:.3f}" if cx is not None else " n/a "
        print(f"\n  {r['name']} ({r['tier']}, {r['location']})")
        print(f"    {r['capacity_mw']:>3d} MW | "
              f"Devs: {r['deviations']:>2d} | "
              f"P={s['precision']:.3f} R={s['recall']:.3f} F1={s['f1']:.3f} | "
              f"Cx={cx_str} | "
              f"Lead: {s['total_lead_time_weeks']}w")
        if s["fp"]:
            print(f"       false positives: {[list(k) for k in s['fp']]}")
        if s["fn"]:
            print(f"       false negatives: {[list(k) for k in s['fn']]}")

    print(f"\n{'~'*70}")
    print(f"  AGGREGATE ACROSS {agg['projects']} PROJECTS")
    print(f"{'~'*70}")
    print(f"  Total deviations        : {agg['total_deviations']}")
    print(f"  True positives          : {agg['total_tp']}")
    print(f"  False positives         : {agg['total_fp']}")
    print(f"  False negatives         : {agg['total_fn']}")
    print(f"  PRECISION               : {agg['aggregate_precision']:.3f}")
    print(f"  RECALL                  : {agg['aggregate_recall']:.3f}")
    print(f"  F1                      : {agg['aggregate_f1']:.3f}")
    _cxa = agg['aggregate_cx_accuracy']
    _cxa_str = f"{_cxa:.3f}" if _cxa is not None else "n/a (detection-only mode)"
    print(f"  Cx prediction accuracy  : {_cxa_str}")
    print(f"  Total lead time saved   : {agg['total_lead_time_weeks']} weeks")
    print(f"  Max lead time           : {agg['max_lead_time_weeks']} weeks")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
