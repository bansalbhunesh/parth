import Link from "next/link";
import { getHealth } from "../../lib/api";

// Judge-readable proof page. Two kinds of number live here, never blurred:
//   • FROZEN benchmark truth — copied from the frozen ps4_external_v1 (v1.2)
//     benchmark_card.json, presented statically and linked to the source file.
//   • LIVE deployment status — fetched from /health at request time; if the
//     backend is unreachable we say so rather than imply anything is green.
// No secrets are ever shown: /health returns only booleans, caps and a commit.

export const metadata = {
  title: "Pramaan — Evidence & Proof",
  description:
    "Every headline number, its limitation, and the live deployment status — in one page.",
};

// A cold Render free-tier backend can take 30s+ to wake; don't block the page on it.
export const revalidate = 0;

const REPO = "https://github.com/bansalbhunesh/parth";
const BLOB = `${REPO}/blob/main`;

// ── FROZEN benchmark card (ps4_external_v1 v1.2) ──────────────────────────────
// Mirrors benchmarks/ps4_external_v1/reports/benchmark_card.json exactly. Frozen —
// regenerated only by scripts/benchmark_report.py. Linked below so it is checkable.
const BENCH = {
  version: "1.2.0",
  featured_model: "gemini-3.1-flash-lite",
  passes: 3,
  recall_mean: 0.862,
  recall_min: 0.841,
  recall_max: 0.873,
  precision_mean: 0.953,
  f1_mean: 0.905,
  exact_recall_mean: 0.698,
  far_mean: 0.0,
  p50_ms: 2481,
  pairs: 53,
  source_documents: 106,
  labels: 129,
  positive_labels: 63,
  clean_negatives: 64,
  contested_labels: 2,
  systems: 17,
  primary_source_derived: 10,
  docs_with_verified_url: 5,
  rule_recall: 0.111,
  rule_tp: 7,
  rule_fp: 0,
  ablation_model: "gemini-2.5-flash",
  ablation_recall_peak: 0.9524,
  review_status: "single-author frozen · two-person adjudication pending",
};

const TEST_COUNT = 594; // `python -m pytest tests --collect-only` (measured, not estimated)

// Verbatim limitation line required next to the benchmark card.
const LIMITATION =
  "Mostly team-authored fixtures, 10 primary-source-derived documents, reviewer-2 human adjudication pending, not a field/customer validation.";

function pct(x: number) {
  return x.toFixed(3);
}

function Stat({ value, label, tone }: { value: string; label: string; tone?: string }) {
  return (
    <div className="ev-stat">
      <div className={`ev-stat-val ${tone ?? ""}`}>{value}</div>
      <div className="ev-stat-label">{label}</div>
    </div>
  );
}

function StatusRow({
  label,
  value,
  state,
}: {
  label: string;
  value: string;
  state: "ok" | "warn" | "muted";
}) {
  return (
    <div className="ev-status-row">
      <span className={`ev-dot ev-dot-${state}`} aria-hidden="true" />
      <span className="ev-status-label">{label}</span>
      <span className="ev-status-value">{value}</span>
    </div>
  );
}

