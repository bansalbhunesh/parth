import { Deviation } from "../lib/api";

export default function DeviationRegister({ rows }: { rows: Deviation[] }) {
  return (
    <table className="reg">
      <thead>
        <tr>
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
        {rows.map((d) => (
          <tr key={`${d.component}-${d.parameter}`}>
            <td className="val">{d.component}</td>
            <td>{d.parameter.replace(/_/g, " ")}</td>
            <td className="val">
              <span className="good">{d.required_value}</span>
              {" → "}
              <span className="bad">
                {d.provided_value} {d.unit}
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
              {d.lead_time_weeks != null ? `${d.lead_time_weeks}w` : "—"}
            </td>
            <td>
              <span className={`sev ${d.severity}`}>{d.severity}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
