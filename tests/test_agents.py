
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

CORPUS = pathlib.Path(__file__).parent.parent / "data" / "corpus"


class TestIngestionAgent:
    def test_ingest_file_markdown(self):
        from backend.agents.ingestion import ingest_file
        path = CORPUS / "specs" / "UPS.md"
        if not path.exists():
            return
        result = ingest_file(path)
        assert "text" in result
        assert result["word_count"] > 0
        assert result["content_hash"]
        assert result["suffix"] == ".md"

    def test_ingest_system(self):
        from backend.agents.ingestion import ingest_system
        result = ingest_system("UPS")
        assert result["system_id"] == "UPS"
        assert result["total_documents"] >= 0

    def test_ingest_standards(self):
        from backend.agents.ingestion import ingest_standards
        docs = ingest_standards()
        assert isinstance(docs, list)
        if docs:
            assert docs[0]["doc_type"] == "standard"
            assert docs[0]["word_count"] > 0

    def test_ingest_corpus_structure(self):
        from backend.agents.ingestion import ingest_corpus
        result = ingest_corpus()
        assert "systems" in result
        assert "standards" in result
        assert "total_documents" in result
        assert result["total_documents"] > 0

    def test_clean_text(self):
        from backend.agents.ingestion import _clean_text
        assert _clean_text("  hello   world  ") == "hello world"
        assert _clean_text("a\r\nb") == "a\nb"
        assert _clean_text("a\n\n\n\nb") == "a\n\nb"

    def test_unsupported_file_type(self):
        from backend.agents.ingestion import ingest_file
        result = ingest_file(pathlib.Path("/fake/file.xyz"))
        assert "error" in result

    def test_get_document_text(self):
        from backend.agents.ingestion import get_document_text
        text = get_document_text("UPS", "spec")
        if text is not None:
            assert len(text) > 0

    def test_get_document_text_missing(self):
        from backend.agents.ingestion import get_document_text
        text = get_document_text("NONEXISTENT_SYSTEM", "spec")
        assert text is None


class TestExtractionAgent:
    def test_extract_prompt_template(self):
        from backend.agents.extraction import EXTRACT_PROMPT
        assert "{text}" in EXTRACT_PROMPT
        assert "{doc_type}" in EXTRACT_PROMPT

    def test_score_extraction(self):
        from backend.agents.extraction import score_extraction
        extracted = [
            {"component": "UPS-02", "parameter": "battery_runtime_min"},
            {"component": "FAKE", "parameter": "fake_param"},
        ]
        ref_path = "ground_truth.json"
        gt = json.loads((CORPUS / ref_path).read_text())
        ref = gt["seeded_deviations"]
        ref_keys = {(r["component"], r["parameter"]) for r in ref}
        ext_keys = {(e["component"], e["parameter"]) for e in extracted}
        tp = ref_keys & ext_keys
        assert len(tp) == 1


class TestCommissioningAgent:
    def test_rules_mapping(self):
        from backend.agents.commissioning import _RULES
        assert ("UPS-02", "battery_runtime_min") in _RULES
        assert ("GEN-FUEL", "onsite_fuel_hours") in _RULES
        assert len(_RULES) == 14

    def test_predict_known_deviation(self):
        from backend.agents.commissioning import predict_cx_impact
        dev = {"component": "UPS-02", "parameter": "battery_runtime_min",
               "severity": "Critical"}
        result = predict_cx_impact(dev)
        assert result["predicted_cx_test"] == "IST-07"
        assert result["predicted_cx_level"] == 4
        assert result["lead_time_weeks"] == 27
        assert result["cx_source"] == "rule"

    def test_predict_all_known_deviations(self):
        from backend.agents.commissioning import predict_cx_impact, _RULES
        for (comp, param), (test_id, level, week_fail, sev) in _RULES.items():
            dev = {"component": comp, "parameter": param, "severity": sev}
            result = predict_cx_impact(dev)
            assert result["predicted_cx_test"] == test_id
            assert result["predicted_cx_level"] == level

    def test_risk_score_critical(self):
        from backend.agents.commissioning import compute_risk_score
        dev = {"severity": "Critical", "lead_time_weeks": 27,
               "predicted_cx_level": 4}
        score = compute_risk_score(dev)
        assert 0.0 < score <= 1.0
        assert score > 0.8

    def test_risk_score_minor(self):
        from backend.agents.commissioning import compute_risk_score
        dev = {"severity": "Minor", "lead_time_weeks": 3,
               "predicted_cx_level": 1}
        score = compute_risk_score(dev)
        assert 0.0 < score <= 1.0
        assert score < 0.5

    def test_cx_plan_loads(self):
        from backend.agents.commissioning import _load_cx_plan
        plan = _load_cx_plan()
        assert "tests" in plan
        assert len(plan["tests"]) > 0

    def test_cx_name_lookup(self):
        from backend.agents.commissioning import _cx_name
        name = _cx_name("IST-07")
        assert name is not None
        assert "battery" in name.lower() or "maintenance" in name.lower()


