from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from backend import case_store, security
from backend.agents.rfi_copilot import draft_rfi
from backend.api_context import _esc
from backend.routers.webhooks import SUBSCRIBED_WEBHOOKS, trigger_webhooks

router = APIRouter()
log = logging.getLogger("pramaan.api")

# ── Cases: persisted, tenant-isolated submittal -> RFI workflow ──────
#
# Everything above this point is either in-memory (jobs.py's result cache)
# or static/read-only (the /projects/{project_id}/* demo fixtures). This is
# the one workflow the project chose to deepen with real persistence instead
# of adding more surface area — see backend/case_store.py's module docstring
# for the honest scope (SQLite, single-instance, tenant-isolated by a
# per-case bearer secret, not real user accounts).

class CreateCaseRequest(BaseModel):
    name: str = Field(default="", max_length=200)


class AddFindingRequest(BaseModel):
    component: str = Field(default="", max_length=200)
    parameter: str = Field(default="", max_length=200)
    required_value: str = Field(default="", max_length=500)
    provided_value: str = Field(default="", max_length=500)
    unit: str = Field(default="", max_length=50)
    severity: str = Field(default="", max_length=50)
    standard_ref: str = Field(default="", max_length=200)
    spec_clause: str = Field(default="", max_length=200)
    predicted_cx_test: str = Field(default="", max_length=200)
    lead_time_weeks: float | None = None
    rationale: str = Field(default="", max_length=2000)


class UpdateFindingRequest(BaseModel):
    status: str | None = Field(default=None, max_length=30)
    owner: str | None = Field(default=None, max_length=120)
    resolution_note: str | None = Field(default=None, max_length=2000)


class UpdateRfiRequest(BaseModel):
    status: str = Field(max_length=30)
    response_text: str | None = Field(default=None, max_length=4000)


_FINDING_TRANSITIONS = {
    "open": {"accepted", "rfi_drafted", "dismissed"},
    "accepted": {"open", "rfi_drafted", "resolved", "dismissed"},
    "rfi_drafted": {"accepted", "resolved"},
    "resolved": {"open"},
    "dismissed": {"open"},
}
_RFI_TRANSITIONS = {
    "draft": {"issued"},
    "issued": {"answered"},
    "answered": {"closed"},
    "closed": set(),
}
_FINDING_OWNER_REQUIRED = {"accepted", "rfi_drafted", "resolved"}
_FINDING_NOTE_REQUIRED = {"resolved", "dismissed"}


def _require_finding_update(req: UpdateFindingRequest) -> None:
    if not any(value is not None for value in (req.status, req.owner, req.resolution_note)):
        raise HTTPException(status_code=422, detail="Provide a workflow field to update.")


def _validate_finding_transition(current_status: str, next_status: str) -> None:
    if next_status not in _FINDING_TRANSITIONS:
        raise HTTPException(status_code=422, detail="Unknown finding status.")
    if next_status != current_status and next_status not in _FINDING_TRANSITIONS[current_status]:
        raise HTTPException(
            status_code=409,
            detail=f"Finding cannot move from {current_status} to {next_status}.",
        )


def _validate_finding_evidence(status: str, owner: str, note: str) -> None:
    if status in _FINDING_OWNER_REQUIRED and not owner:
        raise HTTPException(status_code=422, detail="Assign an owner before accepting or progressing a finding.")
    if status in _FINDING_NOTE_REQUIRED and not note:
        raise HTTPException(status_code=422, detail="Record resolution evidence before closing a finding.")


def _finding_update_values(finding: dict, req: UpdateFindingRequest) -> tuple[str, str, str]:
    _require_finding_update(req)
    current_status = finding["status"]
    next_status = req.status or current_status
    _validate_finding_transition(current_status, next_status)
    next_owner = (req.owner if req.owner is not None else finding["owner"] or "").strip()
    next_note = (req.resolution_note if req.resolution_note is not None else finding["resolution_note"] or "").strip()
    _validate_finding_evidence(next_status, next_owner, next_note)
    return next_status, next_owner, next_note


def _require_answered_rfi(case_id: str, finding_id: str, current_status: str, next_status: str) -> None:
    if next_status != "resolved" or current_status != "rfi_drafted":
        return
    related = [rfi for rfi in case_store.list_rfis(case_id) if rfi["finding_id"] == finding_id]
    if not related or related[-1]["status"] not in {"answered", "closed"}:
        raise HTTPException(status_code=409, detail="Record the RFI response before resolving this finding.")


def _finding_changes(finding: dict, status: str, owner: str, note: str) -> list[str]:
    changes = []
    if status != finding["status"]:
        changes.append(f"status={finding['status']}->{status}")
    if owner != finding["owner"]:
        changes.append(f"owner={owner or 'unassigned'}")
    if note != finding["resolution_note"]:
        changes.append("resolution_evidence=updated")
    return changes


