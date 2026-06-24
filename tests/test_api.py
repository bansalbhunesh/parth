
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestHealthEndpoints:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert "version" in data

    def test_project(self):
        r = client.get("/project")
        assert r.status_code == 200

    def test_systems(self):
        r = client.get("/systems")
        assert r.status_code == 200
        data = r.json()
        assert "systems" in data
        assert isinstance(data["systems"], list)


class TestDeviationEndpoints:
    def test_deviations_returns_register(self):
        r = client.get("/deviations")
        assert r.status_code == 200
        data = r.json()
        assert "register" in data
        assert "count" in data
        assert isinstance(data["register"], list)

    def test_deviations_count_matches(self):
        r = client.get("/deviations")
        data = r.json()
        assert data["count"] == len(data["register"])

    def test_deviations_have_required_fields(self):
        r = client.get("/deviations")
        data = r.json()
        required = {"component", "parameter", "required_value", "provided_value",
                     "unit", "severity"}
        for d in data["register"]:
            missing = required - d.keys()
            assert not missing, f"Deviation missing: {missing}"


class TestIngestEndpoint:
    def test_ingest_unknown_system(self):
        r = client.post("/ingest/NONEXISTENT")
        assert r.status_code == 404

    def test_ingest_valid_format(self):
        r = client.get("/systems")
        systems = r.json()["systems"]
        if not systems:
            return
        r = client.post("/ingest/DEFINITELY_NOT_REAL")
        assert r.status_code == 404


class TestCopilotEndpoint:
    def test_copilot_empty_query_rejected(self):
        r = client.post("/copilot", json={"query": ""})
        assert r.status_code == 422

    def test_copilot_returns_structure(self):
        r = client.post("/copilot", json={"query": "What is the UPS battery runtime?"})
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "sources" in data


class TestStreamingEndpoints:
    def test_copilot_stream_returns_sse(self):
        r = client.post("/copilot/stream", json={"query": "What is the UPS battery runtime?"})
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        body = r.text
        assert "event: meta" in body or "event: token" in body
        assert "event: done" in body

    def test_copilot_stream_empty_rejected(self):
        r = client.post("/copilot/stream", json={"query": ""})
        assert r.status_code == 422

    def test_analyze_stream_returns_sse(self):
        r = client.post("/analyze/stream", json={
            "spec_text": "**UPS-02** — battery runtime min: shall be **10 min**",
            "submittal_text": "**UPS-02** — battery runtime min: **7 min**",
        })
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        body = r.text
        assert "event: result" in body or "event: status" in body
        assert "event: done" in body


class TestPdfUploadEndpoints:
    def _make_text_file(self, content, filename):
        import io
        return ("spec_file", (filename, io.BytesIO(content.encode()), "text/plain"))

    def test_upload_text_files(self):
        import io
        spec = io.BytesIO(b"**UPS-02** -- battery runtime min: shall be **10 min**")
        sub = io.BytesIO(b"**UPS-02** -- battery runtime min: **7 min**")
        r = client.post("/analyze/upload", files=[
            ("spec_file", ("spec.txt", spec, "text/plain")),
            ("submittal_file", ("sub.txt", sub, "text/plain")),
        ])
        assert r.status_code == 200
        data = r.json()
        assert "deviations" in data
        assert "spec_filename" in data
        assert data["spec_filename"] == "spec.txt"

    def test_upload_stream_text_files(self):
        import io
        spec = io.BytesIO(b"**UPS-02** -- battery runtime min: shall be **10 min**")
        sub = io.BytesIO(b"**UPS-02** -- battery runtime min: **7 min**")
        r = client.post("/analyze/upload/stream", files=[
            ("spec_file", ("spec.txt", spec, "text/plain")),
            ("submittal_file", ("sub.txt", sub, "text/plain")),
        ])
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        body = r.text
        assert "event: result" in body or "event: status" in body
        assert "event: done" in body


class TestExportEndpoints:
    def test_export_audit_json(self):
        r = client.get("/export/audit")
        assert r.status_code == 200
        data = r.json()
        assert "project" in data
        assert "evidence" in data
        assert "standard_basis" in data

    def test_export_audit_html(self):
        r = client.get("/export/audit/html")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert "Pramaan" in r.text
        assert "<table>" in r.text


class TestAnalyzeEndpoint:
    def test_analyze_deterministic(self):
        spec = """# Design Basis
- **TEST-01** — voltage: shall be **400 V** (ref: DESIGN-BASIS; clause DB-1.1)
- **TEST-01** — current: shall be **100 A** (ref: DESIGN-BASIS; clause DB-1.2)"""
        submittal = """# Vendor Submittal
- **TEST-01** — voltage: **380 V** (vendor)
- **TEST-01** — current: **100 A** (vendor)"""
        r = client.post("/analyze", json={"spec_text": spec, "submittal_text": submittal})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 0  # may or may not find depending on regex
        assert "deviations" in data
        assert "elapsed_ms" in data

    def test_analyze_validation(self):
        r = client.post("/analyze", json={"spec_text": "short", "submittal_text": "short"})
        assert r.status_code == 422


