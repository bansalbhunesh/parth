"""API tests for the PS4 capability endpoints: schedule risk, supply chain,
project graph, and blast radius. Shape + graceful behaviour only (the numeric
math is covered by the engine unit tests)."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestScheduleEndpoint:
    def test_available_shape(self):
        r = client.get("/projects/meghdoot/schedule")
        assert r.status_code == 200
        d = r.json()
        assert d["available"] is True
        assert d["cpm"]["project_duration"] > 0
        assert "p80" in d["monte_carlo"]
        assert d["deviation_impact"]["slip_weeks"] >= 0
        assert "narrative" in d["narrative"]

    def test_missing_project_is_available_false(self):
        r = client.get("/projects/doesnotexist/schedule")
        assert r.status_code == 200
        assert r.json()["available"] is False

    def test_flag_off(self, monkeypatch):
        monkeypatch.setenv("PRAMAAN_SCHEDULE", "0")
        r = client.get("/projects/meghdoot/schedule")
        assert r.status_code == 200
        assert r.json()["available"] is False


class TestSupplyChainEndpoint:
    def test_available_shape(self):
        r = client.get("/projects/meghdoot/supply-chain")
        assert r.status_code == 200
        d = r.json()
        assert d["available"] is True
        assert d["summary"]["total"] >= 1
        assert "narrative" in d["narrative"]

    def test_flag_off(self, monkeypatch):
        monkeypatch.setenv("PRAMAAN_SUPPLY", "0")
        assert client.get("/projects/meghdoot/supply-chain").json()["available"] is False


class TestGraphEndpoint:
    def test_graph_available(self):
        r = client.get("/projects/meghdoot/graph")
        assert r.status_code == 200
        d = r.json()
        assert d["available"] is True
        assert d["stats"]["nodes"] > 0
        assert len(d["graph"]["nodes"]) > 0
        assert len(d["graph"]["edges"]) > 0

    def test_blast_radius_available(self):
        r = client.get("/projects/meghdoot/blast-radius/DEV-001")
        assert r.status_code == 200
        d = r.json()
        assert d["available"] is True
        assert "worst_milestone_slip" in d
        assert any(s["label"] == "Vertiv" for s in d["suppliers"])

    def test_unknown_deviation_is_available_false(self):
        r = client.get("/projects/meghdoot/blast-radius/DEV-999")
        assert r.status_code == 200
        assert r.json()["available"] is False

    def test_flag_off(self, monkeypatch):
        monkeypatch.setenv("PRAMAAN_GRAPH", "0")
        assert client.get("/projects/meghdoot/graph").json()["available"] is False


class TestExistingProjectEndpointUntouched:
    def test_project_detail_still_works(self):
        r = client.get("/projects/meghdoot")
        assert r.status_code == 200
        assert "deviations" in r.json()

    def test_aggregate_still_works(self):
        r = client.get("/projects/eval/aggregate")
        assert r.status_code == 200
        assert r.json()["aggregate"]["projects"] == 12
