#!/usr/bin/env python3
"""benchmark_lib.py — shared core for the PS4 external validation benchmark.

Standard library ONLY (no pyyaml / jsonschema). CI installs just
backend/requirements.txt + pytest/ruff, so anything imported by tests or the
benchmark scripts must be stdlib. The *.schema.json files are the human-readable
contract; the validators here enforce the same enums by hand.

Nothing in this module reads data/corpus/ground_truth.json or any seeded label —
the external benchmark is deliberately independent of the synthetic corpus.
"""

from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmarks" / "ps4_external_v1"

# ── allowed enum values (mirror manifest.schema.json / labels.schema.json) ──
SYSTEM_TYPES = {
    "ups", "battery", "generator", "transformer", "switchgear", "ats_sts",
    "pdu_rpp", "crac_crah", "chiller", "cooling_tower", "bms", "fire_suppression",
    "rack_aisle", "cabling", "metering_power_quality", "refrigerant", "networking", "other",
}
DOCUMENT_ROLES = {
    "owner_requirement", "vendor_submittal", "datasheet", "standard_summary",
    "test_report", "negative_control", "adversarial_document", "image_or_scanned", "other",
}
SOURCE_ORIGINS = {
    "primary_vendor_public", "government_public", "owner_design_basis_team_authored",
    "team_authored_from_public_values", "synthetic_negative", "adversarial_team_authored",
    "secondary_reference", "unknown_do_not_use_for_claims",
}
LABEL_TYPES = {
    "positive_deviation", "clean_negative", "omission", "ambiguous_contested",
    "adversarial_instruction", "ocr_extraction_case",
}
DIFFICULTIES = {
    "direct_value", "unit_conversion", "derived_arithmetic", "domain_recall",
    "categorical_reasoning", "omission_detection", "table_or_layout",
    "scanned_or_image", "adversarial_noise",
}
# label types that assert a finding SHOULD be produced
POSITIVE_LABEL_TYPES = {"positive_deviation", "omission", "adversarial_instruction", "ocr_extraction_case"}
EVIDENCE_LABELS = {
    "measured", "deterministic_offline", "live_model", "synthetic",
    "team_authored", "scenario", "not_yet_measured",
}
MANIFEST_COLUMNS = [
    "source_id", "pair_id", "file_name", "system_type", "document_role",
    "document_type", "source_origin", "source_url", "source_owner", "retrieval_date",
    "version_or_revision", "sha256", "license_or_usage_basis", "primary_or_secondary",
    "contains_proprietary_standard_text", "notes",
]
_PRIMARY_ORIGINS = {"primary_vendor_public", "government_public"}

_STOP = {"the", "a", "an", "of", "for", "per", "and", "or", "to", "is", "in",
         "at", "on", "with", "not", "no", "min", "max", "value", "rating"}


# ── hashing ──────────────────────────────────────────────────────────
def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── loaders (stdlib) ─────────────────────────────────────────────────
def load_config(path: pathlib.Path | None = None) -> dict:
    """Minimal flat-YAML reader for run_config.yaml (key: value, comments with #).
    Deliberately tiny so we never depend on pyyaml (absent in CI)."""
    path = pathlib.Path(path or (BENCH / "run_config.yaml"))
    cfg: dict = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.lower() in ("true", "false"):
            cfg[key] = (val.lower() == "true")
        elif re.fullmatch(r"-?\d+", val):
            cfg[key] = int(val)
        elif re.fullmatch(r"-?\d+\.\d+", val):
            cfg[key] = float(val)
        else:
            cfg[key] = val
    return cfg


def load_manifest(path: pathlib.Path | None = None) -> list[dict]:
    path = pathlib.Path(path or (BENCH / "manifest.csv"))
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_labels(path: pathlib.Path | None = None) -> list[dict]:
    path = pathlib.Path(path or (BENCH / "labels" / "labels.jsonl"))
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


# ── validators (hand-rolled against the enums above) ─────────────────
def validate_manifest(rows: list[dict], root: pathlib.Path | None = None) -> list[str]:
    root = pathlib.Path(root or BENCH)
    errors: list[str] = []
    seen_ids: set[str] = set()
    for i, r in enumerate(rows, 1):
        sid = (r.get("source_id") or "").strip()
        where = f"manifest row {i} (source_id={sid or '?'})"
        if not sid:
            errors.append(f"{where}: missing source_id")
        elif sid in seen_ids:
            errors.append(f"{where}: duplicate source_id")
        else:
            seen_ids.add(sid)
        st = (r.get("system_type") or "").strip()
        if st and st not in SYSTEM_TYPES:
            errors.append(f"{where}: invalid system_type '{st}'")
        role = (r.get("document_role") or "").strip()
        if role and role not in DOCUMENT_ROLES:
            errors.append(f"{where}: invalid document_role '{role}'")
        origin = (r.get("source_origin") or "").strip()
        if origin and origin not in SOURCE_ORIGINS:
            errors.append(f"{where}: invalid source_origin '{origin}'")
        fname = (r.get("file_name") or "").strip()
        fpath = root / fname if fname else None
        if fpath and fpath.exists():
            actual = sha256_file(fpath)
            declared = (r.get("sha256") or "").strip()
            if not declared:
                errors.append(f"{where}: file present but no sha256 recorded")
            elif declared != actual:
                errors.append(f"{where}: sha256 mismatch (declared {declared[:12]} vs actual {actual[:12]})")
        if origin == "primary_vendor_public" and not (r.get("source_url") or "").strip():
            errors.append(f"{where}: primary_vendor_public requires a source_url")
        if origin in _PRIMARY_ORIGINS and not (r.get("retrieval_date") or "").strip():
            errors.append(f"{where}: primary/government source requires a retrieval_date")
    return errors


