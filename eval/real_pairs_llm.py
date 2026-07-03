#!/usr/bin/env python3
"""real_pairs_llm.py — the LLM layer over the real-datasheet pairs.

Runs each pair in the shared MANIFEST through the live analysis path
(`run_analysis`: LLM reconcile + citation check + rule fallback) and scores
the findings against the independently-authored ground truth.

Honesty rails:
  - Findings are matched ONE-TO-ONE to ground-truth deviations: each finding is
    credited to at most one label and each label to at most one finding, so a
    single broad finding can never inflate recall across several labels, and any
    unmatched finding is surfaced as a false positive (the count is never a
    negative 'extra').
  - Recall is reported TWO ways, both printed: 'executed' over the pairs that
    actually ran on the live model, and 'PRIMARY' which counts the hard
    deviations of NOT-RUN pairs (quota/outage fell back to the rule engine) as
    misses. The primary number is the honest headline; the executed number shows
    what the model did on what ran. Neither is hidden.
  - The contested pair scores against us either way (that is its job).
  - Exit 0 only if every *executed* hard deviation was recovered and no pair
    produced a false positive against its cleared values.

Usage:
  export GEMINI_API_KEY=...            # billing-enabled recommended
  python eval/real_pairs_llm.py                    # all pairs (~14 calls)
  python eval/real_pairs_llm.py --pairs rack-pdu,aspirating-detection,bms-controller
  make eval-real
"""

import argparse
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from backend.analyze import run_analysis  # noqa: E402
from eval.real_pairs_offline import MANIFEST, REAL  # noqa: E402


def _norm(v):
    return re.sub(r"[^a-z0-9.]+", "", str(v).strip().lower())


STOPWORDS = {"only", "not", "and", "the", "for", "per", "of", "a", "an",
             "under", "every", "with", "available", "provided"}


def _words(s) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", str(s).lower())
            if w not in STOPWORDS and len(w) > 1}


def _matches(gt_dev, finding) -> bool:
    """A finding matches a ground-truth deviation when the required/provided
    values line up (normalised), or — for categorical deviations whose value
    phrasing legitimately varies ('inlet only' vs 'inlet and branch/breaker
    only (per-outlet metering not provided)') — when the parameter name and
    the required-side wording both overlap the same physical fact."""
    fr, fp = _norm(finding.get("required_value")), _norm(finding.get("provided_value"))
    gr, gp = _norm(gt_dev["required"]), _norm(gt_dev["provided"])
    if gr and gp and gr in fr and gp in fp:
        return True
    param_overlap = _words(gt_dev["param"]) & _words(finding.get("parameter"))
    if gp and gp in fp and param_overlap:
        return True
    # Categorical fallback: same parameter concept AND the finding's
    # required/provided wording shares content words with the ground truth.
    req_overlap = _words(gt_dev["required"]) & _words(finding.get("required_value"))
    prov_overlap = _words(gt_dev["provided"]) & _words(finding.get("provided_value"))
    if param_overlap and (req_overlap or prov_overlap):
        return True
    # Decomposition tolerance: the model may split one physical fact into
    # per-function findings (e.g. head-end autonomy reported separately for
    # scheduling/trending/alarming). Strong overlap on BOTH sides of the
    # requirement wording counts as the same fact even without a param match.
    if len(req_overlap) >= 2 and prov_overlap:
        return True
    return False


