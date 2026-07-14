"use client";

import { useState } from "react";

type Stage = "idle" | "open" | "accepted" | "issued" | "resolved";

const API = process.env.NEXT_PUBLIC_API ?? "http://127.0.0.1:8000";
const STAGES: Array<{ id: Stage; label: string; note: string }> = [
  { id: "open", label: "Finding opened", note: "Evidence locked" },
  { id: "accepted", label: "Owner assigned", note: "Priya Menon · CxA" },
  { id: "issued", label: "RFI issued", note: "Formal response required" },
  { id: "resolved", label: "Finding closed", note: "Response and audit retained" },
];

function stageIndex(stage: Stage) {
  return STAGES.findIndex((item) => item.id === stage);
}

async function requestJson(path: string, init: RequestInit = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 20_000);
  try {
    const response = await fetch(`${API}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { "Content-Type": "application/json", ...init.headers },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(body.detail || `Request failed (${response.status})`);
    }
    return body;
  } finally {
    window.clearTimeout(timeout);
  }
}

export default function ResolutionWorkflow() {
  const [stage, setStage] = useState<Stage>("idle");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [caseId, setCaseId] = useState("");
  const [secret, setSecret] = useState("");
  const [findingId, setFindingId] = useState("");
  const [rfiId, setRfiId] = useState("");
  const [auditCount, setAuditCount] = useState(0);

  async function advance() {
    setBusy(true);
    setError("");
    try {
      if (stage === "idle") {
        const created = await requestJson("/cases", {
          method: "POST",
          body: JSON.stringify({ name: "Homepage resolution proof" }),
        });
        const headers = { "X-Case-Secret": created.secret };
        const finding = await requestJson(`/cases/${created.case_id}/findings`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            component: "UPS-02",
            parameter: "battery_runtime_min",
            required_value: "10",
            provided_value: "7",
            unit: "min",
            severity: "Critical",
            standard_ref: "UPTIME-TIER4",
            spec_clause: "DB-4.3",
            predicted_cx_test: "IST-07",
            lead_time_weeks: 27,
            rationale: "Battery autonomy is below the project requirement.",
          }),
        });
        setCaseId(created.case_id);
        setSecret(created.secret);
        setFindingId(finding.finding_id);
        setStage("open");
      } else if (stage === "open") {
        await requestJson(`/cases/${caseId}/findings/${findingId}`, {
          method: "PATCH",
          headers: { "X-Case-Secret": secret },
          body: JSON.stringify({ status: "accepted", owner: "Priya Menon" }),
        });
        setStage("accepted");
      } else if (stage === "accepted") {
        const drafted = await requestJson(
          `/cases/${caseId}/findings/${findingId}/rfi`,
          {
            method: "POST",
            headers: { "X-Case-Secret": secret },
          },
        );
        await requestJson(`/cases/${caseId}/rfis/${drafted.rfi_id}`, {
          method: "PATCH",
          headers: { "X-Case-Secret": secret },
          body: JSON.stringify({ status: "issued" }),
        });
        setRfiId(drafted.rfi_id);
        setStage("issued");
      } else if (stage === "issued") {
        const headers = { "X-Case-Secret": secret };
        await requestJson(`/cases/${caseId}/rfis/${rfiId}`, {
          method: "PATCH",
          headers,
          body: JSON.stringify({
            status: "answered",
            response_text: "Vendor confirms a compliant 10-minute battery string in revision C.",
          }),
        });
        await requestJson(`/cases/${caseId}/rfis/${rfiId}`, {
          method: "PATCH",
          headers,
          body: JSON.stringify({ status: "closed" }),
        });
        await requestJson(`/cases/${caseId}/findings/${findingId}`, {
          method: "PATCH",
          headers,
          body: JSON.stringify({
            status: "resolved",
            resolution_note: "Revision C restores the required 10-minute autonomy.",
          }),
        });
        const audit = await requestJson(`/cases/${caseId}/audit-log`, { headers });
        setAuditCount(audit.audit_log.length);
        setStage("resolved");
      }
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "The workflow could not continue.";
      setError(
        message.includes("aborted")
          ? "The API did not respond within 20 seconds. No completed step was presented as successful."
          : message,
      );
    } finally {
      setBusy(false);
    }
  }

  const activeIndex = stageIndex(stage);
  const labels: Record<Stage, string> = {
    idle: "Open a protected case",
    open: "Assign and accept",
    accepted: "Draft and issue RFI",
    issued: "Record response and close",
    resolved: "Resolution complete",
  };

  return (
    <div className="resolution-console">
      <div className="resolution-head">
        <div>
          <p className="section-kicker">Interactive API proof</p>
          <h3>A real case, not a staged animation.</h3>
        </div>
        <span className={`workflow-state workflow-state-${stage}`}>
          {stage === "idle" ? "Ready" : stage}
        </span>
      </div>

      <ol className="workflow-steps" aria-label="Finding resolution progress">
        {STAGES.map((item, index) => {
          const complete = activeIndex >= index;
          const current = activeIndex === index;
          return (
            <li className={complete ? "is-complete" : ""} aria-current={current ? "step" : undefined} key={item.id}>
              <span className="workflow-index" aria-hidden="true">
                {complete ? "✓" : index + 1}
              </span>
              <span>
                <strong>{item.label}</strong>
                <small>{item.note}</small>
              </span>
            </li>
          );
        })}
      </ol>

      {stage === "resolved" ? (
        <div className="resolution-success" role="status">
          <strong>Closed with evidence.</strong>
          <span>{auditCount} immutable audit events recorded for this case.</span>
        </div>
      ) : (
        <button className="button button-primary workflow-action" type="button" onClick={advance} disabled={busy}>
          {busy ? <span className="button-loader" aria-hidden="true" /> : null}
          {busy ? "Working…" : labels[stage]}
        </button>
      )}

      {error ? (
        <div className="inline-error" role="alert">
          <strong>Workflow paused.</strong> {error}
          <button type="button" onClick={advance}>Retry this step</button>
        </div>
      ) : null}
      <p className="resolution-footnote">
        Case credentials stay in this browser tab. The API stores only a one-way hash and scopes every read and write to the case.
      </p>
    </div>
  );
}
