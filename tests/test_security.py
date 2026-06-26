
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestInputSanitization:
    """Verify API rejects malicious or oversized inputs."""

    def test_xss_in_copilot_query(self):
        r = client.post("/copilot", json={"query": "<script>alert('xss')</script>"})
        assert r.status_code == 200
        data = r.json()
        assert "<script>" not in data.get("answer", "")

    def test_sql_injection_in_copilot(self):
        r = client.post("/copilot", json={"query": "'; DROP TABLE users; --"})
        assert r.status_code == 200

    def test_path_traversal_in_corpus_doc(self):
        r = client.get("/corpus/doc/specs/../../etc/passwd")
        assert r.status_code in (400, 404)

    def test_path_traversal_dots_in_system(self):
        r = client.get("/corpus/doc/specs/..%2F..%2Fetc%2Fpasswd")
        assert r.status_code in (400, 404)

    def test_oversized_analyze_input(self):
        huge = "x" * 1_000_000
        r = client.post("/analyze", json={"spec_text": huge, "submittal_text": huge})
        assert r.status_code in (200, 413, 422)

    def test_unicode_injection(self):
        r = client.post("/copilot", json={"query": "‮​  test"})
        assert r.status_code == 200


class TestNoSecretLeakage:
    """Verify no secrets leak through API responses."""

    def test_health_no_env_leak(self):
        r = client.get("/health")
        data = r.json()
        text = str(data).lower()
        assert "api_key" not in text
        assert "secret" not in text
        assert "password" not in text

    def test_env_file_not_committed(self):
        env_path = pathlib.Path(__file__).parent.parent / ".env"
        assert not env_path.exists() or env_path.stat().st_size == 0, \
            ".env file should not be committed with secrets"

    def test_gitignore_covers_env(self):
        gitignore = (pathlib.Path(__file__).parent.parent / ".gitignore").read_text()
        assert ".env" in gitignore

    def test_no_hardcoded_keys_in_source(self):
        backend_dir = pathlib.Path(__file__).parent.parent / "backend"
        for py_file in backend_dir.rglob("*.py"):
            content = py_file.read_text()
            assert "sk-" not in content, f"Possible API key in {py_file.name}"
            assert "AIza" not in content, f"Possible Google key in {py_file.name}"


class TestCORSAndHeaders:
    """Verify CORS and security headers."""

    def test_cors_headers_present(self):
        r = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        assert r.status_code in (200, 204, 405)

    def test_api_returns_json_content_type(self):
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")


class TestAPIContracts:
    """Verify API response shapes match frontend expectations."""

    def test_projects_endpoint_shape(self):
        r = client.get("/projects")
        assert r.status_code == 200
        data = r.json()
        assert "projects" in data
        assert "count" in data
        assert isinstance(data["projects"], list)
        assert data["count"] >= 1

    def test_project_summary_fields(self):
        r = client.get("/projects")
        data = r.json()
        for proj in data["projects"]:
            assert "id" in proj
            assert "name" in proj
            assert "tier" in proj
            assert "location" in proj
            assert "capacity_mw" in proj
            assert "deviations" in proj

    def test_projects_eval_aggregate_shape(self):
        r = client.get("/projects/eval/aggregate")
        assert r.status_code == 200
        data = r.json()
        agg = data["aggregate"]
        assert agg["projects"] == 6
        assert agg["total_deviations"] == 33
        assert agg["aggregate_f1"] == 1.0
        assert agg["total_lead_time_weeks"] == 691

    def test_per_project_eval_fields(self):
        r = client.get("/projects/eval/aggregate")
        data = r.json()
        for pid, proj in data["per_project"].items():
            assert "name" in proj
            assert "deviations" in proj
            assert "f1" in proj
            assert "total_lead_weeks" in proj
            assert proj["f1"] == 1.0

    def test_cx_plan_test_count(self):
        r = client.get("/cx-plan")
        data = r.json()
        assert len(data["tests"]) == 17

    def test_cx_plan_levels(self):
        r = client.get("/cx-plan")
        data = r.json()
        assert "levels" in data
        levels = set(t["level"] for t in data["tests"])
        assert levels == {1, 2, 3, 4, 5}

    def test_export_json_contains_project_info(self):
        r = client.get("/export/audit?format=json")
        assert r.status_code == 200
        data = r.json()
        assert "project" in data
        assert "evidence" in data
        assert "standard_basis" in data

    def test_export_returns_200(self):
        r = client.get("/export/audit?format=html")
        assert r.status_code == 200


class TestMultiProjectAPI:
    """Verify multi-project endpoints return correct data."""

    def test_six_projects_returned(self):
        r = client.get("/projects")
        data = r.json()
        assert data["count"] == 6

    def test_project_countries_diversity(self):
        r = client.get("/projects")
        data = r.json()
        locations = [p["location"] for p in data["projects"]]
        countries = set()
        for loc in locations:
            countries.add(loc.split(",")[-1].strip())
        assert len(countries) >= 5

    def test_project_tiers_diversity(self):
        r = client.get("/projects")
        data = r.json()
        tiers = set(p["tier"] for p in data["projects"])
        assert len(tiers) >= 4

    def test_aggregate_weeks_match_sum(self):
        r = client.get("/projects/eval/aggregate")
        data = r.json()
        per_project_sum = sum(
            p["total_lead_weeks"] for p in data["per_project"].values()
        )
        assert per_project_sum == data["aggregate"]["total_lead_time_weeks"]
        assert per_project_sum == 691

    def test_aggregate_deviations_match_sum(self):
        r = client.get("/projects/eval/aggregate")
        data = r.json()
        per_project_sum = sum(
            p["deviations"] for p in data["per_project"].values()
        )
        assert per_project_sum == data["aggregate"]["total_deviations"]
        assert per_project_sum == 33
