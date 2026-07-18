"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { getBlastRadius, type BlastRadius, type Deviation } from "../lib/api";

// The demo corpus assigns each seeded deviation a stable id; the register rows
// carry only (component, parameter). This reference map joins the two so the
// dossier can request the live blast radius for the finding it shows.
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

function formatValue(value: string | number, unit: string) {
  return `${String(value)}${unit ? ` ${unit}` : ""}`;
}

function devKey(row: Deviation) {
  return `${row.component}/${row.parameter}`;
}

type BlastState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; data: BlastRadius }
  | { status: "unavailable" };

export default function RegisterExplorer({ rows }: { rows: Deviation[] }) {
  const [openKey, setOpenKey] = useState<string | null>(null);
  const [blast, setBlast] = useState<BlastState>({ status: "idle" });
  const closeRef = useRef<HTMLButtonElement>(null);

  const selected = rows.find((row) => devKey(row) === openKey) ?? null;

  useEffect(() => {
    if (!selected) return;
    closeRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpenKey(null);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [selected]);

  useEffect(() => {
    if (!selected) {
      setBlast({ status: "idle" });
      return;
    }
    const devId = DEV_IDS[devKey(selected)];
    if (!devId) {
      setBlast({ status: "unavailable" });
      return;
    }
    let alive = true;
    setBlast({ status: "loading" });
    getBlastRadius(devId).then((data) => {
      if (!alive) return;
      setBlast(data ? { status: "ready", data } : { status: "unavailable" });
    });
    return () => { alive = false; };
  }, [selected]);

  return (
    <>
      <div className="register-scroll" role="region" aria-label="Prioritized deviation register" tabIndex={0}>
        <table className="register-table">
          <thead>
            <tr>
              <th scope="col">Finding</th>
              <th scope="col">Variance</th>
              <th scope="col">Cx consequence</th>
              <th scope="col">Window</th>
              <th scope="col">Dossier</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 6).map((row) => (
              <tr key={devKey(row)}>
                <td>
                  <span className={`severity severity-${row.severity.toLowerCase()}`}>{row.severity}</span>
                  <strong>{row.component}</strong>
                  <small>{row.parameter.replaceAll("_", " ")}</small>
                </td>
                <td>
                  <span className="value-pair">
                    <del>{formatValue(row.provided_value, row.unit)}</del>
                    <span aria-hidden="true">→</span>
                    <ins>{formatValue(row.required_value, row.unit)}</ins>
                  </span>
                </td>
                <td>
                  <strong>{row.predicted_cx_test ?? "Review required"}</strong>
                  <small>{row.predicted_cx_name ?? "Commissioning acceptance check"}</small>
                </td>
                <td>
                  <strong>{row.lead_time_weeks ?? "—"} weeks</strong>
                  <small>Week {row.week_caught} → {row.week_fail ?? "—"}</small>
                </td>
                <td>
                  <button
                    type="button"
                    className="register-open"
                    onClick={() => setOpenKey(devKey(row))}
                    aria-haspopup="dialog"
                  >
                    Open<span className="visually-hidden"> dossier for {row.component} {row.parameter.replaceAll("_", " ")}</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected ? createPortal(
        <div className="drawer-root" role="presentation">
          <button
            className="drawer-backdrop"
            type="button"
            aria-label="Close the finding dossier"
            onClick={() => setOpenKey(null)}
          />
          <div
            className="drawer-panel dossier-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="dossier-title"
          >
            <div className="drawer-head">
              <div>
                <p className="drawer-kicker">
                  Finding dossier · {DEV_IDS[devKey(selected)] ?? "unmapped"}
                </p>
                <h3 id="dossier-title">
                  {selected.component} · {selected.parameter.replaceAll("_", " ")}
                </h3>
              </div>
              <button
                ref={closeRef}
                className="drawer-close"
                type="button"
                onClick={() => setOpenKey(null)}
                aria-label="Close dossier"
              >
                <span aria-hidden="true">✕</span>
              </button>
            </div>

            <div className="dossier-severity-row">
              <span className={`severity severity-${selected.severity.toLowerCase()}`}>{selected.severity}</span>
              <span className="dossier-clause">{selected.spec_clause} · {selected.standard_ref}</span>
            </div>

            <dl className="dossier-ledger">
              <div>
                <dt>Required</dt>
                <dd>{formatValue(selected.required_value, selected.unit)}</dd>
              </div>
              <div>
                <dt>Submitted</dt>
                <dd className="dossier-bad">{formatValue(selected.provided_value, selected.unit)}</dd>
              </div>
              <div>
                <dt>Test at risk</dt>
                <dd>{selected.predicted_cx_test ?? "—"}</dd>
              </div>
              <div>
                <dt>Decision window</dt>
                <dd>{selected.lead_time_weeks ?? "—"} weeks</dd>
              </div>
            </dl>

            {selected.rationale ? (
              <blockquote className="dossier-rationale">
                {selected.rationale}
                <cite>{selected.standard_ref} · clause {selected.spec_clause}</cite>
              </blockquote>
            ) : null}

            <div className="dossier-blast">
              <h4>Blast radius</h4>
              {blast.status === "loading" ? (
                <p className="dossier-blast-note">Querying the live project graph…</p>
              ) : null}
              {blast.status === "unavailable" ? (
                <p className="dossier-blast-note">
                  The project graph did not answer for this finding. Nothing is shown in its place.
                </p>
              ) : null}
              {blast.status === "ready" ? (
                <>
                  <dl className="dossier-ledger dossier-blast-ledger">
                    <div>
                      <dt>Reach</dt>
                      <dd>{blast.data.reach_size} nodes</dd>
                    </div>
                    <div>
                      <dt>Weeks at risk</dt>
                      <dd>{blast.data.weeks_at_risk}</dd>
                    </div>
                    <div>
                      <dt>Worst milestone slip</dt>
                      <dd>{blast.data.worst_milestone_slip} wk</dd>
                    </div>
                    <div>
                      <dt>Caught in time</dt>
                      <dd>{blast.data.caught_in_time ? "Yes" : "No — schedule at risk"}</dd>
                    </div>
                  </dl>
                  {blast.data.cx_tests_at_risk.length > 0 ? (
                    <p className="dossier-blast-list">
                      <span>Tests at risk</span>
                      {blast.data.cx_tests_at_risk.map((test) => test.label).join(" · ")}
                    </p>
                  ) : null}
                  {blast.data.suppliers.length > 0 ? (
                    <p className="dossier-blast-list">
                      <span>Long-lead suppliers</span>
                      {blast.data.suppliers
                        .map((supplier) => `${supplier.label}${supplier.lead_time_weeks ? ` (${supplier.lead_time_weeks}w)` : ""}`)
                        .join(" · ")}
                    </p>
                  ) : null}
                  <p className="dossier-blast-source">
                    Live traversal of the project graph — deviation → Cx test → schedule → supply.
                  </p>
                </>
              ) : null}
            </div>

            <div className="dossier-actions">
              <a className="button button-secondary" href="/war-room">Open intervention brief</a>
              <a className="text-link" href="/judge">Re-run the analysis <span aria-hidden="true">→</span></a>
            </div>
          </div>
        </div>,
        document.body,
      ) : null}
    </>
  );
}
