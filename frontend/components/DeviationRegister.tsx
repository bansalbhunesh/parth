import { Deviation } from "../lib/api";

export default function DeviationRegister({ rows }: { rows: Deviation[] }) {
  return (
    <div className="register-wrap">
      <table className="reg">
        <thead>
          <tr>
            <th>#</th>
            <th>Component</th>
            <th>Requirement</th>
            <th>Spec vs Submittal</th>
            <th>Standard</th>
            <th>Predicted Cx failure</th>
            <th>Lead</th>
            <th>Severity</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((d, i) => (
            <tr
              key={`${d.component}-${d.parameter}`}
              className={d.severity === "Critical" ? "row-critical" : ""}
            >
              <td className="val row-num">{i + 1}</td>
              <td className="val">{d.component}</td>
              <td>{d.parameter.replace(/_/g, " ")}</td>
              <td className="val">
                <span className="good">{String(d.required_value)}</span>
                {" → "}
                <span className="bad">
                  {String(d.provided_value)} {d.unit}
                </span>
              </td>
              <td className="cx">
                {d.standard_ref}
                <br />
                <span style={{ color: "var(--muted)" }}>{d.spec_clause}</span>
              </td>
              <td>
                <span className="cx">
                  {d.predicted_cx_test ?? "—"}
                  {d.predicted_cx_level ? ` · L${d.predicted_cx_level}` : ""}
                </span>
                <br />
                <span style={{ color: "var(--muted)", fontSize: 11 }}>
                  {d.predicted_cx_name}
                </span>
              </td>
              <td className="lead-cell">
                {d.lead_time_weeks != null ? (
                  <span className="lead-badge">{d.lead_time_weeks}w</span>
                ) : (
                  "—"
                )}
              </td>
              <td>
                <span className={`sev ${d.severity}`}>{d.severity}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 0 && (
        <div className="register-footer">
          Total savings: catching {rows.length} deviations an average of{" "}
          {Math.round(
            rows
              .filter((r) => r.lead_time_weeks != null)
              .reduce((a, r) => a + (r.lead_time_weeks ?? 0), 0) /
              rows.filter((r) => r.lead_time_weeks != null).length
          )}{" "}
          weeks early prevents rework, schedule delays, and commissioning failures.
        </div>
      )}
    </div>
  );
}
