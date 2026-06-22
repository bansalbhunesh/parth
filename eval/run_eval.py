"""
Eval harness — scores a detector's deviation findings against ground_truth.json.

Usage:
    python3 eval/run_eval.py                 # scores the deterministic baseline
    python3 eval/run_eval.py --detector llm  # scores the LLM agent (needs GEMINI key)

Reports precision / recall / F1 on deviation DETECTION, plus accuracy of the
commissioning-test PREDICTION on the true positives. These are the exact metrics
the PS4 evaluation focus asks for ("specification compliance detection accuracy
on test cases").
"""

import argparse
import json
import pathlib

CORPUS = pathlib.Path(__file__).parent.parent / "data" / "corpus"


def load_ground_truth():
    gt = json.loads((CORPUS / "ground_truth.json").read_text())
    return gt["seeded_deviations"]


def key(d):
    return (d["component"], d["parameter"])


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

    # commissioning-test prediction accuracy on the true positives
    found_by_key = {key(f): f for f in findings}
    cx_correct = sum(
        1 for k in tp
        if found_by_key[k].get("predicted_cx_test") == gt_by_key[k]["predicted_cx_test"]
    )
    cx_acc = cx_correct / len(tp) if tp else 0.0

    return {
        "tp": sorted(tp), "fp": sorted(fp), "fn": sorted(fn),
        "precision": precision, "recall": recall, "f1": f1,
        "cx_prediction_accuracy": cx_acc,
    }


def get_findings(detector):
    if detector == "baseline":
        from eval.baseline_reconciler import reconcile
        return reconcile()
    elif detector == "llm":
        # Drop-in: the real agent path. Requires GEMINI_API_KEY.
        import sys
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
        from backend.agents.reconciliation import run_reconciliation_over_corpus
        return run_reconciliation_over_corpus()
    raise ValueError(detector)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detector", default="baseline",
                    choices=["baseline", "llm"])
    args = ap.parse_args()

    gt = load_ground_truth()
    findings = get_findings(args.detector)
    r = score(findings, gt)

    print(f"\n=== Pramaan deviation-detection eval [{args.detector}] ===")
    print(f"ground-truth deviations : {len(gt)}")
    print(f"findings                : {len(findings)}")
    print(f"true positives          : {len(r['tp'])}  {r['tp']}")
    print(f"false positives         : {len(r['fp'])}  {r['fp']}")
    print(f"false negatives         : {len(r['fn'])}  {r['fn']}")
    print(f"-----------------------------------------------")
    print(f"precision               : {r['precision']:.3f}")
    print(f"recall                  : {r['recall']:.3f}")
    print(f"F1                      : {r['f1']:.3f}")
    print(f"cx-test prediction acc  : {r['cx_prediction_accuracy']:.3f}")
    print(f"===============================================\n")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    main()
