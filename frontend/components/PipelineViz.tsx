"use client";

import { useEffect, useRef, useState } from "react";

const STAGES = [
  { id: "ingest", label: "Document Ingestion", sub: "Specs · Submittals · Standards", icon: "📄", color: "#5b8cff" },
  { id: "extract", label: "Extraction Agent", sub: "Raw → Structured Triples", icon: "⚡", color: "#ffb020" },
  { id: "reconcile", label: "Reconciliation Agent", sub: "Cross-Document Reasoning", icon: "🧠", color: "#ff4d4d", hero: true },
  { id: "cx", label: "Cx Predictor", sub: "Deviation → Test + Lead Time", icon: "⏱", color: "#35c98b" },
  { id: "copilot", label: "RFI Copilot", sub: "RAG + Prior-RFI Matching", icon: "💬", color: "#36d6e7" },
];

export default function PipelineViz() {
  const [active, setActive] = useState(-1);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        STAGES.forEach((_, i) => {
          setTimeout(() => setActive(i), 300 + i * 400);
        });
      },
      { threshold: 0.2 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="pipeline" ref={ref}>
      {STAGES.map((s, i) => (
        <div key={s.id} className="pipeline-stage-wrap">
          <div
            className={`pipeline-stage ${i <= active ? "pipeline-active" : ""} ${s.hero ? "pipeline-hero" : ""}`}
            style={{ "--stage-color": s.color } as React.CSSProperties}
          >
            <div className="pipeline-icon">{s.icon}</div>
            <div className="pipeline-label">{s.label}</div>
            <div className="pipeline-sub">{s.sub}</div>
          </div>
          {i < STAGES.length - 1 && (
            <div className={`pipeline-arrow ${i < active ? "pipeline-arrow-active" : ""}`}>
              <svg width="32" height="16" viewBox="0 0 32 16">
                <path d="M0 8 L24 8 M18 2 L26 8 L18 14" stroke="currentColor" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
