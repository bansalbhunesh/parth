import { getRegister, getCxPlan, Deviation, CxPlan } from "../lib/api";
import DeviationRegister from "../components/DeviationRegister";
import CommissioningTwin from "../components/CommissioningTwin";
import CopilotPanel from "../components/CopilotPanel";
import StatsBar from "../components/StatsBar";
import PipelineViz from "../components/PipelineViz";
import RiskMatrix from "../components/RiskMatrix";
import NavBar from "../components/NavBar";
import ScrollReveal from "../components/ScrollReveal";

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
      <h1>
        {d.component}: {d.parameter.replace(/_/g, " ")} — {d.provided_value}{" "}
        {d.unit} vs {d.required_value} {d.unit} required
      </h1>
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
      <div className="savings-number">144</div>
      <div className="savings-unit">total weeks of lead time saved</div>
      <div className="savings-sub">
        6 deviations caught at Week 11 — before a single bolt turns on site.
        That&apos;s 144 weeks of avoided commissioning rework, schedule delays,
        and cost overruns across all findings.
      </div>
    </div>
  );
}

export default async function Page() {
  const [rows, cxPlan] = await Promise.all([getRegister(), getCxPlan()]);
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
    <main className="wrap">
      <NavBar />

      <div className="topbar">
        <div className="brand">
          PRA<b>MAAN</b>
        </div>
        <div className="project">Project Meghdoot &middot; 40 MW &middot; Navi Mumbai</div>
        <div className="spacer" />
        <div className="live-badge">
          <span className="live-dot" />
          LIVE
        </div>
        <div className="tier">UPTIME TIER IV</div>
      </div>

      <StatsBar
        totalFindings={rows.length}
        critical={critical}
        major={major}
        maxLeadWeeks={maxLead}
        meanLeadWeeks={meanLead}
        systemsScanned={10}
      />

      {hero && <Sentinel d={hero} />}

      <ScrollReveal>
        <TotalSavingsHero />
      </ScrollReveal>

      <h2 className="section" id="pipeline">
        AI agent pipeline &middot; 5 agents &middot; narratable in 60 seconds
      </h2>
      <ScrollReveal>
        <PipelineViz />
      </ScrollReveal>

      <h2 className="section" id="systems">
        System health overview &middot; {10} systems
      </h2>
      <SystemHealthGrid rows={rows} />

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

      <h2 className="section" id="copilot">
        Project copilot &middot; RAG over specs, submittals, standards &amp; RFIs
      </h2>
      <ScrollReveal>
        <CopilotPanel />
      </ScrollReveal>

      <div className="footer">
        <div className="footer-brand">PRA<b>MAAN</b></div>
        <div className="footer-sub">
          EPC Deviation Intelligence &middot; ET AI Hackathon 2026 &middot; Problem Statement 4
        </div>
        <div className="footer-meta">
          5 AI Agents &middot; 10 Systems &middot; 33 Requirements &middot; 6 Deviations &middot; 144 Weeks Saved
        </div>
      </div>
    </main>
  );
}
