from __future__ import annotations

import tomllib
from collections import Counter
from pathlib import Path

import pytest

from scripts.check_mutation_score import mutation_summary, parse_results

ROOT = Path(__file__).resolve().parents[1]


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


def test_mutmut_isolated_tree_contains_repository_wide_test_inputs() -> None:
    """The mutation runner must execute the real suite, not a partial copy."""
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["mutmut"]
    copied = set(config["also_copy"])
    assert {
        "scripts/",
        "eval/",
        "data/",
        "benchmarks/",
        "contracts/",
        "docs/",
        "supabase/",
        "frontend/app/",
        "frontend/components/",
        "frontend/lib/",
        ".gitignore",
        "README.md",
        "PITCH.md",
        "COMPETITIVE.md",
        "presentation.html",
    } <= copied
    assert set(config["pytest_add_cli_args_test_selection"]) == {
        "--ignore=tests/test_ps4_hardening.py",
        "--ignore=tests/test_schedule_data.py",
        "--ignore=tests/test_schedule_risk.py",
        "--deselect=tests/test_api.py::TestStreamingEndpoints::test_copilot_stream_returns_sse",
        "--deselect=tests/test_api.py::TestStreamingEndpoints::test_analyze_stream_returns_sse",
        "--deselect=tests/test_api.py::TestPdfUploadEndpoints::test_upload_stream_text_files",
        "--deselect=tests/test_architecture.py::test_backend_architecture_gates_pass",
    }
