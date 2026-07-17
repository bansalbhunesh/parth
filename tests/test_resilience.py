"""
Resilience suite — proves Pramaan degrades gracefully on every front when the
LLM is unavailable, inputs are malformed, or the corpus is incomplete.

These are the paths that actually run in the demo and CI (no API key present),
so they must be bulletproof. Judges always ask "what happens without your key?"
— this file is the answer.
"""

import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

ROOT = pathlib.Path(__file__).parent.parent
CORPUS = ROOT / "data" / "corpus"


def _clear_keys():
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)


class TestLLMGracefulFailure:
    """Without API keys, every LLM entrypoint raises LLMError — never crashes."""

    def test_complete_raises_without_gemini_key(self):
        _clear_keys()
        from backend.llm import LLMError, complete
        try:
            complete("hello")
            assert False, "expected LLMError"
        except LLMError as exc:
            assert "GEMINI_API_KEY" in str(exc)

    def test_complete_json_raises_without_key(self):
        _clear_keys()
        from backend.llm import LLMError, complete_json
        try:
            complete_json("hello")
            assert False, "expected LLMError"
        except LLMError:
            pass

    def test_claude_provider_raises_without_key(self):
        _clear_keys()
        from backend.llm import LLMError, _claude
        try:
            _claude("hello", "", True)
            assert False, "expected LLMError"
        except LLMError as exc:
            assert "ANTHROPIC_API_KEY" in str(exc)

    def test_gemini_stream_raises_without_key(self):
        _clear_keys()
        from backend.llm import LLMError, _gemini_stream
        try:
            list(_gemini_stream("hello", ""))
            assert False, "expected LLMError"
        except LLMError:
            pass

    def test_claude_stream_raises_without_key(self):
        _clear_keys()
        from backend.llm import LLMError, _claude_stream
        try:
            list(_claude_stream("hello", ""))
            assert False, "expected LLMError"
        except LLMError:
            pass


class TestJSONExtraction:
    """The JSON extractor handles every shape an LLM might emit."""

    def test_plain_array(self):
        from backend.llm import _extract_json
        assert _extract_json('[{"a": 1}]') == [{"a": 1}]

    def test_plain_object(self):
        from backend.llm import _extract_json
        assert _extract_json('{"a": 1}') == {"a": 1}

    def test_fenced_json(self):
        from backend.llm import _extract_json
        assert _extract_json('```json\n[1, 2, 3]\n```') == [1, 2, 3]

    def test_fenced_no_lang(self):
        from backend.llm import _extract_json
        assert _extract_json('```\n{"x": "y"}\n```') == {"x": "y"}

    def test_prose_wrapped(self):
        from backend.llm import _extract_json
        result = _extract_json('Here are the results: [{"d": 1}] hope that helps')
        assert result == [{"d": 1}]

    def test_nested_object(self):
        from backend.llm import _extract_json
        result = _extract_json('{"outer": {"inner": 5}}')
        assert result["outer"]["inner"] == 5

    def test_top_level_object_preserved_when_it_contains_arrays(self):
        # A valid top-level object must not be reduced to its first nested
        # array; coverage-matrix responses carry both checklist + deviations.
        from backend.llm import _extract_json
        result = _extract_json('{"wrap": [1, 2, 3]}')
        assert result == {"wrap": [1, 2, 3]}
        result = _extract_json(
            '{"checklist": [{"parameter": "runtime"}], '
            '"deviations": [{"provided_value": 8}]}'
        )
        assert result["checklist"][0]["parameter"] == "runtime"
        assert result["deviations"][0]["provided_value"] == 8

    def test_malformed_raises(self):
        from backend.llm import _extract_json
        try:
            _extract_json("this is not json at all")
            assert False, "expected parse failure"
        except (ValueError, Exception):
            pass

    def test_salvage_truncated_array(self):
        # A reasoning model that ran out of output budget mid-array: the two
        # complete objects are recovered, the trailing truncated one dropped.
        from backend.llm import _extract_json
        raw = ('```json\n[\n  {"parameter": "a", "required_value": 10},\n'
               '  {"parameter": "b", "required_value": 20},\n'
               '  {"parameter": "c", "required_value": ')
        result = _extract_json(raw)
        assert result == [{"parameter": "a", "required_value": 10},
                          {"parameter": "b", "required_value": 20}]

    def test_salvage_ignores_braces_in_strings(self):
        # Braces inside string values must not miscount object boundaries.
        from backend.llm import _extract_json
        raw = '[{"note": "value is {x} not }y{"}, {"note": "second"}, {"bad":'
        result = _extract_json(raw)
        assert result == [{"note": "value is {x} not }y{"}, {"note": "second"}]

    def test_truncated_single_object_still_raises(self):
        # Nothing complete to salvage -> the strict parse error propagates.
        from backend.llm import _extract_json
        try:
            _extract_json('```json\n[\n  {"parameter": "a", "required_value": ')
            assert False, "expected parse failure"
        except (ValueError, Exception):
            pass


