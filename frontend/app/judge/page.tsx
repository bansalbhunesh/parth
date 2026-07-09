import Link from "next/link";
import AnalyzePanel from "../../components/AnalyzePanel";
import MultiProjectDashboard from "../../components/MultiProjectDashboard";
import { getRegister, getSchedule } from "../../lib/api";

// Same ISR treatment as the main page — instant reloads from the edge cache.
export const revalidate = 600;

export const metadata = {
  title: "Pramaan — Judge Mode",
  description: "EPC Deviation Intelligence — the 90-second proof.",
  openGraph: {
    title: "Pramaan — Judge Mode: the 90-second proof",
    description:
      "Load the deviation demo, hit Analyze, watch it reason over the raw documents live — each finding cited to the standard and the commissioning test it fails.",
    url: "/judge",
    siteName: "Pramaan",
    type: "website",
    images: [{ url: "/og.png", width: 1200, height: 630 }],
  },
  twitter: { card: "summary_large_image", images: ["/og.png"] },
};

export default async function JudgePage() {
  const [rows, schedule] = await Promise.all([getRegister(), getSchedule()]);
  const hero = rows.find((r) => r.component === "UPS-02") ?? rows[0];
  // Track whatever backend this build points at (NEXT_PUBLIC_API), so the
  // health link never goes stale when the backend URL changes.
  const apiBase = process.env.NEXT_PUBLIC_API ?? "http://127.0.0.1:8000";

  return (
    <main className="jm-wrap">
      <header className="jm-top">
        <div className="jm-brand">
          PRA<span>MAAN</span>
          <em>Judge Mode</em>
        </div>
        <nav className="jm-topnav" aria-label="Judge navigation">
          <Link href="/evidence" className="jm-link jm-link-alt">Evidence &amp; proof</Link>
          <Link href="/" className="jm-link">Full dashboard →</Link>
        </nav>
      </header>

      <section className="jm-hero">
        <div className="jm-eyebrow">
          EPC Deviation Intelligence · ET AI Hackathon 2026 · Problem Statement 4
        </div>
        <h1>
          The missed UPS deviation is not a finding.
          <span> It is a future commissioning failure with a date on it.</span>
        </h1>
        <p className="jm-sub">
          <strong>The differentiator:</strong> Pramaan does not stop at
          spec-vs-submittal mismatch. It names the <strong>commissioning test</strong>{" "}
          that will fail, the <strong>lead-time window</strong> still available,
          and the evidence chain a CxA can audit before signing.
        </p>
        {hero && (
          <div className="jm-failure-strip" aria-label="Hero deviation timeline">
            <div className="jm-failure-step win">
              <div className="jm-failure-k">Caught at review</div>
              <div className="jm-failure-v">Week {hero.week_caught}</div>
              <div className="jm-failure-note">
                {hero.component} {hero.parameter.replace(/_/g, " ")}:
                {" "}<strong>{String(hero.provided_value)} {hero.unit}</strong> submitted
                against <strong>{String(hero.required_value)} {hero.unit}</strong> required.
              </div>
            </div>
            <div className="jm-failure-arrow" aria-hidden="true">→</div>
            <div className="jm-failure-step danger">
              <div className="jm-failure-k">Would fail at</div>
              <div className="jm-failure-v">Week {hero.week_fail}</div>
              <div className="jm-failure-note">
                The deviation maps to <strong>{hero.predicted_cx_test}</strong>,
                not a vague risk bucket.
              </div>
            </div>
            <div className="jm-failure-arrow" aria-hidden="true">→</div>
            <div className="jm-failure-step">
              <div className="jm-failure-k">Action window</div>
              <div className="jm-failure-v">{hero.lead_time_weeks} weeks</div>
              <div className="jm-failure-note">
                Early enough for an RFI or re-submittal, not a late commissioning recovery plan.
              </div>
            </div>
          </div>
        )}
      </section>

      <section className="jm-orient" aria-label="How to read Pramaan in 60 seconds">
        <div className="jm-orient-step">
          <span className="jm-orient-n">1</span>
          <div><strong>What it does</strong><p>Reconciles an owner spec against a vendor submittal and the governing standards, and flags every deviation.</p></div>
        </div>
        <div className="jm-orient-step">
          <span className="jm-orient-n">2</span>
          <div><strong>What you give it</strong><p>A design basis + a vendor submittal — PDF, image, or pasted text. Try the buttons below.</p></div>
        </div>
        <div className="jm-orient-step">
          <span className="jm-orient-n">3</span>
          <div><strong>What it returns</strong><p>Each non-compliance with its standard, the commissioning test it fails, and the lead-time to fix it.</p></div>
        </div>
        <div className="jm-orient-step">
          <span className="jm-orient-n">4</span>
          <div><strong>How it&apos;s proven</strong><p>A frozen, provenance-tracked benchmark + full limitations — <Link href="/evidence">open the evidence page →</Link></p></div>
        </div>
      </section>

      <section className="jm-metrics">
        <div className="jm-metric">
          <div className="jm-metric-val lead">0.862</div>
          <div className="jm-metric-label">mean recall · benchmark v1.2 (3-pass)</div>
        </div>
        <div className="jm-metric">
          <div className="jm-metric-val ok">0</div>
          <div className="jm-metric-label">false alerts on 64 clean-negative controls</div>
        </div>
        <div className="jm-metric">
          <div className="jm-metric-val">53</div>
          <div className="jm-metric-label">spec–submittal pairs · 129 frozen labels · 17 systems</div>
        </div>
        <div className="jm-metric">
          <div className="jm-metric-val accent">27 wk</div>
          <div className="jm-metric-label">lead time on the hero UPS deviation (Cx week 38 − week 11)</div>
        </div>
      </section>
      <p className="jm-metrics-note">
        Numbers are from the frozen <strong>ps4_external_v1 (v1.2)</strong> benchmark:
        team-authored fixtures, single-author frozen labels, two-person reviewer
        adjudication still pending — a benchmark result, not a field-validation
        claim. <Link href="/evidence">See every number and its limitation →</Link>
      </p>

      <section className="jm-section">
        <div className="jm-section-head">
          <h2>Try it live — reasoning over a document, not keywords</h2>
          <p>
            Hit <strong>“Load deviation demo ★”</strong> (a realistic design basis
            vs a vendor submittal, in natural prose — with a hidden 2N→N+1 and a
            10-min→8-min non-compliance), then <strong>“Load compliant demo ✓”</strong>
            {" "}(a fully compliant submittal — the correct answer is zero deviations,
            so you can see it does not false-alarm). Or upload your own spec + submittal.
            Pramaan reasons out the non-compliances from scratch and cites the standard,
            the commissioning test, and the lead time for each. Our fixtures are
            team-authored; where they derive from public primary sources the values are
            cited (10 documents, 5 with a verified public URL) —{" "}
            <a
              href="https://github.com/bansalbhunesh/parth/blob/main/data/samples/real/PROVENANCE.md"
              target="_blank"
              rel="noreferrer"
            >
              see the provenance yourself
            </a>.
          </p>
        </div>
        <AnalyzePanel />
      </section>

      <section className="jm-section">
        <div className="jm-section-head">
          <h2>And it reaches all the way to the handover date</h2>
          <p>
            A deviation isn&apos;t just a compliance flag. Pramaan traces it to the
            commissioning test it fails, the schedule milestone it slips, and the
            long-lead supplier whose re-procurement is the real cost — one connected
            graph where each deviation→standard→Cx-test edge carries the basis it
            rests on (schedule and cost edges are computed by the deterministic
            services, not the LLM). Caught at submittal review, here&apos;s what these{" "}
            {schedule.n_risks} deviations are worth to the ready-for-service date:
          </p>
        </div>
        <div className="jm-metrics">
          <div className="jm-metric">
            <div className="jm-metric-val ok">
              {schedule.baseline.on_time_probability !== null
                ? `${Math.round(schedule.baseline.on_time_probability * 100)}%`
                : "—"}
            </div>
            <div className="jm-metric-label">on-time probability · baseline</div>
          </div>
          <div className="jm-metric">
            <div className="jm-metric-val">
              {schedule.deviation_impact
                ? `${Math.round((schedule.deviation_impact.at_risk_on_time ?? 0) * 100)}%`
                : "—"}
            </div>
            <div className="jm-metric-label">on-time if these deviations slip through</div>
          </div>
          <div className="jm-metric">
            <div className="jm-metric-val lead">
              +{schedule.deviation_impact?.slip_weeks ?? 0} wk
            </div>
            <div className="jm-metric-label">
              ready-for-service slip · worst case, all {schedule.n_risks} uncaught
            </div>
          </div>
        </div>
      </section>

      <section className="jm-section">
        <div className="jm-section-head">
          <h2>Scale check — the whole portfolio</h2>
          <p>
            12 projects across 11 countries and 6 tier standards. This is a
            synthetic breadth corpus where the deviations are <strong>seeded</strong>,
            so the model recovers 50/50 <em>by construction</em> — it proves the
            pipeline scales and reproduces, not detection skill. The real proof is
            the live-analysis panel above (documents outside the seeded corpus).
          </p>
          <p className="jm-generalize">
            <strong>Not just data centres.</strong> The engine is domain-agnostic:
            any field where a written specification must be reconciled against a
            vendor submittal and a downstream acceptance test — pharma GMP
            qualification, aerospace AS9100, medical-device V&amp;V, switchgear type
            testing — is the same problem. Data-centre EPC is simply the
            highest-stakes instance we proved it on.
          </p>
        </div>
        <MultiProjectDashboard />
      </section>

      <section className="jm-section">
        <div className="jm-section-head">
          <h2>The people who live this problem</h2>
          <p>
            <em>
              &ldquo;In data center EPC projects, L1 submittal reviews are a notorious
              bottleneck. If a vendor changes a sensor location or a BACnet register
              mapping in a CRAH submittal and it gets approved without double-checking
              the controls integration, we don&apos;t catch it until L4 functional
              testing — and it can delay Integrated Systems Testing by weeks.
              Automating the comparison of submittals against the Basis of Design to
              flag these integration and testing risks early is a massive win for
              project schedules.&rdquo;
            </em>{" "}
            — a lead data-centre commissioning authority (CxA). Four more
            practitioner perspectives (MEP PM, mechanical PE, controls consultant,
            EPC project director) with provenance notes:{" "}
            <a
              href="https://github.com/bansalbhunesh/parth/blob/main/docs/VALIDATION.md"
              target="_blank"
              rel="noreferrer"
            >
              validation dossier §5
            </a>
            . These validate the <strong>problem and workflow</strong> — the
            accuracy claim remains the frozen benchmark above.
          </p>
        </div>
      </section>

      <p className="jm-limits">
        <strong>What this prototype does not claim:</strong> not field- or
        customer-validated; benchmark fixtures are team-authored (10 derived from
        public primary sources); labels are single-author frozen with two-person
        human adjudication pending; OCR and the live LLM run only where the
        deployment provides them (status is shown truthfully above and at{" "}
        <a href={`${apiBase}/ocr-check`} target="_blank" rel="noreferrer">/ocr-check</a>).
      </p>

      <footer className="jm-foot">
        <Link href="/" className="jm-foot-cta">Open the full 22-section dashboard →</Link>
        <div className="jm-foot-links">
          <Link href="/evidence">Evidence &amp; proof</Link>
          <span>·</span>
          <a href={`${apiBase}/health`} target="_blank" rel="noreferrer">API health</a>
          <span>·</span>
          <a href={`${apiBase}/ocr-check`} target="_blank" rel="noreferrer">OCR status</a>
          <span>·</span>
          <a href="https://github.com/bansalbhunesh/parth" target="_blank" rel="noreferrer">Source</a>
        </div>
      </footer>
    </main>
  );
}
