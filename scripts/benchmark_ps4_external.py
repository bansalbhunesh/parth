#!/usr/bin/env python3
"""benchmark_ps4_external.py — run the PS4 external benchmark and score it.

  python scripts/benchmark_ps4_external.py --mode rule
  python scripts/benchmark_ps4_external.py --mode llm --provider gemini --repeat 3

Rule mode uses the deterministic detector only (no key). LLM mode uses the live
analysis path; a pair that falls back to the rule engine or errors is recorded
`not_run` (never fabricated) and counts as a miss in the PRIMARY metric. Each run
writes a self-contained directory under runs/.
"""

import argparse
import csv
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402

sys.path.insert(0, str(L.ROOT))
from backend.agents.reconciliation import (  # noqa: E402
    COVERAGE_MATRIX_ENV,
    active_prompt_version,
)
from backend.analyze import _resilient_fallback, run_analysis  # noqa: E402

PROMPT_MODE_BASELINE = "baseline"
PROMPT_MODE_COVERAGE_MATRIX = "coverage-matrix-v1.7"

PER_PAIR_COLUMNS = [
    "pair_id", "system_type", "modality", "mode_used", "provider_used", "not_run",
    "error_type", "latency_ms",
    "positives", "negatives", "contested", "tp_exact", "tp_semantic",
    "fp", "fn_semantic", "neg_false_alerts", "error",
]


def _read_pair(pair_id: str, bench_dir: pathlib.Path = L.BENCH):
    d = bench_dir / "pairs" / pair_id
    return (d / "owner_requirement.md").read_text(encoding="utf-8"), \
           (d / "vendor_submittal.md").read_text(encoding="utf-8")


def run_one(
    pair_id: str,
    labels: list[dict],
    mode: str,
    bench_dir: pathlib.Path = L.BENCH,
) -> dict:
    owner, sub = _read_pair(pair_id, bench_dir)
    system_id = pair_id.upper()
    modality = labels[0].get("modality", "text") if labels else "text"
    err = err_type = None
    provider_used = None
    not_run = False
    t0 = time.time()
    if modality == "image":
        png = bench_dir / "pairs" / pair_id / "vendor_submittal.png"
        if mode == "llm" and png.exists():
            # Read values straight from the rendered image via the vision path.
            try:
                from backend.analyze import run_vision_analysis
                res = run_vision_analysis(owner, png.read_bytes(), "image/png", system_id)
                findings, mode_used, latency = res.deviations, res.mode, res.elapsed_ms
                provider_used = res.provider if res.mode == "vision" else None
                if res.mode != "vision":  # vision-unavailable → not an image result
                    not_run = True
                    err, err_type = "vision unavailable (provider/parse failure)", "vision_unavailable"
            except Exception as exc:  # record the failure, never fabricate
                findings, mode_used, not_run = [], "error", True
                latency = round((time.time() - t0) * 1000)
                err, err_type = f"{type(exc).__name__}: {str(exc)[:200]}", type(exc).__name__
        else:
            # rule mode (or no image on disk) — not evaluated here; recorded
            # not_run (a PRIMARY-metric miss) rather than fabricating a prediction.
            findings, mode_used, not_run, latency = [], "image_pending", True, 0
            err = "modality=image; vision runs only in --mode llm"
            err_type = "image_pending"
    elif mode == "rule":
        findings = _resilient_fallback(owner, sub, system_id)
        mode_used = "rule"
        latency = round((time.time() - t0) * 1000)
    else:
        try:
            res = run_analysis(owner, sub, system_id)
            findings = res.deviations
            mode_used = res.mode
            provider_used = res.provider
            latency = res.elapsed_ms
            if res.mode != "llm":
                not_run = True  # fell back to the rule engine — not an LLM result
        except Exception as exc:  # record the failure, never fabricate a prediction
            findings, mode_used, not_run = [], "error", True
            latency = round((time.time() - t0) * 1000)
            err = f"{type(exc).__name__}: {str(exc)[:200]}"
            err_type = type(exc).__name__

    sem = L.score_pair(labels, findings, L.matches_semantic)
    exa = L.score_pair(labels, findings, L.matches_exact)
    return {
        "pair_id": pair_id,
        "system_type": labels[0]["system_type"] if labels else "other",
        "modality": modality, "error_type": err_type,
        "mode_used": mode_used, "provider_used": provider_used,
        "not_run": not_run, "latency_ms": latency,
        "positives": sem["positives"], "negatives": sem["negatives"], "contested": sem["contested"],
        "tp_semantic": sem["tp"], "tp_exact": exa["tp"], "fp": sem["fp"], "fn_semantic": sem["fn"],
        "neg_false_alerts": sem["neg_false_alerts"],
        "matched_semantic": sem["matched_labels"], "matched_exact": exa["matched_labels"],
        "missed_semantic": sem["missed_labels"],
        "error": err,
        "input_sha256": L.sha256_text(owner + "\n---\n" + sub),
        "output_sha256": L.sha256_text(json.dumps(findings, sort_keys=True, ensure_ascii=False)),
        "_findings": findings,
    }


