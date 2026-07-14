import Link from "next/link";
import ThemeToggle from "../../components/ThemeToggle";
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

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <header className="site-header">
        <Link href="/" className="wordmark" aria-label="Pramaan home">Pramaan<span aria-hidden="true">/</span></Link>
        <nav className="site-nav" aria-label="Intervention navigation">
          <Link href="/">Overview</Link>
          <Link href="/judge">Analyze</Link>
          <Link href="/evidence">Evidence</Link>
        </nav>
        <ThemeToggle />
      </header>

      <main id="main-content">
      <section className="route-hero intervention-hero shell">
        <p className="section-kicker">Intervention brief · Project Meghdoot</p>
        <h1>Decide what moves before the schedule does.</h1>
        <p>
          A composed operating view of the highest-consequence finding, its decision window, and the supply-chain conditions that determine whether recovery is still possible.
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

      <footer className="site-footer shell">
        <div><Link href="/" className="wordmark">Pramaan<span aria-hidden="true">/</span></Link><p>Evidence to resolution for consequential infrastructure.</p></div>
        <nav aria-label="Footer navigation"><Link href="/">Overview</Link><Link href="/judge">Analyze</Link><Link href="/evidence">Evidence</Link></nav>
      </footer>
    </>
  );
}
