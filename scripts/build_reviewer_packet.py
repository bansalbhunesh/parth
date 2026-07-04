#!/usr/bin/env python3
"""build_reviewer_packet.py — generate the external reviewer validation packet
for ps4_external_v1. The packet lets a technical reviewer check whether the
benchmark LABELS are correct; it contains NO model predictions and NO scores.

Writes into benchmarks/ps4_external_v1/reviewer_packet/:
  selected_labels.csv, reviewer_form.csv, reviewer_form.jsonl,
  label_review_packet.md, pair_context/*.md, source_excerpts/*.md

Static prose (README_FOR_REVIEWER.md, reviewer_instructions.md) is maintained by
hand. Deterministic selection — re-runnable. No API calls.
"""
import csv
import json
import pathlib
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402

PKT = L.BENCH / "reviewer_packet"
FLAGGED = {"P006-L01", "P018-L03", "P020-L03", "P021-L01", "P029-L01", "P052-L01"}

SOURCE_BASIS_CATEGORY = {
    "owner_design_basis_team_authored": "team-authored (owner design basis)",
    "synthetic_negative": "synthetic negative",
    "adversarial_team_authored": "adversarial (team-authored)",
    "public_product_value": "primary-source-derived (public product value)",
    "team_authored_from_public_values": "primary-source-derived (team-authored from public values)",
}


def _clean(s):
    return str(s or "").replace("Â§", "§").replace("Â", "").strip()


