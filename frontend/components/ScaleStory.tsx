"use client";

import { useEffect, useRef, useState } from "react";

const STAGES = [
  { items: "10", label: "Systems modelled", sub: "Demo corpus", done: true },
  { items: "33", label: "Requirements tracked", sub: "Spec + standard pairs", done: true },
  { items: "87", label: "Active submittals", sub: "Vendor documents", done: true },
  { items: "14K", label: "Line items at scale", sub: "Batch ingest + vector store", done: false },
];

export default function ScaleStory() {
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
      { threshold: 0.2 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="scale-story" ref={ref}>
      <div className="scale-track">
        {STAGES.map((s, i) => (
          <div
            key={i}
            className={`scale-node ${visible ? "scale-node-visible" : ""} ${s.done ? "scale-done" : "scale-future"}`}
            style={{ transitionDelay: `${i * 200}ms` }}
          >
            <div className="scale-num">{s.items}</div>
            <div className="scale-label">{s.label}</div>
            <div className="scale-sub">{s.sub}</div>
            {!s.done && <div className="scale-badge">SCALABLE</div>}
          </div>
        ))}
      </div>
      <div className="scale-detail">
        <div className="scale-detail-item">
          <span className="scale-detail-icon">POST</span>
          <span>/ingest/&#123;system_id&#125; — one system at a time, parallelisable</span>
        </div>
        <div className="scale-detail-item">
          <span className="scale-detail-icon">VEC</span>
          <span>Swap TF-IDF retriever for pgvector / Qdrant at scale</span>
        </div>
        <div className="scale-detail-item">
          <span className="scale-detail-icon">ASYNC</span>
          <span>LangGraph orchestrator supports async execution + queue</span>
        </div>
        <div className="scale-detail-item">
          <span className="scale-detail-icon">MULTI</span>
          <span>Gemini handles PDFs, drawings, and tables natively</span>
        </div>
      </div>
    </div>
  );
}
