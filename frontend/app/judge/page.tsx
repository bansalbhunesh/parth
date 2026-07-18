import Link from "../../components/AppLink";
import AnalyzePanel from "../../components/AnalyzePanel";
import { BENCHMARK_LIMITATION, PRODUCT_CLAIMS } from "../../lib/claims";

export const revalidate = 600;

export const metadata = {
  title: "Analyze documents — Pramaan",
  description: "Compare a design basis and vendor submittal with explicit analysis provenance.",
};

export default function JudgePage() {
  const benchmark = PRODUCT_CLAIMS.benchmark;

  return (
    <main id="main-content">
      <section className="route-hero shell">
        <p className="section-kicker">Document analysis · explicit provenance</p>
        <h1>Put the requirement and the proposal side by side.</h1>
        <p>
          Upload two documents or use the controlled text fixtures. Each result states whether it came
          from a live model, deterministic rules, or an unavailable analysis path.
        </p>
      </section>

      <section className="analysis-stage shell" aria-labelledby="analysis-title">
        <div className="analysis-stage-head">
          <div>
            <p className="section-number">Live workspace</p>
            <h2 id="analysis-title">Compare documents</h2>
          </div>
          <p>No result is relabelled as live when the API or model is unavailable.</p>
        </div>
        <AnalyzePanel />
      </section>

      <section className="under-hood shell" aria-labelledby="under-hood-title">
        <div className="section-intro">
          <p className="section-number">Under the hood</p>
          <div>
            <p className="section-kicker">What a result passes through</p>
            <h2 id="under-hood-title">Generative reasoning inside deterministic gates.</h2>
          </div>
          <p>Depth on demand — each stage opens to its mechanism, and nothing here is required to read a result.</p>
        </div>
        <div className="under-hood-list">
          <details className="disclosure">
            <summary>Extraction and evidence gating</summary>
            <p>
              PDF text layers are read directly; scanned pages fall back to OCR when the deployment supports it,
              and every extraction reports its method, character count and truncation honestly. Findings then pass a
              deterministic evidence gate that scores corroborating signals before anything reaches the register.
            </p>
          </details>
          <details className="disclosure">
            <summary>Provider failover chain</summary>
            <p>
              A single analysis walks a bounded provider chain — each leg time-boxed so one slow provider cannot
              starve the request — and falls to a deterministic rule floor rather than failing silently.
              The result always names the path that produced it, including cache replays.
            </p>
          </details>
          <details className="disclosure">
            <summary>Commissioning mapping</summary>
            <p>
              Confirmed deviations map to the commissioning tests they threaten through a rule table — component
              class to Cx gate, with the scheduled week and the remaining decision window computed from the project plan.
            </p>
          </details>
        </div>
      </section>

      <section className="judge-proof shell" aria-labelledby="judge-proof-title">
        <div>
          <p className="section-kicker">Frozen benchmark · v{benchmark.version}</p>
          <h2 id="judge-proof-title">A measured benchmark, with a stated boundary.</h2>
          <p>{BENCHMARK_LIMITATION}</p>
        </div>
        <dl>
          <div><dt>Recall</dt><dd aria-label="Frozen benchmark recall 0.862">{benchmark.recall.toFixed(3)}</dd></div>
          <div><dt>Precision</dt><dd>{benchmark.precision.toFixed(3)}</dd></div>
          <div><dt>False alerts</dt><dd>{benchmark.falseAlerts} / {benchmark.cleanNegatives}</dd></div>
        </dl>
        <Link className="button button-secondary" href="/evidence">Inspect evidence</Link>
      </section>
    </main>
  );
}
