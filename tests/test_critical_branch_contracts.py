"""Branch contracts for security, idempotency, provenance, and webhook safety.

These tests intentionally exercise failure and bounded-resource paths that are
easy for happy-path integration tests to miss and dangerous for mutations to
silently weaken.
"""

from __future__ import annotations

import hashlib
import runpy
import threading

import pytest
from fastapi import Request

from backend import jobs, security
from backend.agents import reconciliation
from backend.platform.webhook_delivery import WebhookRetryPolicy, WebhookSigner


def _request(
    *, headers: dict[str, str] | None = None, client: tuple[str, int] | None = ("203.0.113.8", 443)
) -> Request:
    encoded_headers = [
        (name.lower().encode("latin-1"), value.encode("latin-1"))
        for name, value in (headers or {}).items()
    ]
    return Request({"type": "http", "headers": encoded_headers, "client": client})


def test_security_invalid_integer_config_fails_to_safe_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAMAAN_ANALYSIS_LIMIT_PER_HOUR", "not-an-integer")
    assert security.analysis_limit() == 20


def test_security_defaults_and_status_contract_are_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend import llm
    from backend.agents import ocr_util

    monkeypatch.delenv("PRAMAAN_CASE_CREATE_LIMIT_PER_HOUR", raising=False)
    monkeypatch.delenv("PRAMAAN_METRICS_TOKEN", raising=False)
    assert security.case_create_limit() == 10
    assert security.metrics_token() == ""

    monkeypatch.setenv("PRAMAAN_REDIS_URL", "redis://cache")
    monkeypatch.setenv("PRAMAAN_CORS_ORIGINS", "https://app.example")
    monkeypatch.setattr(security, "auth_required", lambda: True)
    monkeypatch.setattr(security, "rate_limit_enabled", lambda: True)
    monkeypatch.setattr(security, "analysis_limit", lambda: 21)
    monkeypatch.setattr(security, "upload_limit", lambda: 9)
    monkeypatch.setattr(security, "deep_probe_limit", lambda: 4)
    monkeypatch.setattr(security, "case_create_limit", lambda: 3)
    monkeypatch.setattr(security, "max_upload_mb", lambda: 18)
    monkeypatch.setattr(ocr_util, "max_pdf_pages", lambda: 77)
    monkeypatch.setattr(ocr_util, "max_image_pixels", lambda: 88_000_000)
    monkeypatch.setattr(ocr_util, "tesseract_available_cached", lambda: True)
    monkeypatch.setattr(ocr_util, "ocr_enabled", lambda: True)
    monkeypatch.setattr(llm, "provider_chain", lambda: ["primary", "secondary"])

    assert security.security_status() == {
        "auth_required": True,
        "rate_limit_enabled": True,
        "rate_limit_backend": "redis",
        "rate_limits_per_hour": {
            "analysis": 21,
            "upload": 9,
            "deep_probe": 4,
            "case_create": 3,
        },
        "max_upload_mb": 18,
        "max_pdf_pages": 77,
        "max_image_pixels": 88_000_000,
        "cors_locked": True,
        "ocr_available": True,
        "llm_providers_configured": 2,
        "llm_failover_available": True,
        "deterministic_fallback_available": True,
    }


def test_security_client_key_hashes_tokens_and_honors_trusted_first_hop(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "never-store-this-token"
    monkeypatch.setenv("PRAMAAN_TRUST_PROXY_HEADERS", "true")
    request = _request(
        headers={
            "authorization": f"Bearer {token}",
            "x-forwarded-for": "198.51.100.4, 10.0.0.2",
        }
    )

    key = security._client_key(request)

    assert key == f"198.51.100.4|{hashlib.sha256(token.encode()).hexdigest()[:12]}"
    assert token not in key


def test_deep_probe_dependency_uses_its_own_bucket_and_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Request, str, int]] = []
    request = _request()
    monkeypatch.setattr(security, "deep_probe_limit", lambda: 7)
    monkeypatch.setattr(security, "enforce_rate_limit", lambda *args: calls.append(args))

    security.rl_deep_probe(request)

    assert calls == [(request, "deep_probe", 7)]


def test_job_numeric_config_uses_safe_defaults_for_invalid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_JOB_INTEGER", "invalid")
    monkeypatch.setenv("TEST_JOB_FLOAT", "invalid")
    assert jobs._int_env("TEST_JOB_INTEGER", 11) == 11
    assert jobs._float_env("TEST_JOB_FLOAT", 2.5) == 2.5

    monkeypatch.setenv("TEST_JOB_INTEGER", "17")
    monkeypatch.setenv("TEST_JOB_FLOAT", "3.25")
    assert jobs._int_env("TEST_JOB_INTEGER", 11) == 17
    assert jobs._float_env("TEST_JOB_FLOAT", 2.5) == 3.25

    monkeypatch.delenv("TEST_JOB_INTEGER")
    monkeypatch.delenv("TEST_JOB_FLOAT")
    assert jobs._int_env("TEST_JOB_INTEGER", 11) == 11
    assert jobs._float_env("TEST_JOB_FLOAT", 2.5) == 2.5


