#!/usr/bin/env python3
"""benchmark_report.py — aggregate benchmark runs into reports/.

Writes benchmark_report.md, benchmark_card.json, benchmark_results.csv, and
per_pair_results.csv. Every metric is tagged with an evidence label. Runs with no
provider key (LLM not_run) are reported honestly; nothing is fabricated.
"""

import csv
import json
import pathlib
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402

REPORTS = L.BENCH / "reports"
_PRIMARY = {"primary_vendor_public", "government_public"}


def _load_runs() -> list[dict]:
    runs = []
    for d in sorted((L.BENCH / "runs").glob("*")):
        sp = d / "summary.json"
        if sp.exists():
            s = json.loads(sp.read_text(encoding="utf-8"))
            s["_dir"] = d.name
            runs.append(s)
    return runs


def _latest(runs, mode):
    cand = [r for r in runs if r.get("mode") == mode]
    return sorted(cand, key=lambda r: (r.get("timestamp_utc", ""), r["_dir"]))[-1] if cand else None


def _static_stats(manifest, labels):
    pos = [lb for lb in labels if lb["label_type"] in L.POSITIVE_LABEL_TYPES]
    diff = Counter(lb["difficulty"] for lb in pos)
    systems = sorted({lb["system_type"] for lb in labels})
    origins = Counter(r.get("source_origin", "") for r in manifest)
    primary = sum(v for k, v in origins.items() if k in _PRIMARY)
    with_hash = sum(1 for r in manifest if (r.get("sha256") or "").strip())
    return {
        "sources": len(manifest),
        "pairs": len({lb["pair_id"] for lb in labels}),
        "labels": len(labels),
        "positive_labels": len(pos),
        "clean_negatives": sum(1 for lb in labels if lb["label_type"] == "clean_negative"),
        "contested": sum(1 for lb in labels if lb["label_type"] == "ambiguous_contested"),
        "difficulty_mix": dict(sorted(diff.items())),
        "systems_covered": systems,
        "origin_mix": dict(sorted(origins.items())),
        "primary_sources": primary,
        "team_authored_sources": len(manifest) - primary,
        "provenance_completeness_sha256": L._rate(with_hash, len(manifest)),
    }


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    manifest = L.load_manifest()
    labels = L.load_labels()
    freeze = json.loads((L.BENCH / "labels" / "labels_freeze.json").read_text(encoding="utf-8"))
    st = _static_stats(manifest, labels)
    runs = _load_runs()
    rule = _latest(runs, "rule")
    llm = _latest(runs, "llm")

    # benchmark_results.csv — one row per run
    cols = ["run", "mode", "provider", "model", "primary_recall_semantic", "primary_recall_exact",
            "secondary_recall_semantic", "primary_tp", "positive_labels", "false_positives_total",
            "clean_negative_false_alert_rate", "pairs_not_run", "error_rate",
            "latency_p50_ms", "latency_p95_ms"]
    with (REPORTS / "benchmark_results.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in runs:
            w.writerow({"run": r["_dir"], **{k: r.get(k) for k in cols[1:]}})

    # copy latest run's per_pair into reports (prefer llm, else rule)
    src_run = llm or rule
    if src_run:
        src = L.BENCH / "runs" / src_run["_dir"] / "per_pair_results.csv"
        if src.exists():
            shutil.copyfile(src, REPORTS / "per_pair_results.csv")

    # benchmark_card.json — safe metrics + evidence labels
    def card_metric(run):
        if not run:
            return None
        return {
            "primary_recall_semantic": run["primary_recall_semantic"],
            "primary_recall_exact": run["primary_recall_exact"],
            "primary_tp": run["primary_tp"], "positive_labels": run["positive_labels"],
            "false_positives_total": run["false_positives_total"],
            "clean_negative_false_alert_rate": run["clean_negative_false_alert_rate"],
            "pairs_not_run": run["pairs_not_run"],
            "evidence_label": run.get("evidence_label"),
        }
    card = {
        "benchmark": "ps4_external_v1",
        "benchmark_version": freeze.get("benchmark_version"),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "seed (framework complete; 40-50 pairs target — see backlog)",
        "pairs": {"value": st["pairs"], "evidence_label": "team_authored"},
        "positive_labels": {"value": st["positive_labels"], "evidence_label": "team_authored"},
        "clean_negatives": {"value": st["clean_negatives"], "evidence_label": "team_authored"},
        "contested_labels": {"value": st["contested"], "evidence_label": "team_authored"},
        "systems_covered": st["systems_covered"],
        "difficulty_mix": st["difficulty_mix"],
        "provenance": {"primary_sources": st["primary_sources"],
                       "team_authored_sources": st["team_authored_sources"],
                       "sha256_completeness": st["provenance_completeness_sha256"]},
        "rule_baseline": card_metric(rule),
        "llm_result": card_metric(llm),
        "cost_estimate": {"value": None, "evidence_label": "not_yet_measured"},
        "non_claims": [
            "Not an external-accuracy claim: seed is team-authored, single-author labeled.",
            "Primary-source acquisition and two-reviewer adjudication are backlog.",
        ],
    }
    (REPORTS / "benchmark_card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")

    # benchmark_report.md
    def run_block(title, run, label):
        if not run:
            return f"### {title}\n\n_No {title.lower()} run recorded yet._\n"
        pd = "\n".join(f"| {k} | {v['caught']}/{v['positives']} | {v['recall']} |"
                       for k, v in sorted(run.get("per_difficulty", {}).items()))
        return (
            f"### {title}  \n`{label}`\n\n"
            f"- Primary recall (semantic, not-run counted as miss): **{run['primary_recall_semantic']}** "
            f"({run['primary_tp']}/{run['positive_labels']})\n"
            f"- Primary recall (exact): {run['primary_recall_exact']}\n"
            f"- Secondary recall (semantic, not-run excluded): {run['secondary_recall_semantic']} "
            f"(over {run['secondary_positives']} positives)\n"
            f"- False positives: **{run['false_positives_total']}** · "
            f"clean-negative false-alert rate: **{run['clean_negative_false_alert_rate']}**\n"
            f"- Not-run pairs: {run['pairs_not_run']} {run['not_run_pair_ids'] or ''} · "
            f"error rate: {run['error_rate']}\n"
            f"- Latency p50/p95 (ms): {run['latency_p50_ms']} / {run['latency_p95_ms']}\n\n"
            f"| difficulty | caught | recall |\n|---|---|---|\n{pd}\n"
        )

    md = f"""# PS4 External Benchmark — Report (v{freeze.get('benchmark_version')})

_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} · run
`scripts/benchmark_report.py` to refresh. Every metric carries an evidence label._

## Composition
| item | value | evidence |
|---|---|---|
| Source documents | {st['sources']} | `team_authored` |
| Pairs | {st['pairs']} | `team_authored` |
| Labels | {st['labels']} | `team_authored` |
| Positive-type labels | {st['positive_labels']} | `team_authored` |
| Clean negatives | {st['clean_negatives']} | `team_authored` |
| Contested labels | {st['contested']} | `team_authored` |
| Systems covered | {len(st['systems_covered'])} ({', '.join(st['systems_covered'])}) | — |
| Provenance SHA-256 completeness | {st['provenance_completeness_sha256']} | `measured` |
| Primary-source docs | {st['primary_sources']} | `measured` |
| Team-authored docs | {st['team_authored_sources']} | `measured` |

**Difficulty mix (positive labels):** {st['difficulty_mix']}

**Source-origin mix:** {st['origin_mix']}

## Results
{run_block('Rule-engine baseline', rule, 'deterministic_offline')}
{run_block('LLM-enhanced', llm, 'live_model')}

## Cost
`not_yet_measured` — the analysis path does not currently surface provider token
usage; cost estimation is a backlog item.

## Limitations / non-claims
- Seed pairs are **team-authored** (not downloaded primary sources) → **no
  external-accuracy claim** yet.
- Labels are **single-author frozen**; two-reviewer adjudication is backlog.
- Rule-engine recall is low on reasoning cases **by design** — those need the LLM.
- OCR/vision (`scanned_or_image`, `table_or_layout`) and several systems are backlog.

## What can / cannot be claimed
- **Can:** "On an independent, frozen, provenance-tracked benchmark of {st['pairs']} pairs,
  the rule engine catches {rule['primary_tp'] if rule else 0}/{st['positive_labels']} positive
  checks with {rule['false_positives_total'] if rule else 0} false positives and a
  {rule['clean_negative_false_alert_rate'] if rule else 'n/a'} clean-negative false-alert rate."
- **Cannot (yet):** any headline external-accuracy number — the seed is team-authored and
  single-author labeled; primary-source acquisition + adjudication are pending.

See [`BENCHMARK_PROTOCOL.md`](../BENCHMARK_PROTOCOL.md) for the acquisition backlog to 40–50 pairs.
"""
    (REPORTS / "benchmark_report.md").write_text(md, encoding="utf-8")
    print(f"Wrote reports: benchmark_report.md, benchmark_card.json, benchmark_results.csv "
          f"({'per_pair_results.csv' if src_run else 'no per-pair (no runs yet)'})")
    print(f"  runs found: {len(runs)} | rule: {'yes' if rule else 'no'} | llm: {'yes' if llm else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