def _write_run(
    run_dir: pathlib.Path,
    results: list[dict],
    meta: dict,
    labels: list[dict] | None = None,
) -> dict:
    if run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(
            f"immutable benchmark run already exists: {run_dir}; use --run-tag"
        )
    run_dir.mkdir(parents=True, exist_ok=True)
    # run_config.yaml (flat)
    (run_dir / "run_config.yaml").write_text(
        "".join(f"{k}: {v}\n" for k, v in meta.items()), encoding="utf-8")
    # predictions.jsonl
    with (run_dir / "predictions.jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps({
                "pair_id": r["pair_id"], "mode_used": r["mode_used"], "not_run": r["not_run"],
                "provider_used": r["provider_used"],
                "latency_ms": r["latency_ms"], "input_sha256": r["input_sha256"],
                "output_sha256": r["output_sha256"], "findings": r["_findings"],
            }, ensure_ascii=False) + "\n")
    # per_pair_results.csv
    with (run_dir / "per_pair_results.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PER_PAIR_COLUMNS)
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k) for k in PER_PAIR_COLUMNS})
    # errors.jsonl
    with (run_dir / "errors.jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            if r.get("error"):
                f.write(json.dumps({"pair_id": r["pair_id"], "error": r["error"]}) + "\n")
    # per_label_results.csv (per-label TP/FP/FN visibility)
    labs = labels if labels is not None else load_labels_flat()
    caught_s, caught_e = set(), set()
    for r in results:
        if not r["not_run"]:
            caught_s.update(r.get("matched_semantic", []))
            caught_e.update(r.get("matched_exact", []))
    with (run_dir / "per_label_results.csv").open("w", encoding="utf-8", newline="") as f:
        wl = csv.writer(f)
        wl.writerow(["label_id", "pair_id", "system_type", "label_type", "difficulty",
                     "modality", "caught_semantic", "caught_exact"])
        for lb in labs:
            wl.writerow([lb["label_id"], lb["pair_id"], lb["system_type"], lb["label_type"],
                         lb["difficulty"], lb.get("modality", "text"),
                         int(lb["label_id"] in caught_s), int(lb["label_id"] in caught_e)])
    # summary.json
    agg = L.aggregate(results, labs)
    summary = {**meta, **agg}
    summary["providers_used"] = dict(Counter(
        r["provider_used"] for r in results if r.get("provider_used")
    ))
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def load_labels_flat() -> list[dict]:
    return L.load_labels()


def _sanitize(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9.-]+", "-", s)


def code_provenance() -> dict[str, str | bool]:
    """Bind a run to both HEAD and any uncommitted tracked-file patch.

    The diff is captured and hashed as raw bytes: `git diff --binary` output
    is not text, and decoding it (which on Windows means the locale code page)
    crashes on any byte the code page cannot represent.
    """
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=L.ROOT, check=True,
            capture_output=True, text=True, encoding="utf-8",
        ).stdout.strip()
        diff = subprocess.run(
            ["git", "diff", "--binary", "--no-ext-diff", "HEAD"],
            cwd=L.ROOT, check=True, capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return {"code_revision": "unknown", "worktree_dirty": True,
                "working_tree_diff_sha256": "unavailable"}
    return {
        "code_revision": revision,
        "worktree_dirty": bool(diff),
        "working_tree_diff_sha256": hashlib.sha256(diff).hexdigest(),
    }


def configure_prompt_mode(prompt_mode: str) -> str:
    """Select a prompt pass without allowing state to leak between runs."""
    if prompt_mode == PROMPT_MODE_COVERAGE_MATRIX:
        os.environ[COVERAGE_MATRIX_ENV] = "1"
    elif prompt_mode == PROMPT_MODE_BASELINE:
        os.environ.pop(COVERAGE_MATRIX_ENV, None)
    else:
        raise ValueError(f"unsupported prompt mode: {prompt_mode}")
    return active_prompt_version()


def repeat_indexes(start: int, count: int, total: int) -> range:
    """Return repeat indexes for a resumable immutable benchmark series."""
    if start < 1:
        raise ValueError("repeat start must be at least 1")
    if count < 1:
        raise ValueError("repeat count must be at least 1")
    if total < start + count - 1:
        raise ValueError("repeat total cannot be smaller than the final repeat index")
    return range(start, start + count)


def main() -> int:
    cfg = L.load_config()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=["rule", "llm"], default=cfg.get("default_mode", "rule"))
    ap.add_argument("--provider", default=cfg.get("default_provider", "gemini"))
    ap.add_argument("--model", default=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    ap.add_argument(
        "--repeat", type=int, default=int(cfg.get("default_repeat", 1)),
        help="number of passes to run in this invocation",
    )
    ap.add_argument(
        "--repeat-start", type=int, default=1,
        help="first pass index for resuming an immutable series",
    )
    ap.add_argument(
        "--repeat-total", type=int, default=0,
        help="declared total passes for the series (default: --repeat)",
    )
    ap.add_argument("--pairs", default="", help="comma-separated pair ids (default: all)")
    ap.add_argument("--pair-limit", type=int, default=0, help="cap number of pairs (0 = all); for smoke runs")
    ap.add_argument("--sample", default="", help="comma-separated pair ids to sample (alias of --pairs)")
    ap.add_argument(
        "--prompt-mode",
        choices=[PROMPT_MODE_BASELINE, PROMPT_MODE_COVERAGE_MATRIX],
        default=PROMPT_MODE_BASELINE,
        help="versioned text-reconciliation prompt pass; coverage matrix is an opt-in experiment",
    )
    ap.add_argument(
        "--run-tag",
        default="",
        help="unique immutable series label appended before runN (recommended)",
    )
    ap.add_argument(
        "--publication-role",
        choices=("primary", "branch-comparison"),
        default="primary",
        help="branch-comparison evidence cannot alter the published primary",
    )
    args = ap.parse_args()

    repeats_total = args.repeat_total or args.repeat
    try:
        indexes = repeat_indexes(args.repeat_start, args.repeat, repeats_total)
    except ValueError as exc:
        ap.error(str(exc))

    if args.prompt_mode != PROMPT_MODE_BASELINE and args.mode != "llm":
        ap.error("--prompt-mode coverage-matrix-v1.7 requires --mode llm")
    prompt_version = configure_prompt_mode(args.prompt_mode)

    labels = L.load_labels()
    by_pair = L.group_labels_by_pair(labels)
    wanted = {p.strip() for p in (args.pairs + "," + args.sample).split(",") if p.strip()}
    pair_ids = sorted(by_pair) if not wanted else [p for p in sorted(by_pair) if p in wanted]
    if args.pair_limit and args.pair_limit > 0:
        pair_ids = pair_ids[:args.pair_limit]

    freeze = json.loads((L.BENCH / "labels" / "labels_freeze.json").read_text(encoding="utf-8"))
    provider = "rule" if args.mode == "rule" else args.provider
    model = "rule-engine" if args.mode == "rule" else args.model

    last_summary = {}
    for k in indexes:
        results = [run_one(pid, by_pair[pid], args.mode) for pid in pair_ids]
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        prompt_tag = "" if args.prompt_mode == PROMPT_MODE_BASELINE else f"_{args.prompt_mode}"
        series_tag = f"_{_sanitize(args.run_tag)}" if args.run_tag else ""
        run_dir = L.BENCH / "runs" / (
            f"{stamp}_{_sanitize(provider)}_{_sanitize(model)}{prompt_tag}{series_tag}_run{k}"
        )
        meta = {
            "benchmark": "ps4_external_v1",
            "benchmark_version": freeze.get("benchmark_version"),
            "labels_freeze_sha256": freeze.get("labels_freeze_sha256"),
            "mode": args.mode, "provider": provider, "model": model,
            "repeat_index": k, "repeats_total": repeats_total,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "include_contested_in_primary": bool(cfg.get("include_contested_in_primary", False)),
            "count_not_run_as_miss": bool(cfg.get("count_not_run_as_miss", True)),
            "evidence_label": "deterministic_offline" if args.mode == "rule" else "live_model",
            "prompt_mode": args.prompt_mode,
            "prompt_version": prompt_version,
            "run_tag": args.run_tag,
            "publication_role": args.publication_role,
            **code_provenance(),
        }
        meta["config_sha256"] = L.sha256_text(json.dumps(
            {k: meta[k] for k in ("mode", "provider", "model", "benchmark_version",
                                  "labels_freeze_sha256", "include_contested_in_primary",
                                  "count_not_run_as_miss", "prompt_mode", "run_tag",
                                  "publication_role",
                                  "prompt_version", "code_revision", "worktree_dirty",
                                  "working_tree_diff_sha256")}, sort_keys=True))
        last_summary = _write_run(run_dir, results, meta)
        pr = last_summary
        print(f"[run{k}] {args.mode} {provider}/{model} -> "
              f"primary recall (sem) {pr['primary_recall_semantic']} "
              f"({pr['primary_tp']}/{pr['positive_labels']}), "
              f"FP {pr['false_positives_total']}, "
              f"clean-neg false-alert {pr['clean_negative_false_alert_rate']}, "
              f"not_run {pr['pairs_not_run']}, wrote {run_dir.relative_to(L.ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