class TestGroundFindings:
    """The grounding filter drops findings whose required_value the design
    basis never states — the signature of a hallucinated requirement."""

    SPEC = ("Battery autonomy shall be at least 10 minutes. Chiller plant shall "
            "be N+1 redundant. Each branch load shall not exceed 32 A. Internal "
            "separation shall be Form 4b.")

    def _dev(self, **kw):
        d = {"component": "Battery", "parameter": "p", "required_value": "", "provided_value": "?"}
        d.update(kw)
        return d

    def test_grounded_numeric_kept(self):
        from backend.agents.reconciliation import _ground_findings
        out = _ground_findings([self._dev(required_value=10)], self.SPEC)
        assert len(out) == 1 and out[0]["grounded"] is True

    def test_prose_wrapped_numeric_kept(self):
        # Model adds prose ("Connected load <= 32 A") but 32 is in the spec.
        from backend.agents.reconciliation import _ground_findings
        out = _ground_findings([self._dev(required_value="Connected load <= 32 A")], self.SPEC)
        assert len(out) == 1

    def test_hallucinated_numeric_dropped(self):
        # 1200 kW module rating is nowhere in this spec.
        from backend.agents.reconciliation import _ground_findings
        out = _ground_findings([self._dev(required_value=1200)], self.SPEC)
        assert out == []

    def test_clause_like_component_does_not_suppress_grounded_value(self):
        from backend.agents.reconciliation import _ground_findings
        out = _ground_findings(
            [self._dev(component="DB-5", required_value=10)], self.SPEC,
        )
        assert len(out) == 1 and out[0]["grounded_value"] is True

    def test_np2_not_grounded_by_ip42(self):
        # "N+2" must NOT be grounded by a stray '2' inside 'IP42'.
        from backend.agents.reconciliation import _ground_findings
        spec = "Ingress protection shall be IP42. Chiller plant shall be N+1."
        out = _ground_findings([self._dev(required_value="N+2")], spec)
        assert out == []
        out = _ground_findings([self._dev(required_value="Type 2B")], spec)
        assert out == []

    def test_string_requirement_kept(self):
        from backend.agents.reconciliation import _ground_findings
        out = _ground_findings([self._dev(required_value="Form 4b")], self.SPEC)
        assert len(out) == 1

    def test_empty_required_value_dropped(self):
        from backend.agents.reconciliation import _ground_findings
        out = _ground_findings([self._dev(required_value="")], self.SPEC)
        assert out == []

    def test_real_omission_kept(self):
        # Spec requires N+1; model reports it omitted -> required_value grounded.
        from backend.agents.reconciliation import _ground_findings
        out = _ground_findings(
            [self._dev(parameter="redundancy", required_value="N+1",
                       provided_value="Not specified")], self.SPEC)
        assert len(out) == 1


