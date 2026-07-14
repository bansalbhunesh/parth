"""Coverage-matrix prompt pass (v1.3 CANDIDATE) — opt-in contract.

The frozen benchmark's error analysis names omission under-detection as the
top real false-negative cause. The coverage-matrix mode restructures the
reconciler's output into checklist-then-deviations (schema-guided cascade) so
absence detection becomes a per-item lookup. These tests pin the two
properties that keep the published numbers honest:

1. OFF by default — the default prompt stays byte-identical to the one the
   frozen ps4_external_v1 numbers were measured with.
2. When enabled, the suffix is appended and the object-shaped response
   ({"checklist": [...], "deviations": [...]}) parses to the same deviation
   list the rest of the pipeline expects.
"""

from backend.agents.reconciliation import (
    COVERAGE_MATRIX_ENV,
    COVERAGE_MATRIX_SUFFIX,
    PROMPT_TEMPLATE,
    _prompt_suffix,
    _validate_deviations,
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


class TestOptIn:
    def test_flag_enables_suffix(self, monkeypatch):
        monkeypatch.setenv(COVERAGE_MATRIX_ENV, "1")
        s = _prompt_suffix()
        assert s == COVERAGE_MATRIX_SUFFIX
        # The contract the mode exists for: checklist first, omission rows
        # forced into deviations.
        assert "addressed_in_submittal" in s
        assert "EVERY requirement" in s
        assert '"Not stated"' in s

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
            return {"checklist": [], "deviations": [dict(_DEV)]}

        monkeypatch.setattr("backend.agents.reconciliation.complete_json",
                            fake_complete_json)

        monkeypatch.delenv(COVERAGE_MATRIX_ENV, raising=False)
        devs = reconcile_system_at(base, "UPS", standards_text="")
        assert "COVERAGE MATRIX" not in seen["prompt"]
        assert len(devs) == 1

        monkeypatch.setenv(COVERAGE_MATRIX_ENV, "1")
        devs = reconcile_system_at(base, "UPS", standards_text="")
        assert "COVERAGE MATRIX" in seen["prompt"]
        # Object-shaped response still yields the normal deviation list with
        # system stamped on, exactly like the array-shaped default path.
        assert len(devs) == 1
        assert devs[0]["system"] == "UPS"
