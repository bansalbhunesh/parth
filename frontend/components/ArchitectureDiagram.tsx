"use client";

import { useEffect, useRef, useState } from "react";

const NODES = {
  inputs: [
    { id: "spec", label: "Design Basis", sub: "Owner requirements", detail: "40 MW · 8 data halls · 33 params", color: "#5b8cff" },
    { id: "sub", label: "Vendor Submittals", sub: "87 documents", detail: "Rev A–C · PDF/DOCX/tables", color: "#5b8cff" },
    { id: "std", label: "Standards Corpus", sub: "7 governing standards", detail: "1,580 lines · 317+ clauses", color: "#5b8cff" },
  ],
  // The real LangGraph nodes (backend/orchestrator.py), tagged with what each
  // runs on. Reconcile is the LLM reasoning core on the main path (extraction
  // happens inside it); the rest are deterministic (cx-predict calls an LLM only
  // as a fallback for unmapped classes). Retrieve + Critique are the two bounded
  // cycles that loop back to reconcile. The RFI copilot is a separate service, not
  // a graph node, so it is shown in the services band below — not here.
  agents: [
    { id: "ingest", label: "Ingest", sub: "PDF/image → text", icon: "01", color: "#ffb020", kind: "DET" },
    { id: "reconcile", label: "Reconcile", sub: "Extract + cross-doc reasoning", icon: "02", color: "#ff4d4d", hero: true, kind: "LLM" },
    { id: "retrieve", label: "Retrieve", sub: "Cycle 1 · fetch cited standard", icon: "03", color: "#5b8cff", kind: "DET" },
    { id: "critique", label: "Critique", sub: "Cycle 2 · self-check / reflexion", icon: "04", color: "#5b8cff", kind: "DET" },
    { id: "cx", label: "Cx Predictor", sub: "Test + lead time (rule/graph)", icon: "05", color: "#35c98b", kind: "RULE" },
  ],
  outputs: [
    { id: "register", label: "Deviation Register", sub: "7 findings · 4 critical", color: "#36d6e7" },
    { id: "twin", label: "Cx Risk Twin", sub: "L1–L5 Gantt · at-risk", color: "#36d6e7" },
    { id: "evidence", label: "Evidence Pack", sub: "HTML export · audit", color: "#36d6e7" },
  ],
};

const DATAFLOWS = [
  { label: "Raw documents", from: "inputs", to: "ingest" },
  { label: "Deviations + rationale", from: "reconcile", to: "critique" },
  { label: "Verified findings", from: "critique", to: "cx" },
  { label: "Cx predictions + lead time", from: "cx", to: "outputs" },
];

const TECH = [
  { label: "LLM failover chain", detail: "featured gemini-3.1-flash-lite", color: "#ff4d4d" },
  { label: "LangGraph", detail: "reasoning graph · 2 cycles", color: "#ffb020" },
  { label: "FastAPI", detail: "SSE + async jobs", color: "#35c98b" },
  { label: "TF-IDF / pgvector", detail: "retrieval layer", color: "#5b8cff" },
];

