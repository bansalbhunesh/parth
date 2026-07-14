"""Direct workflow validation tests that do not depend on SQLite timing or platform tools."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend.routers import cases


def _assert_http_error(status: int, operation) -> None:  # noqa: ANN001
    with pytest.raises(HTTPException) as caught:
        operation()
    assert caught.value.status_code == status


def test_finding_update_requires_a_field_and_known_transition() -> None:
    _assert_http_error(422, lambda: cases._require_finding_update(cases.UpdateFindingRequest()))
    _assert_http_error(422, lambda: cases._validate_finding_transition("open", "invented"))
    _assert_http_error(409, lambda: cases._validate_finding_transition("open", "resolved"))


def test_finding_change_log_omits_unchanged_values() -> None:
    finding = {"status": "open", "owner": "", "resolution_note": ""}
    assert cases._finding_changes(finding, "open", "", "") == []


def test_update_and_rfi_draft_reject_missing_or_closed_findings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cases, "_require_case", lambda *_args: "case-secret")
    monkeypatch.setattr(cases.case_store, "get_finding", lambda *_args: None)
    _assert_http_error(
        404,
        lambda: cases.update_case_finding(
            "case", "finding", cases.UpdateFindingRequest(status="open"), object()
        ),
    )

    monkeypatch.setattr(
        cases.case_store,
        "get_finding",
        lambda *_args: {"status": "resolved", "owner": "Engineer"},
    )
    _assert_http_error(409, lambda: cases.draft_case_rfi("case", "finding", object()))

    monkeypatch.setattr(
        cases.case_store,
        "get_finding",
        lambda *_args: {"status": "open", "owner": ""},
    )
    _assert_http_error(422, lambda: cases.draft_case_rfi("case", "finding", object()))


def test_rfi_update_validates_existence_status_order_and_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cases, "_require_case", lambda *_args: "case-secret")
    monkeypatch.setattr(cases.case_store, "get_rfi", lambda *_args: None)
    _assert_http_error(
        404,
        lambda: cases.update_case_rfi(
            "case", "rfi", cases.UpdateRfiRequest(status="issued"), object()
        ),
    )

    monkeypatch.setattr(
        cases.case_store,
        "get_rfi",
        lambda *_args: {"status": "draft", "response_text": "", "finding_id": "finding"},
    )
    _assert_http_error(
        422,
        lambda: cases.update_case_rfi(
            "case", "rfi", cases.UpdateRfiRequest(status="invented"), object()
        ),
    )
    _assert_http_error(
        409,
        lambda: cases.update_case_rfi(
            "case", "rfi", cases.UpdateRfiRequest(status="answered", response_text="response"), object()
        ),
    )

    monkeypatch.setattr(
        cases.case_store,
        "get_rfi",
        lambda *_args: {"status": "issued", "response_text": "", "finding_id": "finding"},
    )
    _assert_http_error(
        422,
        lambda: cases.update_case_rfi(
            "case", "rfi", cases.UpdateRfiRequest(status="answered"), object()
        ),
    )


def test_existing_rfi_draft_is_not_retransitioned_and_noop_rfi_update_is_not_audited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cases, "_require_case", lambda *_args: "case-secret")
    monkeypatch.setattr(
        cases.case_store,
        "get_finding",
        lambda *_args: {"status": "rfi_drafted", "owner": "Engineer", "component": "UPS-1"},
    )
    monkeypatch.setattr(cases.case_store, "list_rfis", lambda *_args: [])
    monkeypatch.setattr(
        cases,
        "draft_rfi",
        lambda _finding: {
            "question": "Confirm rating",
            "drafted_text": "Please confirm rating",
            "sources": [],
            "mode": "rule",
        },
    )
    monkeypatch.setattr(cases.case_store, "add_rfi", lambda *_args: "rfi-id")
    monkeypatch.setattr(cases.case_store, "append_audit", lambda *_args, **_kwargs: None)
    finding_updates: list[tuple[object, ...]] = []
    monkeypatch.setattr(cases.case_store, "update_finding", lambda *args, **_kwargs: finding_updates.append(args))

    drafted = cases.draft_case_rfi("case", "finding", object())

    assert drafted["rfi_id"] == "rfi-id"
    assert finding_updates == []

    rfi = {"status": "draft", "response_text": "", "finding_id": "finding"}
    monkeypatch.setattr(cases.case_store, "get_rfi", lambda *_args: rfi)
    monkeypatch.setattr(cases.case_store, "update_rfi", lambda *_args, **_kwargs: rfi)
    audit_calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(cases.case_store, "append_audit", lambda *args, **_kwargs: audit_calls.append(args))
    assert cases.update_case_rfi(
        "case", "rfi", cases.UpdateRfiRequest(status="draft"), object()
    ) == {"rfi": rfi}
    assert audit_calls == []
