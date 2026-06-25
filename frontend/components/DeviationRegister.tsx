"use client";
import { useState, useMemo } from "react";
import { Deviation } from "../lib/api";

type SortKey = "component" | "severity" | "lead_time_weeks" | "parameter";
type SortDir = "asc" | "desc";

const SEV_ORDER: Record<string, number> = { Critical: 0, Major: 1, Minor: 2 };

export default function DeviationRegister({ rows }: { rows: Deviation[] }) {
  const [search, setSearch] = useState("");
  const [sevFilter, setSevFilter] = useState<string>("all");
  const [sortKey, setSortKey] = useState<SortKey>("severity");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const filtered = useMemo(() => {
    let result = [...rows];
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (d) =>
          d.component.toLowerCase().includes(q) ||
          d.parameter.replace(/_/g, " ").toLowerCase().includes(q) ||
          d.standard_ref.toLowerCase().includes(q) ||
          (d.rationale || "").toLowerCase().includes(q)
      );
    }
    if (sevFilter !== "all") {
      result = result.filter((d) => d.severity === sevFilter);
    }
    result.sort((a, b) => {
      let cmp = 0;
      if (sortKey === "severity") {
        cmp = (SEV_ORDER[a.severity] ?? 3) - (SEV_ORDER[b.severity] ?? 3);
      } else if (sortKey === "lead_time_weeks") {
        cmp = (a.lead_time_weeks ?? 0) - (b.lead_time_weeks ?? 0);
      } else if (sortKey === "component") {
        cmp = a.component.localeCompare(b.component);
      } else {
        cmp = a.parameter.localeCompare(b.parameter);
      }
      return sortDir === "desc" ? -cmp : cmp;
    });
    return result;
  }, [rows, search, sevFilter, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "lead_time_weeks" ? "desc" : "asc");
    }
  };

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const sortIcon = (key: SortKey) =>
    sortKey === key ? (sortDir === "asc" ? " ↑" : " ↓") : "";

  const critCount = rows.filter((r) => r.severity === "Critical").length;
  const majCount = rows.filter((r) => r.severity === "Major").length;
  const minCount = rows.filter((r) => r.severity === "Minor").length;

  return (
    <div>
      <div className="register-controls">
        <input
          className="register-search"
          type="text"
          placeholder="Search components, parameters, standards..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="register-filters">
          {[
            { key: "all", label: `All (${rows.length})` },
            { key: "Critical", label: `Critical (${critCount})` },
            { key: "Major", label: `Major (${majCount})` },
            { key: "Minor", label: `Minor (${minCount})` },
          ].map((f) => (
            <button
              key={f.key}
              className={`register-filter ${sevFilter === f.key ? "register-filter-active" : ""}`}
              onClick={() => setSevFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="register-wrap">
        <table className="reg">
          <thead>
            <tr>
              <th>#</th>
              <th className="reg-sortable" onClick={() => toggleSort("component")}>
                Component{sortIcon("component")}
              </th>
              <th className="reg-sortable" onClick={() => toggleSort("parameter")}>
                Requirement{sortIcon("parameter")}
              </th>
              <th>Spec vs Submittal</th>
              <th>Standard</th>
              <th>Predicted Cx failure</th>
              <th className="reg-sortable" onClick={() => toggleSort("lead_time_weeks")}>
                Lead{sortIcon("lead_time_weeks")}
              </th>
              <th className="reg-sortable" onClick={() => toggleSort("severity")}>
                Severity{sortIcon("severity")}
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((d, i) => {
              const id = `${d.component}-${d.parameter}`;
              const isExpanded = expanded.has(id);
              return (
                <tr
                  key={id}
                  className={`${d.severity === "Critical" ? "row-critical" : ""} reg-clickable`}
                  onClick={() => toggleExpand(id)}
                >
                  <td className="val row-num">{i + 1}</td>
                  <td className="val">{d.component}</td>
                  <td>
                    {d.parameter.replace(/_/g, " ")}
                    {isExpanded && d.rationale && (
                      <div className="reg-rationale">{d.rationale}</div>
                    )}
                  </td>
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
              );
            })}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="register-empty">No deviations match your filters.</div>
        )}
        {filtered.length > 0 && (
          <div className="register-footer">
            Showing {filtered.length} of {rows.length} deviations. Total savings:{" "}
            {filtered
              .filter((r) => r.lead_time_weeks != null)
              .reduce((a, r) => a + (r.lead_time_weeks ?? 0), 0)}{" "}
            weeks of avoided commissioning rework. Click any row to expand rationale.
          </div>
        )}
      </div>
    </div>
  );
}