export default async function EvidencePage() {
  const health = await getHealth();
  const live = health !== null;

  const commit = health?.commit ?? "—";
  const ocrLive = health?.ocr_available ?? false;
  const llmReady = health?.llm?.ready ?? false;
  const chain = health?.llm?.chain ?? [];
  const authOn = health?.security?.auth_required ?? false;
  const rlOn = health?.security?.rate_limit_enabled ?? false;
  const maxUpload = health?.security?.max_upload_mb;

  return (
    <main className="ev-wrap">
      <header className="ev-top">
        <div className="ev-brand">
          PRA<span>MAAN</span>
          <em>Evidence</em>
        </div>
        <nav className="ev-topnav" aria-label="Evidence navigation">
          <Link href="/judge" className="ev-link">★ Judge Mode</Link>
          <Link href="/" className="ev-link">Full dashboard →</Link>
        </nav>
      </header>

      <section className="ev-hero">
        <div className="ev-eyebrow">EVIDENCE &amp; PROOF · ONE PAGE, NO 20-DOC HUNT</div>
        <h1>Every headline number, its limitation, and the live status.</h1>
        <p className="ev-quote">
          On the frozen, provenance-tracked <strong>ps4_external_v1 (v1.2)</strong>{" "}
          benchmark — {BENCH.pairs} team-authored spec–submittal pairs,{" "}
          {BENCH.labels} single-author-frozen labels, {BENCH.systems} systems,{" "}
          {BENCH.clean_negatives} clean negatives — the featured configuration
          (<code>{BENCH.featured_model}</code>, {BENCH.passes}-pass) reports mean
          semantic <strong>recall {pct(BENCH.recall_mean)}</strong>, precision{" "}
          {pct(BENCH.precision_mean)}, F1 {pct(BENCH.f1_mean)}, and{" "}
          <strong>0 false alerts</strong> on the {BENCH.clean_negatives} clean
          negatives, vs a deterministic rule baseline of {pct(BENCH.rule_recall)}.
          This is a benchmark result — <strong>not</strong> a real-world-accuracy or field-validation claim.
        </p>
      </section>

      {/* ── LIVE deployment status ─────────────────────────────────────────── */}
      <section className="ev-section">
        <div className="ev-section-head">
          <h2>Live deployment status</h2>
          <span className={`ev-live-badge ${live ? "on" : "off"}`}>
            <span className="ev-live-dot" />
            {live ? "LIVE — fetched from /health" : "BACKEND NOT REACHED"}
          </span>
        </div>
        {!live && (
          <p className="ev-note">
            The API did not respond in time (a cold free-tier server can take ~30 s
            to wake). The frozen benchmark numbers below are unaffected; only the
            live status could not be read. Retry, or check{" "}
            <a href={`${REPO}`} target="_blank" rel="noreferrer">the repo</a>.
          </p>
        )}
        <div className="ev-status-grid">
          <StatusRow label="Deployed commit" value={live ? commit : "unavailable"} state={live ? "ok" : "muted"} />
          <StatusRow
            label="Analysis mode"
            value={live ? (llmReady ? "live LLM ready" : "deterministic rule floor") : "unavailable"}
            state={live ? (llmReady ? "ok" : "warn") : "muted"}
          />
          <StatusRow
            label="LLM failover chain"
            value={live ? (chain.length ? chain.join(" → ") : "rule floor only") : "unavailable"}
            state={live ? (llmReady ? "ok" : "warn") : "muted"}
          />
          <StatusRow
            label="OCR (scanned PDF / image)"
            value={live ? (ocrLive ? "available (Tesseract)" : "not installed in this deployment") : "unavailable"}
            state={live ? (ocrLive ? "ok" : "warn") : "muted"}
          />
          <StatusRow
            label="Demo auth"
            value={live ? (authOn ? "token required" : "open (demo)") : "unavailable"}
            state={live ? "ok" : "muted"}
          />
          <StatusRow
            label="Rate limiting + upload cap"
            value={live ? `${rlOn ? "per-IP limits on" : "off"}${maxUpload ? ` · ${maxUpload} MB cap` : ""}` : "unavailable"}
            state={live ? (rlOn ? "ok" : "warn") : "muted"}
          />
        </div>
        <p className="ev-fineprint">
          Status is read from <a href="#links">/health</a> and{" "}
          <code>/ocr-check</code> / <code>/llm-check</code> — booleans and a commit
          only, never a key. Provider failover is an <strong>availability</strong>{" "}
          mechanism; every leg is scored the same, so it never improves accuracy.
        </p>
      </section>

      {/* ── FROZEN benchmark card ──────────────────────────────────────────── */}
      <section className="ev-section">
        <div className="ev-section-head">
          <h2>Benchmark card — ps4_external_v1 (v{BENCH.version})</h2>
          <span className="ev-frozen-badge">FROZEN</span>
        </div>
        <div className="ev-card">
          <div className="ev-card-metrics">
            <Stat value={pct(BENCH.recall_mean)} label={`mean recall (${pct(BENCH.recall_min)}–${pct(BENCH.recall_max)})`} tone="lead" />
            <Stat value={pct(BENCH.precision_mean)} label="mean precision" tone="ok" />
            <Stat value={pct(BENCH.f1_mean)} label="mean F1" tone="ok" />
            <Stat value={pct(BENCH.far_mean)} label="false-alert rate (64 clean negatives)" tone="ok" />
            <Stat value={`~${(BENCH.p50_ms / 1000).toFixed(1)}s`} label="p50 latency / pair" />
            <Stat value={pct(BENCH.rule_recall)} label={`rule baseline recall (${BENCH.rule_tp}/${BENCH.positive_labels}, ${BENCH.rule_fp} FP)`} tone="warn" />
          </div>
          <div className="ev-card-compose">
            <span><strong>{BENCH.pairs}</strong> pairs</span>
            <span><strong>{BENCH.labels}</strong> frozen labels</span>
            <span><strong>{BENCH.positive_labels}</strong> positives</span>
            <span><strong>{BENCH.clean_negatives}</strong> clean negatives</span>
            <span><strong>{BENCH.systems}</strong> systems</span>
            <span><strong>{BENCH.source_documents}</strong> source docs</span>
            <span><strong>{BENCH.primary_source_derived}</strong> primary-source-derived ({BENCH.docs_with_verified_url} verified URLs)</span>
            <span><strong>{BENCH.passes}-pass</strong> live run · <code>{BENCH.featured_model}</code></span>
          </div>
          <p className="ev-ablation">
            Ablation (not the primary result): <code>{BENCH.ablation_model}</code>{" "}
            reached a higher peak recall (~{pct(BENCH.ablation_recall_peak)}) but was
            slower and did not complete a clean 3-pass repeat — reported as a model
            comparison only. The <strong>hosted live demo pins this ablation model</strong>{" "}
            (<code>{BENCH.ablation_model}</code>, native API); the featured 3-pass
            numbers above belong to <code>{BENCH.featured_model}</code> and are never
            re-attributed. <code>/llm-check</code> reports which model answered.
          </p>
        </div>
        <p className="ev-limitation">
          <strong>Limitation:</strong> {LIMITATION}
        </p>
      </section>

      {/* ── Reviewer status ────────────────────────────────────────────────── */}
      <section className="ev-section">
        <div className="ev-section-head">
          <h2>Reviewer status</h2>
          <span className="ev-frozen-badge warn">REVIEWER-2 PENDING</span>
        </div>
        <div className="ev-status-grid">
          <StatusRow label="Labels authored & frozen" value="single author (100% reviewer-1 coverage)" state="ok" />
          <StatusRow label="Second human reviewer (reviewer-2)" value="not yet run — pending" state="warn" />
          <StatusRow label="Two-person adjudication" value="pending (0 adjudicated)" state="warn" />
          <StatusRow label="Automated consistency audit" value="123/129 consistent, 6 flagged — machine QA, not a human review" state="muted" />
        </div>
        <p className="ev-fineprint">
          The automated audit is a deterministic second-pass check that flags
          candidates for a human; it does <strong>not</strong> substitute for the
          pending two-person adjudication. We do not claim independent two-reviewer
          adjudication. See{" "}
          <a href={`${BLOB}/benchmarks/ps4_external_v1/labels/REVIEW_STATUS.md`} target="_blank" rel="noreferrer">REVIEW_STATUS.md</a>.
        </p>
      </section>

      {/* ── Evidence summary ───────────────────────────────────────────────── */}
      <section className="ev-section">
        <div className="ev-section-head"><h2>Evidence summary</h2></div>
        <div className="ev-summary-grid">
          <Stat value={live ? commit : "—"} label="deployed commit" />
          <Stat value={String(TEST_COUNT)} label="automated tests (pytest)" tone="lead" />
          <Stat value={`v${BENCH.version}`} label="benchmark version" />
          <Stat value={String(BENCH.pairs)} label="spec–submittal pairs" />
          <Stat value={String(BENCH.labels)} label="frozen labels" />
          <Stat value={String(BENCH.systems)} label="system types" />
          <Stat value={String(BENCH.clean_negatives)} label="clean negatives" />
          <Stat value={pct(BENCH.recall_mean)} label="featured recall" tone="ok" />
          <Stat value={pct(BENCH.rule_recall)} label="rule-engine baseline recall" tone="warn" />
          <Stat value={live ? (ocrLive ? "live" : "off") : "—"} label="OCR status" />
          <Stat value={live ? (llmReady ? "ready" : "rule floor") : "—"} label="LLM failover" />
          <Stat value={live ? (rlOn ? "on" : "off") : "—"} label="rate limiting" />
        </div>
      </section>

      {/* ── Limitations ────────────────────────────────────────────────────── */}
      <section className="ev-section">
        <div className="ev-section-head"><h2>Limitations we do not hide</h2></div>
        <ul className="ev-limits">
          <li>Benchmark fixtures are <strong>team-authored</strong> (10 derived from public primary sources, 5 with a verified URL) — not downloaded real datasheets.</li>
          <li>Labels are <strong>single-author frozen</strong>; two-person human adjudication is <strong>pending</strong>. Stored primary-source PDFs are pending.</li>
          <li>Numbers are a <strong>benchmark result</strong>, not field- or customer-validated; no real-world-accuracy claim is made.</li>
          <li>The rule baseline is deliberately <strong>low recall</strong> (0.111) — it is an availability floor, computed from the documents, never from seeded labels.</li>
          <li>OCR needs the Tesseract binary and is best-effort (not lossless); <code>/ocr-check</code> is authoritative per deployment.</li>
          <li>This is a <strong>hackathon prototype</strong>: security is demo hardening (single-instance, in-memory rate limiting), not production security.</li>
        </ul>
      </section>

      {/* ── Links ──────────────────────────────────────────────────────────── */}
      <section className="ev-section" id="links">
        <div className="ev-section-head"><h2>Verify it yourself</h2></div>
        <div className="ev-links">
          <a href={`${BLOB}/benchmarks/ps4_external_v1/reports/benchmark_report.md`} target="_blank" rel="noreferrer">Benchmark report ↗</a>
          <a href={`${BLOB}/benchmarks/ps4_external_v1/reports/benchmark_card.json`} target="_blank" rel="noreferrer">Benchmark card JSON ↗</a>
          <a href={`${BLOB}/benchmarks/ps4_external_v1/labels/REVIEW_STATUS.md`} target="_blank" rel="noreferrer">Reviewer status ↗</a>
          <a href={`${BLOB}/docs/CLAIMS_REGISTER.md`} target="_blank" rel="noreferrer">Claims register ↗</a>
          <a href={`${BLOB}/docs/ARCHITECTURE.md`} target="_blank" rel="noreferrer">Architecture ↗</a>
          <a href={`${BLOB}/docs/TECHNICAL_OVERVIEW.md`} target="_blank" rel="noreferrer">Technical overview ↗</a>
          <a href={`${BLOB}/docs/OCR_DEPLOYMENT_CHECKLIST.md`} target="_blank" rel="noreferrer">OCR deployment / check ↗</a>
          <a href={`${BLOB}/docs/LLM_FAILOVER_RUNBOOK.md`} target="_blank" rel="noreferrer">LLM failover runbook ↗</a>
          <a href={`${BLOB}/docs/SECURITY_DEMO_RUNBOOK.md`} target="_blank" rel="noreferrer">Security / demo hardening ↗</a>
          <a href={`${BLOB}/docs/Pramaan_Detailed_Submission.pdf`} target="_blank" rel="noreferrer">Detailed submission (PDF) ↗</a>
          <a href={`${BLOB}/docs/Pramaan_Deck.pdf`} target="_blank" rel="noreferrer">Deck (PDF) ↗</a>
          <a href={REPO} target="_blank" rel="noreferrer">GitHub repository ↗</a>
        </div>
      </section>

      <footer className="ev-foot">
        <Link href="/judge" className="ev-foot-cta">← Back to Judge Mode</Link>
        <span className="ev-foot-note">
          Frozen numbers from the benchmark card; live status from <code>/health</code>. No secrets shown.
        </span>
      </footer>
    </main>
  );
}
