"use client";

import { useState } from "react";

const STEPS_BEFORE = [
  { phase: "Document collection", duration: "2–3 weeks", pain: "Manual gathering from 15+ vendors, revision tracking in spreadsheets" },
  { phase: "Requirement extraction", duration: "3–4 weeks", pain: "Senior engineer reads every spec, highlights values in PDFs" },
  { phase: "Cross-reference check", duration: "4–6 weeks", pain: "Compare each value against standards — 200+ clauses, one at a time" },
  { phase: "Deviation logging", duration: "1–2 weeks", pain: "Fill register manually, assign severity by experience" },
  { phase: "Commissioning discovery", duration: "Week 38–44", pain: "Deviations surface during IST — rework, delays, cost overruns" },
];

const STEPS_AFTER = [
  { phase: "Document upload", duration: "3 minutes", pain: "Drag & drop specs, submittals, and standards" },
  { phase: "AI extraction", duration: "< 1 minute", pain: "Deterministic ingest + extraction stages parse all documents simultaneously" },
  { phase: "Cross-reference", duration: "< 1 minute", pain: "The LLM reasoning core checks every requirement × every submittal × 7 standards" },
  { phase: "Register + Cx prediction", duration: "Instant", pain: "Full register with severity, lead time, and predicted Cx test failure" },
  { phase: "Week 11 detection", duration: "Same day", pain: "Caught at upload — 27–33 weeks before commissioning would surface them (scenario)" },
];

export default function BeforeAfter() {
  const [view, setView] = useState<"before" | "after">("after");

  return (
    <div className="ba">
      <div className="ba-toggle">
        <button
          className={`ba-toggle-btn ${view === "before" ? "ba-toggle-active ba-toggle-before" : ""}`}
          onClick={() => setView("before")}
        >
          Traditional process
        </button>
        <button
          className={`ba-toggle-btn ${view === "after" ? "ba-toggle-active ba-toggle-after" : ""}`}
          onClick={() => setView("after")}
        >
          With Pramaan
        </button>
      </div>

      <div className="ba-comparison">
        <div className={`ba-side ${view === "before" ? "ba-side-active" : ""}`}>
          <div className="ba-side-header ba-side-before-header">
            <div className="ba-side-title">Manual review</div>
            <div className="ba-side-duration">10–15 weeks elapsed</div>
          </div>
          {STEPS_BEFORE.map((s, i) => (
            <div key={i} className="ba-step ba-step-before">
              <div className="ba-step-num">{i + 1}</div>
              <div className="ba-step-content">
                <div className="ba-step-phase">{s.phase}</div>
                <div className="ba-step-duration">{s.duration}</div>
                <div className="ba-step-pain">{s.pain}</div>
              </div>
            </div>
          ))}
          <div className="ba-outcome ba-outcome-bad">
            <div className="ba-outcome-icon">✗</div>
            <div>
              <div className="ba-outcome-title">Deviations found at Week 38–44</div>
              <div className="ba-outcome-detail">Rework, schedule slip, long-lead re-orders — the most expensive place to find them</div>
            </div>
          </div>
        </div>

        <div className={`ba-side ${view === "after" ? "ba-side-active" : ""}`}>
          <div className="ba-side-header ba-side-after-header">
            <div className="ba-side-title">Pramaan AI</div>
            <div className="ba-side-duration">&lt; 5 minutes total</div>
          </div>
          {STEPS_AFTER.map((s, i) => (
            <div key={i} className="ba-step ba-step-after">
              <div className="ba-step-num">{i + 1}</div>
              <div className="ba-step-content">
                <div className="ba-step-phase">{s.phase}</div>
                <div className="ba-step-duration">{s.duration}</div>
                <div className="ba-step-pain">{s.pain}</div>
              </div>
            </div>
          ))}
          <div className="ba-outcome ba-outcome-good">
            <div className="ba-outcome-icon">✓</div>
            <div>
              <div className="ba-outcome-title">Deviations caught at Week 11</div>
              <div className="ba-outcome-detail">27–33 weeks of lead time in hand (scenario) — resolved before site mobilisation</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
