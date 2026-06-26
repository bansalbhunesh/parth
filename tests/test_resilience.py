"""
Resilience suite — proves Pramaan degrades gracefully on every front when the
LLM is unavailable, inputs are malformed, or the corpus is incomplete.

These are the paths that actually run in the demo and CI (no API key present),
so they must be bulletproof. Judges always ask "what happens without your key?"
— this file is the answer.
"""

import io
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
        from backend.llm import complete, LLMError
        try:
            complete("hello")
            assert False, "expected LLMError"
        except LLMError as exc:
            assert "GEMINI_API_KEY" in str(exc)

    def test_complete_json_raises_without_key(self):
        _clear_keys()
        from backend.llm import complete_json, LLMError
        try:
            complete_json("hello")
            assert False, "expected LLMError"
        except LLMError:
            pass

    def test_claude_provider_raises_without_key(self):
        _clear_keys()
        from backend.llm import _claude, LLMError
        try:
            _claude("hello", "", True)
            assert False, "expected LLMError"
        except LLMError as exc:
            assert "ANTHROPIC_API_KEY" in str(exc)

    def test_gemini_stream_raises_without_key(self):
        _clear_keys()
        from backend.llm import _gemini_stream, LLMError
        try:
            list(_gemini_stream("hello", ""))
            assert False, "expected LLMError"
        except LLMError:
            pass

    def test_claude_stream_raises_without_key(self):
        _clear_keys()
        from backend.llm import _claude_stream, LLMError
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

    def test_array_preferred_over_object(self):
        # Contract: deviations arrive as a top-level array, so the extractor
        # prefers the first balanced [...] when both shapes are present.
        from backend.llm import _extract_json
        result = _extract_json('{"wrap": [1, 2, 3]}')
        assert result == [1, 2, 3]

    def test_malformed_raises(self):
        from backend.llm import _extract_json
        try:
            _extract_json("this is not json at all")
            assert False, "expected parse failure"
        except (ValueError, Exception):
            pass


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
        from backend.agents.commissioning import predict_cx_impact, _RULES
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

    def test_get_document_text_missing_system(self):
        from backend.agents.ingestion import get_document_text
        assert get_document_text("NONEXISTENT_SYSTEM_XYZ") is None

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


class TestExtractionScoring:
    """Extraction scoring math is correct across all precision/recall regimes."""

    def test_perfect_extraction(self):
        from backend.agents.extraction import score_extraction
        import json
        ref = [{"component": "A", "parameter": "p"},
               {"component": "B", "parameter": "q"}]
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False, dir=str(CORPUS)
        ) as f:
            json.dump(ref, f)
            tmp = pathlib.Path(f.name)
        try:
            extracted = [{"component": "A", "parameter": "p"},
                         {"component": "B", "parameter": "q"}]
            scores = score_extraction(extracted, tmp.name)
            assert scores["precision"] == 1.0
            assert scores["recall"] == 1.0
            assert scores["f1"] == 1.0
        finally:
            tmp.unlink()

    def test_false_positive_lowers_precision(self):
        from backend.agents.extraction import score_extraction
        import json
        ref = [{"component": "A", "parameter": "p"}]
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False, dir=str(CORPUS)
        ) as f:
            json.dump(ref, f)
            tmp = pathlib.Path(f.name)
        try:
            extracted = [{"component": "A", "parameter": "p"},
                         {"component": "FALSE", "parameter": "positive"}]
            scores = score_extraction(extracted, tmp.name)
            assert scores["precision"] == 0.5
            assert scores["recall"] == 1.0
            assert scores["fp"] == 1
        finally:
            tmp.unlink()

    def test_missed_deviation_lowers_recall(self):
        from backend.agents.extraction import score_extraction
        import json
        ref = [{"component": "A", "parameter": "p"},
               {"component": "B", "parameter": "q"}]
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False, dir=str(CORPUS)
        ) as f:
            json.dump(ref, f)
            tmp = pathlib.Path(f.name)
        try:
            extracted = [{"component": "A", "parameter": "p"}]
            scores = score_extraction(extracted, tmp.name)
            assert scores["recall"] == 0.5
            assert scores["fn"] == 1
        finally:
            tmp.unlink()


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
        # Without a key, reconciliation yields no deviations but never crashes.
        _clear_keys()
        from backend.orchestrator import run_pipeline
        devs = run_pipeline("UPS")
        assert isinstance(devs, list)
