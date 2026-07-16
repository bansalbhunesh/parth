"use client";

import { useEffect, useMemo, useState } from "react";
import { analyzeOnce } from "../../lib/api";
import {
  addFinding,
  createCase,
  deleteCase,
  draftAndIssueRfi,
  getAuditCount,
  updateFinding,
  updateRfi,
  type CaseCredentials,
} from "../../lib/case-api";
import type { AnalyzeResult } from "./model";
import { resultIdentity } from "./model";
import {
  buildRevisedSubmittal,
  findingCleared,
  humanActionLabel,
  humanSystemLabel,
  primaryDeviation,
} from "./resolution-model";

type WorkflowStage = "idle" | "opened" | "owned" | "issued" | "resolved";

interface StoredWorkflow {
  stage: WorkflowStage;
  credentials: CaseCredentials | null;
  findingId: string;
  rfiId: string;
  owner: string;
  revisedSubmittal: string;
  auditCount: number;
  remainingFindings: number | null;
  verificationHash: string;
  verificationMode: string;
}

interface AnalyzeResolutionWorkflowProps {
  result: AnalyzeResult;
  specText: string;
  submittalText: string;
}

const EMPTY_WORKFLOW: StoredWorkflow = {
  stage: "idle",
  credentials: null,
  findingId: "",
  rfiId: "",
  owner: "Priya Menon, Commissioning Authority",
  revisedSubmittal: "",
  auditCount: 0,
  remainingFindings: null,
  verificationHash: "",
  verificationMode: "",
};

const STEPS: Array<{ stage: Exclude<WorkflowStage, "idle">; label: string; note: string }> = [
  { stage: "opened", label: "Finding persisted", note: "Evidence and provenance retained" },
  { stage: "owned", label: "Owner assigned", note: "A named decision-maker accepts it" },
  { stage: "issued", label: "RFI issued", note: "Formal vendor response required" },
  { stage: "resolved", label: "Revision verified", note: "Re-analysis and audit close the loop" },
];

function stageIndex(stage: WorkflowStage): number {
  return STEPS.findIndex((step) => step.stage === stage);
}

