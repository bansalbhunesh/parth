"""Validation and degraded-state contracts for analysis utility routes."""

from __future__ import annotations

import json

import pytest
from fastapi import HTTPException

from backend import jobs
from backend.agents import ocr_util
from backend.routers import analysis


def test_job_result_rejects_malformed_and_unknown_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(HTTPException) as malformed:
        analysis.get_job_result("not-a-job-id")
    assert malformed.value.status_code == 404

    monkeypatch.setattr(jobs, "valid_job_id", lambda _job_id: True)
    monkeypatch.setattr(jobs, "job_result", lambda _job_id: (None, None))
    with pytest.raises(HTTPException) as unknown:
        analysis.get_job_result("a" * 32)
    assert unknown.value.status_code == 404


def test_job_result_distinguishes_pending_failure_and_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jobs, "valid_job_id", lambda _job_id: True)
    monkeypatch.setattr(jobs, "job_result", lambda _job_id: ("queued", None))
    pending = analysis.get_job_result("a" * 32)
    assert pending.status_code == 202
    assert json.loads(pending.body) == {"status": "queued", "job_id": "a" * 32}

    monkeypatch.setattr(jobs, "job_result", lambda _job_id: ("error", None))
    failed = analysis.get_job_result("b" * 32)
    assert failed.status_code == 500
    assert json.loads(failed.body)["error"] == "analysis failed"

    monkeypatch.setattr(jobs, "job_result", lambda _job_id: ("done", {"count": 2, "mode": "llm"}))
    assert analysis.get_job_result("c" * 32) == {
        "status": "done",
        "job_id": "c" * 32,
        "count": 2,
        "mode": "llm",
    }


def test_ocr_status_distinguishes_disabled_from_missing_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr_util, "is_tesseract_available", lambda: True)
    monkeypatch.setattr(ocr_util, "ocr_enabled", lambda: False)
    disabled = analysis.ocr_check()
    assert disabled["status"] == "disabled"
    assert disabled["ocr_available"] is False

    monkeypatch.setattr(ocr_util, "is_tesseract_available", lambda: False)
    monkeypatch.setattr(ocr_util, "ocr_enabled", lambda: True)
    missing = analysis.ocr_check()
    assert missing["status"] == "tesseract_not_installed"
    assert missing["ocr_available"] is False
