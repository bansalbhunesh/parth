"use client";
import { useEffect, useState, useMemo } from "react";
import { getRemediation, RemediationSim } from "../lib/api";

interface Props {
  sim?: RemediationSim;
}

export default function RemediationSimulator({ sim: propSim }: Props) {
  const [remediation, setRemediation] = useState<RemediationSim | null>(null);
  const [catchWeek, setCatchWeek] = useState(11);
  const [loading, setLoading] = useState(!propSim);

  useEffect(() => {
    if (propSim) {
      setRemediation(propSim);
      setCatchWeek(propSim.scenarios.pramaan.catch_week || 11);
      setLoading(false);
      return;
    }
    getRemediation("DEV-001", "meghdoot")
      .then((data) => {
        setRemediation(data);
        setCatchWeek(data.scenarios.pramaan.catch_week || 11);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [propSim]);

  const selectedPoint = useMemo(() => {
    if (!remediation) return null;
    const curve = remediation.curve || [];
    const closest = curve.reduce((prev, curr) => 
      Math.abs(curr.catch_week - catchWeek) < Math.abs(prev.catch_week - catchWeek) ? curr : prev
    , curve[0] || { catch_week: catchWeek, slip_weeks: 0, cost_lakh: 0 });
    return closest;
  }, [remediation, catchWeek]);

  if (loading) {
    return <div style={{ color: "#8a8f98", fontSize: 13, padding: 20 }}>Loading simulator data...</div>;
  }

  if (!remediation) {
    return <div style={{ color: "#ff4d4d", fontSize: 13, padding: 20 }}>Simulator data unavailable.</div>;
  }

  const costLakh = selectedPoint ? selectedPoint.cost_lakh : 0;
  const slipWeeks = selectedPoint ? selectedPoint.slip_weeks : 0;
  // Everything below is driven by the engine's numbers (fallback and live
  // data both ship them) so the badge, tiles, and footer can never disagree.
  const slipping = slipWeeks > 0;
  const cxWeek = Math.max(1, remediation.cx_planned_week || 38);
  const uploadWeek = remediation.scenarios?.pramaan?.catch_week ?? 11;
  const fixLead = remediation.fix_lead_weeks;

  return (
    <div className="remediation-simulator-card" style={{ padding: 20, border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, background: "rgba(255,255,255,0.02)", marginTop: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: "#fff" }}>🛠️ What-if Remediation Simulator</h3>
          <p style={{ margin: "4px 0 0", fontSize: 12.5, color: "#8a8f98" }}>
            Slide to adjust the <strong>catch week</strong> for the hero {remediation.component} deviation (requires {fixLead}-week fix lead).
          </p>
        </div>
        <span style={{ fontSize: 12, padding: "2px 8px", borderRadius: 4, background: slipping ? "rgba(239,68,68,0.15)" : "rgba(34,197,94,0.15)", color: slipping ? "#ef4444" : "#22c55e" }}>
          {slipping ? "🚨 Cost of Delay Active" : "✓ On Schedule"}
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 20 }}>
        <div style={{ background: "rgba(0,0,0,0.2)", padding: 12, borderRadius: 8, textAlign: "center" }}>
          <span style={{ display: "block", fontSize: 11, color: "#8a8f98", textTransform: "uppercase" }}>Triage Week</span>
          <strong style={{ display: "block", fontSize: 20, color: "#fff", marginTop: 4 }}>Week {catchWeek}</strong>
        </div>
        <div style={{ background: "rgba(0,0,0,0.2)", padding: 12, borderRadius: 8, textAlign: "center" }}>
          <span style={{ display: "block", fontSize: 11, color: "#8a8f98", textTransform: "uppercase" }}>Project Delay</span>
          <strong style={{ display: "block", fontSize: 20, color: slipWeeks > 0 ? "#ff4d4d" : "#22c55e", marginTop: 4 }}>
            {slipWeeks > 0 ? `+${slipWeeks} weeks` : "None"}
          </strong>
        </div>
        <div style={{ background: "rgba(0,0,0,0.2)", padding: 12, borderRadius: 8, textAlign: "center" }}>
          <span style={{ display: "block", fontSize: 11, color: "#8a8f98", textTransform: "uppercase" }}>Cost Impact</span>
          <strong style={{ display: "block", fontSize: 20, color: costLakh > 0 ? "#ff4d4d" : "#22c55e", marginTop: 4 }}>
            {costLakh > 0 ? `₹${costLakh} lakh` : "₹0"}
          </strong>
        </div>
      </div>

      <div style={{ marginBottom: 20 }}>
        <input
          type="range"
          min={0}
          max={cxWeek}
          value={catchWeek}
          onChange={(e) => setCatchWeek(Number(e.target.value))}
          style={{ width: "100%", height: 6, borderRadius: 3, outline: "none", cursor: "pointer" }}
          aria-label="Week the deviation is caught"
        />
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#8a8f98", marginTop: 8 }}>
          <span>Week 0 (Design Review)</span>
          <span style={{ color: "#35c98b" }}>Week {uploadWeek} (Pramaan Upload)</span>
          <span>Week {cxWeek} (Commissioning Test)</span>
        </div>
      </div>

      <div style={{ fontSize: 12.5, color: "#a1a8b5", lineHeight: 1.5, borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 12 }}>
        {!slipping ? (
          <span style={{ color: "#22c55e" }}>
            💡 <strong>Safe Window:</strong> Catching this deviation before the <strong>Week {remediation.zero_slip_deadline_week}</strong> deadline avoids all project schedule slip. Total savings vs commissioning catch: <strong>₹{remediation.cost_avoided_lakh} lakh</strong>.
          </span>
        ) : remediation.long_lead_trap ? (
          <span style={{ color: "#ffb020" }}>
            ⚠️ <strong>Long-lead trap:</strong> The {fixLead}-week re-procurement exceeds the gap to the Week-{cxWeek} commissioning test, so slip can&apos;t reach zero — but catching at Week {catchWeek} still cuts it to <strong>{slipWeeks} weeks</strong> (vs {remediation.scenarios.commissioning.slip_weeks} weeks if first caught at commissioning).
          </span>
        ) : (
          <span style={{ color: "#ffb020" }}>
            ⚠️ <strong>Slippage:</strong> Finding this after Week {remediation.zero_slip_deadline_week} leads to a <strong>{slipWeeks}-week</strong> delay in ready-for-service date because of the {fixLead}-week vendor replacement lead time.
          </span>
        )}
      </div>
    </div>
  );
}