export default function AnalyzeResolutionWorkflow({
  result,
  specText,
  submittalText,
}: AnalyzeResolutionWorkflowProps) {
  const selected = useMemo(() => primaryDeviation(result), [result]);
  const storageKey = `pramaan-resolution:${resultIdentity(result)}`;
  const [workflow, setWorkflow] = useState<StoredWorkflow>(() => ({
    ...EMPTY_WORKFLOW,
    revisedSubmittal: buildRevisedSubmittal(submittalText, selected),
  }));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(storageKey);
      if (stored) setWorkflow(JSON.parse(stored) as StoredWorkflow);
    } catch {
      sessionStorage.removeItem(storageKey);
    }
  }, [storageKey]);

  useEffect(() => {
    if (workflow.stage === "idle") return;
    sessionStorage.setItem(storageKey, JSON.stringify(workflow));
  }, [storageKey, workflow]);

  const setPatch = (patch: Partial<StoredWorkflow>) => {
    setWorkflow((current) => ({ ...current, ...patch }));
  };

  async function advance() {
    setBusy(true);
    setError("");
    try {
      if (workflow.stage === "idle") {
        const credentials = await createCase(`Judge resolution — ${humanSystemLabel(result)}`);
        const findingId = await addFinding(credentials, {
          component: selected.component,
          parameter: selected.parameter,
          required_value: String(selected.required_value),
          provided_value: String(selected.provided_value),
          unit: selected.unit,
          severity: selected.severity,
          standard_ref: selected.standard_ref ?? "",
          spec_clause: selected.spec_clause ?? "",
          predicted_cx_test: selected.predicted_cx_test ?? "",
          lead_time_weeks: selected.lead_time_weeks ?? null,
          rationale: selected.rationale,
        });
        setPatch({ credentials, findingId, stage: "opened" });
      } else if (workflow.stage === "opened" && workflow.credentials) {
        await updateFinding(workflow.credentials, workflow.findingId, {
          status: "accepted",
          owner: workflow.owner.trim(),
        });
        setPatch({ stage: "owned" });
      } else if (workflow.stage === "owned" && workflow.credentials) {
        const rfiId = await draftAndIssueRfi(workflow.credentials, workflow.findingId);
        setPatch({ rfiId, stage: "issued" });
      } else if (workflow.stage === "issued" && workflow.credentials) {
        if (!specText.trim() || !workflow.revisedSubmittal.trim()) {
          throw new Error("Paste the full design basis and revised vendor text before verification.");
        }
        const verification = await analyzeOnce<AnalyzeResult>(
          specText,
          workflow.revisedSubmittal,
          result.system || selected.component.split("-", 1)[0] || "CUSTOM",
        );
        if (!findingCleared(verification, selected)) {
          throw new Error("The revised submittal still fails this requirement. Correct it and re-run verification.");
        }
        const response = `Revision C verified against ${selected.spec_clause || "the design basis"}; ${selected.component}/${selected.parameter} now satisfies ${selected.required_value} ${selected.unit}.`;
        await updateRfi(workflow.credentials, workflow.rfiId, {
          status: "answered",
          response_text: response,
        });
        await updateRfi(workflow.credentials, workflow.rfiId, {
          status: "closed",
          response_text: response,
        });
        await updateFinding(workflow.credentials, workflow.findingId, {
          status: "resolved",
          resolution_note: `Read-back verification cleared the finding; analysis ${verification.input_hash || "hash unavailable"}.`,
        });
        const auditCount = await getAuditCount(workflow.credentials);
        setPatch({
          stage: "resolved",
          auditCount,
          remainingFindings: verification.count,
          verificationHash: verification.input_hash ?? "",
          verificationMode: verification.mode,
        });
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The resolution workflow could not continue.");
    } finally {
      setBusy(false);
    }
  }

  async function restart() {
    setBusy(true);
    setError("");
    try {
      if (workflow.credentials) await deleteCase(workflow.credentials);
    } catch {
      // The hosted demo may have restarted and already discarded the case.
    } finally {
      sessionStorage.removeItem(storageKey);
      setWorkflow({
        ...EMPTY_WORKFLOW,
        revisedSubmittal: buildRevisedSubmittal(submittalText, selected),
      });
      setBusy(false);
    }
  }

  const activeIndex = stageIndex(workflow.stage);
  const actionLabels: Record<WorkflowStage, string> = {
    idle: "Persist the highest-priority finding",
    opened: "Assign owner and accept",
    owned: "Draft and issue the RFI",
    issued: "Re-analyze revision and close",
    resolved: "Resolution verified",
  };

  return (
    <section className="resolution-console resolution-console-inline" aria-labelledby="live-resolution-title">
      <div className="resolution-head">
        <div>
          <p className="section-kicker">Live consequence → closure</p>
          <h3 id="live-resolution-title">{humanActionLabel(result)}</h3>
          <p className="resolution-summary">
            This workflow persists the finding you just analyzed—never a separate staged example.
          </p>
        </div>
        <span className={`workflow-state workflow-state-${workflow.stage}`}>
          {workflow.stage === "idle" ? "Ready" : workflow.stage}
        </span>
      </div>

      <dl className="resolution-impact" aria-label="Selected finding consequence">
        <div><dt>Finding</dt><dd>{selected.component} · {selected.parameter.replaceAll("_", " ")}</dd></div>
        <div><dt>Commissioning gate</dt><dd>{selected.predicted_cx_test || "Needs project mapping"}</dd></div>
        <div><dt>Decision window</dt><dd>{selected.lead_time_weeks ? `${selected.lead_time_weeks} weeks` : "Not yet quantified"}</dd></div>
      </dl>

      <ol className="workflow-steps" aria-label="Live finding resolution progress">
        {STEPS.map((step, index) => {
          const complete = activeIndex >= index;
          const current = activeIndex === index;
          return (
            <li className={complete ? "is-complete" : ""} aria-current={current ? "step" : undefined} key={step.stage}>
              <span className="workflow-index" aria-hidden="true">{complete ? "✓" : index + 1}</span>
              <span><strong>{step.label}</strong><small>{step.note}</small></span>
            </li>
          );
        })}
      </ol>

      {workflow.stage === "opened" ? (
        <label className="resolution-field" htmlFor="resolution-owner">
          <span>Accountable owner</span>
          <input
            id="resolution-owner"
            aria-label="Accountable owner"
            value={workflow.owner}
            onChange={(event) => setPatch({ owner: event.target.value })}
            disabled={busy}
          />
        </label>
      ) : null}

      {workflow.stage === "issued" ? (
        <label className="resolution-field" htmlFor="resolution-revision">
          <span>Vendor revision to verify</span>
          <textarea
            id="resolution-revision"
            aria-label="Vendor revision to verify"
            rows={9}
            value={workflow.revisedSubmittal}
            onChange={(event) => setPatch({ revisedSubmittal: event.target.value })}
            disabled={busy}
          />
          <small>The demo pre-fills Revision C. Edit it freely; closure only occurs if re-analysis clears this finding.</small>
        </label>
      ) : null}

      {workflow.stage === "resolved" ? (
        <div className="resolution-success" role="status">
          <strong>Closed with read-back evidence.</strong>
          <span>{workflow.auditCount} audit events · {workflow.remainingFindings} other finding(s) remain in the revised document.</span>
          <small>Verification {workflow.verificationMode} · {workflow.verificationHash.slice(0, 12) || "hash unavailable"}</small>
        </div>
      ) : (
        <button
          className="button button-primary workflow-action"
          type="button"
          onClick={advance}
          disabled={busy || (workflow.stage === "opened" && !workflow.owner.trim())}
        >
          {busy ? <span className="button-loader" aria-hidden="true" /> : null}
          {busy ? "Working…" : actionLabels[workflow.stage]}
        </button>
      )}

      {error ? <div className="inline-error" role="alert"><strong>Workflow paused.</strong> {error}</div> : null}

      {workflow.stage !== "idle" ? (
        <button className="resolution-reset" type="button" onClick={restart} disabled={busy}>
          Delete this demo case and restart
        </button>
      ) : null}
      <p className="resolution-footnote">
        The case secret is kept only in this browser tab so the flow can resume after a refresh. The server stores a one-way hash; hosted demo records remain single-instance prototype data.
      </p>
    </section>
  );
}
