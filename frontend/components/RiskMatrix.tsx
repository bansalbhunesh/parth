"use client";

import { Deviation } from "../lib/api";

const SEVERITY_ORDER = ["Minor", "Major", "Critical"] as const;
const LEAD_BUCKETS = [
  { label: "< 15w", min: 0, max: 15 },
  { label: "15–25w", min: 15, max: 25 },
  { label: "> 25w", min: 25, max: 999 },
];

function getCellColor(severity: string, bucket: number): string {
  const s = SEVERITY_ORDER.indexOf(severity as typeof SEVERITY_ORDER[number]);
  const risk = (s + 1) * (bucket + 1);
  if (risk >= 6) return "var(--fault)";
  if (risk >= 3) return "var(--warn)";
  return "var(--ok)";
}

export default function RiskMatrix({ rows }: { rows: Deviation[] }) {
  const matrix: Record<string, Record<number, Deviation[]>> = {};
  for (const sev of SEVERITY_ORDER) {
    matrix[sev] = {};
    for (let b = 0; b < LEAD_BUCKETS.length; b++) matrix[sev][b] = [];
  }
  for (const d of rows) {
    const lead = d.lead_time_weeks ?? 0;
    const bIdx = LEAD_BUCKETS.findIndex((b) => lead >= b.min && lead < b.max);
    const bucket = bIdx >= 0 ? bIdx : LEAD_BUCKETS.length - 1;
    if (matrix[d.severity]) matrix[d.severity][bucket].push(d);
  }

  return (
    <div className="risk-matrix">
      <div className="risk-matrix-ylabel">SEVERITY →</div>
      <div className="risk-matrix-grid">
        <div className="risk-matrix-corner" />
        {LEAD_BUCKETS.map((b, i) => (
          <div key={i} className="risk-matrix-col-head">{b.label}</div>
        ))}
        {[...SEVERITY_ORDER].reverse().map((sev) => (
          <div key={sev} style={{ display: "contents" }}>
            <div className="risk-matrix-row-head">{sev}</div>
            {LEAD_BUCKETS.map((_, bIdx) => {
              const devs = matrix[sev][bIdx];
              return (
                <div
                  key={`${sev}-${bIdx}`}
                  className={`risk-matrix-cell ${devs.length > 0 ? "risk-matrix-cell-filled" : ""}`}
                  style={{
                    borderColor: devs.length > 0 ? getCellColor(sev, bIdx) : undefined,
                    background: devs.length > 0 ? `${getCellColor(sev, bIdx)}15` : undefined,
                  }}
                >
                  {devs.map((d) => (
                    <div key={d.component} className="risk-matrix-dot" title={`${d.component}: ${d.parameter}`}>
                      <span className="risk-dot-id">{d.component}</span>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <div className="risk-matrix-xlabel">LEAD TIME →</div>
    </div>
  );
}