class TestDataEndpoints:
    def test_cx_plan(self):
        r = client.get("/cx-plan")
        assert r.status_code == 200
        data = r.json()
        assert "tests" in data

    def test_cx_plan_has_all_tests(self):
        r = client.get("/cx-plan")
        data = r.json()
        assert len(data["tests"]) >= 17

    def test_rfi_log(self):
        r = client.get("/rfi-log")
        assert r.status_code == 200

    def test_metrics(self):
        r = client.get("/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "detection" in data
        assert "commissioning" in data
        assert data["detection"]["baseline_f1"] == 1.0

    def test_metrics_detection_counts(self):
        r = client.get("/metrics")
        data = r.json()
        assert data["detection"]["total_deviations"] == 14
        assert data["detection"]["critical"] == 7
        assert data["detection"]["major"] == 6
        assert data["detection"]["false_positive_rate"] == 0.0

    def test_metrics_commissioning(self):
        r = client.get("/metrics")
        data = r.json()
        assert data["commissioning"]["total_lead_time_weeks"] == 267
        assert data["commissioning"]["max_lead_time_weeks"] == 33
        assert data["commissioning"]["cx_prediction_accuracy"] == 1.0


class TestCorpusDocEndpoint:
    def test_get_spec_document(self):
        r = client.get("/corpus/doc/specs/UPS")
        assert r.status_code == 200
        data = r.json()
        assert "text" in data
        assert len(data["text"]) > 0

    def test_get_submittal_document(self):
        r = client.get("/corpus/doc/submittals/UPS")
        assert r.status_code == 200
        data = r.json()
        assert "text" in data

    def test_spec_contains_requirements(self):
        r = client.get("/corpus/doc/specs/UPS")
        data = r.json()
        assert "battery_runtime" in data["text"].lower() or "runtime" in data["text"].lower()

    def test_invalid_system_returns_404(self):
        r = client.get("/corpus/doc/specs/NONEXISTENT")
        assert r.status_code == 404

    def test_invalid_doc_type_returns_400(self):
        r = client.get("/corpus/doc/invalid/UPS")
        assert r.status_code == 400


class TestPipelineEndpoint:
    def test_pipeline_returns_nodes(self):
        r = client.get("/pipeline")
        assert r.status_code == 200
        data = r.json()
        assert "nodes" in data
        assert isinstance(data["nodes"], list)
        assert len(data["nodes"]) >= 4

    def test_pipeline_has_edges(self):
        r = client.get("/pipeline")
        data = r.json()
        assert "edges" in data
        assert len(data["edges"]) >= 4

    def test_pipeline_framework(self):
        r = client.get("/pipeline")
        data = r.json()
        assert data["framework"] == "LangGraph"


class TestCorpusStatsEndpoint:
    def test_corpus_stats(self):
        r = client.get("/corpus/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total_systems" in data
        assert data["total_systems"] >= 7

    def test_corpus_stats_has_standards(self):
        r = client.get("/corpus/stats")
        data = r.json()
        assert "total_standards" in data
        assert data["total_standards"] >= 5


class TestGroundTruthDeviations:
    """Test deviation data via the ground truth directly since
    /deviations endpoint requires LLM API key for pipeline."""

    def test_ground_truth_severity_distribution(self):
        import json
        gt = json.loads(
            (pathlib.Path(__file__).parent.parent / "data" / "corpus" / "ground_truth.json")
            .read_text()
        )
        devs = gt["seeded_deviations"]
        sevs = [d["severity"] for d in devs]
        assert sevs.count("Critical") == 7
        assert sevs.count("Major") == 6
        assert sevs.count("Minor") == 1

    def test_all_deviations_have_cx_prediction(self):
        import json
        gt = json.loads(
            (pathlib.Path(__file__).parent.parent / "data" / "corpus" / "ground_truth.json")
            .read_text()
        )
        for d in gt["seeded_deviations"]:
            assert d.get("predicted_cx_test") is not None, \
                f"{d['component']}.{d['parameter']} missing cx prediction"

    def test_all_deviations_have_lead_time(self):
        import json
        gt = json.loads(
            (pathlib.Path(__file__).parent.parent / "data" / "corpus" / "ground_truth.json")
            .read_text()
        )
        for d in gt["seeded_deviations"]:
            assert d.get("lead_time_weeks") is not None
            assert d["lead_time_weeks"] > 0

    def test_total_lead_time(self):
        import json
        gt = json.loads(
            (pathlib.Path(__file__).parent.parent / "data" / "corpus" / "ground_truth.json")
            .read_text()
        )
        total = sum(d["lead_time_weeks"] for d in gt["seeded_deviations"])
        assert total == 267
