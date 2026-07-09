import { getRegister, getCxPlan, getSchedule, getSupplyChain, getProjectGraph, getRemediation, Deviation } from "../lib/api";
import DeviationRegister from "../components/DeviationRegister";
import CommissioningTwin from "../components/CommissioningTwin";
import ScheduleRisk from "../components/ScheduleRisk";
import SupplyChainPanel from "../components/SupplyChainPanel";
import ProjectGraphView from "../components/ProjectGraph";
import RemediationSimulator from "../components/RemediationSimulator";
import CopilotPanel from "../components/CopilotPanel";
import StatsBar from "../components/StatsBar";
import PipelineViz from "../components/PipelineViz";
import RiskMatrix from "../components/RiskMatrix";
import NavBar from "../components/NavBar";
import ScrollReveal from "../components/ScrollReveal";
import EvalDashboard from "../components/EvalDashboard";
import StandardsKB from "../components/StandardsKB";
import ExportButton from "../components/ExportButton";
import AcademicRefs from "../components/AcademicRefs";
import ScaleStory from "../components/ScaleStory";
import HeroIntro from "../components/HeroIntro";
import ArchitectureDiagram from "../components/ArchitectureDiagram";
import ROICalculator from "../components/ROICalculator";
import BeforeAfter from "../components/BeforeAfter";
import ScreenshotShowcase from "../components/ScreenshotShowcase";
import SectionIndex from "../components/SectionIndex";
import AnalyzePanel from "../components/AnalyzePanel";
import ComplianceScore from "../components/ComplianceScore";
import DocumentDiff from "../components/DocumentDiff";
import MultiProjectDashboard from "../components/MultiProjectDashboard";
import ErrorBoundary from "../components/ErrorBoundary";

function Sentinel({ d }: { d: Deviation }) {
  const span = 52;
  const caught = (d.week_caught / span) * 100;
  const fail = ((d.week_fail ?? span) / span) * 100;
  return (
    <section className="sentinel" id="sentinel">
      <div className="sentinel-glow" />
      <div className="sentinel-scan" />
      <div className="eyebrow">
        <span className="eyebrow-dot" />
        DEVIATION SENTINEL — {d.severity.toUpperCase()}
      </div>
      <h2 className="sentinel-headline">
        {d.component}: {d.parameter.replace(/_/g, " ")} — {d.provided_value}{" "}
        {d.unit} vs {d.required_value} {d.unit} required
      </h2>
      <div className="sub">
        Caught the day the submittal was uploaded — Week {d.week_caught}.
        Without Pramaan this surfaces in commissioning at Week {d.week_fail}.
      </div>

      <div className="leadrow">
        <div className="leadnum">
          {d.lead_time_weeks}
          <span>weeks early</span>
        </div>
        <div className="leadlabel">
          Lead time between detection and the integrated systems test this would
          have failed ({d.predicted_cx_test}). That window is the difference
          between an email and a seven-figure schedule slip.
        </div>
      </div>

      <div className="timeline">
        <div className="track">
          <div
            className="fill"
            style={{ left: `${caught}%`, width: `${fail - caught}%` }}
          />
          <div className="marker caught-marker" style={{ left: `${caught}%` }} />
          <div className="marker fail-marker" style={{ left: `${fail}%` }} />
        </div>
        <div className="ticks">
          <span className="tick">W0 Build start</span>
          <span className="tick caught">
            <b>W{d.week_caught} Caught here</b>
          </span>
          <span className="tick fail">
            <b>W{d.week_fail} {d.predicted_cx_test} fails</b>
          </span>
          <span className="tick">W52</span>
        </div>
      </div>

      <div className="chain">
        <div className="cell">
          <div className="k">Design basis</div>
          <div className="v">
            {d.required_value} {d.unit} minimum
            <span className="ref">{d.spec_clause}</span>
          </div>
        </div>
        <div className="cell">
          <div className="k">Vendor submittal</div>
          <div className="v">
            <span style={{ color: "var(--fault)" }}>
              {d.provided_value} {d.unit}
            </span>{" "}
            provided
            <span className="ref">Submittal rev B</span>
          </div>
        </div>
        <div className="cell">
          <div className="k">Governing standard</div>
          <div className="v">
            {d.standard_ref === "UPTIME-TIER4"
              ? "Tier IV fault tolerance + concurrent maintainability"
              : d.standard_ref === "NFPA-75"
                ? "NFPA 75 fire protection of IT equipment"
                : d.standard_ref}
            <span className="ref">{d.standard_ref}</span>
          </div>
        </div>
        {d.rationale && (
          <div className="cell cell-wide">
            <div className="k">AI rationale</div>
            <div className="v">{d.rationale}</div>
          </div>
        )}
      </div>
    </section>
  );
}

