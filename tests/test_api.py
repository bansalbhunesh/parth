"""
Tests for the FastAPI endpoints — verifies all API routes return expected
shapes without requiring LLM API keys.
"""

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
        # We don't actually call ingest (needs LLM keys) but verify
        # the 404 validation works for invalid systems
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


class TestDataEndpoints:
    def test_cx_plan(self):
        r = client.get("/cx-plan")
        assert r.status_code == 200
        data = r.json()
        assert "tests" in data

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
