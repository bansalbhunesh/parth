import Link from "next/link";
import AnalyzePanel from "../../components/AnalyzePanel";
import ThemeToggle from "../../components/ThemeToggle";
import { BENCHMARK_LIMITATION, PRODUCT_CLAIMS } from "../../lib/claims";

export const revalidate = 600;

export const metadata = {
  title: "Analyze documents — Pramaan",
  description: "Compare a design basis and vendor submittal with explicit analysis provenance.",
};

export default function JudgePage() {
  const benchmark = PRODUCT_CLAIMS.benchmark;

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <header className="site-header">
        <Link href="/" className="wordmark" aria-label="Pramaan home">Pramaan<span aria-hidden="true">/</span></Link>
        <nav className="site-nav jm-topnav" aria-label="Judge navigation">
          <Link href="/">Overview</Link>
          <Link href="/evidence">Evidence</Link>
          <Link href="/war-room">Interventions</Link>
        </nav>
        <ThemeToggle />
      </header>

      <main id="main-content">
      <section className="route-hero shell">
        <p className="section-kicker">Document analysis · explicit provenance</p>
        <h1>Put the requirement and the proposal side by side.</h1>
        <p>
          Upload two documents or use the controlled text fixtures. Each result states whether it came from a live model, deterministic rules, or an unavailable analysis path.
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

      <footer className="site-footer shell">
        <div><Link href="/" className="wordmark">Pramaan<span aria-hidden="true">/</span></Link><p>Evidence to resolution for consequential infrastructure.</p></div>
        <nav aria-label="Footer navigation"><Link href="/">Overview</Link><Link href="/evidence">Evidence</Link><Link href="/war-room">Interventions</Link></nav>
      </footer>
    </>
  );
}