def _require_case(case_id: str, request: Request) -> str:
    """Tenant-isolation gate for every /cases/{case_id}/* route. A wrong or
    missing X-Case-Secret returns 404, identical to a nonexistent case_id —
    this deliberately does not distinguish "case doesn't exist" from "wrong
    secret" so a caller can't probe for valid case IDs. Returns the presented
    secret (needed by the caller to compute the audit actor_key)."""
    secret = request.headers.get("x-case-secret", "")
    if not case_store.verify_case(case_id, secret):
        raise HTTPException(status_code=404, detail="No such case.")
    return secret


@router.post("/cases", dependencies=[Depends(security.rl_case_create)])
def create_case(req: CreateCaseRequest):
    """Create a new case. The returned `secret` is shown exactly once — it
    is the only credential for every /cases/{case_id}/* route on this case
    and cannot be recovered if lost, the same way a demo token can't be."""
    case_id, secret = case_store.create_case(req.name)
    return {"case_id": case_id, "secret": secret,
            "warning": "This secret is shown once and cannot be recovered. "
                       "Store it now — it is required for every request "
                       "against this case."}


@router.get("/cases/{case_id}")
def get_case(case_id: str, request: Request):
    _require_case(case_id, request)
    summary = case_store.case_summary(case_id)
    return {
        **summary,
        "findings_count": len(case_store.list_findings(case_id)),
        "rfis_count": len(case_store.list_rfis(case_id)),
    }


@router.post("/cases/{case_id}/findings")
def add_case_finding(case_id: str, req: AddFindingRequest, request: Request):
    secret = _require_case(case_id, request)
    finding = req.model_dump()
    finding_id = case_store.add_finding(case_id, finding)
    case_store.append_audit(case_id, case_store.actor_key_for(secret),
                            "finding_added", detail=f"{req.component}.{req.parameter}")
    trigger_webhooks(
        [finding],
        (req.component.split("-", 1)[0] or "CUSTOM"),
        case_id=case_id,
    )
    return {"finding_id": finding_id}


@router.get("/cases/{case_id}/findings")
def list_case_findings(case_id: str, request: Request):
    _require_case(case_id, request)
    return {"findings": case_store.list_findings(case_id)}


@router.patch("/cases/{case_id}/findings/{finding_id}")
def update_case_finding(case_id: str, finding_id: str,
                        req: UpdateFindingRequest, request: Request):
    secret = _require_case(case_id, request)
    finding = case_store.get_finding(case_id, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="No such finding on this case.")
    current_status = finding["status"]
    next_status, next_owner, next_note = _finding_update_values(finding, req)
    _require_answered_rfi(case_id, finding_id, current_status, next_status)

    updated = case_store.update_finding(
        case_id,
        finding_id,
        status=next_status,
        owner=next_owner,
        resolution_note=next_note,
    )
    changes = _finding_changes(finding, next_status, next_owner, next_note)
    case_store.append_audit(
        case_id,
        case_store.actor_key_for(secret),
        "finding_workflow_updated",
        detail=f"finding={finding_id} {' '.join(changes)}",
    )
    return {"finding": updated}


@router.post("/cases/{case_id}/findings/{finding_id}/rfi", dependencies=[Depends(security.rl_analysis)])
def draft_case_rfi(case_id: str, finding_id: str, request: Request):
    secret = _require_case(case_id, request)
    finding = case_store.get_finding(case_id, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="No such finding on this case.")
    if finding["status"] in {"resolved", "dismissed"}:
        raise HTTPException(
            status_code=409,
            detail="Reopen the finding before drafting an RFI.",
        )
    if not finding["owner"]:
        raise HTTPException(
            status_code=422,
            detail="Assign an owner before drafting an RFI.",
        )
    active_rfi = next(
        (
            rfi
            for rfi in case_store.list_rfis(case_id)
            if rfi["finding_id"] == finding_id and rfi["status"] != "closed"
        ),
        None,
    )
    if active_rfi is not None:
        raise HTTPException(
            status_code=409,
            detail="This finding already has an active RFI.",
        )
    draft = draft_rfi(finding)
    rfi_id = case_store.add_rfi(case_id, finding_id, draft["question"],
                                draft["drafted_text"], draft["sources"], draft["mode"])
    case_store.append_audit(case_id, case_store.actor_key_for(secret),
                            "rfi_drafted", detail=f"finding={finding_id} mode={draft['mode']}")
    if finding["status"] != "rfi_drafted":
        case_store.update_finding(case_id, finding_id, status="rfi_drafted")
    return {"rfi_id": rfi_id, **draft}


@router.get("/cases/{case_id}/rfis")
def list_case_rfis(case_id: str, request: Request):
    _require_case(case_id, request)
    return {"rfis": case_store.list_rfis(case_id)}


