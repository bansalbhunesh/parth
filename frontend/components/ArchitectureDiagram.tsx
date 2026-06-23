"use client";

import { useEffect, useRef, useState } from "react";

const LAYERS = [
  {
    id: "input",
    label: "Document Layer",
    color: "#5b8cff",
    items: [
      { label: "Design Basis (OPR)", sub: "40 MW · 8 data halls" },
      { label: "Vendor Submittals", sub: "87 documents · Rev A–C" },
      { label: "Standards Corpus", sub: "7 standards · 317+ clauses" },
    ],
  },
  {
    id: "agents",
    label: "LangGraph Agent Orchestrator",
    color: "#ff4d4d",
    items: [
      { label: "Ingestion Agent", sub: "PDF/DOCX → structured triples" },
      { label: "Extraction Agent", sub: "Parameter · Value · Unit · Clause" },
      { label: "Reconciliation Agent", sub: "Cross-document deviation detection" },
      { label: "Cx Predictor", sub: "Deviation → Test · Week · Lead time" },
      { label: "RFI Copilot", sub: "RAG + prior-RFI matching" },
    ],
  },
  {
    id: "infra",
    label: "Infrastructure",
    color: "#35c98b",
    items: [
      { label: "Gemini 2.5 Flash", sub: "Multimodal LLM · PDFs + tables" },
      { label: "TF-IDF / pgvector", sub: "Retrieval · scalable to Qdrant" },
      { label: "FastAPI Backend", sub: "Async · 10 endpoints · graceful fallback" },
    ],
  },
  {
    id: "output",
    label: "Output Layer",
    color: "#36d6e7",
    items: [
      { label: "Deviation Register", sub: "Component · Severity · Lead time" },
      { label: "Cx Risk Twin", sub: "L1–L5 Gantt · at-risk tests" },
      { label: "Evidence Pack", sub: "HTML export · audit trail" },
    ],
  },
];

export default function ArchitectureDiagram() {
  const [visible, setVisible] = useState(false);
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
      { threshold: 0.15 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="arch" ref={ref}>
      <div className="arch-flow">
        {LAYERS.map((layer, li) => (
          <div key={layer.id} className="arch-layer-wrap">
            <div
              className={`arch-layer ${visible ? "arch-layer-visible" : ""}`}
              style={{ transitionDelay: `${li * 200}ms`, borderTopColor: layer.color }}
            >
              <div className="arch-layer-label" style={{ color: layer.color }}>
                {layer.label}
              </div>
              <div className="arch-items">
                {layer.items.map((item, ii) => (
                  <div
                    key={ii}
                    className={`arch-item ${visible ? "arch-item-visible" : ""}`}
                    style={{ transitionDelay: `${li * 200 + ii * 100 + 200}ms` }}
                  >
                    <div className="arch-item-label">{item.label}</div>
                    <div className="arch-item-sub">{item.sub}</div>
                  </div>
                ))}
              </div>
            </div>
            {li < LAYERS.length - 1 && (
              <div className={`arch-arrow ${visible ? "arch-arrow-visible" : ""}`} style={{ transitionDelay: `${li * 200 + 300}ms` }}>
                <svg width="24" height="32" viewBox="0 0 24 32">
                  <path d="M12 4 L12 24 M6 18 L12 26 L18 18" stroke={layer.color} fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="arch-callouts">
        <div className="arch-callout">
          <div className="arch-callout-icon">🔄</div>
          <div className="arch-callout-text">
            <strong>LangGraph orchestration</strong> — agents share state, hand off intermediate results, and can retry failed steps
          </div>
        </div>
        <div className="arch-callout">
          <div className="arch-callout-icon">📎</div>
          <div className="arch-callout-text">
            <strong>Citation chain</strong> — every finding traces back to source clause, standard section, and submittal page
          </div>
        </div>
        <div className="arch-callout">
          <div className="arch-callout-icon">🔁</div>
          <div className="arch-callout-text">
            <strong>Deterministic eval</strong> — <code>eval/run_eval.py</code> validates every agent output against ground truth
          </div>
        </div>
      </div>
    </div>
  );
}
