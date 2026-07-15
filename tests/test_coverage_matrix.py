"""Coverage-matrix prompt pass (v1.7 CANDIDATE) — opt-in contract.

The frozen benchmark's error analysis names omission under-detection as the
top real false-negative cause. The coverage-matrix mode restructures the
reconciler's output into checklist-then-deviations (schema-guided cascade) so
absence detection becomes a per-item lookup while preserving the proven
deviation-array response shape. These tests pin the two
properties that keep the published numbers honest:

1. OFF by default — the default builder stays byte-identical to the current,
   separately versioned baseline template.
2. When enabled, the baseline output clause is replaced with an internal
   checklist instruction and the same deviation-array contract.
"""

from backend.agents.reconciliation import (
    BASELINE_PROMPT_VERSION,
    COVERAGE_MATRIX_ENV,
    COVERAGE_MATRIX_PROMPT_VERSION,
    COVERAGE_MATRIX_SUFFIX,
    PROMPT_TEMPLATE,
    _prompt_suffix,
    _validate_deviations,
    active_prompt_version,
    build_reconciliation_prompt,
    reconcile_system_at,
)

_DEV = {
    "component": "UPS-02",
    "parameter": "battery_runtime_min",
    "required_value": "10",
    "provided_value": "Not stated",
    "unit": "min",
    "severity": "Major",
    "confidence": 0.9,
}


class TestOffByDefault:
    def test_no_suffix_without_flag(self, monkeypatch):
        monkeypatch.delenv(COVERAGE_MATRIX_ENV, raising=False)
        assert _prompt_suffix() == ""

    def test_explicit_zero_is_off(self, monkeypatch):
        monkeypatch.setenv(COVERAGE_MATRIX_ENV, "0")
        assert _prompt_suffix() == ""

    def test_measured_template_untouched(self):
        # The default prompt (what the benchmark measured) must not mention
        # the coverage matrix at all.
        assert "COVERAGE MATRIX" not in PROMPT_TEMPLATE
        assert "checklist" not in PROMPT_TEMPLATE

    def test_shared_builder_is_byte_identical_to_measured_template(self, monkeypatch):
        monkeypatch.delenv(COVERAGE_MATRIX_ENV, raising=False)
        expected = PROMPT_TEMPLATE.format(spec="SPEC", submittal="SUB", standards="STD")
        assert build_reconciliation_prompt("SPEC", "SUB", "STD") == expected
        assert active_prompt_version() == BASELINE_PROMPT_VERSION


class TestOptIn:
    def test_flag_enables_suffix(self, monkeypatch):
        monkeypatch.setenv(COVERAGE_MATRIX_ENV, "1")
        s = _prompt_suffix()
        assert s == COVERAGE_MATRIX_SUFFIX
        # The contract the mode exists for: checklist first, omission rows
        # forced into deviations.
        assert "INTERNAL checklist" in s
        assert "SCOPE GATE" in s
        assert "unrelated equipment" in s
        assert "EVERY applicable requirement" in s
        assert '"Not stated"' in s
        assert "return ONLY a JSON array" in s
        assert "Do NOT return this checklist" in s
        assert '"provided_value"' in s
        assert active_prompt_version() == COVERAGE_MATRIX_PROMPT_VERSION

    def test_shared_builder_replaces_baseline_output_clause(self, monkeypatch):
        monkeypatch.setenv(COVERAGE_MATRIX_ENV, "1")
        prompt = build_reconciliation_prompt("SPEC", "SUB", "STD")
        baseline = PROMPT_TEMPLATE.format(spec="SPEC", submittal="SUB", standards="STD")
        assert prompt.startswith(baseline.split(
            "Return a JSON array of deviations found. Each element:")[0])
        assert prompt.endswith(COVERAGE_MATRIX_SUFFIX)
        assert "Return a JSON array of deviations found" not in prompt
        assert "If there are ZERO deviations for this system, return an empty array" not in prompt

    def test_object_with_checklist_parses_deviations(self):
        raw = {"checklist": [{"component": "UPS-02",
                              "parameter": "battery_runtime_min",
                              "required_value": "10",
                              "addressed_in_submittal": False}],
               "deviations": [dict(_DEV)]}
        devs = _validate_deviations(raw)
        assert len(devs) == 1
        assert devs[0]["parameter"] == "battery_runtime_min"
        assert devs[0]["provided_value"] == "Not stated"


