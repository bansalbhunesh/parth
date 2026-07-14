"use client";

import { useState } from "react";

// Real product screenshots shipped in /public/screenshots/*.png (served at
// /screenshots/<id>.png). These replace the earlier CSS mockups — judges in the
// Screenshots section now see the actual app, not stylised placeholders.
const SCREENS = [
  { id: "overview", label: "Overview", desc: "The 90-second evidence-to-resolution journey" },
  { id: "trace", label: "Evidence trace", desc: "Requirement, variance, commissioning consequence, and decision window" },
  { id: "resolution", label: "Resolution", desc: "Protected case workflow with ownership and audit history" },
  { id: "analysis", label: "Document analysis", desc: "Upload or paste documents with explicit analysis provenance" },
  { id: "evidence", label: "Evidence", desc: "Frozen benchmark, current status, sources, and limitations" },
  { id: "interventions", label: "Interventions", desc: "Prioritized action with schedule and supply assumptions" },
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
          <figure className="ss-shot">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`/screenshots/${s.id}.png`}
              alt={`${s.label} — ${s.desc}`}
              loading="lazy"
              className="ss-shot-image"
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