def test_job_stats_report_exact_live_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jobs, "_CACHE_MAX", 7)
    monkeypatch.setattr(jobs, "_MAX_WORKERS", 3)
    monkeypatch.setattr(jobs, "pipeline_signature", lambda: "pipeline-signature")
    with jobs._cache_lock:
        jobs._cache["one"] = {"value": 1}
    with jobs._jobs_lock:
        jobs._jobs["job"] = {"status": "queued"}

    assert jobs.stats() == {
        "cache_entries": 1,
        "cache_max": 7,
        "jobs_tracked": 1,
        "job_workers": 3,
        "pipeline_signature": "pipeline-signature",
    }


def test_cache_and_job_registries_evict_oldest_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jobs, "_CACHE_MAX", 1)
    jobs._cache_put("old", {"value": 1})
    jobs._cache_put("new", {"value": 2})
    assert list(jobs._cache) == ["new"]

    monkeypatch.setattr(jobs, "_JOB_MAX", 1)
    monkeypatch.setattr(jobs._pool, "submit", lambda *_args, **_kwargs: None)
    first = jobs.submit_job("spec-1", "sub-1", "UPS", "request-1")
    second = jobs.submit_job("spec-2", "sub-2", "UPS", "request-2")
    assert first["job_id"] not in jobs._jobs
    assert list(jobs._jobs) == [second["job_id"]]


def test_hash_lock_registry_prunes_only_idle_locks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jobs, "_CACHE_MAX", 1)
    busy = threading.Lock()
    busy.acquire()
    jobs._hash_locks.update(
        {
            "busy": busy,
            "idle-one": threading.Lock(),
            "idle-two": threading.Lock(),
        }
    )
    try:
        created = jobs._lock_for("new")
    finally:
        busy.release()

    assert jobs._hash_locks["busy"] is busy
    assert jobs._hash_locks["new"] is created
    assert "idle-one" not in jobs._hash_locks
    assert "idle-two" not in jobs._hash_locks


def _queued_job(job_id: str) -> dict[str, object]:
    return {
        "job_id": job_id,
        "request_id": "request-id",
        "input_hash": "hash",
        "status": "queued",
        "submitted_at": 1.0,
        "started_at": None,
        "finished_at": None,
        "latency_ms": None,
        "mode": None,
        "count": None,
        "cached": None,
        "error": None,
        "_result": None,
    }


def test_worker_ignores_jobs_evicted_before_or_during_processing(monkeypatch: pytest.MonkeyPatch) -> None:
    missing_id = "a" * 32
    jobs._run_job(missing_id, "spec", "sub", "UPS")

    evicted_id = "b" * 32
    jobs._jobs[evicted_id] = _queued_job(evicted_id)

    def evict_during_analysis(*_args: object) -> dict[str, object]:
        with jobs._jobs_lock:
            jobs._jobs.pop(evicted_id)
        return {"mode": "rule", "count": 0, "cached": False}

    monkeypatch.setattr(jobs, "analyze_cached", evict_during_analysis)
    jobs._run_job(evicted_id, "spec", "sub", "UPS")
    assert evicted_id not in jobs._jobs


def test_worker_records_generic_failure_without_leaking_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    job_id = "c" * 32
    jobs._jobs[job_id] = _queued_job(job_id)
    monkeypatch.setattr(jobs, "analyze_cached", lambda *_args: (_ for _ in ()).throw(RuntimeError("secret detail")))

    jobs._run_job(job_id, "spec", "sub", "UPS")

    assert jobs._jobs[job_id]["status"] == "error"
    assert jobs._jobs[job_id]["finished_at"] is not None
    assert jobs._jobs[job_id]["error"] == "analysis failed"
    assert "secret" not in jobs._jobs[job_id]["error"]


def test_worker_tolerates_eviction_while_handling_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    job_id = "d" * 32
    jobs._jobs[job_id] = _queued_job(job_id)

    def evict_then_fail(*_args: object) -> None:
        with jobs._jobs_lock:
            jobs._jobs.pop(job_id)
        raise RuntimeError("provider failed")

    monkeypatch.setattr(jobs, "analyze_cached", evict_then_fail)
    jobs._run_job(job_id, "spec", "sub", "UPS")
    assert job_id not in jobs._jobs