def _fixture_text(path):
    """Read a fixture doc, dropping benchmark-design annotation lines that
    reference the model — those would bias a label reviewer."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(ln for ln in lines if "the model" not in ln.lower()).strip()


def _excerpt(pair_id, ev):
    """Short evidence span from the label, with a little surrounding context
    pulled from the referenced document (docs are short; no long dumps)."""
    doc = ev.get("document", "")
    span = _clean(ev.get("quote_or_span", ""))
    path = L.BENCH / "pairs" / pair_id / doc
    context = ""
    if path.exists() and span and doc.endswith(".md"):
        text = _fixture_text(path)
        low, needle = text.lower(), span.lower()[:24]
        i = low.find(needle)
        if i != -1:
            a, b = max(0, i - 60), min(len(text), i + len(span) + 60)
            context = " ".join(text[a:b].split())
    return doc, _clean(ev.get("page_or_section", "")), span, context


def select(labels, manifest):
    by_id = {lb["label_id"]: lb for lb in labels}
    pd_pairs = {r["pair_id"] for r in manifest if (r.get("primary_or_secondary") or "") == "primary_derived"}
    chosen = {}  # label_id -> reason

    def add(lb, reason):
        chosen.setdefault(lb["label_id"], reason)

    # 1. every previously-flagged label (needs human judgment)
    for lid in sorted(FLAGGED):
        if lid in by_id:
            add(by_id[lid], "audit-flagged — previously marked needs human judgment")
    # 2. every contested label
    for lb in labels:
        if lb["label_type"] == "ambiguous_contested" or lb.get("contested"):
            add(lb, "contested label — reviewer to resolve")
    # 3. every unit-conversion case (rare + representation-sensitive)
    for lb in labels:
        if lb.get("difficulty") == "unit_conversion":
            add(lb, "unit-conversion case (representation-sensitive; only 2 in benchmark)")
    # 4. difficulty-coverage quotas (spread across systems, deterministic by id)
    quotas = {"derived_arithmetic": 3, "domain_recall": 3, "omission_detection": 4,
              "adversarial_noise": 3, "table_or_layout": 3, "scanned_or_image": 3,
              "direct_value": 5, "categorical_reasoning": 5}
    for diff, q in quotas.items():
        cand = sorted((lb for lb in labels if lb.get("difficulty") == diff),
                      key=lambda lb: lb["label_id"])
        seen_sys, picked = set(), 0
        for lb in cand:  # first pass: one per system
            if picked >= q:
                break
            if lb["system_type"] not in seen_sys:
                add(lb, f"difficulty coverage: {diff}")
                seen_sys.add(lb["system_type"])
                picked += 1
        for lb in cand:  # top up
            if picked >= q:
                break
            if lb["label_id"] not in chosen:
                add(lb, f"difficulty coverage: {diff}")
                picked += 1
    # 5. clean negatives across distinct systems (7)
    cn = sorted((lb for lb in labels if lb["label_type"] == "clean_negative"),
                key=lambda lb: lb["label_id"])
    seen_sys, picked = set(), 0
    for lb in cn:
        if picked >= 7:
            break
        if lb["system_type"] not in seen_sys:
            add(lb, f"clean negative — {lb['system_type']} (should NOT be a deviation)")
            seen_sys.add(lb["system_type"])
            picked += 1
    # 6. ensure >=5 labels on primary-source-derived pairs
    pd_labels = sorted((lb for lb in labels if lb["pair_id"] in pd_pairs),
                       key=lambda lb: lb["label_id"])
    have = sum(1 for lid in chosen if by_id[lid]["pair_id"] in pd_pairs)
    for lb in pd_labels:
        if have >= 6:
            break
        if lb["label_id"] not in chosen:
            add(lb, "primary-source-derived pair (check derivation vs public source)")
            have += 1
    return chosen


def main() -> int:
    labels = L.load_labels()
    manifest = L.load_manifest()
    by_id = {lb["label_id"]: lb for lb in labels}
    url_by_pair = {}
    for r in manifest:
        if r.get("source_url"):
            url_by_pair.setdefault(r["pair_id"], r["source_url"])

    chosen = select(labels, manifest)
    sel = [by_id[lid] for lid in sorted(chosen)]
    (PKT / "pair_context").mkdir(parents=True, exist_ok=True)
    (PKT / "source_excerpts").mkdir(parents=True, exist_ok=True)

    # selected_labels.csv
    with (PKT / "selected_labels.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["label_id", "pair_id", "system_type", "label_type", "difficulty", "reason_selected"])
        for lb in sel:
            w.writerow([lb["label_id"], lb["pair_id"], lb["system_type"], lb["label_type"],
                        lb.get("difficulty"), chosen[lb["label_id"]]])

    # reviewer_form.csv + .jsonl (reviewer fields blank)
    form_cols = ["label_id", "pair_id", "system_type", "label_type", "difficulty", "component",
                 "parameter", "required_value", "submitted_value", "expected_finding",
                 "required_evidence_excerpt", "submitted_evidence_excerpt", "source_basis",
                 "commissioning_test", "schedule_impact_category",
                 "reviewer_verdict", "reviewer_confidence", "evidence_sufficient_yes_no",
                 "severity_ok_yes_no", "difficulty_ok_yes_no", "commissioning_mapping_ok_yes_no",
                 "suggested_correction", "missing_related_label", "reviewer_notes"]
    blank = {k: "" for k in form_cols[15:]}

    def row_for(lb):
        _, _, rq, _ = _excerpt(lb["pair_id"], lb.get("evidence_required", {}))
        _, _, sq, _ = _excerpt(lb["pair_id"], lb.get("evidence_submitted", {}))
        return {
            "label_id": lb["label_id"], "pair_id": lb["pair_id"], "system_type": lb["system_type"],
            "label_type": lb["label_type"], "difficulty": lb.get("difficulty", ""),
            "component": lb.get("component", ""), "parameter": lb.get("parameter", ""),
            "required_value": lb.get("required_value", ""), "submitted_value": lb.get("submitted_value", ""),
            "expected_finding": lb.get("expected_finding", ""),
            "required_evidence_excerpt": rq, "submitted_evidence_excerpt": sq,
            "source_basis": lb.get("source_basis", ""),
            "commissioning_test": lb.get("expected_commissioning_test", ""),
            "schedule_impact_category": lb.get("schedule_impact_category", ""), **blank}

    rows = [row_for(lb) for lb in sel]
    with (PKT / "reviewer_form.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=form_cols)
        w.writeheader()
        w.writerows(rows)
    with (PKT / "reviewer_form.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # label_review_packet.md (NO predictions, NO scores)
    out = ["# Label Review Packet — ps4_external_v1 (v1.2)\n",
           "_For an external technical reviewer. Judge only whether each **label** "
           "(the benchmark ground truth) is correct and well-evidenced. This packet "
           "contains no model output and no scores._\n",
           f"\n{len(sel)} labels selected. Verdict options: `accept` / "
           "`accept_with_minor_edit` / `modify` / `reject` / `contested` / "
           "`needs_more_evidence`.\n"]
    for lb in sel:
        pid = lb["pair_id"]
        rdoc, rsec, rq, rctx = _excerpt(pid, lb.get("evidence_required", {}))
        sdoc, ssec, sq, sctx = _excerpt(pid, lb.get("evidence_submitted", {}))
        r_disp = (rq or "—") + ((" — …" + rctx + "…") if rctx and rctx.lower() != (rq or "").lower() else "")
        s_disp = (sq or "—") + ((" — …" + sctx + "…") if sctx and sctx.lower() != (sq or "").lower() else "")
        img = " *(vendor submittal is provided as an image: `pair_context/`)*" if lb.get("modality") == "image" else ""
        out.append(f"""
---

