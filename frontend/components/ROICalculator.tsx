"use client";

import { useState } from "react";

const DEFAULTS = {
  projectValue: 800,
  reworkCostPerWeek: 12,
  weeksSaved: 149,
  deviations: 7,
  manualReviewDays: 45,
  aiReviewMinutes: 3,
};

export default function ROICalculator() {
  const [projectValue, setProjectValue] = useState(DEFAULTS.projectValue);

  const reworkAvoided = DEFAULTS.weeksSaved * DEFAULTS.reworkCostPerWeek;
  const scaledRework = Math.round(reworkAvoided * (projectValue / DEFAULTS.projectValue));
  const manualCost = Math.round(DEFAULTS.manualReviewDays * 8 * 150 / 1000);
  const aiCost = 2;
  const reviewSavings = manualCost - aiCost;
  const totalROI = scaledRework + reviewSavings;
  const paybackDays = Math.max(1, Math.round((aiCost * 1000) / (totalROI * 1000 / 365)));

  return (
    <div className="roi">
      <div className="roi-header">
        <div className="roi-badge">BUSINESS IMPACT</div>
        <div className="roi-desc">
          Quantified value from catching deviations early — before they become commissioning failures.
          Based on Project Meghdoot (₹800 Cr) with 7 deviations and 149 weeks of total lead time saved.
        </div>
      </div>

      <div className="roi-slider-row">
        <label className="roi-slider-label">
          Project value: <strong>₹{projectValue} Cr</strong>
        </label>
        <input
          type="range"
          min={200}
          max={3000}
          step={50}
          value={projectValue}
          onChange={(e) => setProjectValue(Number(e.target.value))}
          className="roi-slider"
        />
        <div className="roi-slider-range">
          <span>₹200 Cr</span>
          <span>₹3,000 Cr</span>
        </div>
      </div>

      <div className="roi-grid">
        <div className="roi-card roi-card-hero">
          <div className="roi-card-val" style={{ color: "var(--ok)" }}>₹{scaledRework.toLocaleString()} L</div>
          <div className="roi-card-label">Rework cost avoided</div>
          <div className="roi-card-detail">{DEFAULTS.weeksSaved} weeks × ₹{DEFAULTS.reworkCostPerWeek}L/week (scaled)</div>
        </div>
        <div className="roi-card">
          <div className="roi-card-val" style={{ color: "var(--lead)" }}>₹{reviewSavings.toLocaleString()} L</div>
          <div className="roi-card-label">Manual review savings</div>
          <div className="roi-card-detail">{DEFAULTS.manualReviewDays} person-days → {DEFAULTS.aiReviewMinutes} min AI review</div>
        </div>
        <div className="roi-card">
          <div className="roi-card-val" style={{ color: "var(--accent)" }}>{paybackDays}</div>
          <div className="roi-card-label">Days to payback</div>
          <div className="roi-card-detail">Platform cost recovered from first deviation caught</div>
        </div>
        <div className="roi-card roi-card-total">
          <div className="roi-card-val" style={{ color: "var(--warn)" }}>₹{totalROI.toLocaleString()} L</div>
          <div className="roi-card-label">Total value delivered</div>
          <div className="roi-card-detail">Per project, per cycle — multiplied across portfolio</div>
        </div>
      </div>

      <div className="roi-timeline">
        <div className="roi-timeline-title">Cost of delay — when deviations surface</div>
        <div className="roi-timeline-track">
          {[
            { week: "W11", label: "Pramaan catches it", cost: "₹0", color: "var(--ok)", highlight: true },
            { week: "W22", label: "Site inspection", cost: "₹3L rework", color: "var(--warn)", highlight: false },
            { week: "W38", label: "Commissioning", cost: "₹12L+ rework", color: "var(--fault)", highlight: false },
            { week: "W48", label: "Handover", cost: "₹50L+ schedule slip", color: "#ff1a1a", highlight: false },
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
