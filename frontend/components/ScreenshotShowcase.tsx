"use client";

import { useState } from "react";

// Real product screenshots shipped in /public/screenshots/*.png (served at
// /screenshots/<id>.png). These replace the earlier CSS mockups — judges in the
// Screenshots section now see the actual app, not stylised placeholders.
const SCREENS = [
  { id: "hero-full", label: "Full Dashboard", desc: "22-section deep-dive dashboard, dark theme, ISR-cached" },
  { id: "register", label: "Deviation Register", desc: "Every finding with severity, lead time and the Cx test it will fail" },
  { id: "risk", label: "Commissioning Risk Matrix", desc: "Deviations plotted by severity × weeks-to-failure" },
  { id: "pipeline", label: "AI Agent Pipeline", desc: "Ingestion → Extraction → Reconciliation → Cx Predictor → RFI Copilot" },
  { id: "architecture", label: "System Architecture", desc: "LangGraph orchestrator + standards-cited commissioning graph" },
  { id: "eval", label: "Eval Dashboard", desc: "Real-datasheet recall + honest precision; no-key offline harness" },
  { id: "copilot", label: "RFI Copilot", desc: "Streaming RAG over specs, submittals, standards & RFIs" },
  { id: "roi", label: "ROI / Cost-of-Delay", desc: "Weeks-early × cost-per-week model — the asymmetry story" },
  { id: "scale", label: "Multi-Project Portfolio", desc: "12 projects, 11 countries — the breadth (by-construction) test" },
  { id: "refs", label: "Academic References", desc: "Peer-reviewed precedents for cross-document compliance reasoning" },
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
            <div className="ss-frame-url">parth-tan.vercel.app/#{s.id}</div>
          </div>
          <figure className="ss-shot" style={{ margin: 0 }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`/screenshots/${s.id}.png`}
              alt={`${s.label} — ${s.desc}`}
              loading="lazy"
              style={{ width: "100%", height: "auto", display: "block", borderRadius: "0 0 10px 10px" }}
            />
            <figcaption className="ss-mockup-desc">{s.desc}</figcaption>
          </figure>
        </div>
      </div>

      <div className="ss-thumbs" role="tablist" aria-label="Product screenshots">
        {SCREENS.map((sc, i) => (
          <button
            key={sc.id}
            type="button"
            role="tab"
            aria-selected={i === selected}
            aria-label={`Show ${sc.label} screenshot`}
            className={`ss-thumb ${i === selected ? "ss-thumb-active" : ""}`}
            onClick={() => setSelected(i)}
          >
            <div className="ss-thumb-label">{sc.label}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
