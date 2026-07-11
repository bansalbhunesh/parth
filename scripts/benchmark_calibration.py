#!/usr/bin/env python3
"""benchmark_calibration.py — stratified confidence intervals for the frozen
ps4_external_v1 benchmark, so the headline recall isn't the only number a
reviewer can see.

Naming note: this is NOT a probabilistic calibration curve (predicted-
probability vs. observed-frequency, a la a reliability diagram) — Pramaan's
pipeline reports a binary catch/miss per label, not a per-finding confidence
score, so there is nothing to calibrate in that sense. What this script
actually produces — stratified recall with Wilson score confidence intervals
by system type, difficulty class, modality, and construction batch — is the
closest honest analogue, and the audit gap this closes ("avoid emphasizing
only pooled means") is about exactly this: whether the headline 0.862 hides
strata that perform very differently, not about probability calibration.

Stdlib only (matches benchmark_lib.py's constraint — CI installs only
backend/requirements.txt + pytest/ruff/pip-audit/bandit, no numpy/scipy).

Usage: python scripts/benchmark_calibration.py
Writes: benchmarks/ps4_external_v1/reports/calibration_report.md
        benchmarks/ps4_external_v1/reports/calibration.json
"""

import csv
import json
import math
import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402

FEATURED_MODEL = "google/gemini-3.1-flash-lite"
REPORTS = L.BENCH / "reports"
RUNS = L.BENCH / "runs"

# Label types that count as a genuine positive deviation the model must catch
# (excludes clean_negative and ambiguous_contested) — verified to reproduce
# recall_mean=0.862 / exact_recall_mean=0.698 in the committed benchmark_card.json
# exactly before this script is trusted for anything downstream of that.
POSITIVE_TYPES = {"positive_deviation", "omission", "ocr_extraction_case", "adversarial_instruction"}

# The construction-batch split used as a "project holdout" proxy: pairs 1-15
# are the original hand-authored real-evidence set (2026-06-28, cited public
# vendor/standard values, see data/samples/real/PROVENANCE.md's methodology);
# pairs 16-53 are the later expansion batch (2026-07-03/04). If recall on the
# earlier set doesn't hold on the later, larger set, pooling both into one
# headline number would be hiding that, not just averaging it.
EARLY_BATCH_MAX_PAIR = 15


def _model_runs() -> list[pathlib.Path]:
    """Same selection rule as scripts/benchmark_report.py's _model_runs: every
    run directory whose summary.json reports mode=="llm" and this model,
    sorted by directory name. Dynamic, not hardcoded to run1/2/3, so a future
    run4 is picked up automatically."""
    out = []
    for d in sorted(RUNS.glob("*")):
        sp = d / "summary.json"
        if not sp.exists():
            continue
        s = json.loads(sp.read_text(encoding="utf-8"))
        if s.get("mode") == "llm" and s.get("model") == FEATURED_MODEL:
            out.append(d)
    return out


def _load_labels(run_dir: pathlib.Path) -> list[dict]:
    path = run_dir / "per_label_results.csv"
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score interval for a binomial proportion (95% by default).
    Preferred over the normal approximation at the sample sizes here (some
    strata have single-digit n) — it doesn't produce an out-of-[0,1] bound
    and is markedly less overconfident than +/- 1.96*sqrt(p(1-p)/n) when n
    is small. Returns (point_estimate, lower, upper)."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half_width = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (round(p, 4), round(max(0.0, center - half_width), 4), round(min(1.0, center + half_width), 4))


def _bar(p: float, width: int = 20) -> str:
    filled = round(p * width)
    return "#" * filled + "-" * (width - filled)


