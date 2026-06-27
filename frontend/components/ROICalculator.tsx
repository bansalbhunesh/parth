"use client";

import { useState } from "react";

// Defaults match docs/BUSINESS.md (cited market + impact model).
const LEASE_PER_KW_MONTH = 180;   // USD/kW·month — industry benchmark (India lower; order-of-magnitude)
const DELAY_WEEKS = 4;            // slip one undetected deviation can trigger (BUSINESS.md: 2–8 wks)
const MANUAL_REVIEW_DAYS = 45;
const AI_REVIEW_MINUTES = 3;
const PRAMAAN_LICENCE_USD = 250_000; // per-project licence (BUSINESS.md: $100–500K)

const fmtM = (n: number) =>
  n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(1)}M` : `$${Math.round(n / 1000)}K`;

export default function ROICalculator() {
  const [capacityMW, setCapacityMW] = useState(50);

  const monthlyRevenue = capacityMW * 1000 * LEASE_PER_KW_MONTH; // $/month at risk during a slip
  const slipCost = Math.round(monthlyRevenue * (DELAY_WEEKS / 4.33)); // one deviation-driven slip
  const roiMultiple = Math.max(1, Math.round(slipCost / PRAMAAN_LICENCE_USD));

  return (
    <div className="roi">
      <div className="roi-header">
        <div className="roi-badge">BUSINESS IMPACT</div>
        <div className="roi-desc">
          India is investing ~$30B toward 2 GW of data-centre capacity by 2026, and 9 in 10 large
          builds slip schedule — most expensively at commissioning. Catching one vendor deviation on
          submittal day, not months later, is the value. Sources &amp; model: <code>docs/BUSINESS.md</code>.
        </div>
      </div>

      <div className="roi-slider-row">
        <label className="roi-slider-label">
          Data-hall capacity: <strong>{capacityMW} MW</strong>
        </label>
        <input
          type="range"
          min={10}
          max={300}
          step={5}
          value={capacityMW}
          onChange={(e) => setCapacityMW(Number(e.target.value))}
          className="roi-slider"
        />
        <div className="roi-slider-range">
          <span>10 MW</span>
          <span>300 MW</span>
        </div>
      </div>

      <div className="roi-grid">
        <div className="roi-card roi-card-hero">
          <div className="roi-card-val" style={{ color: "var(--fault)" }}>{fmtM(slipCost)}</div>
          <div className="roi-card-label">Revenue at risk — one undetected deviation</div>
          <div className="roi-card-detail">{capacityMW} MW × ${LEASE_PER_KW_MONTH}/kW·mo × {DELAY_WEEKS}-wk slip</div>
        </div>
        <div className="roi-card">
          <div className="roi-card-val" style={{ color: "var(--ok)" }}>≈ one RFI</div>
          <div className="roi-card-label">Cost to fix it on submittal day</div>
          <div className="roi-card-detail">Caught before procurement &amp; build — analysis ≈ paise</div>
        </div>
        <div className="roi-card roi-card-total">
          <div className="roi-card-val" style={{ color: "var(--warn)" }}>{roiMultiple}×</div>
          <div className="roi-card-label">ROI on a single prevented slip</div>
          <div className="roi-card-detail">vs a ~$250K/project licence</div>
        </div>
        <div className="roi-card">
          <div className="roi-card-val" style={{ color: "var(--lead)" }}>{MANUAL_REVIEW_DAYS}d → {AI_REVIEW_MINUTES}m</div>
          <div className="roi-card-label">Manual review → Pramaan</div>
          <div className="roi-card-detail">Weeks of one engineer → minutes, full audit trail to the CxA</div>
        </div>
      </div>

      <div className="roi-timeline">
        <div className="roi-timeline-title">Cost of delay — the later it surfaces, the more it costs</div>
        <div className="roi-timeline-track">
          {[
            { week: "Day 1", label: "Submittal — Pramaan flags it", cost: "$0", color: "var(--ok)", highlight: true },
            { week: "Procure", label: "Non-compliant gear ordered", cost: "12–18mo lead", color: "var(--warn)", highlight: false },
            { week: "Commission", label: "Test fails, schedule slips", cost: fmtM(slipCost * 0.5), color: "var(--fault)", highlight: false },
            { week: "Go-live", label: "Lost revenue + penalties", cost: fmtM(slipCost), color: "#ff1a1a", highlight: false },
          ].map((stage, i) => (
            <div key={i} className={`roi-timeline-stage ${stage.highlight ? "roi-timeline-highlight" : ""}`}>
              <div className="roi-timeline-week" style={{ color: stage.color }}>{stage.week}</div>
              <div className="roi-timeline-dot" style={{ background: stage.color }} />
              <div className="roi-timeline-label">{stage.label}</div>
              <div className="roi-timeline-cost" style={{ color: stage.color }}>{stage.cost}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
