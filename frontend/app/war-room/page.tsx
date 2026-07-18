import Link from "../../components/AppLink";
import BlastRadiusExplorer from "../../components/BlastRadiusExplorer";
import { getRegisterSnapshot, getRemediation, getSchedule, getSupplyChain } from "../../lib/api";

export const revalidate = 600;

export const metadata = {
  title: "Intervention brief — Pramaan",
  description: "Prioritized EPC interventions with timing, schedule, and supply-chain assumptions.",
};

export default async function WarRoomPage() {
  const [snapshot, schedule, supply, remediation] = await Promise.all([
    getRegisterSnapshot(),
    getSchedule(),
    getSupplyChain(),
    getRemediation(),
  ]);
  const hero = snapshot.rows.find((row) => row.component === "UPS-02") ?? snapshot.rows[0];
  const shipments = [...supply.shipments].sort((a, b) => b.delivery_risk.score - a.delivery_risk.score).slice(0, 3);
  const scenarios = remediation.scenarios;

  return (
    <main id="main-content">
      <section className="route-hero intervention-hero shell">
        <p className="section-kicker">Intervention brief · Project Meghdoot</p>
        <h1>Decide what moves before the schedule does.</h1>
        <p>
          A composed operating view of the highest-consequence finding, its decision window, and the
          supply-chain conditions that determine whether recovery is still possible.
        </p>
        <div className="provenance-line"><span className={`provenance-dot provenance-${snapshot.provenance.kind}`} aria-hidden="true" />{snapshot.provenance.label}</div>
      </section>

      {hero ? (
        <section className="intervention-brief shell" aria-labelledby="priority-title">
          <div className="intervention-title">
            <p className="section-number">Priority 01</p>
            <div><span className={`severity severity-${hero.severity.toLowerCase()}`}>{hero.severity}</span><h2 id="priority-title">{hero.component} · {hero.parameter.replaceAll("_", " ")}</h2></div>
            <p>{hero.rationale}</p>
          </div>
          <dl className="decision-ledger">
            <div><dt>Caught</dt><dd>Week {hero.week_caught}</dd><dd className="ledger-note"><small>submittal review</small></dd></div>
            <div><dt>Test at risk</dt><dd>{hero.predicted_cx_test}</dd><dd className="ledger-note"><small>week {hero.week_fail}</small></dd></div>
            <div><dt>Action window</dt><dd>{hero.lead_time_weeks} weeks</dd><dd className="ledger-note"><small>review to test</small></dd></div>
            <div><dt>Fix lead</dt><dd>{remediation.fix_lead_weeks} weeks</dd><dd className="ledger-note"><small>scenario assumption</small></dd></div>
          </dl>
          <div className="decision-action">
            <div><p className="section-kicker">Recommended move</p><h3>Assign the CxA, issue the battery-autonomy RFI, and request a compliant revision with a dated delivery commitment.</h3></div>
            <Link className="button button-primary" href="/#resolve">Run resolution workflow</Link>
          </div>
        </section>
      ) : null}

      <section className="blast-section shell" aria-labelledby="blast-title">
        <div className="section-intro">
          <p className="section-number">Blast radius</p>
          <div>
            <p className="section-kicker">Live project-graph traversal</p>
            <h2 id="blast-title">What one deviation actually reaches.</h2>
          </div>
          <p>
            Pick a finding. The project graph answers with every commissioning test, milestone and
            long-lead supplier it touches — computed live, never staged.
          </p>
        </div>
        <BlastRadiusExplorer rows={snapshot.rows} />
      </section>

      <section className="intervention-grid shell" aria-label="Schedule and supply evidence">
        <article>
          <p className="section-number">Schedule exposure</p>
          <h2>{schedule.deviation_impact?.slip_weeks ?? "—"} weeks</h2>
          <p>Modeled ready-for-service slip if the current deviation set reaches downstream execution.</p>
          <dl>
            <div><dt>Baseline P80</dt><dd>{schedule.baseline.p80.toFixed(1)} wk</dd></div>
            <div><dt>At-risk P80</dt><dd>{schedule.deviation_impact?.at_risk_p80?.toFixed(1) ?? "—"} wk</dd></div>
          </dl>
        </article>
        <article>
          <p className="section-number">Timing consequence</p>
          <h2>{remediation.slip_avoided_weeks} weeks</h2>
          <p>Scenario difference between the Pramaan catch week and commissioning discovery.</p>
          <small>{remediation.assumption}</small>
        </article>
      </section>

      <section className="catch-week-section shell" aria-labelledby="catch-week-title">
        <div className="section-intro">
          <p className="section-number">When it is caught</p>
          <div>
            <p className="section-kicker">Same deviation, three discovery moments</p>
            <h2 id="catch-week-title">The catch week decides the cost.</h2>
          </div>
          <p>Deterministic remediation scenarios for the priority finding — flat until the zero-slip deadline (week {remediation.zero_slip_deadline_week}), then every week compounds.</p>
        </div>
        <ol className="catch-week-ledger">
          <li>
            <span className="catch-week-label">Design review</span>
            <span className="catch-week-week">week {scenarios.design_review.catch_week}</span>
            <span className="catch-week-out">{scenarios.design_review.slip_weeks} wk slip · ₹{scenarios.design_review.cost_lakh} lakh</span>
          </li>
          <li className="catch-week-pramaan">
            <span className="catch-week-label">Pramaan catch</span>
            <span className="catch-week-week">week {scenarios.pramaan.catch_week}</span>
            <span className="catch-week-out">{scenarios.pramaan.slip_weeks} wk slip · ₹{scenarios.pramaan.cost_lakh} lakh</span>
          </li>
          <li>
            <span className="catch-week-label">Commissioning discovery</span>
            <span className="catch-week-week">week {scenarios.commissioning.catch_week}</span>
            <span className="catch-week-out">{scenarios.commissioning.slip_weeks} wk slip · ₹{scenarios.commissioning.cost_lakh} lakh</span>
          </li>
        </ol>
      </section>

      <section className="shipment-section shell" aria-labelledby="shipments-title">
        <div className="shipment-head"><div><p className="section-kicker">Long-lead watch</p><h2 id="shipments-title">Supply conditions that can close the window.</h2></div><p>{supply.summary.at_risk} of {supply.summary.total} modeled shipments are currently at risk.</p></div>
        <div className="shipment-list">
          {shipments.map((shipment) => (
            <article key={shipment.id}>
              <div><strong>{shipment.equipment_type}</strong><span>{shipment.supplier} · {shipment.origin_country}</span></div>
              <div><span>Required</span><strong>Week {shipment.required_on_site_week}</strong></div>
              <div><span>P80 arrival</span><strong>Week {shipment.eta_p80.toFixed(1)}</strong></div>
              <div><span>Delivery risk</span><strong>{shipment.delivery_risk.score.toFixed(1)} / 100</strong></div>
            </article>
          ))}
        </div>
      </section>

      <section className="assumption-note shell"><strong>Scenario, not forecast truth.</strong><span>Schedule and cost edges are deterministic outputs under stated assumptions. They are decision support, not measured savings.</span></section>
    </main>
  );
}