def _stratum_table(rows: list[dict], key_fn, title: str, min_n_warn: int = 10) -> tuple[str, dict]:
    """Pools (label, run) as independent Bernoulli trials within each stratum
    (each run is a genuinely separate LLM call over the same label — treating
    the 3 runs as repeated trials, not just averaging 3 point estimates,
    tightens the interval honestly instead of hiding run-to-run agreement)."""
    buckets: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        buckets[key_fn(r)].append(int(r["caught_semantic"]))

    lines = [f"### {title}", "", "| Stratum | n (label x pass) | Recall | 95% Wilson CI | |", "|---|---:|---:|---|---|"]
    out = {}
    for k in sorted(buckets, key=lambda x: -len(buckets[x])):
        vals = buckets[k]
        n = len(vals)
        successes = sum(vals)
        p, lo, hi = wilson_ci(successes, n)
        flag = " ⚠ small n" if n < min_n_warn else ""
        lines.append(f"| {k} | {n} | {p:.3f} | [{lo:.3f}, {hi:.3f}]{flag} | `{_bar(p)}` |")
        out[k] = {"n": n, "successes": successes, "recall": p, "ci95_low": lo, "ci95_high": hi}
    return "\n".join(lines), out


def main() -> None:
    run_dirs = _model_runs()
    if not run_dirs:
        print("No completed LLM runs found for", FEATURED_MODEL, "- nothing to analyze.")
        return

    all_rows: list[dict] = []
    for d in run_dirs:
        all_rows.extend(_load_labels(d))

    positive_rows = [r for r in all_rows if r["label_type"] in POSITIVE_TYPES]
    negative_rows = [r for r in all_rows if r["label_type"] == "clean_negative"]

    # Sanity check against the committed benchmark_card.json before anything
    # downstream is trusted — if this drifts, the strata below would too.
    per_run_recall = []
    for d in run_dirs:
        rows = [r for r in _load_labels(d) if r["label_type"] in POSITIVE_TYPES]
        per_run_recall.append(sum(int(r["caught_semantic"]) for r in rows) / len(rows))
    card = json.loads((REPORTS / "benchmark_card.json").read_text(encoding="utf-8"))
    card_mean = card["primary_result"]["recall_mean"]
    computed_mean = round(sum(per_run_recall) / len(per_run_recall), 3)
    if abs(computed_mean - card_mean) > 0.001:
        print(f"WARNING: recomputed recall_mean {computed_mean} != benchmark_card.json's "
              f"{card_mean} - per_label_results.csv and benchmark_card.json have drifted "
              f"apart. Re-run scripts/benchmark_report.py before trusting this report.")

    overall_p, overall_lo, overall_hi = wilson_ci(
        sum(int(r["caught_semantic"]) for r in positive_rows), len(positive_rows))
    far_p, far_lo, far_hi = wilson_ci(
        sum(int(r["caught_semantic"]) for r in negative_rows), len(negative_rows))

    sys_table, sys_data = _stratum_table(positive_rows, lambda r: r["system_type"], "By system type")
    diff_table, diff_data = _stratum_table(positive_rows, lambda r: r["difficulty"], "By difficulty class")
    mod_table, mod_data = _stratum_table(positive_rows, lambda r: r["modality"], "By modality")
    batch_table, batch_data = _stratum_table(
        positive_rows,
        lambda r: ("pairs 1-15 (original real-evidence set, 2026-06-28)"
                   if int(r["pair_id"].split("_")[1]) <= EARLY_BATCH_MAX_PAIR
                   else "pairs 16-53 (expansion batch, 2026-07-03/04)"),
        "By construction batch (project-holdout proxy)",
        min_n_warn=20,
    )

    # Surface strata whose CI doesn't overlap the overall interval at all —
    # the exact "pooled mean hides a real gap" pattern this report exists to
    # catch, called out explicitly instead of left for a reader to spot
    # inside a 30-row table (n>=10 only: small-n outliers get flagged in the
    # tables themselves but aren't strong enough evidence for a headline claim).
    notable = []
    for label, data in (("system type", sys_data), ("difficulty class", diff_data), ("modality", mod_data)):
        for stratum, d in data.items():
            if d["n"] >= 10 and d["ci95_high"] < overall_lo:
                notable.append((label, stratum, d))
    notable.sort(key=lambda t: t[2]["recall"])

    notable_section = ""
    if notable:
        rows = "\n".join(
            f"- **{label} = `{stratum}`**: recall {d['recall']:.3f} "
            f"[{d['ci95_low']:.3f}, {d['ci95_high']:.3f}], n={d['n']} — "
            f"this interval sits entirely below the overall recall interval "
            f"[{overall_lo:.3f}, {overall_hi:.3f}]; not noise, a real gap."
            for label, stratum, d in notable
        )
        notable_section = f"""
## Notable findings — strata that do NOT overlap the headline number

{rows}

This is the specific thing "avoid emphasizing only pooled means" is about:
the headline {overall_p:.3f} is a true average, but it is not a representative
number for the stratum/strata above. A reviewer relying on the headline alone
would materially overestimate performance on that slice.
"""

    report = f"""# Calibration Report — ps4_external_v1, {FEATURED_MODEL}

Generated by `scripts/benchmark_calibration.py` from {len(run_dirs)} completed
passes ({", ".join(d.name for d in run_dirs)}). Wilson score 95% confidence
intervals, not the normal approximation — several strata below have fewer
than 10 label-pass observations, where a normal-approximation interval can
overstate precision or exceed [0,1].

**This is a stratified robustness analysis, not a probability-calibration
curve.** Pramaan reports a binary catch/miss per label, not a per-finding
confidence score, so there is no predicted-probability axis to calibrate
against a reliability diagram — see this file's module docstring for the
full distinction.
{notable_section}
## Overall (matches benchmark_card.json)

| Metric | Point estimate | 95% Wilson CI | n |
|---|---:|---|---:|
| Recall (positive labels) | {overall_p:.3f} | [{overall_lo:.3f}, {overall_hi:.3f}] | {len(positive_rows)} |
| False-alert rate (clean negatives) | {far_p:.3f} | [{far_lo:.3f}, {far_hi:.3f}] | {len(negative_rows)} |

{sys_table}

{diff_table}

{mod_table}

{batch_table}

## Reading this honestly

- Strata flagged **small n** (fewer than 10 label-pass observations, fewer
  than 20 for the batch split) have wide intervals for a real reason — there
  is not enough data in that slice to say more than the interval says. A
  91% point estimate on n=9 is not the same claim as 91% on n=180, and the
  CI column is what actually carries that distinction; the point-estimate
  column alone would hide it.
- Any stratum whose CI does not overlap the overall recall interval is a
  real, not-noise difference from the headline number — that is precisely
  what "pooled means hide" looks like, made visible instead of hidden.
- This report is generated from the 3 completed `{FEATURED_MODEL}` passes
  already in `benchmarks/ps4_external_v1/runs/` — it does not run a new
  model call, and re-running it against the same run directories reproduces
  identical numbers.
"""
    (REPORTS / "calibration_report.md").write_text(report, encoding="utf-8")

    payload = {
        "featured_model": FEATURED_MODEL,
        "passes": [d.name for d in run_dirs],
        "overall": {"recall": overall_p, "ci95_low": overall_lo, "ci95_high": overall_hi, "n": len(positive_rows)},
        "false_alert_rate": {"rate": far_p, "ci95_low": far_lo, "ci95_high": far_hi, "n": len(negative_rows)},
        "by_system_type": sys_data,
        "by_difficulty": diff_data,
        "by_modality": mod_data,
        "by_construction_batch": batch_data,
    }
    (REPORTS / "calibration.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {REPORTS / 'calibration_report.md'} and {REPORTS / 'calibration.json'}")
    print(f"Overall recall: {overall_p:.3f} [{overall_lo:.3f}, {overall_hi:.3f}], n={len(positive_rows)}")


if __name__ == "__main__":
    main()
