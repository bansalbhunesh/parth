"use client";

import { useEffect, useState } from "react";
import { getBlastRadius, type BlastRadius, type Deviation } from "../lib/api";

const DEV_IDS: Record<string, string> = {
  "UPS-02/battery_runtime_min": "DEV-001",
  "UPS-02/efficiency_pct": "DEV-002",
  "GEN-FUEL/onsite_fuel_hours": "DEV-003",
  "GEN-01/start_time_sec": "DEV-004",
  "COOL-LOOP/redundancy": "DEV-005",
  "COOL-LOOP/delta_t_c": "DEV-006",
  "SWGR-MV/short_circuit_rating_ka": "DEV-007",
  "SWGR-MV/arc_flash_rating": "DEV-008",
  "CABLE-DC/fire_rating": "DEV-009",
  "CABLE-DC/max_bundle_size": "DEV-010",
  "BMS/critical_alarm_points": "DEV-011",
  "BMS/monitoring_redundancy": "DEV-012",
  "FLOOR/load_rating_kpa": "DEV-013",
  "FLOOR/height_mm": "DEV-014",
};

function devKey(row: Deviation) {
  return `${row.component}/${row.parameter}`;
}

type BlastState =
  | { status: "loading" }
  | { status: "ready"; data: BlastRadius }
  | { status: "unavailable" };

/**
 * Interactive consequence traversal: pick a finding, and the live project
 * graph answers with everything it reaches — Cx tests, milestones, suppliers.
 */
export default function BlastRadiusExplorer({ rows }: { rows: Deviation[] }) {
  const mapped = rows.filter((row) => DEV_IDS[devKey(row)]).slice(0, 5);
  const [selectedKey, setSelectedKey] = useState<string | null>(mapped[0] ? devKey(mapped[0]) : null);
  const [blast, setBlast] = useState<BlastState>({ status: "loading" });

  const selected = mapped.find((row) => devKey(row) === selectedKey) ?? null;

  useEffect(() => {
    if (!selected) return;
    let alive = true;
    setBlast({ status: "loading" });
    getBlastRadius(DEV_IDS[devKey(selected)]).then((data) => {
      if (!alive) return;
      setBlast(data ? { status: "ready", data } : { status: "unavailable" });
    });
    return () => { alive = false; };
  }, [selected]);

  if (mapped.length === 0) {
    return (
      <p className="blast-empty">
        No register finding maps to the demo project graph right now, so no radius is shown.
      </p>
    );
  }

  return (
    <div className="blast-explorer">
      <div className="blast-picker" role="group" aria-label="Choose a finding to trace">
        {mapped.map((row) => {
          const key = devKey(row);
          const active = key === selectedKey;
          return (
            <button
              key={key}
              type="button"
              className={`blast-chip ${active ? "is-active" : ""}`}
              aria-pressed={active}
              onClick={() => setSelectedKey(key)}
            >
              <span className="blast-chip-id">{DEV_IDS[key]}</span>
              <span className="blast-chip-name">{row.component} · {row.parameter.replaceAll("_", " ")}</span>
            </button>
          );
        })}
      </div>

      <div className="blast-result" aria-live="polite">
        {blast.status === "loading" ? (
          <p className="blast-note">Traversing the live project graph…</p>
        ) : null}
        {blast.status === "unavailable" ? (
          <p className="blast-note">
            The project graph did not answer. Nothing is simulated in its place — retry when the API is reachable.
          </p>
        ) : null}
        {blast.status === "ready" && selected ? (
          <>
            <dl className="blast-ledger">
              <div><dt>Graph reach</dt><dd>{blast.data.reach_size} nodes</dd></div>
              <div><dt>Weeks at risk</dt><dd>{blast.data.weeks_at_risk}</dd></div>
              <div><dt>Cx test week</dt><dd>{blast.data.cx_planned_week}</dd></div>
              <div><dt>Fix complete by</dt><dd>week {blast.data.fix_complete_week}</dd></div>
              <div><dt>Worst milestone slip</dt><dd>{blast.data.worst_milestone_slip} wk</dd></div>
              <div>
                <dt>Caught in time</dt>
                <dd className={blast.data.caught_in_time ? "blast-ok" : "blast-bad"}>
                  {blast.data.caught_in_time ? "Yes" : "No"}
                </dd>
              </div>
            </dl>
            <div className="blast-tree">
              <div className="blast-branch">
                <span className="blast-branch-label">Commissioning tests at risk</span>
                <ul>
                  {blast.data.cx_tests_at_risk.length > 0
                    ? blast.data.cx_tests_at_risk.map((test) => <li key={test.id}>{test.label}</li>)
                    : <li>None reached</li>}
                </ul>
              </div>
              <div className="blast-branch">
                <span className="blast-branch-label">Milestones</span>
                <ul>
                  {blast.data.milestones.length > 0
                    ? blast.data.milestones.map((milestone) => (
                      <li key={milestone.id}>
                        {milestone.label}
                        {milestone.planned_week != null ? ` · planned wk ${milestone.planned_week}` : ""}
                        {milestone.slip_weeks > 0 ? ` · slips ${milestone.slip_weeks} wk` : ""}
                      </li>
                    ))
                    : <li>None reached</li>}
                </ul>
              </div>
              <div className="blast-branch">
                <span className="blast-branch-label">Long-lead suppliers</span>
                <ul>
                  {blast.data.suppliers.length > 0
                    ? blast.data.suppliers.map((supplier) => (
                      <li key={supplier.id}>
                        {supplier.label}
                        {supplier.lead_time_weeks != null ? ` · ${supplier.lead_time_weeks} wk lead` : ""}
                      </li>
                    ))
                    : <li>None reached</li>}
                </ul>
              </div>
            </div>
            <p className="blast-source">
              Live traversal: deviation → equipment → Cx test → schedule task → milestone → supplier.
            </p>
          </>
        ) : null}
      </div>
    </div>
  );
}
