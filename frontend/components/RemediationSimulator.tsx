"use client";

import { useMemo, useState } from "react";
import { RemediationSim } from "../lib/api";

// What-if remediation: a slider for the week the deviation is CAUGHT, driving
// the schedule slip and its cost. Deterministic — the curve comes straight from
// the engine. The story it tells: catch early, slip shrinks; the gap between
// "Pramaan (upload day)" and "commissioning (too late)" is the lead-time metric,
// made causal. Hand-rolled SVG, no deps.

const W = 640;
const H = 180;
const PAD_L = 44;
const PAD_B = 26;
const PAD_T = 12;

export default function RemediationSimulator({ sim }: { sim: RemediationSim }) {
  const maxWeek = sim.cx_planned_week;
  const [catchWeek, setCatchWeek] = useState(Math.round(sim.scenarios.pramaan.catch_week));

  const maxSlip = useMemo(
    () => Math.max(1, ...sim.curve.map((p) => p.slip_weeks)),
    [sim.curve],
  );
  const point = useMemo(() => {
    const exact = sim.curve.find((p) => p.catch_week === catchWeek);
    if (exact) return exact;
    const slip = Math.max(0, catchWeek + sim.fix_lead_weeks - sim.cx_planned_week);
    return { catch_week: catchWeek, slip_weeks: Math.round(slip * 10) / 10, cost_lakh: Math.round(slip * sim.cost_per_week_lakh * 10) / 10 };
  }, [catchWeek, sim]);

  const x = (w: number) => PAD_L + (w / maxWeek) * (W - PAD_L - 8);
  const y = (s: number) => PAD_T + (1 - s / maxSlip) * (H - PAD_T - PAD_B);

  const path = sim.curve.map((p, i) => `${i ? "L" : "M"}${x(p.catch_week).toFixed(1)},${y(p.slip_weeks).toFixed(1)}`).join(" ");
  const areaPath = `${path} L${x(sim.curve[sim.curve.length - 1].catch_week).toFixed(1)},${y(0).toFixed(1)} L${x(0).toFixed(1)},${y(0).toFixed(1)} Z`;
  const cliff = sim.zero_slip_deadline_week;

  const crore = (lakh: number) => (lakh / 100).toFixed(1);

  return (
    <div className="remsim">
      <div className="remsim-head">
        <span className="remsim-tag">WHAT-IF · REMEDIATION SIMULATOR</span>
        <span className="remsim-dev">{sim.component} · {sim.deviation}</span>
      </div>
      <p className="remsim-lead">
        Catch this deviation <strong>{sim.slip_avoided_weeks} weeks earlier</strong> and you
        avoid <strong>₹{crore(sim.cost_avoided_lakh)} crore</strong> of schedule slip —
        the lead-time number, made causal. Drag to see the cost of catching it late.
      </p>

      <svg viewBox={`0 0 ${W} ${H}`} className="remsim-chart" role="img"
           aria-label={`Schedule slip vs the week the deviation is caught. Catching at week ${catchWeek} yields ${point.slip_weeks} weeks of slip.`}>
        {/* zero-slip cliff (only meaningful for short-lead items) */}
        {cliff > 0 && (
          <g>
            <line x1={x(cliff)} y1={PAD_T} x2={x(cliff)} y2={H - PAD_B} className="remsim-cliff" />
            <text x={x(cliff) + 4} y={PAD_T + 10} className="remsim-cliff-lbl">zero-slip deadline · wk {cliff}</text>
          </g>
        )}
        {/* the slip curve */}
        <path d={areaPath} className="remsim-area" />
        <path d={path} className="remsim-line" />
        {/* scenario markers */}
        {([["commissioning", "var(--fault)"], ["pramaan", "var(--ok)"]] as const).map(([name, c]) => {
          const s = sim.scenarios[name];
          return (
            <g key={name}>
              <circle cx={x(s.catch_week)} cy={y(s.slip_weeks)} r={3.5} fill={c} />
              <text x={Math.min(x(s.catch_week), W - 12)} y={y(s.slip_weeks) - 7} className="remsim-marker" fill={c}
                    textAnchor={name === "commissioning" ? "end" : "start"}>
                {name === "pramaan" ? "Pramaan (upload)" : "Commissioning"}
              </text>
            </g>
          );
        })}
        {/* live cursor */}
        <line x1={x(catchWeek)} y1={PAD_T} x2={x(catchWeek)} y2={H - PAD_B} className="remsim-cursor" />
        <circle cx={x(catchWeek)} cy={y(point.slip_weeks)} r={4.5} className="remsim-dot" />
        {/* axes labels */}
        <text x={PAD_L} y={H - 8} className="remsim-axis">wk 0</text>
        <text x={W - 8} y={H - 8} className="remsim-axis" textAnchor="end">commissioning · wk {maxWeek}</text>
        <text x={4} y={y(maxSlip) + 4} className="remsim-axis">{maxSlip}w slip</text>
      </svg>

      <input
        type="range" min={0} max={maxWeek} step={1} value={catchWeek}
        onChange={(e) => setCatchWeek(Number(e.target.value))}
        className="remsim-range" aria-label="Week the deviation is caught"
      />
      <div className="remsim-readout">
        <div><span className="remsim-k">Caught at</span><span className="remsim-v">week {catchWeek}</span></div>
        <div><span className="remsim-k">Schedule slip</span><span className={`remsim-v ${point.slip_weeks > 0 ? "bad" : "good"}`}>{point.slip_weeks} wk</span></div>
        <div><span className="remsim-k">Cost of delay</span><span className={`remsim-v ${point.slip_weeks > 0 ? "bad" : "good"}`}>₹{crore(point.cost_lakh)} cr</span></div>
      </div>
      {sim.long_lead_trap && (
        <p className="remsim-note">
          <strong>Long-lead trap:</strong>{" "}
          the {sim.fix_lead_weeks}-week re-procurement exceeds the gap to the
          week-{sim.cx_planned_week} test, so slip can&apos;t reach zero — but catching on
          upload day still cuts it from {sim.scenarios.commissioning.slip_weeks} weeks
          to {sim.scenarios.pramaan.slip_weeks}.
        </p>
      )}
      <p className="remsim-assumption">{sim.assumption}</p>
    </div>
  );
}