function SystemHealthGrid({ rows }: { rows: Deviation[] }) {
  const systems = [
    { id: "UPS", label: "UPS & Battery", icon: "⚡" },
    { id: "GEN", label: "Generators", icon: "🔋" },
    { id: "COOL", label: "Cooling", icon: "❄️" },
    { id: "SWGR", label: "Switchgear", icon: "🔌" },
    { id: "CABLE", label: "Cabling", icon: "🔗" },
    { id: "BMS", label: "BMS/EPMS", icon: "📡" },
    { id: "FIRE", label: "Fire Suppression", icon: "🔥" },
    { id: "BUSWAY", label: "Busway", icon: "⏚" },
    { id: "PDU", label: "PDU", icon: "🔧" },
    { id: "STRUCT", label: "Structural", icon: "🏗️" },
  ];

  const devsBySys: Record<string, Deviation[]> = {};
  for (const d of rows) {
    const sys =
      systems.find((s) =>
        d.component.startsWith(s.id) ||
        d.component === "BMS" ||
        d.component === "FLOOR"
      )?.id || d.component.split("-")[0];
    if (!devsBySys[sys]) devsBySys[sys] = [];
    devsBySys[sys].push(d);
  }

  return (
    <div className="health-grid">
      {systems.map((s, i) => {
        const devs = devsBySys[s.id] || [];
        const hasCritical = devs.some((d) => d.severity === "Critical");
        const hasMajor = devs.some((d) => d.severity === "Major");
        const status = hasCritical ? "critical" : hasMajor ? "major" : "ok";
        return (
          <ScrollReveal key={s.id} delay={i * 60}>
            <div className={`health-card ${status}`}>
              <div className="health-icon">{s.icon}</div>
              <div className="health-label">{s.label}</div>
              <div className="health-status">
                {devs.length === 0 ? (
                  <span className="health-ok">COMPLIANT</span>
                ) : (
                  <span className={`health-alert ${status}`}>
                    {devs.length} {devs.length === 1 ? "finding" : "findings"}
                  </span>
                )}
              </div>
              {devs.length > 0 && (
                <div className="health-lead">
                  {Math.max(...devs.map((d) => d.lead_time_weeks ?? 0))}w lead
                </div>
              )}
            </div>
          </ScrollReveal>
        );
      })}
    </div>
  );
}

function TotalSavingsHero() {
  return (
    <div className="savings-hero">
      <div className="savings-glow" />
      <div className="savings-number">267</div>
      <div className="savings-unit">weeks of lead-time window · synthetic demo portfolio</div>
      <div className="savings-sub">
        Summed lead time across 14 findings in the synthetic demo portfolio — the window
        between catching each deviation at submittal review (Week 11) and the commissioning
        test it would otherwise fail. An illustrative scenario, not a measured saving.
      </div>
    </div>
  );
}

// Demo data changes rarely; serve the page from Vercel's edge cache and
// revalidate in the background every 10 min. Reloads are instant instead of
// re-rendering against a (possibly cold) backend on every request.
export const revalidate = 600;

