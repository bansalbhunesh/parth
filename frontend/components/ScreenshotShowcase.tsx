"use client";

import { useState } from "react";
import Image from "next/image";

const SCREENS = [
  { id: "hero-full", label: "Dashboard Overview", desc: "Hero intro, stats bar, and sentinel deviation alert" },
  { id: "sentinel", label: "Deviation Sentinel", desc: "UPS-02 battery runtime: 7 min vs 10 min required — 27 weeks early" },
  { id: "pipeline", label: "AI Agent Pipeline", desc: "5 agents: Ingestion, Extraction, Reconciliation, Cx Predictor, RFI Copilot" },
  { id: "architecture", label: "System Architecture", desc: "LangGraph multi-agent orchestrator with 4-layer data flow" },
  { id: "systems", label: "System Health Grid", desc: "10 systems: 7 with findings (4 critical), 3 compliant" },
  { id: "register", label: "Deviation Register", desc: "Full register with severity, lead time, Cx test mapping" },
  { id: "twin", label: "Commissioning Twin", desc: "L1–L5 Gantt timeline with at-risk test predictions" },
  { id: "eval", label: "Eval Dashboard", desc: "P/R/F1 = 1.000, Cx accuracy 1.000, 149 weeks total lead time" },
  { id: "roi", label: "ROI Calculator", desc: "Interactive cost savings model with project value slider" },
  { id: "standards", label: "Standards Knowledge Base", desc: "7 governing standards with deviation counts per standard" },
];

export default function ScreenshotShowcase() {
  const [selected, setSelected] = useState(0);

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
            <div className="ss-frame-url">pramaan.app/{SCREENS[selected].id}</div>
          </div>
          <div className="ss-image-wrap">
            <Image
              src={`/screenshots/${SCREENS[selected].id}.png`}
              alt={SCREENS[selected].label}
              width={1400}
              height={700}
              className="ss-image"
              priority={selected === 0}
            />
          </div>
        </div>
        <div className="ss-caption">
          <div className="ss-caption-title">{SCREENS[selected].label}</div>
          <div className="ss-caption-desc">{SCREENS[selected].desc}</div>
        </div>
      </div>

      <div className="ss-thumbs">
        {SCREENS.map((s, i) => (
          <button
            key={s.id}
            className={`ss-thumb ${i === selected ? "ss-thumb-active" : ""}`}
            onClick={() => setSelected(i)}
          >
            <Image
              src={`/screenshots/${s.id}.png`}
              alt={s.label}
              width={160}
              height={90}
              className="ss-thumb-img"
            />
            <div className="ss-thumb-label">{s.label}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
