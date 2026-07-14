"use client";
import { useState, useEffect } from "react";
import { getProjects, getMultiProjectEval, type ProjectSummary, type MultiProjectEval } from "../lib/api";

const TIER_COLORS: Record<string, string> = {
  "Uptime Tier IV": "#ef4444",
  "Uptime Tier III": "#f59e0b",
  "Uptime Tier II": "#22c55e",
  "EN 50600 Class 3": "#3b82f6",
  "GB 50174 Grade A": "#a855f7",
};

function tierColor(tier: string) {
  return TIER_COLORS[tier] || "#64748b";
}

export default function MultiProjectDashboard() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [evalData, setEvalData] = useState<MultiProjectEval | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    getProjects().then((p) => {
      setProjects(p);
      setLoaded(true);
    });
    getMultiProjectEval().then(setEvalData);
  }, []);

  const agg = evalData?.aggregate;
  const perProject = evalData?.per_project || {};

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {agg && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: 12,
        }}>
          {[
            { label: "Projects", value: agg.projects, color: "#36d6e7" },
            { label: "Total Deviations", value: agg.total_deviations, color: "#ef4444" },
            { label: "Precision", value: agg.aggregate_precision.toFixed(3), color: "#22c55e" },
            { label: "Recall", value: agg.aggregate_recall.toFixed(3), color: "#22c55e" },
            { label: "F1 Score", value: agg.aggregate_f1.toFixed(3), color: "#22c55e" },
            { label: "Cx Accuracy", value: agg.aggregate_cx_accuracy.toFixed(3), color: "#3b82f6" },
            { label: "Lead-time window", value: `${agg.total_lead_time_weeks}w`, color: "#f59e0b" },
          ].map((m) => (
            <div key={m.label} style={{
              background: "#111827",
              border: "1px solid #1f2937",
              borderRadius: 8,
              padding: "14px 12px",
              textAlign: "center",
            }}>
              <div style={{ fontSize: 10, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1, fontFamily: "var(--font-mono)" }}>{m.label}</div>
              <div style={{ fontSize: 26, fontWeight: 800, color: m.color, fontFamily: "var(--font-mono)", marginTop: 4 }}>{m.value}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ fontSize: 11, color: "#9ca3af", lineHeight: 1.5 }}>
        These 12 projects are a <strong>synthetic breadth check</strong>: the corpus recovers all seeded
        deviations <em>by construction</em>, so precision/recall/F1 read 1.000 — a plumbing check, not an
        accuracy claim. The measured accuracy signal is the frozen <code>ps4_external_v1</code> benchmark
        (v1.2): recall 0.862, precision 0.953, F1 0.905. Lead-time weeks are an illustrative scenario.
      </div>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
        gap: 16,
      }}>
        {projects.map((p) => {
          const pe = perProject[p.id];
          return (
            <div key={p.id} style={{
              background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
              border: "1px solid #334155",
              borderRadius: 10,
              padding: 20,
              position: "relative",
              overflow: "hidden",
            }}>
              <div style={{
                position: "absolute", top: 0, left: 0, right: 0, height: 3,
                background: tierColor(p.tier),
              }} />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: "#e2e8f0" }}>{p.name}</div>
                  <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 2 }}>{p.location}</div>
                </div>
                <span style={{
                  fontSize: 10,
                  padding: "3px 8px",
                  borderRadius: 4,
                  background: tierColor(p.tier) + "22",
                  color: tierColor(p.tier),
                  fontWeight: 600,
                  fontFamily: "var(--font-mono)",
                  whiteSpace: "nowrap",
                }}>
                  {p.tier}
                </span>
              </div>

              <div style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: 8,
                marginTop: 16,
              }}>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: "#36d6e7", fontFamily: "var(--font-mono)" }}>{p.capacity_mw}</div>
                  <div style={{ fontSize: 9, color: "#64748b", textTransform: "uppercase" }}>MW</div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: "#ef4444", fontFamily: "var(--font-mono)" }}>{p.deviations}</div>
                  <div style={{ fontSize: 9, color: "#64748b", textTransform: "uppercase" }}>Deviations</div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: "#f59e0b", fontFamily: "var(--font-mono)" }}>{pe?.total_lead_weeks || "—"}</div>
                  <div style={{ fontSize: 9, color: "#64748b", textTransform: "uppercase" }}>Weeks saved</div>
                </div>
              </div>

              {pe && (
                <div style={{
                  display: "flex",
                  gap: 6,
                  marginTop: 14,
                  justifyContent: "center",
                }}>
                  {[
                    { label: "P", value: pe.precision },
                    { label: "R", value: pe.recall },
                    { label: "F1", value: pe.f1 },
                    { label: "Cx", value: pe.cx_accuracy },
                  ].map((s) => (
                    <span key={s.label} style={{
                      fontSize: 10,
                      padding: "2px 6px",
                      borderRadius: 3,
                      background: s.value === 1 ? "#16a34a22" : "#dc262622",
                      color: s.value === 1 ? "#4ade80" : "#f87171",
                      fontFamily: "var(--font-mono)",
                      fontWeight: 600,
                    }}>
                      {s.label}={s.value.toFixed(2)}
                    </span>
                  ))}
                </div>
              )}

              <div style={{
                fontSize: 10,
                color: "#475569",
                marginTop: 10,
                fontFamily: "var(--font-mono)",
                textAlign: "center",
              }}>
                {p.systems} systems &middot; {p.id}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{
        fontSize: 11,
        color: "#8896ab",
        textAlign: "center",
        fontStyle: "italic",
      }}>
        {loaded && projects.length > 0 ? (
          <>
            Breadth check: {projects.length} projects,{" "}
            {projects.reduce((s, p) => s + p.deviations, 0)} seeded deviations,{" "}
            {new Set(projects.map(p => p.tier)).size} tier standards,{" "}
            {new Set(projects.map(p => p.location.split(",").pop()?.trim())).size} countries
            {" "}— pipeline scaling and reproduction, not an accuracy claim
          </>
        ) : (
          <>Loading the multi-project portfolio&hellip;</>
        )}
      </div>
    </div>
  );
}