def score_pair(gt_devs: list[dict], findings: list[dict]) -> dict:
    """One-to-one match findings against a pair's ground-truth deviations.

    Greedy over the ground-truth order: each ground-truth deviation claims the
    first still-unclaimed finding that _matches it, so every finding is credited
    to at most one label and every label is satisfied by at most one finding.
    This kills the two scoring bugs the old code had:
      * a single broad finding can no longer be counted as catching several
        labels (recall inflation);
      * 'extra' can no longer go negative and hide false positives — unmatched
        findings are counted as FP directly.

    Returns per-pair counts and the unmatched (false-positive) findings.
    """
    remaining = list(range(len(findings)))
    matched: dict[int, int] = {}  # gt index -> finding index
    for gi, dev in enumerate(gt_devs):
        for pos, fi in enumerate(remaining):
            if _matches(dev, findings[fi]):
                matched[gi] = fi
                remaining.pop(pos)
                break

    hard_total = hard_caught = 0
    contested_total = contested_caught = 0
    misses: list[str] = []
    per: list[tuple[str, str, str]] = []
    for gi, dev in enumerate(gt_devs):
        caught = gi in matched
        if dev["detection"] == "contested":
            contested_total += 1
            contested_caught += int(caught)
            verdict = "flagged (judgment call)" if caught else "cleared (judgment call)"
        else:
            hard_total += 1
            hard_caught += int(caught)
            verdict = "CAUGHT" if caught else "MISSED"
            if not caught:
                misses.append(dev["param"])
        per.append((dev["param"], dev["detection"], verdict))

    fp_findings = [findings[fi] for fi in remaining]
    return {
        "hard_total": hard_total, "hard_caught": hard_caught,
        "fn": hard_total - hard_caught,
        "contested_total": contested_total, "contested_caught": contested_caught,
        "fp": len(fp_findings), "fp_findings": fp_findings,
        "misses": misses, "per": per,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pairs", default="",
                    help="comma-separated pair ids (default: all)")
    ap.add_argument("--sleep", type=float, default=6.0,
                    help="seconds between pairs (free-tier RPM hygiene)")
    args = ap.parse_args()
    wanted = {p.strip() for p in args.pairs.split(",") if p.strip()}

    ran = skipped = fp_pairs = 0
    hard_total = hard_caught = contested_caught = 0
    total_fp = 0
    not_run_hard = 0          # hard devs of NOT-RUN pairs — misses in the primary metric
    not_run: list[str] = []
    misses: list[str] = []

    print(f"{'=' * 68}")
    print("  PRAMAAN — REAL-DATASHEET LLM EVAL (live reasoning layer)")
    print(f"{'=' * 68}")
    for pair in MANIFEST:
        if wanted and pair["id"] not in wanted:
            continue
        spec = (REAL / pair["spec"]).read_text(encoding="utf-8")
        sub = (REAL / pair["submittal"]).read_text(encoding="utf-8")
        result = run_analysis(spec, sub, pair["id"].upper())
        hard_in_pair = sum(1 for d in pair["devs"] if d["detection"] != "contested")
        if result.mode != "llm":
            print(f"  {pair['id']:<22} NOT-RUN (fell back to rule engine — "
                  "quota/outage; counted as a miss in the PRIMARY metric)")
            not_run.append(pair["id"])
            skipped += 1
            not_run_hard += hard_in_pair
            time.sleep(args.sleep)
            continue
        ran += 1
        s = score_pair(pair["devs"], result.deviations)
        for param, tag, verdict in s["per"]:
            print(f"  {pair['id']:<22} {param:<26} {tag:<10} {verdict}")
        hard_total += s["hard_total"]
        hard_caught += s["hard_caught"]
        contested_caught += s["contested_caught"]
        misses += [f"{pair['id']}:{m}" for m in s["misses"]]
        print(f"  {pair['id']:<22} TP={s['hard_caught']} FN={s['fn']} FP={s['fp']}")
        if s["fp"] > 0:
            fp_pairs += 1
            total_fp += s["fp"]
            for f in s["fp_findings"]:
                print(f"      false positive: param={f.get('parameter')!r} "
                      f"required={f.get('required_value')!r} "
                      f"provided={f.get('provided_value')!r}")
        time.sleep(args.sleep)

    print(f"{'-' * 68}")
    print(f"  pairs executed (llm)    : {ran}   not-run: {skipped} {not_run or ''}")
    exec_recall = hard_caught / hard_total if hard_total else 0.0
    primary_denom = hard_total + not_run_hard
    primary_recall = hard_caught / primary_denom if primary_denom else 0.0
    print(f"  HARD recall (executed)  : {hard_caught}/{hard_total}"
          + (f" = {exec_recall:.3f}" if hard_total else ""))
    print(f"  HARD recall (PRIMARY)   : {hard_caught}/{primary_denom}"
          + (f" = {primary_recall:.3f}" if primary_denom else "")
          + (f"   [{not_run_hard} hard dev(s) in {skipped} not-run pair(s) counted as misses]"
             if not_run_hard else ""))
    if misses:
        print(f"  missed (executed)       : {misses}")
    print(f"  false positives (total) : {total_fp}  in {fp_pairs} pair(s) (0 expected)")
    print(f"{'=' * 68}")
    ok = (hard_total == 0 or hard_caught == hard_total) and total_fp == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
