"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  BlastRadius,
  Deviation,
  ProjectGraph,
  ProjectSummary,
  RemediationSim,
  ScheduleAnalysis,
  Shipment,
  SupplyChainAnalysis,
} from "../lib/api";

function devId(index: number): string {
  return `DEV-${String(index + 1).padStart(3, "0")}`;
}

function sevWeight(severity: Deviation["severity"]): number {
  if (severity === "Critical") return 3;
  if (severity === "Major") return 2;
  return 1;
}

function fmt(value: number | null | undefined, suffix = ""): string {
  if (value == null || Number.isNaN(value)) return "-";
  return `${Math.round(value)}${suffix}`;
}

function moneyLakh(value: number): string {
  if (value >= 100) return `Rs ${(value / 100).toFixed(1)} cr`;
  return `Rs ${Math.round(value)} lakh`;
}

function nodeKindCounts(graph: ProjectGraph): Array<[string, number]> {
  return Object.entries(graph.stats.by_kind).sort((a, b) => b[1] - a[1]).slice(0, 7);
}

export default function WarRoomConsole({
  deviations,
  schedule,
  supply,
  graph,
  remediation,
  projects,
  apiBase,
}: {
  deviations: Deviation[];
  schedule: ScheduleAnalysis;
  supply: SupplyChainAnalysis;
  graph: ProjectGraph;
  remediation: RemediationSim;
  projects: ProjectSummary[];
  apiBase: string;
}) {
  const ranked = useMemo(() => {
    return deviations
      .map((d, index) => ({ d, index, id: devId(index) }))
      .sort((a, b) => {
        const aw = (a.d.lead_time_weeks ?? 0) + sevWeight(a.d.severity) * 10;
        const bw = (b.d.lead_time_weeks ?? 0) + sevWeight(b.d.severity) * 10;
        return bw - aw;
      });
  }, [deviations]);

  const [selected, setSelected] = useState(ranked[0]?.id ?? "DEV-001");
  const [catchWeek, setCatchWeek] = useState(remediation.scenarios.pramaan.catch_week);
  const [selectedRemediation, setSelectedRemediation] = useState<RemediationSim | null>(remediation);
  const [blastRadius, setBlastRadius] = useState<BlastRadius | null>(null);
  const [loadingGraph, setLoadingGraph] = useState(false);

  const selectedItem = ranked.find((item) => item.id === selected) ?? ranked[0];
  const selectedDeviation = selectedItem?.d;

  useEffect(() => {
    let alive = true;
    setLoadingGraph(true);
    Promise.all([
      fetch(`${apiBase}/projects/meghdoot/remediation/${selected}`, { cache: "no-store" })
        .then((response) => (response.ok ? response.json() : null))
        .catch(() => null),
      fetch(`${apiBase}/projects/meghdoot/blast-radius/${selected}`, { cache: "no-store" })
        .then((response) => (response.ok ? response.json() : null))
        .catch(() => null),
    ]).then(([remediationPayload, blastPayload]) => {
      if (!alive) return;
      setSelectedRemediation(
        remediationPayload?.available && remediationPayload?.scenarios
          ? remediationPayload as RemediationSim
          : null,
      );
      setBlastRadius(blastPayload?.available ? blastPayload as BlastRadius : null);
      setLoadingGraph(false);
    });
    return () => {
      alive = false;
    };
  }, [apiBase, selected]);

  const intervention = useMemo(() => {
    const activeRemediation = selectedRemediation ?? remediation;
    const fixLead = selectedRemediation?.fix_lead_weeks ?? selectedDeviation?.lead_time_weeks ?? 0;
    const failWeek = selectedDeviation?.week_fail ?? selectedRemediation?.cx_planned_week ?? remediation.cx_planned_week;
    const slipWeeks = Math.max(0, catchWeek + fixLead - failWeek);
    const costLakh = slipWeeks * activeRemediation.cost_per_week_lakh;
    const savedVsCommissioning = Math.max(0, activeRemediation.scenarios.commissioning.slip_weeks - slipWeeks);
    return { fixLead, failWeek, slipWeeks, costLakh, savedVsCommissioning, activeRemediation };
  }, [catchWeek, remediation, selectedDeviation, selectedRemediation]);

  const lateShipments = useMemo(() => {
    return [...supply.shipments].sort((a, b) => b.delivery_risk.score - a.delivery_risk.score).slice(0, 4);
  }, [supply.shipments]);

  const topProjects = useMemo(() => {
    return [...projects]
      .map((p) => ({ ...p, riskDensity: p.deviations / Math.max(1, p.systems) }))
      .sort((a, b) => b.riskDensity - a.riskDensity)
      .slice(0, 6);
  }, [projects]);

  const totalLead = deviations.reduce((sum, d) => sum + (d.lead_time_weeks ?? 0), 0);
  const critical = deviations.filter((d) => d.severity === "Critical").length;
  const averageLead = deviations.length ? totalLead / deviations.length : 0;

  return (
    <section className="wr-wrap" aria-label="Experimental commissioning war room">
      <header className="wr-hero">
        <div className="wr-status">
          <span>Experiment branch</span>
          <strong>Intervention console</strong>
        </div>
        <div>
          <p className="wr-kicker">Deviation to test failure to schedule exposure to action decision</p>
          <h1>Commissioning War Room</h1>
          <p className="wr-copy">
            A judge should not have to imagine the impact. Pick a deviation, move the catch week,
            and watch Pramaan translate review timing into slip, cost exposure, supplier risk,
            and the evidence chain that can be audited.
          </p>
        </div>
      </header>

      <div className="wr-command-grid">
        <article className="wr-panel wr-panel-tall">
          <div className="wr-panel-head">
            <div>
              <p className="wr-label">Live triage queue</p>
              <h2>Findings ranked by failure leverage</h2>
            </div>
            <span className="wr-chip">{deviations.length} deviations</span>
          </div>
          <div className="wr-queue">
            {ranked.slice(0, 8).map(({ d, id }) => (
              <button
                className={`wr-finding ${selected === id ? "is-active" : ""}`}
                key={id}
                onClick={() => {
                  setSelected(id);
                  setCatchWeek(d.week_caught);
                  setSelectedRemediation(null);
                  setBlastRadius(null);
                }}
                type="button"
              >
                <span className={`wr-sev ${d.severity.toLowerCase()}`}>{d.severity}</span>
                <strong>{id} / {d.component}</strong>
                <span>{d.parameter.replace(/_/g, " ")}</span>
                <em>{fmt(d.lead_time_weeks, " wk")} action window</em>
              </button>
            ))}
          </div>
        </article>

        <article className="wr-panel wr-panel-wide">
          <div className="wr-panel-head">
            <div>
              <p className="wr-label">Selected failure thread</p>
              <h2>{selectedDeviation ? `${selected} / ${selectedDeviation.component}` : "No finding selected"}</h2>
            </div>
            <span className={`wr-chip ${selectedDeviation?.severity.toLowerCase() ?? ""}`}>
              {loadingGraph ? "loading graph" : selectedDeviation?.severity ?? "-"}
            </span>
          </div>

          {selectedDeviation && (
            <>
              <div className="wr-thread">
                <div>
                  <span>Review catches</span>
                  <strong>Week {catchWeek}</strong>
                </div>
                <i aria-hidden="true" />
                <div>
                  <span>Fix lead</span>
                  <strong>{fmt(intervention.fixLead, " wk")}</strong>
                </div>
                <i aria-hidden="true" />
                <div className={intervention.slipWeeks > 0 ? "danger" : "ok"}>
                  <span>{selectedDeviation.predicted_cx_test ?? "Cx test"}</span>
                  <strong>Week {intervention.failWeek}</strong>
                </div>
              </div>

              <label className="wr-slider">
                <span>Intervention week</span>
                <input
                  type="range"
                  min={0}
                  max={Math.max(52, intervention.failWeek + 12)}
                  value={catchWeek}
                  onChange={(event) => setCatchWeek(Number(event.target.value))}
                />
              </label>

              <div className="wr-impact">
                <div>
                  <span>Predicted slip</span>
                  <strong className={intervention.slipWeeks > 0 ? "danger" : "ok"}>
                    {fmt(intervention.slipWeeks, " wk")}
                  </strong>
                </div>
                <div>
                  <span>Cost exposure</span>
                  <strong>{moneyLakh(intervention.costLakh)}</strong>
                </div>
                <div>
                  <span>Saved vs commissioning catch</span>
                  <strong className="ok">{fmt(intervention.savedVsCommissioning, " wk")}</strong>
                </div>
              </div>

              <div className="wr-evidence">
                <p><strong>Required:</strong> {String(selectedDeviation.required_value)} {selectedDeviation.unit}</p>
                <p><strong>Submitted:</strong> {String(selectedDeviation.provided_value)} {selectedDeviation.unit}</p>
                <p><strong>Standard:</strong> {selectedDeviation.standard_ref} / {selectedDeviation.spec_clause}</p>
                <p><strong>Failure mode:</strong> {selectedDeviation.rationale ?? "backend rationale unavailable"}</p>
              </div>

              <div className="wr-playbook">
                <div className="wr-playbook-head">
                  <p className="wr-label">Action playbook</p>
                  <span>{blastRadius ? "live graph response" : "derived fallback"}</span>
                </div>
                <div className="wr-playbook-grid">
                  <div>
                    <strong>{blastRadius?.cx_tests_at_risk[0]?.id ?? selectedDeviation.predicted_cx_test ?? "Cx test"}</strong>
                    <span>test at risk</span>
                  </div>
                  <div>
                    <strong>{fmt(blastRadius?.weeks_at_risk ?? intervention.slipWeeks, " wk")}</strong>
                    <span>weeks exposed</span>
                  </div>
                  <div>
                    <strong>{blastRadius?.suppliers[0]?.label ?? "supplier path unknown"}</strong>
                    <span>supplier exposure</span>
                  </div>
                  <div>
                    <strong>{blastRadius?.milestones[0]?.label ?? "RFS impact scenario"}</strong>
                    <span>milestone threatened</span>
                  </div>
                </div>
              </div>
            </>
          )}
        </article>

        <article className="wr-panel">
          <p className="wr-label">Portfolio pulse</p>
          <div className="wr-score">
            <strong>{fmt(averageLead, " wk")}</strong>
            <span>mean action window</span>
          </div>
          <div className="wr-mini-grid">
            <div><strong>{critical}</strong><span>critical</span></div>
            <div><strong>{fmt(schedule.deviation_impact?.slip_weeks, " wk")}</strong><span>worst-case slip</span></div>
            <div><strong>{fmt(supply.summary.at_risk)}</strong><span>supply risks</span></div>
          </div>
        </article>

        <article className="wr-panel">
          <p className="wr-label">Graph anatomy</p>
          <div className="wr-score">
            <strong>{graph.stats.nodes}</strong>
            <span>nodes / {graph.stats.edges} edges</span>
          </div>
          <div className="wr-kind-bars">
            {nodeKindCounts(graph).map(([kind, count]) => (
              <div className="wr-kind" key={kind}>
                <span>{kind}</span>
                <b style={{ width: `${Math.max(8, (count / graph.stats.nodes) * 100)}%` }} />
                <em>{count}</em>
              </div>
            ))}
          </div>
        </article>
      </div>

      <div className="wr-lower-grid">
        <article className="wr-panel">
          <div className="wr-panel-head">
            <div>
              <p className="wr-label">Supplier exposure</p>
              <h2>Long-lead risks that make findings expensive</h2>
            </div>
            <span className="wr-chip">{supply.summary.at_risk} at risk</span>
          </div>
          <div className="wr-shipments">
            {lateShipments.map((shipment: Shipment) => (
              <div className="wr-shipment" key={shipment.id}>
                <div>
                  <strong>{shipment.equipment_type}</strong>
                  <span>{shipment.supplier} / {shipment.origin_country}</span>
                </div>
                <meter min={0} max={1} value={shipment.delivery_risk.score} />
                <em>{Math.round(shipment.p_late * 100)}% late</em>
              </div>
            ))}
          </div>
        </article>

        <article className="wr-panel">
          <div className="wr-panel-head">
            <div>
              <p className="wr-label">Synthetic portfolio stress</p>
              <h2>Where the corpus is loudest</h2>
            </div>
            <span className="wr-chip">breadth, not field validation</span>
          </div>
          <div className="wr-projects">
            {topProjects.map((project) => (
              <div className="wr-project" key={project.id}>
                <div>
                  <strong>{project.name}</strong>
                  <span>{project.location}</span>
                </div>
                <b>{project.deviations}</b>
                <i style={{ width: `${Math.min(100, project.riskDensity * 100)}%` }} />
              </div>
            ))}
          </div>
        </article>
      </div>

      <footer className="wr-footnote">
        Experimental surface on a protected branch. Schedule and cost are deterministic scenario math,
        not a field-validated forecast. The useful unit is the direction of action: catch earlier, reduce slip.
      </footer>
    </section>
  );
}
