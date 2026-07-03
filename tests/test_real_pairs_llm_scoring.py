"""P0-4 / P1-1 — the real-pair LLM scorer must match one-to-one.

The old scorer let a single broad finding be credited to several ground-truth
labels (inflating recall) and decremented an 'extra' counter per matched label
so it could go negative and hide false positives. These tests pin the corrected
behaviour of `score_pair`: bipartite (greedy) one-to-one matching, FN surfaced,
and false positives counted directly (never negative).
"""

from eval.real_pairs_llm import score_pair


def _gt(param, req, prov, detection="llm"):
    return {"param": param, "required": req, "provided": prov, "detection": detection}


def _f(param, req, prov):
    return {"parameter": param, "required_value": req, "provided_value": prov}


def test_one_finding_cannot_satisfy_two_labels():
    # Two identical hard labels, one finding: exactly ONE is caught, the other
    # is a miss (the old code credited both -> recall inflation).
    gt = [_gt("battery", "10", "7"), _gt("battery", "10", "7")]
    findings = [_f("battery", "10", "7")]
    s = score_pair(gt, findings)
    assert s["hard_total"] == 2
    assert s["hard_caught"] == 1
    assert s["fn"] == 1
    assert s["fp"] == 0


def test_extra_findings_count_as_false_positives_never_negative():
    gt = [_gt("battery", "10", "7")]
    findings = [
        _f("battery", "10", "7"),      # the true match
        _f("humidity", "5", "3"),      # unmatched -> FP
        _f("voltage", "99", "1"),      # unmatched -> FP
    ]
    s = score_pair(gt, findings)
    assert s["hard_caught"] == 1
    assert s["fp"] == 2                 # counted directly, not a negative 'extra'
    assert s["fp"] >= 0
    assert len(s["fp_findings"]) == 2


def test_clean_full_match_no_fp_no_fn():
    gt = [_gt("battery", "10", "7"), _gt("efficiency", "96", "95.9", "offline")]
    findings = [_f("battery", "10", "7"), _f("efficiency", "96", "95.9")]
    s = score_pair(gt, findings)
    assert s["hard_total"] == 2
    assert s["hard_caught"] == 2
    assert s["fn"] == 0
    assert s["fp"] == 0


def test_contested_is_separate_and_not_a_false_positive():
    gt = [_gt("setpoint", "27", "30", detection="contested")]
    # A finding that matches the contested dev is NOT a hard TP and NOT an FP.
    s = score_pair(gt, [_f("setpoint", "27", "30")])
    assert s["hard_total"] == 0
    assert s["contested_total"] == 1
    assert s["contested_caught"] == 1
    assert s["fp"] == 0
    # And with no finding, the contested dev is simply cleared, still no hard math.
    s2 = score_pair(gt, [])
    assert s2["hard_total"] == 0
    assert s2["contested_caught"] == 0
    assert s2["fp"] == 0
