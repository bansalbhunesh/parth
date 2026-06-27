import Link from "next/link";
import AnalyzePanel from "../../components/AnalyzePanel";
import MultiProjectDashboard from "../../components/MultiProjectDashboard";
import { getRegister } from "../../lib/api";

// Same ISR treatment as the main page — instant reloads from the edge cache.
export const revalidate = 600;

export const metadata = {
  title: "Pramaan — Judge Mode",
  description: "EPC Deviation Intelligence — the 90-second proof.",
};

export default async function JudgePage() {
  const rows = await getRegister();
  const hero = rows.find((r) => r.component === "UPS-02") ?? rows[0];

  return (
    <div className="jm-wrap">
      <header className="jm-top">
        <div className="jm-brand">
          PRA<span>MAAN</span>
          <em>Judge Mode</em>
        </div>
        <Link href="/" className="jm-link">Full dashboard →</Link>
      </header>

      <section className="jm-hero">
        <div className="jm-eyebrow">
          EPC Deviation Intelligence · ET AI Hackathon 2026 · Problem Statement 4
        </div>
        <h1>
          It catches the spec deviation the day the submittal lands —
          <span> not in commissioning, six months and a few crore too late.</span>
        </h1>
        {hero && (
          <p className="jm-sub">
            Live example — <strong>{hero.component} {hero.parameter.replace(/_/g, " ")}</strong>:
            {" "}provided <strong className="bad">{String(hero.provided_value)} {hero.unit}</strong> vs
            {" "}<strong>{String(hero.required_value)} {hero.unit}</strong> required —
            flagged <strong className="good">{hero.lead_time_weeks} weeks</strong> before the
            commissioning test it would have failed.
          </p>
        )}
      </section>

      <section className="jm-metrics">
        <div className="jm-metric">
          <div className="jm-metric-val">50</div>
          <div className="jm-metric-label">deviations caught</div>
        </div>
        <div className="jm-metric">
          <div className="jm-metric-val lead">1,024</div>
          <div className="jm-metric-label">weeks of lead time saved</div>
        </div>
        <div className="jm-metric">
          <div className="jm-metric-val ok">1.000</div>
          <div className="jm-metric-label">F1 — real LLM, 12 projects</div>
        </div>
        <div className="jm-metric">
          <div className="jm-metric-val accent">12 · 11</div>
          <div className="jm-metric-label">projects · countries</div>
        </div>
      </section>

      <section className="jm-section">
        <div className="jm-section-head">
          <h2>Try it live — on a document we’ve never seen</h2>
          <p>
            Hit <strong>“Load real document ★”</strong> (a real Vertiv UPS datasheet
            vs a design basis), or upload your own spec + submittal. Pramaan reasons
            out the non-compliances from scratch and cites the standard, the
            commissioning test, and the lead time for each.
          </p>
        </div>
        <AnalyzePanel />
      </section>

      <section className="jm-section">
        <div className="jm-section-head">
          <h2>Not one lucky project — the whole portfolio</h2>
          <p>
            12 projects across 11 countries and 6 tier standards. A real frontier
            model recovers <strong>50/50 deviations</strong> from raw documents —
            Recall 1.000, Precision 1.000.
          </p>
        </div>
        <MultiProjectDashboard />
      </section>

      <footer className="jm-foot">
        <Link href="/" className="jm-foot-cta">Open the full 19-section dashboard →</Link>
        <div className="jm-foot-links">
          <a href="https://parth-3puc.onrender.com/health" target="_blank" rel="noreferrer">API health</a>
          <span>·</span>
          <a href="https://github.com/bansalbhunesh/parth" target="_blank" rel="noreferrer">Source</a>
        </div>
      </footer>
    </div>
  );
}