export default async function Page() {
  const [rows, cxPlan, schedule, supply, graph, remediation] = await Promise.all([
    getRegister(), getCxPlan(), getSchedule(), getSupplyChain(), getProjectGraph(), getRemediation(),
  ]);
  const hero = rows.find((r) => r.component === "UPS-02") ?? rows[0];
  const critical = rows.filter((r) => r.severity === "Critical").length;
  const major = rows.filter((r) => r.severity === "Major").length;
  const leadTimes = rows
    .map((r) => r.lead_time_weeks)
    .filter((l): l is number => l != null);
  const maxLead = Math.max(...leadTimes, 0);
  const meanLead =
    leadTimes.length > 0
      ? Math.round(leadTimes.reduce((a, b) => a + b, 0) / leadTimes.length)
      : 0;

  return (
    <ErrorBoundary>
    <main className="wrap">
      <NavBar />

      <ScrollReveal>
        <HeroIntro />
      </ScrollReveal>

      <ScrollReveal>
        <SectionIndex />
      </ScrollReveal>

      <div className="topbar">
        <div className="brand">
          PRA<b>MAAN</b>
        </div>
        <div className="project">Project Meghdoot &middot; 40 MW &middot; Navi Mumbai</div>
        <div className="spacer" />
        <ExportButton />
        <div className="live-badge">
          <span className="live-dot" />
          LIVE
        </div>
        <div className="tier">UPTIME TIER IV</div>
      </div>

      <StatsBar
        totalLeadWeeks={rows.reduce((a, r) => a + (r.lead_time_weeks ?? 0), 0)}
        totalFindings={rows.length}
        critical={critical}
        major={major}
        maxLeadWeeks={maxLead}
        meanLeadWeeks={meanLead}
      />

      {hero && <Sentinel d={hero} />}

      <ScrollReveal>
        <TotalSavingsHero />
      </ScrollReveal>

      <h2 className="section" id="workflow">
        Before vs after &middot; manual review vs Pramaan
      </h2>
      <ScrollReveal>
        <BeforeAfter />
      </ScrollReveal>

      <h2 className="section" id="pipeline">
        Reasoning pipeline &middot; one LLM core + deterministic services &middot; narratable in 60 seconds
      </h2>
      <ScrollReveal>
        <PipelineViz />
      </ScrollReveal>

      <h2 className="section" id="architecture">
        System architecture &middot; LangGraph compliance reasoning graph
      </h2>
      <ScrollReveal>
        <ArchitectureDiagram />
      </ScrollReveal>

      <h2 className="section" id="screenshots">
        Live screenshots &middot; interactive dashboard gallery
      </h2>
      <ScrollReveal>
        <ScreenshotShowcase />
      </ScrollReveal>

      <h2 className="section" id="systems">
        System health overview &middot; {10} systems
      </h2>
      <SystemHealthGrid rows={rows} />

      <h2 className="section" id="compliance">
        Compliance score &middot; per-system conformance tracking
      </h2>
      <ScrollReveal>
        <ComplianceScore />
      </ScrollReveal>

      <h2 className="section" id="diff">
        Document comparison &middot; spec vs submittal &middot; deviation highlights
      </h2>
      <ScrollReveal>
        <DocumentDiff rows={rows} />
      </ScrollReveal>

      <h2 className="section" id="risk">
        Risk matrix &middot; severity × lead time
      </h2>
      <ScrollReveal>
        <RiskMatrix rows={rows} />
      </ScrollReveal>

      <h2 className="section" id="register">
        Deviation register &middot; {rows.length} findings &middot; {critical}{" "}
        critical
      </h2>
      <ScrollReveal>
        <DeviationRegister rows={rows} />
      </ScrollReveal>

      <h2 className="section" id="twin">
        Commissioning risk twin &middot; L1&ndash;L5 test schedule
      </h2>
      <ScrollReveal>
        {cxPlan && <CommissioningTwin cxPlan={cxPlan} deviations={rows} />}
      </ScrollReveal>

      <h2 className="section" id="schedule">
        Predictive schedule risk &middot; Monte-Carlo CPM &middot; P80 finish
      </h2>
      <ScrollReveal>
        <ErrorBoundary><ScheduleRisk analysis={schedule} /></ErrorBoundary>
      </ScrollReveal>

      <h2 className="section" id="supply">
        Supply-chain visibility &middot; long-lead equipment &middot; delivery risk
      </h2>
      <ScrollReveal>
        <ErrorBoundary><SupplyChainPanel analysis={supply} /></ErrorBoundary>
      </ScrollReveal>

      <h2 className="section" id="graph">
        Living project graph &middot; deviation &rarr; commissioning &rarr; schedule &rarr; supply
      </h2>
      <ScrollReveal>
        <ErrorBoundary><ProjectGraphView graph={graph} /></ErrorBoundary>
      </ScrollReveal>
      <ScrollReveal>
        <ErrorBoundary><RemediationSimulator sim={remediation} /></ErrorBoundary>
      </ScrollReveal>

      <h2 className="section" id="standards">
        Standards knowledge base &middot; 7 governing standards
      </h2>
      <ScrollReveal>
        <StandardsKB />
      </ScrollReveal>

      <h2 className="section" id="multiproject">
        Multi-project eval &middot; 12 projects &middot; 11 countries &middot; synthetic breadth (by construction)
      </h2>
      <ScrollReveal>
        <MultiProjectDashboard />
      </ScrollReveal>

      <h2 className="section" id="eval">
        Eval harness &middot; precision &middot; recall &middot; F1
      </h2>
      <ScrollReveal>
        <EvalDashboard />
      </ScrollReveal>

      <h2 className="section" id="roi">
        ROI calculator &middot; quantified business impact
      </h2>
      <ScrollReveal>
        <ROICalculator />
      </ScrollReveal>

      <h2 className="section" id="scale">
        Scale story &middot; 10 systems → 14,000 line items
      </h2>
      <ScrollReveal>
        <ScaleStory />
      </ScrollReveal>

      <h2 className="section" id="analyze">
        Live analysis &middot; upload PDFs or paste text
      </h2>
      <ScrollReveal>
        <AnalyzePanel />
      </ScrollReveal>

      <h2 className="section" id="copilot">
        Project copilot &middot; RAG over specs, submittals, standards &amp; RFIs
      </h2>
      <ScrollReveal>
        <CopilotPanel />
      </ScrollReveal>

      <h2 className="section" id="refs">
        Academic references &middot; peer-reviewed foundations
      </h2>
      <ScrollReveal>
        <AcademicRefs />
      </ScrollReveal>

      <div className="footer">
        <div className="footer-brand">PRA<b>MAAN</b></div>
        <div className="footer-sub">
          EPC Deviation Intelligence &middot; ET AI Hackathon 2026 &middot; Problem Statement 4
        </div>
        <div className="footer-meta">
          12 Projects &middot; 11 Countries &middot; 50 Synthetic Deviations &middot; 1,024 Lead-time-weeks (synthetic sum) &middot; 15 Team-authored Pairs &middot; Offline 0 FP &middot; Synthetic F1 1.000 by construction
        </div>
      </div>
    </main>
    </ErrorBoundary>
  );
}