class TestPromptWiring:
    def _corpus(self, tmp_path):
        (tmp_path / "specs").mkdir()
        (tmp_path / "submittals").mkdir()
        (tmp_path / "specs" / "UPS.md").write_text(
            "UPS-02 battery_runtime_min shall be 10 min", encoding="utf-8")
        (tmp_path / "submittals" / "UPS.md").write_text(
            "UPS-02 efficiency 96 percent", encoding="utf-8")
        return tmp_path

    def test_suffix_reaches_llm_only_when_enabled(self, tmp_path, monkeypatch):
        base = self._corpus(tmp_path)
        seen = {}

        def fake_complete_json(prompt, system=None):
            seen["prompt"] = prompt
            return [dict(_DEV)]

        monkeypatch.setattr("backend.agents.reconciliation.complete_json",
                            fake_complete_json)

        monkeypatch.delenv(COVERAGE_MATRIX_ENV, raising=False)
        devs = reconcile_system_at(base, "UPS", standards_text="")
        assert "COVERAGE MATRIX" not in seen["prompt"]
        assert len(devs) == 1

        monkeypatch.setenv(COVERAGE_MATRIX_ENV, "1")
        devs = reconcile_system_at(
            base, "UPS", standards_text="", feedback="Check omissions again."
        )
        assert "COVERAGE MATRIX" in seen["prompt"]
        assert "Return ONLY the corrected JSON array of deviations" in seen["prompt"]
        assert "Return the coverage-matrix JSON object" not in seen["prompt"]
        # Candidate mode preserves the normal deviation-list contract and
        # stamps the system exactly like the default path.
        assert len(devs) == 1
        assert devs[0]["system"] == "UPS"

    def test_live_analysis_path_uses_candidate_only_when_enabled(self, monkeypatch):
        from backend import analyze

        seen = []

        def fake_complete_json(prompt, system=None):
            seen.append(prompt)
            return {"checklist": [], "deviations": [dict(_DEV)]}

        monkeypatch.setattr("backend.llm.complete_json", fake_complete_json)
        monkeypatch.setattr(analyze, "_all_standards_text", lambda **_kwargs: "")

        monkeypatch.delenv(COVERAGE_MATRIX_ENV, raising=False)
        assert analyze.run_analysis("SPEC 10", "SUB 8", "UPS").mode == "llm"
        assert "COVERAGE MATRIX" not in seen[-1]

        monkeypatch.setenv(COVERAGE_MATRIX_ENV, "1")
        assert analyze.run_analysis("SPEC 10", "SUB 8", "UPS").mode == "llm"
        assert "COVERAGE MATRIX" in seen[-1]


def test_benchmark_prompt_mode_is_versioned_and_isolated(monkeypatch):
    import os
    import pathlib
    import sys

    scripts = pathlib.Path(__file__).resolve().parents[1] / "scripts"
    sys.path.insert(0, str(scripts))
    import benchmark_ps4_external as benchmark

    monkeypatch.setenv(COVERAGE_MATRIX_ENV, "1")
    assert benchmark.configure_prompt_mode(benchmark.PROMPT_MODE_BASELINE) == BASELINE_PROMPT_VERSION
    assert COVERAGE_MATRIX_ENV not in os.environ

    assert benchmark.configure_prompt_mode(
        benchmark.PROMPT_MODE_COVERAGE_MATRIX
    ) == COVERAGE_MATRIX_PROMPT_VERSION
    assert os.environ[COVERAGE_MATRIX_ENV] == "1"
    provenance = benchmark.code_provenance()
    assert len(provenance["code_revision"]) == 40
    assert len(provenance["working_tree_diff_sha256"]) == 64
    assert benchmark._sanitize("branch e2e / exact") == "branch-e2e-exact"
