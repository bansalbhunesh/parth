#!/usr/bin/env python3
"""real_pairs_llm.py — the LLM layer over the real-datasheet pairs.

Runs each pair in the shared MANIFEST through the live analysis path
(`run_analysis`: LLM reconcile + citation check + rule fallback) and scores
the findings against the independently-authored ground truth.

Honesty rails:
  - A pair whose analysis fell back to the rule engine (quota/outage) is
    reported as NOT-RUN, never as a recall miss. Free-tier Gemini keys allow
    ~20 requests/day; partial runs must not read as reasoning failures.
  - The contested pair scores against us either way (that is its job).
  - Exit 0 only if every *executed* hard deviation was recovered and no
    pair produced a false positive against its cleared values.

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
        if result.mode != "llm":
            print(f"  {pair['id']:<22} NOT-RUN (fell back to rule engine — "
                  "quota/outage; not a miss)")
            not_run.append(pair["id"])
            skipped += 1
            time.sleep(args.sleep)
            continue
        ran += 1
        extra = len(result.deviations)
        for dev in pair["devs"]:
            caught = any(_matches(dev, f) for f in result.deviations)
            if caught:
                extra -= 1
            tag = dev["detection"]
            if tag == "contested":
                contested_caught += 1 if caught else 0
                verdict = "flagged (judgment call)" if caught else "cleared (judgment call)"
            else:
                hard_total += 1
                hard_caught += 1 if caught else 0
                verdict = "CAUGHT" if caught else "MISSED"
                if not caught:
                    misses.append(f"{pair['id']}:{dev['param']}")
            print(f"  {pair['id']:<22} {dev['param']:<26} {tag:<10} {verdict}")
        # Findings beyond ground truth are potential false positives against
        # the pair's deliberately-compliant values — surface, don't hide.
        if extra > 0:
            fp_pairs += 1
            print(f"  {pair['id']:<22} !! {extra} finding(s) beyond ground truth "
                  "— review for false positives")
            matched_ids = {id(f) for f in result.deviations
                           if any(_matches(d, f) for d in pair["devs"])}
            for f in result.deviations:
                if id(f) not in matched_ids:
                    print(f"      unmatched: param={f.get('parameter')!r} "
                          f"required={f.get('required_value')!r} "
                          f"provided={f.get('provided_value')!r}")
        time.sleep(args.sleep)

    print(f"{'-' * 68}")
    print(f"  pairs executed (llm)    : {ran}   not-run: {skipped} {not_run or ''}")
    print(f"  HARD recall (executed)  : {hard_caught}/{hard_total}"
          + (f" = {hard_caught / hard_total:.3f}" if hard_total else ""))
    if misses:
        print(f"  missed                  : {misses}")
    print(f"  pairs with extra finds  : {fp_pairs} (0 expected)")
    print(f"{'=' * 68}")
    ok = (hard_total == 0 or hard_caught == hard_total) and fp_pairs == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
