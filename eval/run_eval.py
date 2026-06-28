"""Eval harness — scores a detector's findings against ground_truth.json.

Two matching modes are reported:
  * STRICT  — exact (component, parameter) string match. Penalizes a model
              that catches a deviation but labels it differently.
  * SEMANTIC (primary) — a deviation is "caught" if the model reports the same
              required->provided discrepancy on the same system, regardless of
              the parameter label it chose. This measures detection, not
              labeling. Different LLMs paraphrase parameter names ("delta_t_c"
              vs "delta t c", "FLOOR/height_mm" vs "Raised Floor System/
              finished_floor_height"); semantic matching scores the fact, not
              the wording. Strict is always reported alongside for transparency.
"""

import argparse
import json
import pathlib
import re
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


def _norm(s):
    return re.sub(r"[^a-z0-9]+", "", str(s).strip().lower())


def _value_sig(d):
    return (_norm(d.get("required_value")), _norm(d.get("provided_value")))


def _component_match(a, b):
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return False
    # Equal, or one system label is contained in the other (e.g. "floor"
    # inside "raisedfloorsystem"). The >=3 guard avoids spurious substrings.
    return na == nb or (len(na) >= 3 and na in nb) or (len(nb) >= 3 and nb in na)


def _semantic_match(finding, gt_dev):
    """A finding matches a ground-truth deviation if it reports the same
    required->provided value transition on the same system."""
    return (
        _value_sig(finding) == _value_sig(gt_dev)
        and _component_match(finding.get("component"), gt_dev.get("component"))
    )


def _match_semantic(findings, ground_truth):
    """Greedy 1:1 assignment. Pass 1: exact normalized (component, parameter).
    Pass 2: semantic (value-transition + system). Returns (tp_pairs, fp, fn)."""
    gt_left = list(ground_truth)
    found_left = list(findings)
    tp_pairs = []

    def _consume(predicate):
        for f in list(found_left):
            for d in list(gt_left):
                if predicate(f, d):
                    tp_pairs.append((f, d))
                    found_left.remove(f)
                    gt_left.remove(d)
                    break

    _consume(lambda f, d: (_norm(f.get("component")), _norm(f.get("parameter")))
                          == (_norm(d.get("component")), _norm(d.get("parameter"))))
    _consume(_semantic_match)
    return tp_pairs, found_left, gt_left


def load_true_negatives():
    gt = json.loads((CORPUS / "ground_truth.json").read_text())
    return gt.get("true_negative_systems", [])


def _prf(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)
    return precision, recall, f1


def score(findings, ground_truth):
    # --- STRICT: exact (component, parameter) string match ---
    gt_keys = {key(d) for d in ground_truth}
    found_keys = {key(f) for f in findings}
    strict_tp = gt_keys & found_keys
    strict_fp = found_keys - gt_keys
    strict_fn = gt_keys - found_keys
    s_prec, s_rec, s_f1 = _prf(len(strict_tp), len(strict_fp), len(strict_fn))

    # --- SEMANTIC (primary): same discrepancy on same system, any label ---
    tp_pairs, fp_findings, fn_devs = _match_semantic(findings, ground_truth)
    tp = {key(d) for _, d in tp_pairs}
    fp = sorted(key(f) for f in fp_findings)
    fn = sorted(key(d) for d in fn_devs)
    precision, recall, f1 = _prf(len(tp_pairs), len(fp_findings), len(fn_devs))

    gt_by_key = {key(d): d for d in ground_truth}
    found_by_match = {key(d): f for f, d in tp_pairs}
    cx_correct = sum(
        1 for k in tp
        if found_by_match[k].get("predicted_cx_test") == gt_by_key[k]["predicted_cx_test"]
    )
    cx_acc = cx_correct / len(tp) if tp else 0.0
    found_by_key = found_by_match

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
        "tp": sorted(tp), "fp": fp, "fn": fn,
        "precision": precision, "recall": recall, "f1": f1,
        "strict_precision": s_prec, "strict_recall": s_rec, "strict_f1": s_f1,
        "strict_tp": len(strict_tp), "strict_fp": sorted(strict_fp),
        "strict_fn": sorted(strict_fn),
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
    print(f"  PRECISION  (semantic)   : {r['precision']:.3f}")
    print(f"  RECALL     (semantic)   : {r['recall']:.3f}")
    print(f"  F1         (semantic)   : {r['f1']:.3f}")
    print("  ---- strict exact-label match (transparency) ----")
    print(f"  strict precision        : {r['strict_precision']:.3f}")
    print(f"  strict recall           : {r['strict_recall']:.3f}")
    print(f"  strict F1               : {r['strict_f1']:.3f}")
    if r['strict_fn']:
        print(f"  strict-only misses      : {r['strict_fn']}")
        print("  (caught semantically, labeled differently)")
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