def validate_labels(labels: list[dict]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for i, lb in enumerate(labels, 1):
        lid = (lb.get("label_id") or "").strip()
        where = f"label {i} (label_id={lid or '?'})"
        if not lid:
            errors.append(f"{where}: missing label_id")
        elif lid in seen:
            errors.append(f"{where}: duplicate label_id")
        else:
            seen.add(lid)
        lt = lb.get("label_type")
        if lt not in LABEL_TYPES:
            errors.append(f"{where}: invalid label_type '{lt}'")
        diff = lb.get("difficulty")
        if diff not in DIFFICULTIES:
            errors.append(f"{where}: invalid difficulty '{diff}'")
        st = lb.get("system_type")
        if st not in SYSTEM_TYPES:
            errors.append(f"{where}: invalid system_type '{st}'")
        if lt in POSITIVE_LABEL_TYPES:
            for side in ("evidence_required", "evidence_submitted"):
                ev = lb.get(side) or {}
                if not ev.get("document") or not ev.get("quote_or_span"):
                    errors.append(f"{where}: positive-type label missing {side}.document/quote_or_span")
        if lt == "clean_negative" and lb.get("deviation_type") not in (None, "", "none", "compliant"):
            errors.append(f"{where}: clean_negative should not carry a deviation_type")
        if lb.get("contested") and lt != "ambiguous_contested":
            errors.append(f"{where}: contested=true only allowed on ambiguous_contested labels")
    return errors


def labels_freeze_hash(labels: list[dict]) -> str:
    """Deterministic hash of the frozen label set (order-independent)."""
    canon = sorted(json.dumps(lb, sort_keys=True, ensure_ascii=False) for lb in labels)
    return sha256_text("\n".join(canon))


# ── matching / scoring ───────────────────────────────────────────────
def norm(v) -> str:
    return re.sub(r"[^a-z0-9.]+", "", str(v).strip().lower())


def toks(s) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", str(s).lower()) if w not in _STOP and len(w) > 1}


def _param_overlap(label: dict, finding: dict) -> set:
    lab = toks(label.get("component", "")) | toks(label.get("parameter", ""))
    fnd = toks(finding.get("component", "")) | toks(finding.get("parameter", ""))
    return lab & fnd


def _lead_num(v):
    m = re.search(r"-?\d+(?:\.\d+)?", str(v))
    return float(m.group(0)) if m else None


def _val_eq(a, b) -> bool:
    """Value equality tolerant of the label carrying a unit ('10 min') while the
    rule engine emits a bare number ('10'): compare numerically when both sides
    have a number, else fall back to normalized string containment."""
    na, nb = _lead_num(a), _lead_num(b)
    if na is not None and nb is not None:
        return abs(na - nb) < 1e-9
    na_, nb_ = norm(a), norm(b)
    if not na_ or not nb_:
        return False
    return na_ == nb_ or na_ in nb_ or nb_ in na_


def matches_exact(label: dict, finding: dict) -> bool:
    return (_val_eq(label.get("required_value"), finding.get("required_value"))
            and _val_eq(label.get("submitted_value"), finding.get("provided_value")))


def matches_semantic(label: dict, finding: dict) -> bool:
    if matches_exact(label, finding):
        return True
    ov = _param_overlap(label, finding)
    if not ov:
        return False
    ls, fp = norm(label.get("submitted_value")), norm(finding.get("provided_value"))
    lr, fr = norm(label.get("required_value")), norm(finding.get("required_value"))
    if (ls and ls in fp) or (lr and lr in fr):
        return True
    if (toks(label.get("required_value")) & toks(finding.get("required_value"))) and \
       (toks(label.get("submitted_value")) & toks(finding.get("provided_value"))):
        return True
    return False


def _one_to_one(pos_labels: list[dict], findings: list[dict], matcher) -> tuple[dict, list[int]]:
    """Greedy one-to-one: each positive label claims the first still-unclaimed
    finding it matches. Returns (label_idx -> finding_idx, unmatched finding idxs)."""
    remaining = list(range(len(findings)))
    matched: dict[int, int] = {}
    for i, lab in enumerate(pos_labels):
        for pos, fi in enumerate(remaining):
            if matcher(lab, findings[fi]):
                matched[i] = fi
                remaining.pop(pos)
                break
    return matched, remaining


def score_pair(pair_labels: list[dict], findings: list[dict], matcher,
               include_contested: bool = False) -> dict:
    """One-to-one score of predicted findings against one pair's labels.

    TP/FN over positive-type labels; FP = findings not matched to any positive
    label (never negative); clean-negative false alerts = leftover findings that
    touch a negative-control parameter; contested labels are excluded unless
    include_contested is set.
    """
    pos = [lb for lb in pair_labels if lb["label_type"] in POSITIVE_LABEL_TYPES]
    negs = [lb for lb in pair_labels if lb["label_type"] == "clean_negative"]
    contested = [lb for lb in pair_labels if lb["label_type"] == "ambiguous_contested"]
    if include_contested:
        pos = pos + contested
        contested = []

    matched, unmatched = _one_to_one(pos, findings, matcher)
    tp = len(matched)
    fn = len(pos) - tp
    fp = len(unmatched)
    neg_false = sum(1 for nl in negs if any(_param_overlap(nl, findings[fi]) for fi in unmatched))
    contested_flagged = sum(1 for cl in contested if any(matcher(cl, f) for f in findings))
    return {
        "tp": tp, "fn": fn, "fp": fp,
        "positives": len(pos), "negatives": len(negs),
        "neg_false_alerts": neg_false,
        "contested": len(contested), "contested_flagged": contested_flagged,
        "matched_labels": [pos[i].get("label_id") for i in matched],
        "missed_labels": [pos[i].get("label_id") for i in range(len(pos)) if i not in matched],
    }


def group_labels_by_pair(labels: list[dict]) -> dict:
    by: dict[str, list[dict]] = {}
    for lb in labels:
        by.setdefault(lb["pair_id"], []).append(lb)
    return by


def _percentile(values: list[float], pct: float):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * pct
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 1)


