"use client";

import { useState } from "react";

// Expected-value model — mirrors docs/BUSINESS.md §2/§7 exactly (same formula,
// same low/base/high inputs, same reference 50 MW project). Do not hand-tune
// these numbers independently of that file; if the model changes, change it
// there first and port the constants here.
//
//   EV(months avoided) = P(>=1 critical-path catch) * months-avoided-if-critical
//   P(>=1 critical-path catch) = 1 - (1 - pCritical) ^ n
//   n = submittals * deviationPrevalence * incrementalRecall * adoption
//   EV(gross benefit) = EV(months avoided) * (capacityKW * marginPerKwMonth)
//   netEV = EV(gross benefit) - (licence + onboarding)
//
// Five of these eight inputs are unvalidated assumptions, not field data —
// see docs/BUSINESS.md §2 for which, and §9 for the pilot designed to
// replace them with measured numbers.
type Scenario = "low" | "base" | "high";

const SCENARIOS: Record<Scenario, {
  label: string;
  submittalsPer50MW: number;
  deviationPrevalence: number;
  incrementalRecall: number;
  adoption: number;
  pCritical: number;
  monthsIfCritical: number;
  marginPerKwMonth: number; // contribution margin at risk, not gross lease rate
  licence: number;
  onboarding: number;
}> = {
  low: {
    label: "Low", submittalsPer50MW: 400, deviationPrevalence: 0.08, incrementalRecall: 0.10,
    adoption: 0.40, pCritical: 0.05, monthsIfCritical: 0.5, marginPerKwMonth: 9,
    licence: 100_000, onboarding: 20_000,
  },
  base: {
    label: "Base", submittalsPer50MW: 800, deviationPrevalence: 0.15, incrementalRecall: 0.20,
    adoption: 0.65, pCritical: 0.12, monthsIfCritical: 1.0, marginPerKwMonth: 21,
    licence: 250_000, onboarding: 35_000,
  },
  high: {
    label: "High", submittalsPer50MW: 1500, deviationPrevalence: 0.25, incrementalRecall: 0.35,
    adoption: 0.90, pCritical: 0.25, monthsIfCritical: 3.0, marginPerKwMonth: 90,
    licence: 500_000, onboarding: 50_000,
  },
};

const MANUAL_REVIEW_DAYS = 45;
const AI_REVIEW_MINUTES = 3;

const fmtM = (n: number) => {
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  return abs >= 1_000_000 ? `${sign}$${(abs / 1_000_000).toFixed(2)}M` : `${sign}$${Math.round(abs / 1000)}K`;
};

function computeEV(capacityMW: number, s: (typeof SCENARIOS)[Scenario]) {
  const submittals = s.submittalsPer50MW * (capacityMW / 50);
  const n = submittals * s.deviationPrevalence * s.incrementalRecall * s.adoption;
  const pAtLeastOneCritical = 1 - Math.pow(1 - s.pCritical, n);
  const evMonths = pAtLeastOneCritical * s.monthsIfCritical;
  const marginPerMonth = capacityMW * 1000 * s.marginPerKwMonth;
  const evGrossBenefit = evMonths * marginPerMonth;
  const cost = s.licence + s.onboarding;
  const netEV = evGrossBenefit - cost;
  const ratio = evGrossBenefit / cost;
  return { n, pAtLeastOneCritical, evGrossBenefit, cost, netEV, ratio };
}

export default function ROICalculator() {
  const [capacityMW, setCapacityMW] = useState(50);
  const [scenario, setScenario] = useState<Scenario>("base");

  const s = SCENARIOS[scenario];
  const ev = computeEV(capacityMW, s);
  const netPositive = ev.netEV >= 0;

  return (
    <div className="roi">
      <div className="roi-header">
        <div className="roi-badge">BUSINESS IMPACT — EXPECTED VALUE, NOT A BEST CASE</div>
        <div className="roi-desc">
          India has committed &gt;$120B to data-centre build-out (KPMG, Jul 2026), and 9 in 10 large
          infrastructure builds slip schedule — most expensively at commissioning. This calculator
          multiplies the full probability chain (deviation prevalence × incremental catch rate over
          human review × adoption × chance a catch is critical-path) rather than presenting the size
          of the industry risk as the product&apos;s value. Full model, sources, and which inputs are
          still unvalidated assumptions: <code>docs/BUSINESS.md</code> §2/§7.
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

      <div className="roi-scenario-row" role="group" aria-label="Scenario">
        {(Object.keys(SCENARIOS) as Scenario[]).map((key) => (
          <button
            key={key}
            type="button"
            className={`roi-scenario-btn${scenario === key ? " roi-scenario-btn-active" : ""}`}
            aria-pressed={scenario === key}
            onClick={() => setScenario(key)}
          >
            {SCENARIOS[key].label}
          </button>
        ))}
        <span className="roi-scenario-hint">
          {scenario === "low" && "Pessimistic inputs — net expected value can be negative."}
          {scenario === "base" && "Our stated base-case assumptions (docs/BUSINESS.md §2)."}
          {scenario === "high" && "Optimistic inputs — upper end of the honest range."}
        </span>
      </div>

      <div className="roi-grid">
        <div className="roi-card roi-card-hero">
          <div className="roi-card-val" style={{ color: netPositive ? "var(--ok)" : "var(--fault)" }}>
            {fmtM(ev.netEV)}
          </div>
          <div className="roi-card-label">Net expected value — this project</div>
          <div className="roi-card-detail">EV gross benefit ({fmtM(ev.evGrossBenefit)}) − licence &amp; onboarding ({fmtM(ev.cost)})</div>
        </div>
        <div className="roi-card">
          <div className="roi-card-val" style={{ color: "var(--ok)" }}>≈ one RFI</div>
          <div className="roi-card-label">Cost to fix it on submittal day</div>
          <div className="roi-card-detail">Caught before procurement &amp; build — analysis ≈ paise</div>
        </div>
        <div className="roi-card roi-card-total">
          <div className="roi-card-val" style={{ color: netPositive ? "var(--warn)" : "var(--fault)" }}>
            {ev.ratio.toFixed(1)}×
          </div>
          <div className="roi-card-label">Expected gross-benefit / cost</div>
          <div className="roi-card-detail">vs {fmtM(ev.cost)} licence + onboarding, {scenario} case</div>
        </div>
        <div className="roi-card">
          <div className="roi-card-val" style={{ color: "var(--lead)" }}>{MANUAL_REVIEW_DAYS}d → {AI_REVIEW_MINUTES}m</div>
          <div className="roi-card-label">Manual review → Pramaan</div>
          <div className="roi-card-detail">Weeks of one engineer → minutes, full audit trail to the CxA</div>
        </div>
      </div>

      <div className="roi-timeline">
        <div className="roi-timeline-title">
          Expected schedule recovery — P(≥1 critical-path catch) × months avoided
        </div>
        <div className="roi-timeline-track">
          {[
            { week: "Day 1", label: "Submittal — Pramaan flags it", cost: "$0", color: "var(--ok)", highlight: true },
            { week: "n catches", label: "Expected incremental catches", cost: ev.n.toFixed(1), color: "var(--lead)", highlight: false },
            { week: "P(critical)", label: "≥1 sits on the critical path", cost: `${Math.round(ev.pAtLeastOneCritical * 100)}%`, color: "var(--warn)", highlight: false },
            { week: "EV benefit", label: "Expected gross benefit", cost: fmtM(ev.evGrossBenefit), color: netPositive ? "var(--ok)" : "var(--fault)", highlight: false },
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
