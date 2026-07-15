import Link from "next/link";
import ThemeToggle from "../../components/ThemeToggle";
import { getHealth } from "../../lib/api";
import { BENCHMARK_LIMITATION, PRODUCT_CLAIMS } from "../../lib/claims";

export const revalidate = 0;

export const metadata = {
  title: "Evidence and limitations — Pramaan",
  description: "Frozen benchmark claims, current deployment status, verification, and limitations.",
};

const REPO = "https://github.com/bansalbhunesh/parth";
const FILE = `${REPO}/blob/main`;

function Status({ label, value, state }: { label: string; value: string; state: "good" | "warn" | "muted" }) {
  return (
    <div className="evidence-status-row">
      <span className={`status-mark status-${state}`} aria-hidden="true" />
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export default async function EvidencePage() {
  const health = await getHealth();
  const benchmark = PRODUCT_CLAIMS.benchmark;
  const live = health !== null;

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <header className="site-header">
        <Link href="/" className="wordmark" aria-label="Pramaan home">Pramaan<span aria-hidden="true">/</span></Link>
        <nav className="site-nav" aria-label="Evidence navigation">
          <Link href="/">Overview</Link>
          <Link href="/judge">Analyze</Link>
          <Link href="/war-room">Interventions</Link>
        </nav>
        <ThemeToggle />
      </header>

      <main id="main-content">
      <section className="route-hero evidence-hero shell">
        <p className="section-kicker">Evidence · provenance · limitations</p>
        <h1>Every headline number should survive a second question.</h1>
        <p>
          This page separates frozen benchmark evidence from live deployment status and keeps the limitation next to the claim it qualifies.
        </p>
        <nav className="evidence-index" aria-label="Evidence sections">
          <a href="#deployment">Deployment</a>
          <a href="#benchmark">Benchmark</a>
          <a href="#verification">Verification</a>
          <a href="#limitations">Limitations</a>
          <a href="#links">Sources</a>
        </nav>
      </section>

      <section className="evidence-section shell" id="deployment" aria-labelledby="deployment-title">
        <div className="evidence-section-head">
          <p className="section-number">01 / Deployment</p>
          <div><p className="section-kicker">Fetched for this request</p><h2 id="deployment-title">Current service state</h2></div>
          <span className={`deployment-badge ${live ? "is-reached" : "is-unreached"}`}>{live ? "API reached" : "API not reached"}</span>
        </div>
        {!live ? <p className="evidence-callout">The API did not respond within the page timeout. Frozen benchmark evidence remains available below; no unavailable capability is shown as live.</p> : null}
        <dl className="evidence-status-list">
          <Status label="Deployed commit" value={health?.commit ?? "unavailable"} state={live ? "good" : "muted"} />
          <Status label="Analysis provider" value={health?.llm?.ready ? "model provider ready" : live ? "deterministic floor only" : "unavailable"} state={health?.llm?.ready ? "good" : live ? "warn" : "muted"} />
          <Status label="OCR" value={health?.ocr_available ? "available" : live ? "not installed" : "unavailable"} state={health?.ocr_available ? "good" : live ? "warn" : "muted"} />
          <Status label="Authentication" value={health?.security?.auth_required ? "token required" : live ? "open demo mode" : "unavailable"} state={live ? "good" : "muted"} />
          <Status label="Rate limiting" value={health?.security?.rate_limit_enabled ? "enabled" : live ? "disabled" : "unavailable"} state={health?.security?.rate_limit_enabled ? "good" : live ? "warn" : "muted"} />
        </dl>
      </section>

      <section className="evidence-section shell" id="benchmark" aria-labelledby="benchmark-title">
        <div className="evidence-section-head">
          <p className="section-number">02 / Benchmark</p>
          <div><p className="section-kicker">{benchmark.name} · frozen v{benchmark.version}</p><h2 id="benchmark-title">Detection evidence</h2></div>
          <span className="deployment-badge">Frozen record</span>
        </div>
        <dl className="evidence-ledger">
          <div><dt>Semantic recall</dt><dd>{benchmark.recall.toFixed(3)}</dd><dd className="ledger-note"><small>mean of three repeat runs</small></dd></div>
          <div><dt>Precision</dt><dd>{benchmark.precision.toFixed(3)}</dd><dd className="ledger-note"><small>semantic match criterion</small></dd></div>
          <div><dt>F1</dt><dd>{benchmark.f1.toFixed(3)}</dd><dd className="ledger-note"><small>precision/recall balance</small></dd></div>
          <div><dt>False-alert rate</dt><dd>{benchmark.falseAlerts} / {benchmark.cleanNegatives}</dd><dd className="ledger-note"><small>clean-negative controls</small></dd></div>
          <div><dt>Rule baseline recall</dt><dd>{benchmark.ruleRecall.toFixed(3)}</dd><dd className="ledger-note"><small>deterministic comparator</small></dd></div>
          <div><dt>Corpus</dt><dd>{benchmark.pairs} pairs</dd><dd className="ledger-note"><small>{benchmark.labels} labels · {benchmark.systems} systems</small></dd></div>
        </dl>
        <p className="evidence-callout"><strong>Boundary:</strong> {BENCHMARK_LIMITATION}</p>
      </section>

      <section className="evidence-section shell" id="verification" aria-labelledby="verification-title">
        <div className="evidence-section-head">
          <p className="section-number">03 / Verification</p>
          <div><p className="section-kicker">Current repository</p><h2 id="verification-title">What is checked</h2></div>
        </div>
        <div className="verification-list">
          <div><strong>{PRODUCT_CLAIMS.verification.backendTests}</strong><span>backend tests collected in the current tree</span></div>
          <div><strong>{PRODUCT_CLAIMS.verification.frontendTests}</strong><span>active-component tests with branch coverage</span></div>
          <div><strong>{PRODUCT_CLAIMS.verification.browserJourneys}</strong><span>production-mode journeys across five browser/device projects</span></div>
          <div><strong>Typed</strong><span>strict frontend typecheck and production build</span></div>
          <div><strong>End to end</strong><span>document analysis, keyboard, links, responsive layout, and resolution workflow</span></div>
          <div><strong>Fail closed</strong><span>configured auth, case secrets, bounded LLM capacity, and case-scoped webhooks</span></div>
        </div>
      </section>

      <section className="evidence-section shell" id="limitations" aria-labelledby="limitations-title">
        <div className="evidence-section-head">
          <p className="section-number">04 / Limits</p>
          <div><p className="section-kicker">Deliberately explicit</p><h2 id="limitations-title">What this prototype does not prove</h2></div>
        </div>
        <ul className="limitations-list">
          <li><strong>No field-validation claim.</strong><span>The frozen corpus is primarily team-authored and is not customer outcome data.</span></li>
          <li><strong>Reviewer adjudication is incomplete.</strong><span>The second independent label review remains pending.</span></li>
          <li><strong>Local case persistence is single-instance.</strong><span>SQLite is honest prototype persistence, not multi-region durability.</span></li>
          <li><strong>Provider availability varies.</strong><span>The interface states whether analysis used a model, deterministic rules, or was unavailable.</span></li>
        </ul>
      </section>

      <section className="evidence-section shell" id="links" aria-labelledby="links-title">
        <div className="evidence-section-head">
          <p className="section-number">05 / Sources</p>
          <div><p className="section-kicker">Primary repository records</p><h2 id="links-title">Open the evidence</h2></div>
        </div>
        <div className="source-links">
          <a href={REPO} target="_blank" rel="noreferrer"><strong>GitHub repository ↗</strong><span>Source, history, and runnable project</span></a>
          <a href={`${FILE}/benchmarks/ps4_external_v1/reports/benchmark_card.json`} target="_blank" rel="noreferrer"><strong>Frozen benchmark card ↗</strong><span>Machine-readable v1.2 record</span></a>
          <a href={`${FILE}/benchmarks/ps4_external_v1/BENCHMARK_PROTOCOL.md`} target="_blank" rel="noreferrer"><strong>Benchmark protocol ↗</strong><span>Scoring, freezing, and repeat-run protocol</span></a>
          <a href={`${FILE}/data/samples/real/PROVENANCE.md`} target="_blank" rel="noreferrer"><strong>Corpus provenance ↗</strong><span>Source-document lineage</span></a>
          <a href={`${FILE}/docs/VALIDATION.md`} target="_blank" rel="noreferrer"><strong>Validation dossier ↗</strong><span>Practitioner evidence and constraints</span></a>
          <a href={`${FILE}/docs/DATA_HANDLING.md`} target="_blank" rel="noreferrer"><strong>Data handling ↗</strong><span>Retention and security boundaries</span></a>
          <a href={`${FILE}/docs/SECURITY_DEMO_RUNBOOK.md`} target="_blank" rel="noreferrer"><strong>Security runbook ↗</strong><span>Deployment controls and verification</span></a>
          <a href={`${FILE}/README.md`} target="_blank" rel="noreferrer"><strong>Reproduction guide ↗</strong><span>Install, run, and test</span></a>
        </div>
      </section>

      </main>

      <footer className="site-footer shell">
        <div><Link href="/" className="wordmark">Pramaan<span aria-hidden="true">/</span></Link><p>Evidence to resolution for consequential infrastructure.</p></div>
        <nav aria-label="Footer navigation"><Link href="/">Overview</Link><Link href="/judge">Analyze</Link><Link href="/war-room">Interventions</Link></nav>
      </footer>
    </>
  );
}