def _rate(a: int, b: int):
    return round(a / b, 4) if b else None


def aggregate(pair_results: list[dict], labels: list[dict]) -> dict:
    """Aggregate per-pair results into run metrics.

    PRIMARY recall counts not-run pairs' positive labels as misses (only findings
    from pairs that actually ran are credited). SECONDARY recall excludes not-run
    pairs and is labelled as such. False positives are summed over run pairs.
    """
    pos_labels = [lb for lb in labels if lb["label_type"] in POSITIVE_LABEL_TYPES]
    total_positives = len(pos_labels)
    total_negatives = sum(1 for lb in labels if lb["label_type"] == "clean_negative")
    total_contested = sum(1 for lb in labels if lb["label_type"] == "ambiguous_contested")

    run = [r for r in pair_results if not r.get("not_run")]
    not_run = [r for r in pair_results if r.get("not_run")]
    caught_sem: set = set()
    caught_exact: set = set()
    for r in run:
        caught_sem.update(r.get("matched_semantic", []))
        caught_exact.update(r.get("matched_exact", []))

    primary_tp = len(caught_sem)
    primary_tp_exact = len(caught_exact)
    fp_total = sum(r.get("fp", 0) for r in run)
    neg_false = sum(r.get("neg_false_alerts", 0) for r in run)
    run_pair_ids = {r["pair_id"] for r in run}
    sec_positives = sum(1 for lb in pos_labels if lb["pair_id"] in run_pair_ids)
    errors = sum(1 for r in pair_results if r.get("error"))

    def by_key(keyfn) -> dict:
        out: dict[str, dict] = {}
        for lb in pos_labels:
            key = keyfn(lb)
            slot = out.setdefault(key, {"positives": 0, "caught": 0})
            slot["positives"] += 1
            if lb["label_id"] in caught_sem:
                slot["caught"] += 1
        for slot in out.values():
            slot["recall"] = _rate(slot["caught"], slot["positives"])
        return out

    lat = [r["latency_ms"] for r in run if r.get("latency_ms") is not None]
    return {
        "pairs_total": len(pair_results),
        "pairs_run": len(run),
        "pairs_not_run": len(not_run),
        "not_run_pair_ids": sorted(r["pair_id"] for r in not_run),
        "positive_labels": total_positives,
        "clean_negative_labels": total_negatives,
        "contested_labels": total_contested,
        "primary_recall_semantic": _rate(primary_tp, total_positives),
        "primary_recall_exact": _rate(primary_tp_exact, total_positives),
        "primary_tp": primary_tp,
        "primary_fn": total_positives - primary_tp,
        "secondary_recall_semantic": _rate(primary_tp, sec_positives),
        "secondary_positives": sec_positives,
        "false_positives_total": fp_total,
        "clean_negative_false_alerts": neg_false,
        "clean_negative_false_alert_rate": _rate(neg_false, total_negatives),
        "error_or_timeout_pairs": errors,
        "error_rate": _rate(errors, len(pair_results)),
        "latency_p50_ms": _percentile(lat, 0.5),
        "latency_p95_ms": _percentile(lat, 0.95),
        "per_difficulty": by_key(lambda lb: lb["difficulty"]),
        "per_system": by_key(lambda lb: lb["system_type"]),
    }