def test_reconciliation_feedback_and_cx_enrichment_are_preserved(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "specs").mkdir()
    (tmp_path / "submittals").mkdir()
    (tmp_path / "specs" / "UPS.md").write_text("owner requirement", encoding="utf-8")
    (tmp_path / "submittals" / "UPS.md").write_text("vendor offer", encoding="utf-8")
    calls: list[tuple[str, dict[str, object]]] = []
    finding = {"component": "UPS-1", "parameter": "runtime"}
    monkeypatch.setattr(
        reconciliation,
        "complete_json",
        lambda prompt, **kwargs: calls.append((prompt, kwargs)) or [],
    )
    monkeypatch.setattr(reconciliation, "_validate_deviations", lambda _raw: [finding.copy()])
    monkeypatch.setattr(reconciliation, "_check_citation_faithfulness", lambda devs, *_args: devs)
    predicted: list[dict[str, object]] = []
    monkeypatch.setattr(
        reconciliation,
        "predict_cx_impact",
        lambda received: predicted.append(received.copy()) or {"cx_stage": "L4"},
    )

    result = reconciliation.reconcile_system_at(
        tmp_path,
        "UPS",
        "governing standard",
        with_cx=True,
        feedback="Correct the unsupported citation",
    )

    expected_prompt = reconciliation.PROMPT_TEMPLATE.format(
        spec="owner requirement",
        submittal="vendor offer",
        standards="governing standard",
    ) + (
        "\n\n=== SELF-REVIEW FEEDBACK (revise your previous answer) ===\n"
        "Correct the unsupported citation"
        "\nReturn the corrected JSON array of deviations.\n"
    )
    assert calls == [(expected_prompt, {"system": reconciliation.SYSTEM_PROMPT})]
    assert predicted == [{"component": "UPS-1", "parameter": "runtime", "system": "UPS"}]
    assert result == [{"component": "UPS-1", "parameter": "runtime", "system": "UPS", "cx_stage": "L4"}]


def test_reconciliation_defaults_missing_inputs_and_wrapper_contract(
    tmp_path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    (tmp_path / "specs").mkdir()
    (tmp_path / "submittals").mkdir()
    (tmp_path / "specs" / "UPS.md").write_text("owner requirement", encoding="utf-8")

    with caplog.at_level("WARNING", logger=reconciliation.log.name):
        assert reconciliation.reconcile_system_at(tmp_path, "UPS", "standard") == []
    assert caplog.messages == ["Missing spec or submittal for UPS"]

    (tmp_path / "submittals" / "UPS.md").write_text("vendor offer", encoding="utf-8")
    finding = {"component": "UPS-1", "parameter": "runtime"}
    monkeypatch.setattr(reconciliation, "complete_json", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(reconciliation, "_validate_deviations", lambda _raw: [finding.copy()])
    monkeypatch.setattr(reconciliation, "_check_citation_faithfulness", lambda devs, *_args: devs)
    monkeypatch.setattr(
        reconciliation,
        "predict_cx_impact",
        lambda _finding: pytest.fail("default with_cx=False must not predict commissioning impact"),
    )
    assert reconciliation.reconcile_system_at(tmp_path, "UPS", "standard") == [
        {"component": "UPS-1", "parameter": "runtime", "system": "UPS"}
    ]

    wrapper_calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        reconciliation,
        "reconcile_system_at",
        lambda *args, **kwargs: wrapper_calls.append((*args, kwargs)) or ["result"],
    )
    assert reconciliation.reconcile_system("UPS", "standard", feedback="review") == ["result"]
    assert wrapper_calls == [
        (reconciliation.CORPUS, "UPS", "standard", {"with_cx": True, "feedback": "review"})
    ]


def test_reconciliation_word_grounding_requires_every_word() -> None:
    assert reconciliation._words_are_grounded(["battery", "runtime"], "battery runtime requirement") is True
    assert reconciliation._words_are_grounded(["battery", "missing"], "battery runtime requirement") is False
    assert reconciliation._words_are_grounded([], "battery runtime requirement") is False


def test_reconciliation_corpus_walk_and_reader_are_deterministic(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "standards").mkdir()
    (tmp_path / "specs").mkdir()
    (tmp_path / "standards" / "standard.md").write_text("standard", encoding="utf-8")
    for system_id in ("B", "A"):
        (tmp_path / "specs" / f"{system_id}.md").write_text(system_id, encoding="utf-8")
    monkeypatch.setattr(reconciliation, "CORPUS", tmp_path)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        reconciliation,
        "reconcile_system",
        lambda system_id, standards: calls.append((system_id, standards)) or [{"system": system_id}],
    )

    assert reconciliation._read("standards/standard.md") == "standard"
    assert reconciliation.run_reconciliation_over_corpus() == [{"system": "A"}, {"system": "B"}]
    assert calls == [("A", "standard"), ("B", "standard")]


def test_reconciliation_cli_entrypoint_is_executable(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr("backend.llm.complete_json", lambda *_args, **_kwargs: [])
    runpy.run_path(reconciliation.__file__, run_name="__main__")
    assert capsys.readouterr().out.strip() == "[]"


@pytest.mark.parametrize(
    "active, previous",
    [
        ("short", ()),
        ("a" * 32, ("also-short",)),
    ],
)
def test_webhook_signer_rejects_every_short_rotation_secret(active: str, previous: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="at least 32"):
        WebhookSigner(active, previous)


@pytest.mark.parametrize(
    "policy",
    [
        {"max_attempts": 0},
        {"initial_delay_seconds": 0},
        {"maximum_delay_seconds": 0},
    ],
)
def test_webhook_retry_policy_rejects_non_positive_bounds(policy: dict[str, int]) -> None:
    with pytest.raises(ValueError, match="positive"):
        WebhookRetryPolicy(**policy)