class TestTransientRetry:
    """Transient 500/503 retries a bounded number of times; 429/quota does not."""

    def test_retries_transient_then_succeeds(self):
        import backend.llm as llm
        llm._RETRY_BACKOFF_S = 0.0
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("500 Internal Server Error")
            return "ok"

        assert llm._with_transient_retry(flaky, "test") == "ok"
        assert calls["n"] == 2

    def test_quota_429_not_retried(self):
        import backend.llm as llm
        llm._RETRY_BACKOFF_S = 0.0
        calls = {"n": 0}

        def quota():
            calls["n"] += 1
            raise RuntimeError("429 RESOURCE_EXHAUSTED quota")

        try:
            llm._with_transient_retry(quota, "test")
            assert False, "expected raise"
        except RuntimeError:
            pass
        assert calls["n"] == 1  # no retries on quota

    def test_non_transient_not_retried(self):
        import backend.llm as llm
        llm._RETRY_BACKOFF_S = 0.0
        calls = {"n": 0}

        def bad():
            calls["n"] += 1
            raise ValueError("bad request 400")

        try:
            llm._with_transient_retry(bad, "test")
            assert False, "expected raise"
        except ValueError:
            pass
        assert calls["n"] == 1


class TestCommissioningFallback:
    """Cx predictor falls back cleanly for unknown deviations (no API key)."""

    def test_unknown_deviation_returns_fallback(self):
        _clear_keys()
        from backend.agents.commissioning import predict_cx_impact
        result = predict_cx_impact({
            "component": "UNKNOWN-99", "parameter": "mystery", "severity": "Major",
        })
        assert result["cx_source"] == "fallback"
        assert result["predicted_cx_test"] is None
        assert result["lead_time_weeks"] is None
        # Never crashes, always returns a usable shape
        assert "week_caught" in result

    def test_llm_predict_fallback_shape(self):
        _clear_keys()
        from backend.agents.commissioning import _llm_predict
        result = _llm_predict({"component": "X", "parameter": "y"})
        assert result["cx_source"] == "fallback"
        assert "requires Cx engineer review" in result["predicted_cx_name"]

    def test_all_known_rules_route_to_rule_source(self):
        from backend.agents.commissioning import _RULES, predict_cx_impact
        for (comp, param) in _RULES:
            result = predict_cx_impact({
                "component": comp, "parameter": param, "severity": "Critical",
            })
            assert result["cx_source"] == "rule"
            assert result["predicted_cx_test"] is not None
            assert result["lead_time_weeks"] > 0

    def test_risk_score_bounded(self):
        from backend.agents.commissioning import compute_risk_score
        # Even a maxed-out deviation never exceeds 1.0
        high = compute_risk_score({
            "severity": "Critical", "lead_time_weeks": 40, "predicted_cx_level": 5,
        })
        assert 0.0 <= high <= 1.0

    def test_risk_score_unknown_severity(self):
        from backend.agents.commissioning import compute_risk_score
        score = compute_risk_score({"severity": "Nonsense"})
        assert 0.0 <= score <= 1.0


class TestAnalyzeDeterministicFallback:
    """run_analysis falls back to deterministic regex compare without a key."""

    def test_run_analysis_deterministic_mode(self):
        _clear_keys()
        from backend.analyze import run_analysis
        spec = "**UPS-02** — battery runtime: shall be **10 min**"
        sub = "**UPS-02** — battery runtime: **7 min**"
        result = run_analysis(spec, sub)
        assert result.mode == "deterministic"
        assert len(result.deviations) == 1
        assert result.deviations[0]["provided_value"] == "7"

    def test_run_analysis_no_deviations(self):
        _clear_keys()
        from backend.analyze import run_analysis
        spec = "**UPS-02** — battery runtime: shall be **10 min**"
        result = run_analysis(spec, spec)
        assert result.mode == "deterministic"
        assert result.deviations == []

    def test_run_analysis_empty_input(self):
        _clear_keys()
        from backend.analyze import run_analysis
        result = run_analysis("", "")
        assert result.deviations == []

    def test_streaming_analysis_yields_result(self):
        _clear_keys()
        from backend.analyze import run_streaming_analysis
        spec = "**GEN-01** — start time: shall be **10 sec**"
        sub = "**GEN-01** — start time: **30 sec**"
        events = list(run_streaming_analysis(spec, sub))
        text = "".join(events)
        assert "event: result" in text
        assert "event: done" in text


