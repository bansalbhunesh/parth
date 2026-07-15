#!/usr/bin/env python3
"""Compare a clean three-pass branch series with the published primary series."""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402

FEATURED_MODEL = "google/gemini-3.1-flash-lite"
RUNS = L.BENCH / "runs"
REPORTS = L.BENCH / "reports"


def _load_runs() -> list[dict]:
    runs = []
    for directory in sorted(RUNS.iterdir()):
        summary_path = directory / "summary.json"
        if not summary_path.exists():
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["_dir"] = directory.name
        runs.append(summary)
    return runs


def _metrics(summary: dict) -> dict[str, float]:
    positives = int(summary["positive_labels"])
    tp = int(summary["primary_tp"])
    fp = int(summary["false_positives_total"])
    recall = tp / positives if positives else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "recall": recall,
        "precision": precision,
        "f1": f1,
        "exact_recall": float(summary["primary_recall_exact"]),
        "clean_far": float(summary["clean_negative_false_alert_rate"]),
        "false_positives": float(fp),
        "p50_ms": float(summary["latency_p50_ms"]),
        "p95_ms": float(summary["latency_p95_ms"]),
        "not_run": float(summary["pairs_not_run"]),
    }


def _aggregate(runs: list[dict]) -> dict:
    rows = [_metrics(run) for run in runs]
    keys = rows[0]
    return {
        **{f"{key}_mean": round(statistics.mean(row[key] for row in rows), 4) for key in keys},
        "passes": len(runs),
        "run_dirs": [run["_dir"] for run in runs],
        "code_revisions": sorted({run.get("code_revision", "unknown") for run in runs}),
        "providers_used": sorted({
            provider
            for run in runs
            for provider in (run.get("providers_used") or {})
        }),
    }


def _select_series(runs: list[dict], run_tag: str) -> tuple[list[dict], list[dict]]:
    main = [run for run in runs if L.is_featured_primary_run(run, FEATURED_MODEL)]
    branch = [
        run for run in runs
        if run.get("mode") == "llm"
        and run.get("model") == FEATURED_MODEL
        and run.get("run_tag") == run_tag
        and run.get("publication_role") == "branch-comparison"
        and run.get("repeats_total") == 3
        and run.get("prompt_mode", "baseline") == "baseline"
        and not run.get("worktree_dirty", False)
    ]
    return sorted(main, key=lambda run: run["_dir"]), sorted(branch, key=lambda run: run["repeat_index"])


def _validate(main: list[dict], branch: list[dict]) -> None:
    if len(main) != 3:
        raise ValueError(f"expected exactly 3 published primary passes, found {len(main)}")
    if len(branch) != 3:
        raise ValueError(f"expected exactly 3 branch-comparison passes, found {len(branch)}")
    if {run["repeat_index"] for run in branch} != {1, 2, 3}:
        raise ValueError("branch comparison must contain repeat indexes 1, 2, and 3")
    branch_revisions = {run.get("code_revision") for run in branch}
    if len(branch_revisions) != 1:
        raise ValueError("branch passes do not share one exact code revision")
    hashes = {run.get("labels_freeze_sha256") for run in [*main, *branch]}
    if len(hashes) != 1:
        raise ValueError("main and branch do not share the frozen label hash")


def _verdict(main: dict, branch: dict) -> str:
    if (
        branch["recall_mean"] >= main["recall_mean"]
        and branch["f1_mean"] >= main["f1_mean"]
        and branch["clean_far_mean"] <= main["clean_far_mean"]
    ):
        return "branch_stronger"
    if branch["recall_mean"] < main["recall_mean"] and branch["f1_mean"] < main["f1_mean"]:
        return "main_stronger"
    return "mixed"


def build_comparison(run_tag: str) -> dict:
    main_runs, branch_runs = _select_series(_load_runs(), run_tag)
    _validate(main_runs, branch_runs)
    main = _aggregate(main_runs)
    branch = _aggregate(branch_runs)
    return {
        "benchmark": "ps4_external_v1",
        "model": FEATURED_MODEL,
        "run_tag": run_tag,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "main": main,
        "branch": branch,
        "delta_branch_minus_main": {
            key: round(branch[key] - main[key], 4)
            for key in (
                "recall_mean", "precision_mean", "f1_mean", "exact_recall_mean",
                "clean_far_mean", "false_positives_mean", "p50_ms_mean", "p95_ms_mean",
            )
        },
        "verdict": _verdict(main, branch),
        "complete_vision_branch": branch["not_run_mean"] == 0,
        "limitations": [
            "Three passes estimate run-to-run variation but do not establish field accuracy.",
            "The benchmark sources and labels remain team-authored and single-author frozen.",
            "The published main summaries predate exact code-revision and "
            "provider-used metadata, so this is same-model/dataset evidence "
            "rather than an isolated code-only A/B test.",
            "Main averaged 0.333 not-run pairs; branch ran every pair including "
            "vision, so recall also reflects evaluation completeness.",
        ],
    }


def _markdown(result: dict) -> str:
    main, branch = result["main"], result["branch"]
    rows = [
        ("Semantic recall", "recall_mean"),
        ("Precision", "precision_mean"),
        ("F1", "f1_mean"),
        ("Exact recall", "exact_recall_mean"),
        ("Clean-negative FAR", "clean_far_mean"),
        ("False positives", "false_positives_mean"),
        ("Latency p50 (ms)", "p50_ms_mean"),
        ("Latency p95 (ms)", "p95_ms_mean"),
        ("Not-run pairs", "not_run_mean"),
    ]
    table = "\n".join(
        f"| {label} | {main[key]:.4f} | {branch[key]:.4f} | {branch[key] - main[key]:+.4f} |"
        for label, key in rows
    )
    limitations = "\n".join(f"- {item}" for item in result["limitations"])
    return f"""# Main vs branch — clean three-pass comparison

Generated `{result['generated_utc']}` from frozen `ps4_external_v1` evidence.

| Metric | Main published series | Branch `{result['run_tag']}` | Δ branch − main |
|---|---:|---:|---:|
{table}

**Verdict:** `{result['verdict']}`

**Branch vision completeness:** `{result['complete_vision_branch']}`

**Branch revision:** `{', '.join(branch['code_revisions'])}`

Main runs: {', '.join(f'`{name}`' for name in main['run_dirs'])}

Branch runs: {', '.join(f'`{name}`' for name in branch['run_dirs'])}

## Limitations

{limitations}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-tag", required=True)
    parser.add_argument("--output-stem", default="branch_vs_main")
    args = parser.parse_args()
    result = build_comparison(args.run_tag)
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS / f"{args.output_stem}.json"
    md_path = REPORTS / f"{args.output_stem}.md"
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_markdown(result), encoding="utf-8")
    print(f"Wrote {json_path.relative_to(L.ROOT)} and {md_path.relative_to(L.ROOT)}")
    print(f"Verdict: {result['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
