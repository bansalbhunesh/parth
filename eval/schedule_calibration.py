"""Honest calibration check for the schedule-risk Monte Carlo.

This is NOT a real-world delay-prediction accuracy claim — published EPC delay
models top out around 71% accuracy / 0.82 AUC, and our schedule data is synthetic.
What it measures is whether the simulation is *internally calibrated*: does the P80
finish week actually contain ~80% of independently-sampled outcomes, and how does
that calibration degrade under model misspecification (an optimism-biased plan)?

On synthetic data, calibration — not accuracy — is the defensible metric, and the
honest story is "our 80% predictions come true ~80% of the time (and here's how
that erodes if the real durations run longer than planned)."
"""

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.agents import schedule_risk  # noqa: E402


def load_meghdoot_schedule() -> dict:
    d = ROOT / "data" / "corpus"
    sch = json.loads((d / "schedule.json").read_text(encoding="utf-8"))
    gt = json.loads((d / "ground_truth.json").read_text(encoding="utf-8"))
    sch["risks"] = schedule_risk.derive_risks(sch, gt.get("seeded_deviations", []))
    return sch


def _perturb(tasks: list[dict], factor: float) -> list[dict]:
    """Inflate the most-likely/pessimistic durations — a stand-in for an
    optimism-biased plan where real work runs `factor`x longer than estimated."""
    out = []
    for t in tasks:
        t2 = dict(t)
        d = t.get("duration", {})
        if "fixed" not in d:
            t2["duration"] = {
                "optimistic": d["optimistic"],
                "most_likely": d["most_likely"] * factor,
                "pessimistic": d["pessimistic"] * factor,
            }
        out.append(t2)
    return out


def _coverage(actuals: np.ndarray, q: float) -> float:
    return float(np.mean(actuals <= q))


def calibration_report(schedule: dict, n: int = 20000, seed: int = 11) -> dict:
    tasks = schedule["tasks"]
    risks = schedule.get("risks", [])
    pred = schedule_risk.simulate_finish(tasks, risks, n=n, seed=seed)
    p50, p80, p90 = (float(x) for x in np.percentile(pred, [50, 80, 90]))
    self_actual = schedule_risk.simulate_finish(tasks, risks, n=n, seed=seed + 1)
    biased = schedule_risk.simulate_finish(_perturb(tasks, 1.08), risks, n=n, seed=seed + 2)
    return {
        "p50": round(p50, 1), "p80": round(p80, 1), "p90": round(p90, 1),
        "self_coverage": {
            "p50": round(_coverage(self_actual, p50), 3),
            "p80": round(_coverage(self_actual, p80), 3),
            "p90": round(_coverage(self_actual, p90), 3),
        },
        "optimism_bias_coverage": {
            "p50": round(_coverage(biased, p50), 3),
            "p80": round(_coverage(biased, p80), 3),
            "p90": round(_coverage(biased, p90), 3),
        },
    }


def main() -> None:
    rep = calibration_report(load_meghdoot_schedule())
    print("Schedule-risk Monte-Carlo calibration — Project Meghdoot")
    print(f"  Predicted finish:  P50 {rep['p50']}  P80 {rep['p80']}  P90 {rep['p90']} weeks")
    print(f"  Self-calibration (targets .50/.80/.90): {rep['self_coverage']}")
    print(f"  Under +8% optimism bias:                {rep['optimism_bias_coverage']}")
    print("  Honest read: the P-levels are well-calibrated to the model; an optimism-biased")
    print("  plan shifts real coverage below target. This measures calibration on synthetic")
    print("  data, NOT field-validated delay-prediction accuracy.")


if __name__ == "__main__":
    main()
