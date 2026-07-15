"""Contract tests for versioning, problem details, and platform probes."""

from __future__ import annotations

import inspect

from fastapi.testclient import TestClient

from backend.main import V1_COMPATIBILITY_ROUTE_COUNT, app
from backend.platform.config import reset_platform_settings
from backend.routers.analysis import health
from backend.routers.platform import live

client = TestClient(app)


def test_nonblocking_health_handlers_stay_off_the_worker_thread_pool() -> None:
    assert inspect.iscoroutinefunction(live)
    assert inspect.iscoroutinefunction(health)


def _operations(prefix: str) -> set[tuple[str, str]]:
    schema = app.openapi()
    return {
        (method.upper(), path)
        for path, methods in schema["paths"].items()
        if path.startswith(prefix)
        for method in methods
        if method in {"get", "post", "put", "patch", "delete"}
    }


def test_every_legacy_operation_has_v1_compatibility_route() -> None:
    excluded = ("/api/v1", "/health/", "/internal/")
    schema = app.openapi()
    legacy = {
        (method.upper(), path)
        for path, methods in schema["paths"].items()
        if not path.startswith(excluded)
        for method, operation in methods.items()
        if method in {"get", "post", "put", "patch", "delete"} and operation.get("deprecated")
    }
    v1 = _operations("/api/v1")
    expected = {(method, f"/api/v1{path}") for method, path in legacy}
    assert expected <= v1
    assert V1_COMPATIBILITY_ROUTE_COUNT == len(legacy)


def test_legacy_operations_are_marked_deprecated() -> None:
    legacy = [
        operation
        for path, methods in app.openapi()["paths"].items()
        if not path.startswith(("/api/v1", "/health/", "/internal/"))
        for method, operation in methods.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]
    assert legacy
    assert all(operation.get("deprecated") is True for operation in legacy)


def test_request_id_is_preserved_when_valid() -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "judge-run-1234"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "judge-run-1234"


def test_invalid_request_id_is_replaced() -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "bad"})
    assert response.status_code == 200
    assert len(response.headers["X-Request-ID"]) == 32


def test_v1_validation_uses_problem_details() -> None:
    response = client.post("/api/v1/analyze", json={"spec_text": "", "submittal_text": ""})
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"].endswith("/validation_failed")
    assert body["code"] == "validation_failed"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert {error["field"] for error in body["errors"]} == {"spec_text", "submittal_text"}


def test_v1_http_error_uses_problem_details() -> None:
    response = client.post("/api/v1/ingest/DOES_NOT_EXIST")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert response.json()["detail"]


def test_deterministic_demo_is_bounded_and_non_persistent(monkeypatch) -> None:
    def provider_must_not_run(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("provider access is prohibited in deterministic demo mode")

    monkeypatch.setattr("backend.llm.complete_json", provider_must_not_run)
    response = client.post(
        "/api/v1/demo/analyze",
        json={
            "spec_text": "Battery runtime shall be at least 30 min for the UPS.",
            "submittal_text": "UPS battery runtime is 10 min.",
            "system_id": "UPS",
        },
    )
    assert response.status_code == 200
    provenance = response.json()["provenance"]
    assert provenance == {
        "mode": "rule-based-deterministic",
        "provider": None,
        "durable_retention": False,
        "deterministic": True,
    }


def test_demo_rejects_oversized_fields_as_problem_details() -> None:
    response = client.post(
        "/api/v1/demo/analyze",
        json={"spec_text": "s" * 20_001, "submittal_text": "valid submission text"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_failed"


def test_managed_v1_route_requires_bearer_but_legacy_route_does_not(monkeypatch) -> None:
    monkeypatch.setenv("PRAMAAN_AUTH_BACKEND", "supabase")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    reset_platform_settings()
    payload = {"spec_text": "x" * 9, "submittal_text": "y" * 9}
    assert client.post("/api/v1/analyze", json=payload).status_code == 401
    # Compatibility behavior remains available only because this is not a
    # production configuration; existing clients are not silently broken.
    legacy = client.post("/analyze", json=payload)
    assert legacy.status_code == 422


def test_readiness_and_private_metrics(monkeypatch) -> None:
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    assert client.get("/internal/metrics").status_code == 404
    monkeypatch.setenv("PRAMAAN_METRICS_TOKEN", "metrics-secret-value")
    metrics = client.get(
        "/internal/metrics",
        headers={"Authorization": "Bearer metrics-secret-value"},
    )
    assert metrics.status_code == 200
    assert set(metrics.json()) == {"jobs", "analysis_capacity"}


def test_openapi_has_unique_operation_ids_and_bearer_security() -> None:
    schema = app.openapi()
    operations = [
        operation
        for methods in schema["paths"].values()
        for method, operation in methods.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]
    operation_ids = [operation["operationId"] for operation in operations]
    assert len(operation_ids) == len(set(operation_ids))
    assert "HTTPBearer" in schema["components"]["securitySchemes"]
    assert schema["paths"]["/api/v1/analyze"]["post"]["security"] == [{"HTTPBearer": []}]


def test_every_protected_v1_operation_declares_bearer_security() -> None:
    protected_roots = (
        "/api/v1/analyze",
        "/api/v1/jobs",
        "/api/v1/cases",
        "/api/v1/copilot",
        "/api/v1/export",
        "/api/v1/ingest",
        "/api/v1/webhooks",
    )
    schema = app.openapi()
    protected_operations = [
        operation
        for path, methods in schema["paths"].items()
        if path.startswith(protected_roots)
        for method, operation in methods.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]
    assert protected_operations
    assert all(operation.get("security") == [{"HTTPBearer": []}] for operation in protected_operations)


def test_bounded_demo_operation_remains_public() -> None:
    operation = app.openapi()["paths"]["/api/v1/demo/analyze"]["post"]
    assert operation.get("security") in (None, [])