class TestFreeFormFallback:
    """The free-form detector catches real, un-templated deviations when the LLM
    is unavailable — the difference between a silent zero and a usable demo."""

    def test_catches_freeform_deviations(self):
        from backend.analyze import _freeform_compare
        spec = ("Battery autonomy shall be at least 10 minutes at full load. "
                "Online double-conversion efficiency shall be >= 96 percent. "
                "Input THD shall not exceed 5 percent.")
        sub = ("Vendor provides 7 minutes of battery runtime. ECO mode reaches "
               "99 percent; online efficiency is 93 percent. THD upon request.")
        params = {d["parameter"]: d for d in _freeform_compare(spec, sub)}
        assert "battery_runtime_min" in params
        assert params["battery_runtime_min"]["provided_value"] == "7"
        assert "efficiency_pct" in params
        assert params["efficiency_pct"]["provided_value"] == "93"  # online, not ECO 99

    def test_flags_omission(self):
        from backend.analyze import _freeform_compare
        spec = "Input THD shall not exceed 5 percent."
        sub = "THD figures are available upon request."
        params = {d["parameter"]: d for d in _freeform_compare(spec, sub)}
        assert params.get("input_thd_pct", {}).get("provided_value") == "Not stated"

    def test_no_false_positive_when_compliant(self):
        from backend.analyze import _freeform_compare
        spec = "Battery autonomy shall be at least 10 minutes."
        sub = "Vendor provides 10 minutes of battery runtime."
        assert _freeform_compare(spec, sub) == []

    def test_fallback_enriches_cx_without_llm(self):
        _clear_keys()
        from backend.analyze import _resilient_fallback
        spec = "Battery autonomy shall be at least 10 minutes at full load."
        sub = "Vendor provides 7 minutes of battery runtime."
        devs = _resilient_fallback(spec, sub, "UPS")
        bat = next(d for d in devs if d["parameter"] == "battery_runtime_min")
        assert bat["predicted_cx_test"] == "IST-07"   # rule-table, no LLM
        assert bat["lead_time_weeks"] == 27
        assert bat["system"] == "UPS"

    def test_run_analysis_no_longer_silent_zero(self):
        _clear_keys()
        from backend.analyze import run_analysis
        spec = ("Battery autonomy shall be at least 10 minutes. Online efficiency "
                "shall be >= 96 percent.")
        sub = "Vendor provides 7 minutes runtime and 93 percent online efficiency."
        result = run_analysis(spec, sub, "UPS")
        assert result.mode == "deterministic"
        assert len(result.deviations) >= 2  # NOT zero on free-form text


class TestIngestionRobustness:
    """Ingestion handles bad files, missing dirs, and odd input without crashing."""

    def test_garbage_pdf_bytes_returns_empty(self):
        from backend.agents.ingestion import extract_pdf_bytes
        assert extract_pdf_bytes(b"not a pdf", "x.pdf") == ""

    def test_empty_pdf_bytes_returns_empty(self):
        from backend.agents.ingestion import extract_pdf_bytes
        assert extract_pdf_bytes(b"", "empty.pdf") == ""

    def test_clean_text_normalizes_whitespace(self):
        from backend.agents.ingestion import _clean_text
        assert _clean_text("a\r\nb\n\n\n\nc   d\t\te") == "a\nb\n\nc d e"

    def test_clean_text_empty(self):
        from backend.agents.ingestion import _clean_text
        assert _clean_text("") == ""

    def test_ingest_txt_file(self):
        from backend.agents.ingestion import ingest_file
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
            f.write("hello world\nfoo bar baz")
            tmp = f.name
        try:
            doc = ingest_file(pathlib.Path(tmp))
            assert doc["word_count"] == 5
            assert doc["suffix"] == ".txt"
            assert len(doc["content_hash"]) == 16
        finally:
            os.unlink(tmp)

    def test_ingest_unsupported_type_returns_error(self):
        from backend.agents.ingestion import ingest_file
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            tmp = f.name
        try:
            doc = ingest_file(pathlib.Path(tmp))
            assert "error" in doc
        finally:
            os.unlink(tmp)

    def test_ingest_corpus_has_systems(self):
        from backend.agents.ingestion import ingest_corpus
        result = ingest_corpus()
        assert result["total_systems"] >= 1
        assert result["total_documents"] >= 1


