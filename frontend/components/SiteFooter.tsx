import Link from "./AppLink";
import { PRODUCT_CLAIMS } from "../lib/claims";

export default function SiteFooter() {
  const verification = PRODUCT_CLAIMS.verification;
  const benchmark = PRODUCT_CLAIMS.benchmark;
  return (
    <footer className="site-footer">
      <div className="shell site-footer-grid">
        <div className="footer-identity">
          <Link href="/" className="wordmark">Pramaan<span aria-hidden="true">/</span></Link>
          <p>Evidence to resolution for consequential infrastructure.</p>
          <p className="footer-honesty">
            Every result states its provenance. A fallback is never relabelled as live.
          </p>
        </div>
        <nav className="footer-column" aria-label="Footer navigation">
          <span className="footer-heading">Product</span>
          <Link href="/">Overview</Link>
          <Link href="/judge">Analyze</Link>
          <Link href="/war-room">Interventions</Link>
          <Link href="/evidence">Evidence</Link>
        </nav>
        <nav className="footer-column" aria-label="Footer sources">
          <span className="footer-heading">Record</span>
          <a href="https://github.com/bansalbhunesh/parth" target="_blank" rel="noreferrer">Source ↗</a>
          <a href="https://github.com/bansalbhunesh/parth/blob/main/benchmarks/ps4_external_v1/BENCHMARK_PROTOCOL.md" target="_blank" rel="noreferrer">Benchmark protocol ↗</a>
          <a href="https://github.com/bansalbhunesh/parth/blob/main/docs/VALIDATION.md" target="_blank" rel="noreferrer">Validation dossier ↗</a>
          <a href="https://github.com/bansalbhunesh/parth/actions" target="_blank" rel="noreferrer">CI runs ↗</a>
        </nav>
        <div className="footer-column footer-ledger-column">
          <span className="footer-heading">Verified</span>
          <dl className="footer-ledger">
            <div><dt>Backend tests</dt><dd>{verification.backendTests}+</dd></div>
            <div><dt>Frontend tests</dt><dd>{verification.frontendTests}+</dd></div>
            <div><dt>Browser journeys</dt><dd>{verification.browserJourneys}+</dd></div>
            <div><dt>Benchmark recall</dt><dd>{benchmark.recall.toFixed(3)}</dd></div>
          </dl>
        </div>
      </div>
    </footer>
  );
}
