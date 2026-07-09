"use client";
import { useState } from "react";
import { Deviation } from "../lib/api";

const SYSTEMS = [
  { id: "UPS", label: "UPS & Battery" },
  { id: "GEN", label: "Generators" },
  { id: "COOL", label: "Cooling" },
  { id: "SWGR", label: "Switchgear" },
  { id: "CABLE", label: "Cabling" },
  { id: "BMS", label: "BMS/EPMS" },
  { id: "STRUCT", label: "Structural" },
];

function highlightDeviations(text: string, deviations: Deviation[], side: "spec" | "submittal") {
  if (!deviations.length) return <pre className="diff-pre">{text}</pre>;

  let result = text;
  for (const d of deviations) {
    const val = side === "spec" ? String(d.required_value) : String(d.provided_value);
    if (val && result.includes(val)) {
      const cls = side === "spec" ? "diff-highlight-spec" : "diff-highlight-sub";
      result = result.replace(
        new RegExp(`(\\*\\*${val.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[^*]*)`, 'g'),
        `<span class="${cls}">$1</span>`
      );
    }
  }
  return <pre className="diff-pre" dangerouslySetInnerHTML={{ __html: result }} />;
}

const API = process.env.NEXT_PUBLIC_API ?? "http://127.0.0.1:8000";

export default function DocumentDiff({ rows }: { rows: Deviation[] }) {
  const [selected, setSelected] = useState("UPS");
  const [specText, setSpecText] = useState<string | null>(null);
  const [subText, setSubText] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadDocs = async (sysId: string) => {
    setSelected(sysId);
    setLoading(true);
    try {
      const [specRes, subRes] = await Promise.all([
        fetch(`${API}/corpus/doc/specs/${sysId}`).then(r => r.ok ? r.json() : null),
        fetch(`${API}/corpus/doc/submittals/${sysId}`).then(r => r.ok ? r.json() : null),
      ]);
      setSpecText(specRes?.text || null);
      setSubText(subRes?.text || null);
    } catch {
      setSpecText(null);
      setSubText(null);
    }
    setLoading(false);
  };

  const sysDevs = rows.filter(r => {
    const sys = r.component === "BMS" ? "BMS" : r.component === "FLOOR" ? "STRUCT" : r.component.split("-")[0];
    return sys === selected;
  });

  return (
    <div className="diff-viewer">
      <div className="diff-tabs">
        {SYSTEMS.map((s) => {
          const hasDevs = rows.some(r => {
            const sys = r.component === "BMS" ? "BMS" : r.component === "FLOOR" ? "STRUCT" : r.component.split("-")[0];
            return sys === s.id;
          });
          return (
            <button
              key={s.id}
              className={`diff-tab ${selected === s.id ? "diff-tab-active" : ""} ${hasDevs ? "diff-tab-deviant" : ""}`}
              onClick={() => loadDocs(s.id)}
            >
              {s.label}
              {hasDevs && <span className="diff-tab-dot" />}
            </button>
          );
        })}
      </div>

      {sysDevs.length > 0 && (
        <div className="diff-findings-summary">
          {sysDevs.map((d, i) => (
            <span key={i} className={`diff-finding-chip ${d.severity.toLowerCase()}`}>
              {d.component}.{d.parameter.replace(/_/g, " ")}: {d.provided_value} vs {d.required_value} {d.unit}
            </span>
          ))}
        </div>
      )}

      <div className="diff-panels">
        <div className="diff-panel">
          <div className="diff-panel-header diff-panel-spec">
            <span>Design Basis (Spec)</span>
            <span className="diff-panel-status">Required values</span>
          </div>
          <div className="diff-panel-body">
            {loading ? (
              <div className="diff-loading">Loading...</div>
            ) : specText ? (
              highlightDeviations(specText, sysDevs, "spec")
            ) : (
              <div className="diff-placeholder">Click a system tab to load documents from the API, or view the static comparison below.</div>
            )}
          </div>
        </div>
        <div className="diff-panel">
          <div className="diff-panel-header diff-panel-sub">
            <span>Vendor Submittal</span>
            <span className="diff-panel-status">Provided values</span>
          </div>
          <div className="diff-panel-body">
            {loading ? (
              <div className="diff-loading">Loading...</div>
            ) : subText ? (
              highlightDeviations(subText, sysDevs, "submittal")
            ) : (
              <div className="diff-placeholder">Click a system tab to load documents from the API, or view the static comparison below.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