@router.patch("/cases/{case_id}/rfis/{rfi_id}")
def update_case_rfi(case_id: str, rfi_id: str, req: UpdateRfiRequest,
                    request: Request):
    secret = _require_case(case_id, request)
    rfi = case_store.get_rfi(case_id, rfi_id)
    if rfi is None:
        raise HTTPException(status_code=404, detail="No such RFI on this case.")
    next_status = req.status.strip().lower()
    if next_status not in _RFI_TRANSITIONS:
        raise HTTPException(status_code=422, detail="Unknown RFI status.")
    current_status = rfi["status"]
    if next_status != current_status and next_status not in _RFI_TRANSITIONS[current_status]:
        raise HTTPException(
            status_code=409,
            detail=f"RFI cannot move from {current_status} to {next_status}.",
        )
    next_response = (
        req.response_text
        if req.response_text is not None
        else rfi["response_text"]
    ).strip()
    if next_status in {"answered", "closed"} and not next_response:
        raise HTTPException(
            status_code=422,
            detail="Record the formal response before answering or closing an RFI.",
        )
    updated = case_store.update_rfi(
        case_id, rfi_id, status=next_status, response_text=next_response
    )
    if next_status != current_status or next_response != rfi["response_text"]:
        case_store.append_audit(
            case_id,
            case_store.actor_key_for(secret),
            "rfi_workflow_updated",
            detail=f"rfi={rfi_id} status={current_status}->{next_status}",
        )
    return {"rfi": updated}


@router.get("/cases/{case_id}/rfis/{rfi_id}/export", response_class=HTMLResponse)
def export_case_rfi(case_id: str, rfi_id: str, request: Request):
    secret = _require_case(case_id, request)
    rfi = case_store.get_rfi(case_id, rfi_id)
    if rfi is None:
        raise HTTPException(status_code=404, detail="No such RFI on this case.")
    finding = case_store.get_finding(case_id, rfi["finding_id"]) or {}
    case = case_store.case_summary(case_id) or {}
    case_store.append_audit(case_id, case_store.actor_key_for(secret),
                            "rfi_exported", detail=rfi_id)
    sources_html = "".join(f"<li>{_esc(s)}</li>" for s in rfi.get("sources", []))
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>RFI Export — {_esc(case.get('name') or case_id)}</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 0; background: #fafbfc; color: #1a1a2e; }}
.header {{ background: #0c0f13; color: #e7ecf3; padding: 32px 40px; }}
.header h1 {{ font-size: 22px; margin: 0 0 6px; }}
.header p {{ color: #7a8899; font-size: 13px; margin: 0; }}
.content {{ max-width: 800px; margin: 0 auto; padding: 32px 40px; }}
.finding {{ background: #f0f2f5; border-radius: 8px; padding: 16px 20px; margin-bottom: 24px; font-size: 13px; }}
.drafted {{ white-space: pre-wrap; line-height: 1.6; font-size: 14px; }}
h2 {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.04em; color: #555; }}
</style></head>
<body>
<div class="header">
  <h1>RFI Export</h1>
  <p>Case: {_esc(case.get('name') or case_id)} · RFI {_esc(rfi_id)} · Mode: {_esc(rfi.get('mode', ''))}</p>
</div>
<div class="content">
  <h2>Finding</h2>
  <div class="finding">
    <b>{_esc(finding.get('component', ''))}</b> — {_esc(finding.get('parameter', '').replace('_', ' '))}<br>
    Required: {_esc(finding.get('required_value', ''))} {_esc(finding.get('unit', ''))} ·
    Submitted: {_esc(finding.get('provided_value', ''))} {_esc(finding.get('unit', ''))} ·
    Severity: {_esc(finding.get('severity', ''))}<br>
    Standard: {_esc(finding.get('standard_ref', ''))} {_esc(finding.get('spec_clause', ''))}
  </div>
  <h2>Drafted RFI</h2>
  <div class="drafted">{_esc(rfi.get('drafted_text', ''))}</div>
  <h2>Cited Sources</h2>
  <ul>{sources_html or '<li>none</li>'}</ul>
</div>
</body></html>"""


@router.get("/cases/{case_id}/export/itp.pdf")
def export_case_itp_pdf(case_id: str, request: Request):
    """A physically-signable Inspection & Test Plan, distinct from the
    JSON/HTML exports — a commissioning authority can print and hand this
    off rather than work from a screen. Built from the case's own findings
    against the same commissioning-test catalog `backend/agents/commissioning.py`
    uses; adds no new AI reasoning, just a different export format."""
    secret = _require_case(case_id, request)
    case = case_store.case_summary(case_id) or {}
    findings = case_store.list_findings(case_id)
    from backend.agents.itp_export import build_itp_pdf
    pdf_bytes = build_itp_pdf(case, findings)
    case_store.append_audit(case_id, case_store.actor_key_for(secret),
                            "itp_pdf_exported", detail=f"{len(findings)} findings")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="itp_{case_id[:8]}.pdf"'},
    )


@router.get("/cases/{case_id}/audit-log")
def get_case_audit_log(case_id: str, request: Request):
    _require_case(case_id, request)
    return {"audit_log": case_store.get_audit_log(case_id)}


@router.delete("/cases/{case_id}", status_code=200)
def delete_case_endpoint(case_id: str, request: Request):
    """Permanently delete a case and all its findings, RFIs, and audit log.

    Requires the X-Case-Secret header. Returns 404 for wrong/missing secret
    (indistinguishable from a nonexistent case).
    """
    _require_case(case_id, request)
    SUBSCRIBED_WEBHOOKS.pop(case_id, None)
    case_store.delete_case(case_id)
    return {"deleted": True, "case_id": case_id}
