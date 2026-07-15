import Link from "../components/AppLink";
import ResolutionWorkflow from "../components/ResolutionWorkflow";
import ThemeToggle from "../components/ThemeToggle";
import { BENCHMARK_LIMITATION, PRODUCT_CLAIMS } from "../lib/claims";
import { Deviation, getRegisterSnapshot } from "../lib/api";

export const revalidate = 600;

function formatValue(value: string | number, unit: string) {
  return `${String(value)}${unit ? ` ${unit}` : ""}`;
}

function EvidencePath({ finding }: { finding: Deviation }) {
  const steps = [
    {
      key: "01",
      label: "Requirement",
      value: `${formatValue(finding.required_value, finding.unit)} minimum`,
      note: finding.spec_clause,
    },
    {
      key: "02",
      label: "Submittal",
      value: `${formatValue(finding.provided_value, finding.unit)} proposed`,
      note: "Vendor revision B",
    },
    {
      key: "03",
      label: "Consequence",
      value: `${finding.predicted_cx_test ?? "Cx test"} at week ${finding.week_fail ?? "—"}`,
      note: finding.standard_ref,
    },
    {
      key: "04",
      label: "Decision window",
      value: `${finding.lead_time_weeks ?? "—"} weeks to act`,
      note: "Before commissioning",
    },
  ];

  return (
    <ol className="evidence-path" aria-label="Evidence to consequence trace">
      {steps.map((step) => (
        <li key={step.key}>
          <span className="path-number">{step.key}</span>
          <div>
            <span className="path-label">{step.label}</span>
            <strong>{step.value}</strong>
            <small>{step.note}</small>
          </div>
        </li>
      ))}
    </ol>
  );
}

