"""Guards against the benchmark's headline numbers drifting out of sync
across the doc surfaces that quote them (P2-3).

The benchmark's raw numbers are quoted by hand in ~20 files (README, PITCH,
DECK, CLAIMS_REGISTER, the judge page, ...) rather than generated from a
single source, because those are narrative documents, not templates - a full
generate-everything rewrite would risk breaking carefully-written prose for
marginal benefit. What actually matters is that a future benchmark re-run
can't silently leave any of those quotes wrong. This test is that guarantee:
if benchmark_card.json's numbers ever change, every file below must be
updated to match or this test fails - the same enforcement pattern
test_claims_register.py already uses for banned wording, applied to the
benchmark's numeric claims instead.
"""

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CARD = json.loads(
    (ROOT / "benchmarks/ps4_external_v1/reports/benchmark_card.json").read_text(encoding="utf-8")
)

# The canonical values every surface below must quote exactly, derived from
# the same rounding benchmark_report.py itself uses (round to 3 decimals for
# recall/precision/F1, 4 for the rule baseline's raw 0.1111 which is
# conventionally displayed truncated to 0.111 everywhere in prose).
RECALL = f"{CARD['primary_result']['recall_mean']:.3f}"
PRECISION = f"{CARD['primary_result']['precision_mean']:.3f}"
F1 = f"{CARD['primary_result']['f1_mean']:.3f}"
FAR = f"{CARD['primary_result']['clean_negative_false_alert_rate_mean']:.3f}"
RULE_BASELINE = "0.111"  # 0.1111 truncated — matches every existing surface's convention
PAIRS = str(CARD["composition"]["pairs"])
LABELS = str(CARD["composition"]["labels"])

assert CARD["rule_baseline"]["primary_recall_semantic"] == 0.1111, (
    "rule_baseline.primary_recall_semantic changed from 0.1111 - update RULE_BASELINE above"
)

# Surfaces that state the full headline (recall + precision + F1 together) -
# the ones a judge is actually likely to read for the "real" number. Scoped
# to what each file actually contains today (verified by hand, not assumed) -
# a file that only ever states recall alone doesn't belong here; see
# RECALL_ONLY_SURFACES below for those.
FULL_HEADLINE_SURFACES = [
    "README.md",
    "PITCH.md",
    "docs/DECK.md",
    "docs/CLAIMS_REGISTER.md",
]

# States recall only (no precision/F1) - still worth pinning so a re-run
# can't leave a stale recall number here even without the full triple.
RECALL_ONLY_SURFACES = [
    "frontend/app/judge/page.tsx",
]

# Surfaces that only ever quote the rule-baseline comparison (recall +
# 0.111), not the full precision/F1 triple.
RULE_BASELINE_SURFACES = [
    "README.md",
    "PITCH.md",
    "docs/CLAIMS_REGISTER.md",
]

PAIRS_LABELS_SURFACES = [
    "README.md",
]


def _text(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


@pytest.mark.parametrize("rel_path", FULL_HEADLINE_SURFACES)
def test_headline_metrics_match_benchmark_card(rel_path):
    text = _text(rel_path)
    for value, name in ((RECALL, "recall"), (PRECISION, "precision"), (F1, "F1")):
        assert value in text, (
            f"{rel_path} does not contain the current benchmark_card.json {name} "
            f"({value}) - this file has drifted from the frozen benchmark, or the "
            f"benchmark was re-run and this file wasn't updated to match"
        )


@pytest.mark.parametrize("rel_path", RECALL_ONLY_SURFACES)
def test_recall_only_metric_matches_benchmark_card(rel_path):
    text = _text(rel_path)
    assert RECALL in text, (
        f"{rel_path} does not contain the current benchmark_card.json recall "
        f"({RECALL}) - this file has drifted from the frozen benchmark"
    )


@pytest.mark.parametrize("rel_path", RULE_BASELINE_SURFACES)
def test_rule_baseline_matches_benchmark_card(rel_path):
    text = _text(rel_path)
    assert RULE_BASELINE in text, (
        f"{rel_path} does not contain the current rule-baseline recall ({RULE_BASELINE})"
    )


@pytest.mark.parametrize("rel_path", PAIRS_LABELS_SURFACES)
def test_pair_and_label_counts_match_benchmark_card(rel_path):
    text = _text(rel_path)
    assert f"{PAIRS} pairs" in text, (
        f"{rel_path} does not state the current pair count ({PAIRS} pairs) - "
        f"benchmark composition changed without updating this file"
    )
    assert f"{LABELS} labels" in text, (
        f"{rel_path} does not state the current label count ({LABELS} labels)"
    )


def test_claims_register_pair_and_label_counts_match_benchmark_card():
    # CLAIMS_REGISTER.md phrases these as "53 team-authored spec-submittal
    # pairs" / "129 single-author-frozen labels" - the exact adjective
    # between the number and the noun varies by file, so this checks the
    # numbers are present at all (a regex on "\bNN\b" near "pair"/"label"),
    # not one fixed phrase, while still failing if the benchmark's actual
    # composition counts change and this file isn't updated to match.
    import re

    text = _text("docs/CLAIMS_REGISTER.md")
    assert re.search(rf"\b{PAIRS}\b[^.]{{0,40}}pairs?\b", text), (
        f"docs/CLAIMS_REGISTER.md does not state the current pair count ({PAIRS})"
    )
    assert re.search(rf"\b{LABELS}\b[^.]{{0,40}}labels?\b", text), (
        f"docs/CLAIMS_REGISTER.md does not state the current label count ({LABELS})"
    )


def test_far_is_stated_as_zero_everywhere_it_appears():
    # FAR is 0.000 today; if it's ever non-zero, every "0 false alerts" /
    # "FAR 0.000" claim across the repo becomes false simultaneously. This
    # doesn't scan every surface (too many phrasings of "zero"), but it
    # pins the underlying fact so a future non-zero FAR fails loudly here
    # first, prompting a manual audit of every place that currently claims
    # zero, rather than the benchmark quietly regressing unnoticed.
    assert FAR == "0.000", (
        "clean_negative_false_alert_rate_mean is no longer 0.000 - every "
        "'0 false alerts' / 'FAR 0.000' claim in README/PITCH/CLAIMS_REGISTER/"
        "the judge page needs a manual audit, not just this test updated"
    )
