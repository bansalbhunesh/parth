"use client";
import type { ReactNode } from "react";
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

type HighlightRule = {
  value: string;
  className: string;
};

function highlightParts(text: string, rules: HighlightRule[]): ReactNode[] {
  const parts: ReactNode[] = [];
  let cursor = 0;

  while (cursor < text.length) {
    let nextIndex = -1;
    let nextRule: HighlightRule | null = null;

    for (const rule of rules) {
      const index = text.indexOf(rule.value, cursor);
      if (index !== -1 && (nextIndex === -1 || index < nextIndex)) {
        nextIndex = index;
        nextRule = rule;
      }
    }

    if (!nextRule || nextIndex === -1) {
      parts.push(text.slice(cursor));
      break;
    }

    if (nextIndex > cursor) {
      parts.push(text.slice(cursor, nextIndex));
    }
    parts.push(
      <span key={`${nextIndex}-${nextRule.value}`} className={nextRule.className}>
        {nextRule.value}
      </span>
    );
    cursor = nextIndex + nextRule.value.length;
  }

  return parts;
}

export function highlightDeviations(text: string, deviations: Deviation[], side: "spec" | "submittal") {
  if (!deviations.length) return <pre className="diff-pre">{text}</pre>;

  const className = side === "spec" ? "diff-highlight-spec" : "diff-highlight-sub";
  const rules = deviations
    .map((d) => side === "spec" ? d.required_value : d.provided_value)
    .map((value) => String(value).trim())
    .filter((value, index, values) => value.length > 0 && values.indexOf(value) === index)
    .map((value) => ({ value, className }));

  return <pre className="diff-pre">{highlightParts(text, rules)}</pre>;
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
