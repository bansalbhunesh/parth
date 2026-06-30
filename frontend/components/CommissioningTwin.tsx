"use client";

import { CxPlan, Deviation } from "../lib/api";

export default function CommissioningTwin({
  cxPlan,
  deviations,
}: {
  cxPlan: CxPlan;
  deviations: Deviation[];
}) {
  const atRiskTests = new Set(
    deviations
      .map((d) => d.predicted_cx_test)
      .filter((t): t is string => t != null)
  );

  const levelColors: Record<number, string> = {
    1: "#8a96a8",
    2: "#5b8cff",
    3: "#ffb020",
    4: "#ff4d4d",
    5: "#35c98b",
  };

  const currentWeek = 11;
  const maxWeek = 52;

  return (
    <div className="cx-twin">
      <div className="cx-timeline-header">
        <div className="cx-legend">
          {Object.entries(cxPlan.levels).map(([lvl, desc]) => (
            <span key={lvl} className="cx-legend-item">
              <span
                className="cx-dot"
                style={{ background: levelColors[Number(lvl)] }}
              />
              L{lvl} {desc.split("(")[0].trim()}
            </span>
          ))}
        </div>
      </div>

      <div className="cx-gantt">
        <div className="cx-gantt-header">
          {Array.from({ length: 13 }, (_, i) => i * 4).map((w) => (
            <div
              key={w}
              className="cx-week-mark"
              style={{ left: `${(w / maxWeek) * 100}%` }}
            >
              <span>W{w}</span>
            </div>
          ))}
          <div
            className="cx-now-line"
            style={{ left: `${(currentWeek / maxWeek) * 100}%` }}
          >
            <span>NOW W{currentWeek}</span>
          </div>
        </div>

        <div className="cx-gantt-body">
          {cxPlan.tests.map((test) => {
            const isAtRisk = atRiskTests.has(test.id);
            const left = (test.scheduled_week / maxWeek) * 100;
            const devForTest = deviations.find(
              (d) => d.predicted_cx_test === test.id
            );
            return (
              <div key={test.id} className={`cx-row ${isAtRisk ? "at-risk" : ""}`}>
                <div className="cx-row-label">
                  <span className="cx-test-id">{test.id}</span>
                  <span className="cx-test-name">{test.name}</span>
                </div>
                <div className="cx-row-bar">
                  <div
                    className={`cx-bar ${isAtRisk ? "cx-bar-risk" : "cx-bar-ok"}`}
                    style={{
                      left: `${left - 1}%`,
                      background: isAtRisk
                        ? "var(--fault)"
                        : levelColors[test.level] || "var(--muted)",
                    }}
                  >
                    <span className="cx-bar-week">W{test.scheduled_week}</span>
                  </div>
                  {isAtRisk && devForTest && (
                    <div
                      className="cx-risk-link"
                      style={{
                        left: `${(currentWeek / maxWeek) * 100}%`,
                        width: `${left - (currentWeek / maxWeek) * 100 - 1}%`,
                      }}
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="cx-risk-summary">
        <div className="cx-risk-title">At-risk commissioning tests</div>
        <div className="cx-risk-cards">
          {deviations
            .filter((d) => d.predicted_cx_test)
            .map((d, i) => (
              <div
                key={`${d.component}-${d.parameter}-${i}`}
                className="cx-risk-card"
              >
                <div className="cx-risk-test">
                  <span className="cx-risk-id">{d.predicted_cx_test}</span>
                  <span className={`sev ${d.severity}`}>{d.severity}</span>
                </div>
                <div className="cx-risk-name">{d.predicted_cx_name}</div>
                <div className="cx-risk-detail">
                  {d.component}: {String(d.provided_value)} {d.unit} vs{" "}
                  {String(d.required_value)} {d.unit} required
                </div>
                <div className="cx-risk-lead">
                  {d.lead_time_weeks != null && (
                    <span className="lead-badge">{d.lead_time_weeks}w early</span>
                  )}
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
