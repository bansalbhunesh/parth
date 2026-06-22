import { getRegister, Deviation } from "../lib/api";
import DeviationRegister from "../components/DeviationRegister";

function Sentinel({ d }: { d: Deviation }) {
  // timeline geometry: project start (0) -> current week -> fail week -> ~52
  const span = 52;
  const caught = (d.week_caught / span) * 100;
  const fail = ((d.week_fail ?? span) / span) * 100;
  return (
    <section className="sentinel">
      <div className="eyebrow">● Deviation Sentinel — Critical</div>
      <h1>
        {d.component} battery autonomy {d.provided_value} {d.unit} vs{" "}
        {d.required_value} {d.unit} required
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
          have failed. That window is the difference between an email and a
          seven-figure schedule slip.
        </div>
      </div>

      <div className="timeline">
        <div className="track">
          <div
            className="fill"
            style={{ left: `${caught}%`, width: `${fail - caught}%` }}
          />
        </div>
        <div className="ticks">
          <span className="tick">
            W0 · build start
          </span>
          <span className="tick">
            <b>W{d.week_caught} · caught here</b>
          </span>
          <span className="tick fail">
            <b>
              W{d.week_fail} · {d.predicted_cx_test} fails
            </b>
          </span>
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
            {d.provided_value} {d.unit} provided
            <span className="ref">UPS battery datasheet, rev B</span>
          </div>
        </div>
        <div className="cell">
          <div className="k">Governing standard</div>
          <div className="v">
            Tier IV concurrent maintainability
            <span className="ref">{d.standard_ref}</span>
          </div>
        </div>
      </div>
    </section>
  );
}

export default async function Page() {
  const rows = await getRegister();
  const hero =
    rows.find((r) => r.component === "UPS-02") ?? rows[0];
  const critical = rows.filter((r) => r.severity === "Critical").length;

  return (
    <main className="wrap">
      <div className="topbar">
        <div className="brand">
          PRA<b>MAAN</b>
        </div>
        <div className="project">Project Meghdoot · 40 MW · Navi Mumbai</div>
        <div className="spacer" />
        <div className="tier">UPTIME TIER IV</div>
      </div>

      {hero && <Sentinel d={hero} />}

      <h2 className="section">
        Deviation register · {rows.length} findings · {critical} critical
      </h2>
      <DeviationRegister rows={rows} />
    </main>
  );
}
