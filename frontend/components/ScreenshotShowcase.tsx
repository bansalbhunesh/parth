"use client";

import { useState } from "react";

const SCREENS = [
  { id: "sentinel", label: "Deviation Sentinel", desc: "UPS-02 battery runtime: 7 min vs 10 min required — 27 weeks early", color: "#ff4d4d", icon: "!" },
  { id: "pipeline", label: "AI Agent Pipeline", desc: "5 agents: Ingestion, Extraction, Reconciliation, Cx Predictor, RFI Copilot", color: "#36d6e7", icon: "→" },
  { id: "architecture", label: "System Architecture", desc: "LangGraph multi-agent orchestrator with conditional routing", color: "#a855f7", icon: "◦" },
  { id: "systems", label: "System Health Grid", desc: "10 systems: 7 with findings (4 critical), 3 compliant", color: "#35c98b", icon: "▓" },
  { id: "register", label: "Deviation Register", desc: "Full register with severity, lead time, Cx test mapping", color: "#ffb020", icon: "≡" },
  { id: "twin", label: "Commissioning Twin", desc: "L1–L5 Gantt timeline with at-risk test predictions", color: "#5b8cff", icon: "▮" },
  { id: "eval", label: "Eval Dashboard", desc: "P/R/F1 = 1.000, Cx accuracy 1.000, 267 weeks lead time", color: "#35c98b", icon: "✓" },
  { id: "copilot", label: "RFI Copilot", desc: "Streaming RAG over specs, submittals, standards & RFIs", color: "#36d6e7", icon: "❖" },
  { id: "analyze", label: "Live Analysis", desc: "Upload PDFs or paste text for real-time deviation detection", color: "#a855f7", icon: "▶" },
  { id: "multiproject", label: "Multi-Project Eval", desc: "6 projects, 5 countries, 33 deviations, F1=1.000", color: "#ffb020", icon: "★" },
];

export default function ScreenshotShowcase() {
  const [selected, setSelected] = useState(0);
  const s = SCREENS[selected];

  return (
    <div className="ss">
      <div className="ss-viewer">
        <div className="ss-frame">
          <div className="ss-frame-bar">
            <div className="ss-frame-dots">
              <span className="ss-dot ss-dot-r" />
              <span className="ss-dot ss-dot-y" />
              <span className="ss-dot ss-dot-g" />
            </div>
            <div className="ss-frame-url">localhost:3000/#{s.id}</div>
          </div>
          <div className="ss-mockup" style={{ borderColor: s.color }}>
            <div className="ss-mockup-header">
              <div className="ss-mockup-icon" style={{ background: s.color }}>{s.icon}</div>
              <div className="ss-mockup-title">{s.label}</div>
            </div>
            <div className="ss-mockup-body">
              <div className="ss-mockup-bar" style={{ background: s.color, width: "75%" }} />
              <div className="ss-mockup-bar" style={{ background: s.color, width: "60%", opacity: 0.6 }} />
              <div className="ss-mockup-bar" style={{ background: s.color, width: "85%", opacity: 0.3 }} />
              <div className="ss-mockup-grid">
                {[1,2,3,4].map(i => (
                  <div key={i} className="ss-mockup-card" style={{ borderColor: s.color }}>
                    <div className="ss-mockup-card-dot" style={{ background: s.color }} />
                  </div>
                ))}
              </div>
            </div>
            <div className="ss-mockup-desc">{s.desc}</div>
          </div>
        </div>
      </div>

      <div className="ss-thumbs">
        {SCREENS.map((sc, i) => (
          <button
            key={sc.id}
            className={`ss-thumb ${i === selected ? "ss-thumb-active" : ""}`}
            onClick={() => setSelected(i)}
          >
            <div className="ss-thumb-color" style={{ background: sc.color }} />
            <div className="ss-thumb-label">{sc.label}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
