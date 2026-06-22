"""
Baseline reconciler (deterministic).

Compares perfectly-extracted requirement triples against submittal triples and
flags mismatches, attaching the commissioning-test prediction. This is:
  (a) a correctness proof for the eval harness + register schema, and
  (b) an honest BASELINE for the Technical Excellence rubric ("vs baseline").

The REAL product (backend/agents/reconciliation.py) replaces this with an LLM
agent that recovers the same deviations from RAW, unstructured documents and
reasons against the standards corpus — a far harder task this baseline cannot do.
"""

import json
import pathlib

CORPUS = pathlib.Path(__file__).parent.parent / "data" / "corpus"


def _load(p):
    return json.loads((CORPUS / p).read_text())


def reconcile():
    reqs = _load("extracted/requirements.json")
    subs = {(s["component"], s["parameter"]): s
            for s in _load("extracted/submittals.json")}
    gt = _load("ground_truth.json")
    # cx mapping is embedded in ground truth for the baseline's prediction step
    cx_by_key = {(d["component"], d["parameter"]): d
                 for d in gt["seeded_deviations"]}

    findings = []
    for r in reqs:
        key = (r["component"], r["parameter"])
        sub = subs.get(key)
        if not sub:
            continue
        required = r["required_value"]
        provided = sub["provided_value"]
        if str(provided) != str(required):
            cx = cx_by_key.get(key, {})
            findings.append({
                "component": r["component"],
                "parameter": r["parameter"],
                "required_value": required,
                "provided_value": provided,
                "unit": r["unit"],
                "standard_ref": r["standard_ref"],
                "spec_clause": r["clause"],
                "severity": cx.get("severity", "Major"),
                "predicted_cx_test": cx.get("predicted_cx_test"),
                "predicted_cx_level": cx.get("predicted_cx_level"),
                "lead_time_weeks": cx.get("lead_time_weeks"),
            })
    return findings


if __name__ == "__main__":
    for f in reconcile():
        print(f"{f['component']}.{f['parameter']}: "
              f"{f['provided_value']} vs {f['required_value']} {f['unit']} "
              f"-> {f['predicted_cx_test']} (lead {f['lead_time_weeks']}w)")
