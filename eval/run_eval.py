"""Eval harness — scores a detector's findings against ground_truth.json."""

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from backend.paths import CORPUS


def load_ground_truth():
    gt = json.loads((CORPUS / "ground_truth.json").read_text())
    return gt["seeded_deviations"]


def key(d):
    comp = d.get("component")
    param = d.get("parameter")
    if not comp or not param:
        raise ValueError(f"Finding missing component/parameter: {d}")
    return (comp, param)


def load_true_negatives():
    gt = json.loads((CORPUS / "ground_truth.json").read_text())
    return gt.get("true_negative_systems", [])


def score(findings, ground_truth):
    gt_keys = {key(d) for d in ground_truth}
    gt_by_key = {key(d): d for d in ground_truth}
    found_keys = {key(f) for f in findings}

    tp = gt_keys & found_keys
    fp = found_keys - gt_keys
    fn = gt_keys - found_keys

    precision = len(tp) / (len(tp) + len(fp)) if (tp or fp) else 0.0
    recall = len(tp) / (len(tp) + len(fn)) if (tp or fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)

    found_by_key = {key(f): f for f in findings}
    cx_correct = sum(
        1 for k in tp
        if found_by_key[k].get("predicted_cx_test") == gt_by_key[k]["predicted_cx_test"]
    )
    cx_acc = cx_correct / len(tp) if tp else 0.0

    faithful = sum(
        1 for f in findings
        if f.get("citation_faithful", True)
    )
    faith_pct = faithful / len(findings) if findings else 0.0

    lead_times = [
        found_by_key[k].get("lead_time_weeks")
        for k in tp
        if found_by_key[k].get("lead_time_weeks") is not None
    ]
    mean_lead = sum(lead_times) / len(lead_times) if lead_times else 0
    max_lead = max(lead_times) if lead_times else 0
    total_lead = sum(lead_times)

    conf_scores = [
        f.get("confidence") for f in findings if f.get("confidence") is not None
    ]
    mean_conf = sum(conf_scores) / len(conf_scores) if conf_scores else None

    tn_systems = load_true_negatives()
    tn_fp = [f for f in findings if f.get("system") in tn_systems
             or any(s in str(f.get("component", "")) for s in tn_systems)]
    fp_rate = len(tn_fp) / len(findings) if findings else 0.0

    return {
        "tp": sorted(tp), "fp": sorted(fp), "fn": sorted(fn),
        "precision": precision, "recall": recall, "f1": f1,
        "cx_prediction_accuracy": cx_acc,
        "citation_faithfulness": faith_pct,
        "mean_lead_time_weeks": mean_lead,
        "max_lead_time_weeks": max_lead,
        "total_lead_time_weeks": total_lead,
        "mean_confidence": mean_conf,
        "true_negative_systems": len(tn_systems),
        "false_positives_in_clean_systems": len(tn_fp),
        "false_positive_rate": fp_rate,
    }


def get_findings(detector):
    if detector == "baseline":
        from eval.baseline_reconciler import reconcile
        return reconcile()
    elif detector == "llm":
        import sys
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
        from backend.agents.reconciliation import run_reconciliation_over_corpus
        return run_reconciliation_over_corpus()
    raise ValueError(detector)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detector", default="baseline",
                    choices=["baseline", "llm"])
    ap.add_argument("--json", action="store_true",
                    help="Output results as JSON")
    args = ap.parse_args()

    gt = load_ground_truth()
    t0 = time.time()
    findings = get_findings(args.detector)
    elapsed = time.time() - t0
    r = score(findings, gt)

    if args.json:
        print(json.dumps({
            "detector": args.detector,
            "elapsed_seconds": round(elapsed, 2),
            **{k: v for k, v in r.items() if k not in ("tp", "fp", "fn")},
            "tp": [list(k) for k in r["tp"]],
            "fp": [list(k) for k in r["fp"]],
            "fn": [list(k) for k in r["fn"]],
        }, indent=2))
        return

    print(f"\n{'='*55}")
    print(f"  PRAMAAN DEVIATION-DETECTION EVAL [{args.detector.upper()}]")
    print(f"{'='*55}")
    print(f"  ground-truth deviations : {len(gt)}")
    print(f"  findings                : {len(findings)}")
    print(f"  elapsed                 : {elapsed:.1f}s")
    print(f"{'~'*55}")
    print(f"  true positives          : {len(r['tp'])}  {r['tp']}")
    print(f"  false positives         : {len(r['fp'])}  {r['fp']}")
    print(f"  false negatives         : {len(r['fn'])}  {r['fn']}")
    print(f"{'~'*55}")
    print(f"  PRECISION               : {r['precision']:.3f}")
    print(f"  RECALL                  : {r['recall']:.3f}")
    print(f"  F1                      : {r['f1']:.3f}")
    print(f"{'~'*55}")
    print(f"  Cx-test prediction acc  : {r['cx_prediction_accuracy']:.3f}")
    print(f"  Citation faithfulness   : {r['citation_faithfulness']:.3f}")
    if r['mean_confidence'] is not None:
        print(f"  Mean confidence         : {r['mean_confidence']:.3f}")
    print(f"{'~'*55}")
    print(f"  Mean lead time          : {r['mean_lead_time_weeks']:.1f} weeks")
    print(f"  Max lead time           : {r['max_lead_time_weeks']} weeks")
    print(f"  Total lead time saved   : {r['total_lead_time_weeks']} weeks")
    print(f"{'~'*55}")
    print(f"  True-negative systems   : {r['true_negative_systems']}  (FIRE, BUSWAY, PDU)")
    print(f"  FP in clean systems     : {r['false_positives_in_clean_systems']}")
    print(f"  False-positive rate     : {r['false_positive_rate']:.3f}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
