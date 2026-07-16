#!/usr/bin/env python3
"""Evaluate prompt candidates on the isolated coverage-matrix dev corpus.

This runner deliberately cannot read or select frozen ``ps4_external_v1``
pairs. It reuses that benchmark's validator, one-to-one scorer, run writer, and
prompt-mode wiring while binding every run to a hash of the complete dev corpus.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402
import benchmark_ps4_external as B  # noqa: E402

sys.path.insert(0, str(L.ROOT))
from backend.agents.reconciliation import _prompt_suffix  # noqa: E402

DEV = L.ROOT / "benchmarks" / "dev_corpus_v1"
PROMPT_MODES = (
    B.PROMPT_MODE_BASELINE,
    B.PROMPT_MODE_COVERAGE_MATRIX,
)


def load_labels(root: pathlib.Path = DEV) -> list[dict]:
    labels: list[dict] = []
    for path in sorted((root / "pairs").glob("dev_pair_*/label.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"{path}: label.json must contain an array")
        labels.extend(payload)
    return labels


def corpus_content_hash(root: pathlib.Path = DEV) -> str:
    """Hash every scored input and label with platform-neutral newlines."""
    records = []
    for path in sorted((root / "pairs").glob("dev_pair_*/*")):
        if path.is_file() and path.name in {
            "owner_requirement.md", "vendor_submittal.md", "label.json"
        }:
            content_hash = L.sha256_text(path.read_text(encoding="utf-8"))
            records.append(f"{path.relative_to(root).as_posix()}:{content_hash}")
    return L.sha256_text("\n".join(records))


def validate_corpus(
    root: pathlib.Path = DEV,
    *,
    require_frozen: bool = False,
) -> tuple[list[dict], list[str]]:
    labels = load_labels(root)
    errors = L.validate_labels(labels)
    pair_dirs = sorted((root / "pairs").glob("dev_pair_*"))
    for pair_dir in pair_dirs:
        for name in ("owner_requirement.md", "vendor_submittal.md", "label.json"):
            if not (pair_dir / name).is_file():
                errors.append(f"{pair_dir.name}: missing {name}")
        label_path = pair_dir / "label.json"
        if label_path.is_file():
            payload = json.loads(label_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                for lb in payload:
                    if lb.get("pair_id") != pair_dir.name:
                        errors.append(f"{pair_dir.name}: label pair_id mismatch")
    known_pairs = {p.name for p in pair_dirs}
    for lb in labels:
        if lb.get("pair_id") not in known_pairs:
            errors.append(f"{lb.get('label_id', '?')}: pair directory is missing")

    if require_frozen:
        if any(lb.get("status") != "frozen" for lb in labels):
            errors.append("--require-frozen needs every dev label status=frozen")
        freeze_path = root / "labels_freeze.json"
        if not freeze_path.is_file():
            errors.append("--require-frozen needs labels_freeze.json")
        else:
            freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
            actual = L.labels_freeze_hash(labels)
            if freeze.get("labels_freeze_sha256") != actual:
                errors.append("labels_freeze.json hash does not match current labels")
            if freeze.get("corpus_content_sha256") != corpus_content_hash(root):
                errors.append("labels_freeze.json corpus hash does not match current files")
            if freeze.get("pair_count") != len(pair_dirs):
                errors.append("labels_freeze.json pair_count does not match")
            if freeze.get("label_count") != len(labels):
                errors.append("labels_freeze.json label_count does not match")
    return labels, errors


def _rate(numerator: int, denominator: int):
    return round(numerator / denominator, 4) if denominator else None


def add_dev_metrics(summary: dict, results: list[dict], labels: list[dict]) -> None:
    caught = {
        label_id
        for result in results if not result.get("not_run")
        for label_id in result.get("matched_semantic", [])
    }
    counts: dict[str, dict[str, int | float | None]] = {}
    for label_type, total in Counter(lb["label_type"] for lb in labels).items():
        positive = label_type in L.POSITIVE_LABEL_TYPES
        caught_count = sum(
            1 for lb in labels
            if lb["label_type"] == label_type and lb["label_id"] in caught
        ) if positive else 0
        counts[label_type] = {
            "labels": total,
            "caught": caught_count if positive else None,
            "recall": _rate(caught_count, total) if positive else None,
        }
    tp = summary["primary_tp"]
    fp = summary["false_positives_total"]
    precision = _rate(tp, tp + fp)
    recall = summary["primary_recall_semantic"]
    summary["precision_semantic"] = precision
    summary["f1_semantic"] = (
        round(2 * precision * recall / (precision + recall), 4)
        if precision is not None and recall is not None and precision + recall else None
    )
    summary["per_label_type"] = counts
    omissions = [lb for lb in labels if lb["label_type"] == "omission"]
    summary["omission_labels"] = len(omissions)
    summary["omissions_caught"] = sum(lb["label_id"] in caught for lb in omissions)
    summary["omission_recall"] = _rate(
        summary["omissions_caught"], summary["omission_labels"]
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=("rule", "llm"), default="rule")
    ap.add_argument("--provider", default="openai")
    ap.add_argument("--model", default="google/gemini-3.1-flash-lite")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--repeat-start", type=int, default=1)
    ap.add_argument("--repeat-total", type=int, default=0)
    ap.add_argument("--pairs", default="", help="comma-separated dev pair ids")
    ap.add_argument("--pair-limit", type=int, default=0)
    ap.add_argument(
        "--delay-seconds", type=float, default=0.0,
        help="delay between live calls when a provider has a low token-per-minute limit",
    )
    ap.add_argument(
        "--abort-after-not-run", type=int, default=0,
        help="abort without saving a run after this many provider fallbacks (0 disables)",
    )
    ap.add_argument("--prompt-mode", choices=PROMPT_MODES, default=B.PROMPT_MODE_BASELINE)
    ap.add_argument("--run-tag", default="")
    ap.add_argument("--require-frozen", action="store_true")
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()

    labels, errors = validate_corpus(require_frozen=args.require_frozen)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.validate_only:
        print(f"valid dev corpus: {len(set(lb['pair_id'] for lb in labels))} pairs, "
              f"{len(labels)} labels, content {corpus_content_hash()[:12]}")
        return 0
    if args.prompt_mode != B.PROMPT_MODE_BASELINE and args.mode != "llm":
        ap.error("a coverage-matrix --prompt-mode requires --mode llm")

    repeats_total = args.repeat_total or args.repeat
    try:
        indexes = B.repeat_indexes(args.repeat_start, args.repeat, repeats_total)
    except ValueError as exc:
        ap.error(str(exc))
    prompt_version = B.configure_prompt_mode(args.prompt_mode)
    by_pair = L.group_labels_by_pair(labels)
    wanted = {p.strip() for p in args.pairs.split(",") if p.strip()}
    pair_ids = sorted(by_pair) if not wanted else [p for p in sorted(by_pair) if p in wanted]
    if args.pair_limit > 0:
        pair_ids = pair_ids[:args.pair_limit]
    selected_labels = [lb for lb in labels if lb["pair_id"] in pair_ids]

    content_hash = corpus_content_hash()
    labels_hash = L.labels_freeze_hash(labels)
    status = "frozen" if all(lb.get("status") == "frozen" for lb in labels) else "draft"
    last_summary = {}
    for index in indexes:
        results = []
        for pair_index, pair_id in enumerate(pair_ids):
            if pair_index and args.delay_seconds > 0:
                time.sleep(args.delay_seconds)
            results.append(B.run_one(pair_id, by_pair[pair_id], args.mode, DEV))
            not_run_count = sum(result.get("not_run", False) for result in results)
            if args.abort_after_not_run and not_run_count >= args.abort_after_not_run:
                print(
                    f"aborting unsaved run after {not_run_count} provider fallbacks",
                    file=sys.stderr,
                )
                return 3
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        prompt_tag = "" if args.prompt_mode == B.PROMPT_MODE_BASELINE else f"_{args.prompt_mode}"
        series_tag = f"_{B._sanitize(args.run_tag)}" if args.run_tag else ""
        run_dir = DEV / "runs" / (
            f"{stamp}_{B._sanitize(args.provider)}_{B._sanitize(args.model)}"
            f"{prompt_tag}{series_tag}_run{index}"
        )
        meta = {
            "benchmark": "dev_corpus_v1",
            "corpus_version": "1.0.0",
            "corpus_status": status,
            "labels_freeze_sha256": labels_hash,
            "corpus_content_sha256": content_hash,
            "mode": args.mode,
            "provider": "rule" if args.mode == "rule" else args.provider,
            "model": "rule-engine" if args.mode == "rule" else args.model,
            "repeat_index": index,
            "repeats_total": repeats_total,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "evidence_label": "deterministic_offline" if args.mode == "rule" else "live_model",
            "prompt_mode": args.prompt_mode,
            "prompt_version": prompt_version,
            "prompt_suffix_sha256": L.sha256_text(_prompt_suffix()),
            "run_tag": args.run_tag,
            "selected_pair_ids": ",".join(pair_ids),
            "publication_role": "development-only",
            **B.code_provenance(),
        }
        meta["config_sha256"] = L.sha256_text(json.dumps(meta, sort_keys=True))
        last_summary = B._write_run(run_dir, results, meta, selected_labels)
        add_dev_metrics(last_summary, results, selected_labels)
        (run_dir / "summary.json").write_text(
            json.dumps(last_summary, indent=2), encoding="utf-8"
        )
        print(
            f"[run{index}] {args.prompt_mode}: recall "
            f"{last_summary['primary_recall_semantic']}, omission "
            f"{last_summary['omission_recall']}, precision "
            f"{last_summary['precision_semantic']}, clean-neg FAR "
            f"{last_summary['clean_negative_false_alert_rate']}, wrote "
            f"{run_dir.relative_to(L.ROOT).as_posix()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
