#!/usr/bin/env python3
"""benchmark_label_audit.py — independent, deterministic second-pass audit of
every benchmark label against its own pair documents.

This is an AUTOMATED consistency check, NOT a second human reviewer. It does not
adjudicate correctness — it flags labels whose values are not grounded in the
documents, or whose deviation direction looks inconsistent, so a human reviewer
can focus on the suspect ones. Writes labels/automated_audit.jsonl and prints a
summary. stdlib only.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402

AUDIT_OUT = L.BENCH / "labels" / "automated_audit.jsonl"


_OMISSION_SENTINELS = {"not stated", "not provided", "not specified", "omitted",
                       "not included", "missing", "none", "not addressed", "absent"}


def _normalize(s: str) -> str:
    """Fold unicode super/subscripts so 'm³/h' grounds against 'm3/h'."""
    return (s.replace("³", "3").replace("²", "2").replace("¹", "1")
            .replace("μ", "u").replace("°", " "))


def _grounded(value, text: str) -> bool:
    """True if the value is present in the text: whole compacted value, or every
    number as a standalone token, or every 3+-letter word."""
    if value is None or str(value).strip() == "":
        return True
    tl = _normalize(text.lower())
    tc = re.sub(r"[^a-z0-9+]", "", tl)
    vs = _normalize(str(value).strip().lower())
    compact = re.sub(r"[^a-z0-9+]", "", vs)
    nums = re.findall(r"\d+\.?\d*", vs)
    toks = [t for t in re.findall(r"[a-z]+", vs) if len(t) > 2]
    return ((bool(compact) and compact in tc)
            or (bool(nums) and all(re.search(r"(?<!\d)" + re.escape(n) + r"(?!\d)", tl) for n in nums))
            or (bool(toks) and all(t in tl for t in toks)))


def audit_label(lb: dict, owner: str, vendor: str, is_image: bool) -> list[str]:
    """High-signal checks only. Deliberately does NOT flag 'exceeds'-type clean
    negatives (whose values legitimately differ) or omission sentinels (whose
    submitted value is meant to be absent) — those produce noise, not findings."""
    flags = []
    rv, sv = lb.get("required_value"), lb.get("submitted_value")
    lt = lb["label_type"]
    sv_is_sentinel = str(sv).strip().lower() in _OMISSION_SENTINELS if sv is not None else True
    # 1. the REQUIRED value must be grounded in the owner design basis
    if not _grounded(rv, owner):
        flags.append(f"required_value {rv!r} not found in owner document")
    # 2. a stated (non-sentinel) submitted value must be grounded in the vendor
    #    doc — skip for image pairs (values live in the image) and omissions
    if not is_image and lt != "omission" and not sv_is_sentinel and not _grounded(sv, vendor):
        flags.append(f"submitted_value {sv!r} not found in vendor document")
    # 3. a positive deviation must actually differ
    if lt == "positive_deviation" and rv is not None and sv is not None \
            and L.norm(rv) == L.norm(sv):
        flags.append("positive_deviation but required == submitted")
    return flags


def main() -> int:
    labels = L.load_labels()
    audited, flagged = [], 0
    for lb in labels:
        pid = lb["pair_id"]
        d = L.BENCH / "pairs" / pid
        owner = (d / "owner_requirement.md").read_text(encoding="utf-8")
        vendor = (d / "vendor_submittal.md").read_text(encoding="utf-8")
        is_image = lb.get("modality") == "image"
        flags = audit_label(lb, owner, vendor, is_image)
        verdict = "needs_human_review" if flags else "consistent"
        flagged += bool(flags)
        audited.append({
            "label_id": lb.get("label_id"), "pair_id": pid,
            "label_type": lb["label_type"], "verdict": verdict, "flags": flags,
            "auditor": "automated_consistency_v1",
        })
    AUDIT_OUT.write_text(
        "".join(json.dumps(a, ensure_ascii=False) + "\n" for a in audited), encoding="utf-8")
    print(f"audited {len(audited)} labels -> {AUDIT_OUT.relative_to(L.ROOT).as_posix()}")
    print(f"consistent: {len(audited) - flagged} | needs_human_review: {flagged}")
    for a in audited:
        if a["flags"]:
            print(f"  [{a['pair_id']} {a['label_id']}] {a['label_type']}: {'; '.join(a['flags'])}")
    print("\nNOTE: automated consistency audit — NOT a second human reviewer. "
          "Flagged labels are candidates for human adjudication, not confirmed errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
