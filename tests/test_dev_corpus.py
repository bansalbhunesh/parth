"""Safety contracts for the isolated prompt-development corpus."""

from __future__ import annotations

from collections import Counter

from scripts import benchmark_lib as L
from scripts import benchmark_ps4_external as B
from scripts import dev_corpus_eval as D


def test_dev_corpus_is_complete_frozen_and_disjoint() -> None:
    labels, errors = D.validate_corpus(require_frozen=True)

    assert errors == []
    assert len(labels) == 25
    assert len({label["pair_id"] for label in labels}) == 14
    assert Counter(label["label_type"] for label in labels) == {
        "clean_negative": 11,
        "omission": 5,
        "positive_deviation": 8,
        "adversarial_instruction": 1,
    }
    assert {label["pair_id"] for label in labels}.isdisjoint(
        label["pair_id"] for label in L.load_labels()
    )
    assert D.corpus_content_hash() == (
        "e2065a9ee7afd748bdc4955c061b5dbf39a48b5d3bb21d9efc175ad816ee131f"
    )


def test_main_dev_runner_exposes_no_rejected_prompt_mode() -> None:
    assert D.PROMPT_MODES == (
        B.PROMPT_MODE_BASELINE,
        B.PROMPT_MODE_COVERAGE_MATRIX,
    )
    assert all("v1.8" not in mode for mode in D.PROMPT_MODES)


def test_benchmark_helpers_read_the_explicit_dev_corpus() -> None:
    labels = D.load_labels()
    by_pair = L.group_labels_by_pair(labels)
    owner, submittal = B._read_pair("dev_pair_001", D.DEV)
    result = B.run_one("dev_pair_001", by_pair["dev_pair_001"], "rule", D.DEV)

    assert "External Lightning Protection" in owner
    assert "Vendor Submittal" in submittal
    assert result["pair_id"] == "dev_pair_001"
    assert result["mode_used"] == "rule"
