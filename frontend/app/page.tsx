import Link from "../components/AppLink";
import RegisterExplorer from "../components/RegisterExplorer";
import ResolutionWorkflow from "../components/ResolutionWorkflow";
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

function DocumentPair() {
  return (
    <div className="doc-pair" aria-label="A specification clause and the vendor submittal line that deviates from it" role="img">
      <figure className="doc-sheet doc-sheet-spec" aria-hidden="true">
        <figcaption>
          <span className="doc-ref">SECTION 26 33 53 · STATIC UPS</span>
          <span className="doc-stamp doc-stamp-issued">Issued for construction</span>
        </figcaption>
        <div className="doc-lines">
          <p><span className="doc-clause">2.1</span> System configuration — distributed redundant, <strong>2N across two paths</strong></p>
          <p className="doc-line-marked"><span className="doc-clause">2.3</span> Battery autonomy at full load — not less than <strong>10 minutes, at end of life</strong></p>
          <p><span className="doc-clause">2.4</span> Efficiency at 100% load — ≥ 96.0%</p>
        </div>
      </figure>
      <figure className="doc-sheet doc-sheet-submittal" aria-hidden="true">
        <figcaption>
          <span className="doc-ref">SUBMITTAL APX-EL-0241 · REV B</span>
          <span className="doc-stamp doc-stamp-approval">For approval</span>
        </figcaption>
        <div className="doc-lines">
          <p><span className="doc-clause">2.3</span> System redundancy (per bus) — <strong className="doc-flag">N+1</strong></p>
          <p className="doc-line-marked"><span className="doc-clause">2.4</span> Battery autonomy at full load — <strong className="doc-flag">8 minutes</strong> (beginning of life @ 25 °C)</p>
          <p><span className="doc-clause">2.5</span> Online efficiency at 100% load — 96.5%</p>
        </div>
      </figure>
      <div className="doc-annotation" aria-hidden="true">
        <span className="doc-annotation-mark">Deviation</span>
        <span className="doc-annotation-note">IST-07 at risk · converges week 36</span>
      </div>
    </div>
  );
}

export default async function Page() {
  const snapshot = await getRegisterSnapshot();
  const hero = snapshot.rows.find((row) => row.component === "UPS-02") ?? snapshot.rows[0];
  const claims = PRODUCT_CLAIMS.benchmark;

  return (
    <main id="main-content">
      <section className="hero shell" aria-labelledby="hero-title">
        <div className="hero-grid">
          <div className="hero-copy">
            <div className="provenance-line">
              <span className={`provenance-dot provenance-${snapshot.provenance.kind}`} aria-hidden="true" />
              {snapshot.provenance.label}
            </div>
            <h1 id="hero-title">Find the deviation. Prove the consequence. Close it before commissioning.</h1>
            <p className="hero-lede">
              Pramaan reads the design basis and the vendor submittal the way a senior reviewer would —
              then keeps the requirement, the variance, the test at risk and the closure record attached to each other.
            </p>
            <div className="hero-actions">
              <Link className="button button-primary" href="/judge">Run the live analysis</Link>
              <a className="button button-secondary" href="#proof">Follow one finding</a>
            </div>
            <p className="provenance-description">{snapshot.provenance.description}</p>
          </div>
          <DocumentPair />
        </div>

        <ol className="judge-journey" aria-label="The 90-second review">
          <li>
            <Link href="/judge">
              <span className="journey-index">1</span>
              <span className="journey-body"><strong>Run the analysis</strong><small>Load the deviation demo and watch it reason live</small></span>
            </Link>
          </li>
          <li>
            <a href="#register">
              <span className="journey-index">2</span>
              <span className="journey-body"><strong>Open a dossier</strong><small>Any finding unfolds to its live blast radius</small></span>
            </a>
          </li>
          <li>
            <a href="#resolve">
              <span className="journey-index">3</span>
              <span className="journey-body"><strong>Close it with an RFI</strong><small>A real case against the API, audited end to end</small></span>
            </a>
          </li>
          <li>
            <Link href="/evidence">
              <span className="journey-index">4</span>
              <span className="journey-body"><strong>Verify every number</strong><small>Each claim travels with its limitation</small></span>
            </Link>
          </li>
        </ol>
      </section>

      {hero ? (
        <section className="section-block section-rule shell" id="proof" aria-labelledby="proof-title">
          <div className="section-intro">
            <p className="section-number">01 · Trace</p>
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
      ) : (
        <section className="section-block section-rule shell" id="proof" aria-labelledby="proof-title">
          <div className="section-intro">
            <p className="section-number">01 · Trace</p>
            <div>
              <p className="section-kicker">Register unavailable</p>
              <h2 id="proof-title">The evidence chain stays attached to the consequence.</h2>
            </div>
            <p>No finding could be loaded, and the page will not invent one. Open Evidence for the frozen benchmark record.</p>
          </div>
        </section>
      )}

      <section className="section-block section-ink" id="resolve" aria-labelledby="resolve-title">
        <div className="shell">
          <div className="section-intro section-intro-inverse">
            <p className="section-number">02 · Resolve</p>
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
          <p className="section-number">03 · Prioritize</p>
          <div>
            <p className="section-kicker">Commissioning-aware register</p>
            <h2 id="register-title">Review by consequence, not document order.</h2>
          </div>
          <p>
            {snapshot.rows.length} findings loaded from {snapshot.provenance.label.toLowerCase()}.
            Open any row: its dossier unfolds with the live blast radius from the project graph.
          </p>
        </div>
        <RegisterExplorer rows={snapshot.rows} />
        <div className="register-actions">
          <Link className="text-link" href="/judge">Run a new document comparison <span aria-hidden="true">→</span></Link>
          <Link className="text-link" href="/war-room">Open intervention analysis <span aria-hidden="true">→</span></Link>
        </div>
      </section>

      <section className="section-block proof-section shell" aria-labelledby="benchmark-title">
        <div className="section-intro">
          <p className="section-number">04 · Verify</p>
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
  );
}