**Label ID:** {lb['label_id']}
**Pair ID:** {pid}
**System:** {lb['system_type']}
**Label type:** {lb['label_type']}
**Difficulty:** {lb.get('difficulty', '')}
**Component:** {lb.get('component', '')}
**Parameter:** {lb.get('parameter', '')}

**Owner requirement (excerpt):**
> {r_disp} ({rdoc} {rsec})

**Vendor/submittal (excerpt):**{img}
> {s_disp} ({sdoc} {ssec})

**Benchmark label:**
- Required value: {lb.get('required_value', '')}
- Submitted value: {lb.get('submitted_value', '')}
- Expected finding: {lb.get('expected_finding', '')}
- Severity: {lb.get('severity', '')}
- Expected commissioning test: {lb.get('expected_commissioning_test', '')}
- Schedule impact category: {lb.get('schedule_impact_category', '')}
- Source basis: {SOURCE_BASIS_CATEGORY.get(lb.get('source_basis'), lb.get('source_basis', ''))}

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:
""")
    (PKT / "label_review_packet.md").write_text("".join(out), encoding="utf-8")

    # pair_context/*.md
    by_pair = defaultdict(list)
    for lb in sel:
        by_pair[lb["pair_id"]].append(lb)
    for pid, lbs in sorted(by_pair.items()):
        owner = _fixture_text(L.BENCH / "pairs" / pid / "owner_requirement.md")
        vendor = _fixture_text(L.BENCH / "pairs" / pid / "vendor_submittal.md")
        is_img = any(lb.get("modality") == "image" for lb in lbs)
        prov = url_by_pair.get(pid)
        basis = SOURCE_BASIS_CATEGORY.get(lbs[0].get("source_basis"), lbs[0].get("source_basis", ""))
        lines = [f"# Pair context — {pid}\n",
                 f"- **System type:** {lbs[0]['system_type']}",
                 f"- **Source basis:** {basis}",
                 f"- **Vendor submittal modality:** {'image (vendor_submittal.png)' if is_img else 'text'}"]
        if prov:
            lines.append(f"- **Provenance note:** value derived from a public source — {prov} "
                         "(URL is for derivation-checking; the file here is team-authored, not a stored datasheet)")
        lines.append("\n## Owner requirement (design basis — team-authored, not a public standard)\n")
        lines.append("```\n" + owner + "\n```")
        lines.append("\n## Vendor/submittal (team-authored fixture — NOT a real vendor datasheet)\n")
        if is_img:
            lines.append("_Rendered as an image in the benchmark (`vendor_submittal.png`); the text below is the "
                         "source the image was rendered from, provided for review._\n")
        lines.append("```\n" + vendor + "\n```")
        lines.append("\n## Labels from this pair included for review\n")
        for lb in lbs:
            lines.append(f"- `{lb['label_id']}` — {lb['label_type']} / {lb.get('difficulty', '')} "
                         f"— {lb.get('parameter', '')}")
        lines.append("\n## Known limitation\n")
        lines.append("- Single-author frozen label, pending two-person review. Fixture is team-authored.")
        (PKT / "pair_context" / f"{pid}_context.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # source_excerpts/*.md
    for lb in sel:
        pid = lb["pair_id"]
        rdoc, rsec, rq, _ = _excerpt(pid, lb.get("evidence_required", {}))
        sdoc, ssec, sq, _ = _excerpt(pid, lb.get("evidence_submitted", {}))
        cat = SOURCE_BASIS_CATEGORY.get(lb.get("source_basis"), lb.get("source_basis", ""))
        prov = url_by_pair.get(pid)
        lines = [f"# Evidence excerpt — {lb['label_id']} ({pid})\n",
                 f"- **Source category:** {cat}",
                 f"- **Provenance:** {prov if prov else 'team-authored fixture (no external source)'}\n",
                 f"## Required-value evidence — `{rdoc}` {rsec}",
                 f"> {rq or '(none recorded)'}\n",
                 f"## Submitted-value evidence — `{sdoc}` {ssec}"
                 + (" *(value appears in the rendered image `vendor_submittal.png`)*"
                    if lb.get("modality") == "image" else ""),
                 f"> {sq or '(none recorded)'}\n"]
        (PKT / "source_excerpts" / f"{lb['label_id']}.md").write_text("\n".join(lines), encoding="utf-8")

    # summary to stdout
    print(f"selected {len(sel)} labels into {PKT.relative_to(L.ROOT).as_posix()}")
    print("systems:", len({lb['system_type'] for lb in sel}),
          dict(Counter(lb["system_type"] for lb in sel)))
    print("difficulty:", dict(Counter(lb.get("difficulty") for lb in sel)))
    print("types:", dict(Counter(lb["label_type"] for lb in sel)))
    print("pairs:", len(by_pair))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