function RegisterTable({ rows }: { rows: Deviation[] }) {
  return (
    <div className="register-scroll" role="region" aria-label="Prioritized deviation register" tabIndex={0}>
      <table className="register-table">
        <thead>
          <tr>
            <th scope="col">Finding</th>
            <th scope="col">Variance</th>
            <th scope="col">Cx consequence</th>
            <th scope="col">Window</th>
            <th scope="col">Evidence</th>
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 6).map((row) => (
            <tr key={`${row.component}-${row.parameter}`}>
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
                <strong>{row.spec_clause}</strong>
                <small>{row.standard_ref}</small>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default async function Page() {
  const snapshot = await getRegisterSnapshot();
  const hero = snapshot.rows.find((row) => row.component === "UPS-02") ?? snapshot.rows[0];
  const claims = PRODUCT_CLAIMS.benchmark;

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <header className="site-header">
        <Link href="/" className="wordmark" aria-label="Pramaan home">
          Pramaan<span aria-hidden="true">/</span>
        </Link>
        <nav className="site-nav" aria-label="Primary navigation">
          <a href="#proof">Trace</a>
          <a href="#resolve">Resolve</a>
          <a href="#register">Register</a>
          <Link href="/evidence">Evidence</Link>
        </nav>
        <ThemeToggle />
      </header>

      <main id="main-content">
      <section className="hero shell" aria-labelledby="hero-title">
        <div className="hero-copy">
          <div className="provenance-line">
            <span className={`provenance-dot provenance-${snapshot.provenance.kind}`} aria-hidden="true" />
            {snapshot.provenance.label}
          </div>
          <h1 id="hero-title">Find the deviation. Prove the consequence. Close it before commissioning.</h1>
          <p className="hero-lede">
            Pramaan turns a specification mismatch into a cited, owned decision: the requirement, the vendor variance, the test at risk, and the record that closes it.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#proof">Follow one finding</a>
            <Link className="button button-secondary" href="/judge">Analyze documents</Link>
          </div>
          <p className="provenance-description">{snapshot.provenance.description}</p>
        </div>

        {hero ? (
          <aside className="hero-dossier" aria-label="Priority finding">
            <div className="dossier-meta">
              <span>Priority finding</span>
              <span className={`severity severity-${hero.severity.toLowerCase()}`}>{hero.severity}</span>
            </div>
            <p className="dossier-id">{hero.component} · {hero.spec_clause}</p>
            <h2>{hero.parameter.replaceAll("_", " ")}</h2>
            <div className="dossier-values">
              <div><span>Required</span><strong>{formatValue(hero.required_value, hero.unit)}</strong></div>
              <div><span>Submitted</span><strong>{formatValue(hero.provided_value, hero.unit)}</strong></div>
            </div>
            <p>{hero.rationale}</p>
            <div className="dossier-foot">
              <strong>{hero.lead_time_weeks} weeks</strong>
              <span>between review and {hero.predicted_cx_test}</span>
            </div>
          </aside>
        ) : (
          <aside className="hero-dossier dossier-unavailable" role="status">
            <p className="section-kicker">Register unavailable</p>
            <h2>No finding could be loaded.</h2>
            <p>The page will not invent a live result. Open Evidence for the frozen benchmark record.</p>
          </aside>
        )}
      </section>

      {hero ? (
        <section className="section-block section-rule shell" id="proof" aria-labelledby="proof-title">
          <div className="section-intro">
            <p className="section-number">01 / Trace</p>
            <div>
              <p className="section-kicker">One finding, end to end</p>
              <h2 id="proof-title">The evidence chain stays attached to the consequence.</h2>
            </div>
            <p>Every step answers the next reviewer’s question without turning the interface into a wall of metrics.</p>
          </div>
          <EvidencePath finding={hero} />
          <blockquote className="evidence-quote">
            <span>Decision basis</span>
            “{hero.rationale}”
            <cite>{hero.standard_ref} · clause {hero.spec_clause}</cite>
          </blockquote>
        </section>
      ) : null}

      <section className="section-block section-ink" id="resolve" aria-labelledby="resolve-title">
        <div className="shell">
          <div className="section-intro section-intro-inverse">
            <p className="section-number">02 / Resolve</p>
            <div>
              <p className="section-kicker">Finding to closure</p>
              <h2 id="resolve-title">A finding only matters when someone owns the next action.</h2>
            </div>
            <p>Run the protected case workflow against the API. Failed steps remain visibly failed; successful steps are written to the case audit log.</p>
          </div>
          <ResolutionWorkflow />
        </div>
      </section>

      <section className="section-block shell" id="register" aria-labelledby="register-title">
        <div className="section-intro">
          <p className="section-number">03 / Prioritize</p>
          <div>
            <p className="section-kicker">Commissioning-aware register</p>
            <h2 id="register-title">Review by consequence, not document order.</h2>
          </div>
          <p>{snapshot.rows.length} findings loaded from {snapshot.provenance.label.toLowerCase()}. The six highest-priority rows are shown here.</p>
        </div>
        <RegisterTable rows={snapshot.rows} />
        <div className="register-actions">
          <Link className="text-link" href="/judge">Run a new document comparison <span aria-hidden="true">→</span></Link>
          <Link className="text-link" href="/war-room">Open intervention analysis <span aria-hidden="true">→</span></Link>
        </div>
      </section>

      <section className="section-block proof-section shell" aria-labelledby="benchmark-title">
        <div className="section-intro">
          <p className="section-number">04 / Verify</p>
          <div>
            <p className="section-kicker">Frozen benchmark · v{claims.version}</p>
            <h2 id="benchmark-title">The claim and its boundary travel together.</h2>
          </div>
          <p>{BENCHMARK_LIMITATION}</p>
        </div>
        <dl className="proof-ledger">
          <div><dt>Semantic recall</dt><dd>{claims.recall.toFixed(3)}</dd><dd className="ledger-note"><small>mean of three repeat runs</small></dd></div>
          <div><dt>Precision / F1</dt><dd>{claims.precision.toFixed(3)} / {claims.f1.toFixed(3)}</dd><dd className="ledger-note"><small>{claims.labels} frozen labels</small></dd></div>
          <div><dt>False alerts</dt><dd>{claims.falseAlerts} / {claims.cleanNegatives}</dd><dd className="ledger-note"><small>clean-negative controls</small></dd></div>
          <div><dt>Automated verification</dt><dd>{PRODUCT_CLAIMS.verification.backendTests} + {PRODUCT_CLAIMS.verification.frontendTests} + {PRODUCT_CLAIMS.verification.browserJourneys}</dd><dd className="ledger-note"><small>backend · frontend · browser journeys</small></dd></div>
        </dl>
        <Link className="button button-secondary" href="/evidence">Inspect sources and limitations</Link>
      </section>

      </main>

      <footer className="site-footer shell">
        <div>
          <Link href="/" className="wordmark">Pramaan<span aria-hidden="true">/</span></Link>
          <p>Evidence to resolution for consequential infrastructure.</p>
        </div>
        <nav aria-label="Footer navigation">
          <Link href="/judge">Analyze</Link>
          <Link href="/evidence">Evidence</Link>
          <Link href="/war-room">Interventions</Link>
          <a href="https://github.com/bansalbhunesh/parth" target="_blank" rel="noreferrer">Source ↗</a>
        </nav>
      </footer>
    </>
  );
}