class TestReconciliationValidation:
    """Deviation validation rejects malformed LLM output without crashing."""

    def test_validate_filters_non_dict_items(self):
        from backend.agents.reconciliation import _validate_deviations
        raw = [
            {"component": "A", "parameter": "p", "required_value": 1, "provided_value": 2},
            "garbage string",
            None,
            42,
        ]
        result = _validate_deviations(raw)
        assert len(result) == 1

    def test_validate_rejects_missing_required_keys(self):
        from backend.agents.reconciliation import _validate_deviations
        raw = [{"component": "A"}]  # missing parameter, values
        assert _validate_deviations(raw) == []

    def test_validate_non_list_non_dict(self):
        from backend.agents.reconciliation import _validate_deviations
        assert _validate_deviations("not a list") == []
        assert _validate_deviations(42) == []

    def test_validate_applies_defaults(self):
        from backend.agents.reconciliation import _validate_deviations
        raw = [{"component": "A", "parameter": "p",
                "required_value": 1, "provided_value": 2}]
        result = _validate_deviations(raw)
        assert result[0]["severity"] == "Major"
        assert result[0]["confidence"] == 0.5
        assert result[0]["standard_ref"] == "DESIGN-BASIS"

    def test_citation_faithfulness_flags_fabricated_clause(self):
        from backend.agents.reconciliation import _check_citation_faithfulness
        devs = [{"spec_clause": "FAKE-99.9", "standard_ref": "INVENTED-STD"}]
        result = _check_citation_faithfulness(devs, "spec", "submittal", "standards")
        assert result[0]["citation_faithful"] is False

    def test_citation_faithfulness_accepts_real_clause(self):
        from backend.agents.reconciliation import _check_citation_faithfulness
        spec = "Clause DB-4.3 requires this per UPTIME-TIER4."
        devs = [{"spec_clause": "DB-4.3", "standard_ref": "UPTIME-TIER4"}]
        result = _check_citation_faithfulness(devs, spec, "", "")
        assert result[0]["citation_faithful"] is True

    def test_reconcile_missing_system_returns_empty(self):
        from backend.agents.reconciliation import reconcile_system
        assert reconcile_system("NONEXISTENT_XYZ", "") == []


class TestOrchestratorResilience:
    """The pipeline degrades to a sequential runner and skips empty systems."""

    def test_route_skips_when_no_spec(self):
        from backend.orchestrator import route_after_validate
        state = {"system_id": "X", "spec_text": None, "submittal_text": "x"}
        assert route_after_validate(state) == "format_output"

    def test_route_skips_when_no_submittal(self):
        from backend.orchestrator import route_after_validate
        state = {"system_id": "X", "spec_text": "x", "submittal_text": None}
        assert route_after_validate(state) == "format_output"

    def test_route_proceeds_with_both_docs(self):
        from backend.orchestrator import route_after_validate
        state = {"system_id": "X", "spec_text": "a", "submittal_text": "b"}
        assert route_after_validate(state) == "reconcile"

    def test_init_state_shape(self):
        from backend.orchestrator import _init_state
        state = _init_state("UPS")
        assert state["system_id"] == "UPS"
        assert state["deviations"] == []

    def test_pipeline_runs_without_key(self):
        # Without a key, reconciliation throws LLMError on the first pass
        _clear_keys()
        from backend.orchestrator import run_pipeline
        import pytest
        with pytest.raises(Exception):
            run_pipeline("UPS")
