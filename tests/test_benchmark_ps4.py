"""Tests for the PS4 external validation benchmark (benchmarks/ps4_external_v1).

Covers manifest/label validation, duplicate rejection, clean-negative handling,
one-to-one matching, false-positive counting, timeout-as-miss accounting,
contested exclusion, report generation without provider keys, and the guarantee
that the benchmark uses none of the seeded ground_truth.json labels.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import benchmark_lib as L  # noqa: E402


def _pos(pair_id, lid, req, sub, comp="battery autonomy", param="runtime_minutes",
         ltype="positive_deviation", diff="direct_value", system="ups"):
    return {
        "pair_id": pair_id, "label_id": lid, "system_type": system,
        "label_type": ltype, "difficulty": diff, "component": comp, "parameter": param,
        "required_value": req, "submitted_value": sub, "expected_finding": "x",
        "evidence_required": {"document": "owner_requirement.md", "quote_or_span": "q"},
        "evidence_submitted": {"document": "vendor_submittal.md", "quote_or_span": "q"},
        "source_basis": "owner_design_basis_team_authored", "status": "frozen", "contested": False,
    }


def _find(comp, param, req, prov):
    return {"component": comp, "parameter": param, "required_value": req, "provided_value": prov}


# ── manifest / label validation ──────────────────────────────────────
def test_seed_manifest_and_labels_are_valid():
    assert L.validate_manifest(L.load_manifest()) == []
    assert L.validate_labels(L.load_labels()) == []


# ── automated label audit (reviewer-2 QA, not a human) ───────────────
def test_label_audit_flags_ungrounded_and_passes_valid():
    import benchmark_label_audit as A
    owner = "Battery autonomy shall be at least 10 minutes. Redundancy shall be N+1."
    vendor = "Rated runtime: 8 minutes. Redundancy: N."
    # grounded positive deviation -> no flags
    ok = A.audit_label(_pos("p", "L1", 10, 8), owner, vendor, is_image=False)
    assert ok == []
    # required_value invented (1200 not in owner) -> flagged
    bad = A.audit_label(_pos("p", "L2", 1200, 8), owner, vendor, is_image=False)
    assert any("required_value" in f for f in bad)
    # omission sentinel submitted value is NOT flagged as missing from vendor
    om = A.audit_label(
        _pos("p", "L3", "N+1", "Not stated", ltype="omission"), owner, vendor, is_image=False)
    assert om == []


def test_label_audit_runs_on_seed():
    import benchmark_label_audit as A
    labels = L.load_labels()
    verdicts = 0
    for lb in labels:
        d = L.BENCH / "pairs" / lb["pair_id"]
        owner = (d / "owner_requirement.md").read_text(encoding="utf-8")
        vendor = (d / "vendor_submittal.md").read_text(encoding="utf-8")
        A.audit_label(lb, owner, vendor, lb.get("modality") == "image")
        verdicts += 1
    assert verdicts == len(labels)


def test_manifest_flags_missing_and_bad_fields(tmp_path):
    rows = [{"source_id": "", "system_type": "nope", "document_role": "owner_requirement",
             "source_origin": "primary_vendor_public", "file_name": "", "sha256": "",
             "source_url": "", "retrieval_date": ""}]
    errs = L.validate_manifest(rows, root=tmp_path)
    assert any("missing source_id" in e for e in errs)
    assert any("invalid system_type" in e for e in errs)
    assert any("requires a source_url" in e for e in errs)


def test_label_schema_and_duplicate_rejection():
    dup = L.validate_labels([_pos("p", "D1", "10", "8"), _pos("p", "D1", "10", "8")])
    assert any("duplicate label_id" in e for e in dup)
    bad = _pos("p", "B1", "10", "8")
    bad["label_type"] = "not_a_type"
    assert any("invalid label_type" in e for e in L.validate_labels([bad]))
    missing_ev = _pos("p", "B2", "10", "8")
    missing_ev["evidence_required"] = {}
    assert any("evidence_required" in e for e in L.validate_labels([missing_ev]))


# ── scoring: one-to-one, FP, clean-negative, contested ───────────────
def test_one_to_one_no_double_credit():
    labs = [_pos("p", "L1", "10", "8"), _pos("p", "L2", "10", "8")]
    s = L.score_pair(labs, [_find("UPS", "battery_runtime_min", "10", "8")], L.matches_semantic)
    assert s["tp"] == 1 and s["fn"] == 1 and s["fp"] == 0


def test_false_positive_counting_never_negative():
    labs = [_pos("p", "L1", "10", "8")]
    finds = [_find("UPS", "battery_runtime_min", "10", "8"),
             _find("humidity", "rh", "40", "70"), _find("voltage", "v", "400", "380")]
    s = L.score_pair(labs, finds, L.matches_semantic)
    assert s["tp"] == 1 and s["fp"] == 2 and s["fp"] >= 0


def test_clean_negative_not_counted_positive_and_false_alert():
    neg = {**_pos("p", "N1", "10", "10"), "label_type": "clean_negative"}
    s = L.score_pair([neg], [], L.matches_semantic)
    assert s["positives"] == 0 and s["negatives"] == 1 and s["neg_false_alerts"] == 0
    s2 = L.score_pair([neg], [_find("UPS", "battery_runtime_min", "10", "8")], L.matches_semantic)
    assert s2["neg_false_alerts"] == 1 and s2["fp"] == 1


def test_clean_negative_alert_requires_parameter_overlap_when_available():
    neg = {
        **_pos(
            "p", "N1", "0.67", "0.60",
            comp="generator SCR and DEF", param="nox_g_bhp_hr",
        ),
        "label_type": "clean_negative",
    }
    unrelated = _find("generator SCR and DEF", "ammonia_slip_ppm", "5", "Not stated")
    score = L.score_pair([neg], [unrelated], L.matches_semantic)
    assert score["fp"] == 1
    assert score["neg_false_alerts"] == 0


def test_contested_excluded_from_primary_unless_configured():
    con = {**_pos("p", "C1", "27", "30", comp="supply-air", param="supply_air_temp_c"),
           "label_type": "ambiguous_contested", "contested": True}
    f = _find("CRAH", "supply_air_temp_c", "27", "30")
    s = L.score_pair([con], [f], L.matches_semantic, include_contested=False)
    assert s["positives"] == 0 and s["contested"] == 1
    s2 = L.score_pair([con], [f], L.matches_semantic, include_contested=True)
    assert s2["positives"] == 1 and s2["tp"] == 1


# ── aggregation: not-run counted as miss in primary ──────────────────
def test_timeout_not_run_counted_as_miss_in_primary():
    labels = [_pos("pa", "L1", "10", "8"), _pos("pb", "L2", "5", "8", param="thd")]
    run = {"pair_id": "pa", "not_run": False, "fp": 0, "neg_false_alerts": 0,
           "matched_semantic": ["L1"], "matched_exact": ["L1"], "latency_ms": 10}
    not_run = {"pair_id": "pb", "not_run": True, "fp": 0, "neg_false_alerts": 0,
               "matched_semantic": [], "matched_exact": [], "latency_ms": None}
    agg = L.aggregate([run, not_run], labels)
    assert agg["primary_recall_semantic"] == 0.5      # pb's positive counted as a miss
    assert agg["secondary_recall_semantic"] == 1.0    # pb excluded from secondary
    assert agg["pairs_not_run"] == 1
    import benchmark_revision_compare as C
    metrics = C._metrics({
        "positive_labels": 2, "primary_tp": 1, "false_positives_total": 1,
        "primary_recall_exact": 0.5, "clean_negative_false_alert_rate": 0.25,
        "latency_p50_ms": 10, "latency_p95_ms": 20, "pairs_not_run": 1,
    })
    assert metrics["recall"] == metrics["precision"] == metrics["f1"] == 0.5


# ── independence from the seeded corpus ──────────────────────────────
def test_no_seeded_ground_truth_labels_used():
    import benchmark_manifest_check as C
    seeded = C._ground_truth_ids()
    bench = {lb["label_id"] for lb in L.load_labels()}
    assert seeded and not (seeded & bench)   # seeded corpus exists, but no id overlap
    assert C.main() == 0


# ── scripts run without provider keys (no fabrication) ───────────────
def test_hash_and_report_run_without_keys(monkeypatch, tmp_path):
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    import benchmark_hash_sources as H
    import benchmark_report as R
    monkeypatch.setattr(R, "REPORTS", tmp_path / "reports")  # don't clobber committed reports
    assert H.main() == 0
    assert R.main() == 0
    assert (tmp_path / "reports" / "benchmark_card.json").exists()
    clean_primary = {
        "mode": "llm", "model": "google/gemini-3.1-flash-lite",
        "repeats_total": 3, "prompt_mode": "baseline", "worktree_dirty": False,
    }
    assert L.is_featured_primary_run(clean_primary, clean_primary["model"])
    assert not L.is_featured_primary_run(
        {**clean_primary, "publication_role": "branch-comparison"}, clean_primary["model"]
    )


def test_rule_mode_run_one_no_key(monkeypatch):
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    import benchmark_ps4_external as B
    labels = L.group_labels_by_pair(L.load_labels())["pair_001"]
    r = B.run_one("pair_001", labels, "rule")
    assert r["mode_used"] == "rule" and r["not_run"] is False
    assert r["tp_semantic"] == 1        # battery 10 -> 8 caught by the rule engine
    assert r["fp"] == 0


def test_image_pair_recorded_not_run_never_fabricated():
    import benchmark_ps4_external as B
    labels = L.group_labels_by_pair(L.load_labels())["pair_039"]
    r = B.run_one("pair_039", labels, "rule")
    assert r["not_run"] is True and r["modality"] == "image"
    assert r["error_type"] == "image_pending" and r["tp_semantic"] == 0  # not evaluated by the text path


def test_labels_carry_review_status_and_modality():
    labels = L.load_labels()
    assert labels
    assert all(lb.get("review_status") == "single_author_frozen_pending_review" for lb in labels)
    assert all(lb.get("modality") in ("text", "image") for lb in labels)


def test_multi_label_pair_has_multiple_checks():
    by = L.group_labels_by_pair(L.load_labels())
    assert len(by["pair_018"]) >= 5          # chiller pair carries several independent checks
    assert sum(1 for lb in L.load_labels() if lb["label_type"] == "clean_negative") >= 15


def test_code_provenance_hashes_binary_diff_without_decoding(monkeypatch):
    """`git diff --binary` output is bytes, not text. Decoding it with the
    platform code page (the Windows default under text=True) crashes on any
    byte the code page cannot represent, so provenance must hash raw bytes."""
    import benchmark_ps4_external as B

    class _Result:
        def __init__(self, stdout):
            self.stdout = stdout

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "rev-parse"]:
            return _Result("abc1234\n")
        assert "text" not in kwargs and "encoding" not in kwargs, (
            "the diff capture must stay binary"
        )
        return _Result("₹ utf-8 line\n".encode("utf-8") + b"\x81\xfe\x00raw")

    monkeypatch.setattr(B.subprocess, "run", fake_run)
    prov = B.code_provenance()
    assert prov["code_revision"] == "abc1234"
    assert prov["worktree_dirty"] is True
    digest = prov["working_tree_diff_sha256"]
    assert len(digest) == 64 and int(digest, 16) >= 0