class TestReconciliationValidation:
    def test_validate_valid_deviation(self):
        from backend.agents.reconciliation import _validate_deviations
        raw = [{"component": "X", "parameter": "y",
                "required_value": 10, "provided_value": 5}]
        result = _validate_deviations(raw)
        assert len(result) == 1
        assert result[0]["unit"] == ""
        assert result[0]["severity"] == "Major"

    def test_validate_missing_keys(self):
        from backend.agents.reconciliation import _validate_deviations
        raw = [{"component": "X"}]
        result = _validate_deviations(raw)
        assert len(result) == 0

    def test_validate_non_list(self):
        from backend.agents.reconciliation import _validate_deviations
        result = _validate_deviations("not a list")
        assert result == []

    def test_validate_dict_with_deviations_key(self):
        from backend.agents.reconciliation import _validate_deviations
        raw = {"deviations": [{"component": "X", "parameter": "y",
                               "required_value": 10, "provided_value": 5}]}
        result = _validate_deviations(raw)
        assert len(result) == 1

    def test_validate_empty_list(self):
        from backend.agents.reconciliation import _validate_deviations
        result = _validate_deviations([])
        assert result == []

    def test_citation_faithfulness(self):
        from backend.agents.reconciliation import _check_citation_faithfulness
        devs = [{"spec_clause": "DB-4.3", "standard_ref": "UPTIME-TIER4"}]
        text = "This document references DB-4.3 and UPTIME-TIER4 standards."
        result = _check_citation_faithfulness(devs, text, "", "")
        assert result[0]["citation_faithful"] is True

    def test_citation_faithfulness_missing(self):
        from backend.agents.reconciliation import _check_citation_faithfulness
        devs = [{"spec_clause": "FAKE-99", "standard_ref": "FAKE-STD"}]
        result = _check_citation_faithfulness(devs, "nothing here", "", "")
        assert result[0]["citation_faithful"] is False


class TestOrchestrator:
    def test_conditional_routing_with_docs(self):
        from backend.orchestrator import route_after_validate
        state = {"system_id": "UPS", "spec_text": "spec", "submittal_text": "sub",
                 "standards_text": "", "ingestion_meta": None,
                 "extracted_triples": None, "deviations": [], "elapsed_ms": 0}
        assert route_after_validate(state) == "reconcile"

    def test_conditional_routing_missing_spec(self):
        from backend.orchestrator import route_after_validate
        state = {"system_id": "UPS", "spec_text": None, "submittal_text": "sub",
                 "standards_text": "", "ingestion_meta": None,
                 "extracted_triples": None, "deviations": [], "elapsed_ms": 0}
        assert route_after_validate(state) == "format_output"

    def test_conditional_routing_missing_submittal(self):
        from backend.orchestrator import route_after_validate
        state = {"system_id": "UPS", "spec_text": "spec", "submittal_text": None,
                 "standards_text": "", "ingestion_meta": None,
                 "extracted_triples": None, "deviations": [], "elapsed_ms": 0}
        assert route_after_validate(state) == "format_output"

    def test_build_graph_returns_compiled(self):
        from backend.orchestrator import build_graph
        graph = build_graph()
        if graph is not None:
            assert hasattr(graph, "invoke")

    def test_pipeline_nodes(self):
        from backend.orchestrator import (
            node_ingest, node_load_standards, node_validate,
            node_cx_predict, node_format_output,
        )
        assert callable(node_ingest)
        assert callable(node_load_standards)
        assert callable(node_validate)
        assert callable(node_cx_predict)
        assert callable(node_format_output)


class TestLLMModule:
    def test_extract_json_array(self):
        from backend.llm import _extract_json
        result = _extract_json('[{"a": 1}, {"b": 2}]')
        assert isinstance(result, list)
        assert len(result) == 2

    def test_extract_json_object(self):
        from backend.llm import _extract_json
        result = _extract_json('{"key": "value"}')
        assert result["key"] == "value"

    def test_extract_json_with_fences(self):
        from backend.llm import _extract_json
        result = _extract_json('```json\n[{"a": 1}]\n```')
        assert isinstance(result, list)

    def test_extract_json_with_prose(self):
        from backend.llm import _extract_json
        result = _extract_json('Here is the result:\n{"x": 42}\nDone.')
        assert result["x"] == 42

    def test_extract_json_nested(self):
        from backend.llm import _extract_json
        result = _extract_json('{"a": {"b": "c"}, "d": 4}')
        assert result["a"]["b"] == "c"
        assert result["d"] == 4

    def test_llm_error_class(self):
        from backend.llm import LLMError
        err = LLMError("test error")
        assert str(err) == "test error"
        assert isinstance(err, Exception)
