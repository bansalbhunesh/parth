from __future__ import annotations

from collections import Counter

import pytest

from scripts.check_mutation_score import mutation_summary, parse_results


def _results(*statuses: str) -> str:
    return "\n".join(f"backend.module.x__mutmut_{index}: {status}" for index, status in enumerate(statuses))


def test_mutation_score_counts_only_explicit_kills() -> None:
    counts = parse_results(_results(*(["killed"] * 17), *(["survived"] * 2), "no tests", "skipped"))
    summary = mutation_summary(counts)
    assert summary == {
        "score": 85.0,
        "killed": 17,
        "scored": 20,
        "excluded": 1,
        "statuses": {"killed": 17, "no tests": 1, "skipped": 1, "survived": 2},
    }


def test_type_checker_kills_are_valid_when_present() -> None:
    summary = mutation_summary(Counter({"caught by type check": 1, "killed": 3, "survived": 1}))
    assert summary["score"] == 80.0
    assert summary["killed"] == 4


@pytest.mark.parametrize("status", ["not checked", "check was interrupted by user"])
def test_incomplete_mutation_results_fail_closed(status: str) -> None:
    with pytest.raises(ValueError, match="incomplete"):
        mutation_summary(parse_results(_results("killed", status)))


def test_unknown_and_empty_results_fail_closed() -> None:
    with pytest.raises(ValueError, match="unknown"):
        parse_results(_results("mystery"))
    with pytest.raises(ValueError, match="no mutation results"):
        parse_results("Mutmut did not emit any result lines")