export default function ArchitectureDiagram() {
  const [visible, setVisible] = useState(false);
  const [activeAgent, setActiveAgent] = useState(-1);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible) return;
    const timers = NODES.agents.map((_, i) =>
      setTimeout(() => setActiveAgent(i), 600 + i * 300)
    );
    return () => timers.forEach(clearTimeout);
  }, [visible]);

  return (
    <div className="arch2" ref={ref}>
      {/* Input layer */}
      <div className={`arch2-section arch2-inputs ${visible ? "arch2-visible" : ""}`}>
        <div className="arch2-section-label">
          <span className="arch2-section-dot" style={{ background: "#5b8cff" }} />
          INPUT DOCUMENTS
        </div>
        <div className="arch2-input-cards">
          {NODES.inputs.map((n, i) => (
            <div
              key={n.id}
              className={`arch2-input-card ${visible ? "arch2-card-visible" : ""}`}
              style={{ transitionDelay: `${i * 120}ms` }}
            >
              <div className="arch2-input-icon" style={{ borderColor: n.color }}>
                {n.id === "spec" ? (
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="2" width="14" height="16" rx="2" stroke="#5b8cff" strokeWidth="1.5"/><line x1="6" y1="6" x2="14" y2="6" stroke="#5b8cff" strokeWidth="1" opacity="0.5"/><line x1="6" y1="9" x2="14" y2="9" stroke="#5b8cff" strokeWidth="1" opacity="0.5"/><line x1="6" y1="12" x2="10" y2="12" stroke="#5b8cff" strokeWidth="1" opacity="0.5"/></svg>
                ) : n.id === "sub" ? (
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="2" y="3" width="12" height="14" rx="2" stroke="#5b8cff" strokeWidth="1.5"/><rect x="6" y="3" width="12" height="14" rx="2" stroke="#5b8cff" strokeWidth="1.5" opacity="0.5"/></svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2L18 7V13L10 18L2 13V7L10 2Z" stroke="#5b8cff" strokeWidth="1.5"/><line x1="10" y1="8" x2="10" y2="14" stroke="#5b8cff" strokeWidth="1" opacity="0.5"/></svg>
                )}
              </div>
              <div>
                <div className="arch2-input-name">{n.label}</div>
                <div className="arch2-input-sub">{n.sub}</div>
                <div className="arch2-input-detail">{n.detail}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Flow arrow: inputs -> agents */}
      <div className={`arch2-flow-connector ${visible ? "arch2-connector-visible" : ""}`} style={{ transitionDelay: "400ms" }}>
        <div className="arch2-flow-line" />
        <div className="arch2-flow-label">{DATAFLOWS[0].label}</div>
        <div className="arch2-flow-pulse" />
      </div>

      {/* Agent orchestrator */}
      <div className={`arch2-section arch2-agents ${visible ? "arch2-visible" : ""}`} style={{ transitionDelay: "300ms" }}>
        <div className="arch2-section-label">
          <span className="arch2-section-dot" style={{ background: "#ff4d4d" }} />
          LANGGRAPH COMPLIANCE REASONING GRAPH
          <span className="arch2-orchestrator-badge">1 LLM CORE · 2 CYCLES</span>
        </div>
        <div className="arch2-agent-track">
          {NODES.agents.map((a, i) => (
            <div key={a.id} className="arch2-agent-wrap">
              <div
                className={`arch2-agent ${i <= activeAgent ? "arch2-agent-active" : ""} ${a.hero ? "arch2-agent-hero" : ""}`}
                style={{ "--agent-color": a.color, transitionDelay: `${i * 150}ms` } as React.CSSProperties}
              >
                <div className="arch2-agent-num" style={{ color: a.color }}>{a.icon}</div>
                <div className="arch2-agent-label">{a.label}</div>
                <div className="arch2-agent-sub">{a.sub}</div>
                <span
                  className="arch2-agent-kind"
                  style={{
                    color: a.kind === "LLM" ? "#ff8a8a" : a.kind === "RULE" ? "#7fe3b8" : "#9fb2cc",
                    borderColor: a.kind === "LLM" ? "rgba(255,77,77,0.4)" : a.kind === "RULE" ? "rgba(53,201,139,0.4)" : "rgba(122,136,153,0.4)",
                  }}
                >
                  {a.kind === "LLM" ? "LLM" : a.kind === "RULE" ? "RULE" : "DET"}
                </span>
                {a.hero && <div className="arch2-agent-brain-tag">CORE</div>}
              </div>
              {i < NODES.agents.length - 1 && (
                <div className={`arch2-agent-arrow ${i < activeAgent ? "arch2-arrow-active" : ""}`}>
                  <svg width="28" height="12" viewBox="0 0 28 12">
                    <path d="M0 6 L20 6 M16 2 L22 6 L16 10" stroke="currentColor" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Data flow annotations between agents */}
        <div className="arch2-flow-annotations">
          {DATAFLOWS.slice(1, 3).map((f, i) => (
            <div key={i} className={`arch2-flow-annotation ${visible ? "arch2-annotation-visible" : ""}`} style={{ transitionDelay: `${800 + i * 200}ms` }}>
              <svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" fill="none" stroke="currentColor" strokeWidth="1"/></svg>
              <span>{f.label}</span>
            </div>
          ))}
        </div>
        <div
          className={visible ? "arch2-annotation-visible" : ""}
          style={{
            marginTop: 14, textAlign: "center", fontFamily: "var(--mono)",
            fontSize: 10.5, lineHeight: 1.6, color: "var(--muted)",
            opacity: visible ? 1 : 0, transition: "opacity 0.6s 1s",
          }}
        >
          ↺ <strong style={{ color: "#ff8a8a" }}>Retrieve</strong> and{" "}
          <strong style={{ color: "#ff8a8a" }}>Critique</strong> each loop back to
          Reconcile — the two bounded cycles (retrieval tool-call · self-critique
          reflexion). Reconcile is the LLM core; Cx-predict falls back to an LLM
          only for unmapped classes.
        </div>
      </div>

      {/* Flow arrow: agents -> outputs */}
      <div className={`arch2-flow-connector ${visible ? "arch2-connector-visible" : ""}`} style={{ transitionDelay: "900ms" }}>
        <div className="arch2-flow-line arch2-flow-line-out" />
        <div className="arch2-flow-label">{DATAFLOWS[3].label}</div>
        <div className="arch2-flow-pulse" />
      </div>

      {/* Output layer */}
      <div className={`arch2-section arch2-outputs ${visible ? "arch2-visible" : ""}`} style={{ transitionDelay: "600ms" }}>
        <div className="arch2-section-label">
          <span className="arch2-section-dot" style={{ background: "#36d6e7" }} />
          OUTPUT ARTIFACTS
        </div>
        <div className="arch2-output-cards">
          {NODES.outputs.map((o, i) => (
            <div
              key={o.id}
              className={`arch2-output-card ${visible ? "arch2-card-visible" : ""}`}
              style={{ transitionDelay: `${700 + i * 120}ms` }}
            >
              <div className="arch2-output-icon">
                {o.id === "register" ? (
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect x="2" y="2" width="14" height="14" rx="2" stroke="#36d6e7" strokeWidth="1.5"/><path d="M5 7L8 10L13 5" stroke="#36d6e7" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                ) : o.id === "twin" ? (
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect x="2" y="4" width="4" height="10" rx="1" stroke="#36d6e7" strokeWidth="1.5"/><rect x="7" y="7" width="4" height="7" rx="1" stroke="#36d6e7" strokeWidth="1.5" opacity="0.7"/><rect x="12" y="2" width="4" height="12" rx="1" stroke="#36d6e7" strokeWidth="1.5" opacity="0.5"/></svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2L16 6V12L9 16L2 12V6L9 2Z" stroke="#36d6e7" strokeWidth="1.5"/><circle cx="9" cy="9" r="2" stroke="#36d6e7" strokeWidth="1"/></svg>
                )}
              </div>
              <div className="arch2-output-name">{o.label}</div>
              <div className="arch2-output-sub">{o.sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Tech stack bar */}
      <div className={`arch2-tech ${visible ? "arch2-visible" : ""}`} style={{ transitionDelay: "900ms" }}>
        <div className="arch2-tech-label">INFRASTRUCTURE</div>
        <div className="arch2-tech-items">
          {TECH.map((t, i) => (
            <div key={i} className={`arch2-tech-item ${visible ? "arch2-card-visible" : ""}`} style={{ transitionDelay: `${1000 + i * 100}ms` }}>
              <span className="arch2-tech-dot" style={{ background: t.color }} />
              <span className="arch2-tech-name">{t.label}</span>
              <span className="arch2-tech-detail">{t.detail}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Key properties */}
      <div className={`arch2-props ${visible ? "arch2-visible" : ""}`} style={{ transitionDelay: "1100ms" }}>
        {[
          { icon: "01", title: "Benchmarked", desc: "recall 0.862 · precision 0.953 · F1 0.905 on ps4_external_v1 v1.2 (team-authored, reviewer-2 pending)", color: "#35c98b" },
          { icon: "02", title: "Citation chain", desc: "every finding traces to spec clause + standard + submittal", color: "#5b8cff" },
          { icon: "03", title: "0 false alerts", desc: "on 64 clean-negative controls in the benchmark (not a zero-false-positive claim overall)", color: "#36d6e7" },
          { icon: "04", title: "27-week lead", desc: "on the hero UPS deviation — caught week 11 vs the week-38 commissioning test", color: "#ffb020" },
        ].map((p, i) => (
          <div key={i} className={`arch2-prop ${visible ? "arch2-card-visible" : ""}`} style={{ transitionDelay: `${1200 + i * 100}ms` }}>
            <div className="arch2-prop-num" style={{ color: p.color }}>{p.icon}</div>
            <div>
              <div className="arch2-prop-title">{p.title}</div>
              <div className="arch2-prop-desc">{p.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
