const STANDARDS = [
  {
    id: "UPTIME-TIER4",
    name: "Uptime Tier IV",
    scope: "Fault tolerance, 2N power, N+2 cooling",
    detail: "99.995% availability, 26.3 min/yr downtime, concurrent maintainability + fault tolerance",
    color: "#ff4d4d",
    deviations: 3,
  },
  {
    id: "TIA-942-C",
    name: "TIA-942-C",
    scope: "Cabling infrastructure, Rated 1–4",
    detail: "Cat6A copper, OS2/OM4 fibre, 800mm cabinet width, structured cabling topology",
    color: "#5b8cff",
    deviations: 0,
  },
  {
    id: "BICSI-002",
    name: "BICSI-002-2024",
    scope: "Data centre design, L1–L5 commissioning",
    detail: "48 cables/bundle max, 900mm raised floor, Red→White tag commissioning levels",
    color: "#35c98b",
    deviations: 1,
  },
  {
    id: "NFPA-75",
    name: "NFPA 75 / 262",
    scope: "Fire protection, plenum cable ratings",
    detail: "CMP (UL 910) mandatory for plenum, clean-agent suppression, VESDA detection",
    color: "#ffb020",
    deviations: 1,
  },
  {
    id: "ASHRAE",
    name: "ASHRAE TC 9.9",
    scope: "Thermal guidelines, Class A1–A4",
    detail: "18–27°C recommended, ≤60% RH, server inlet measurement, 5°C/hr max rate of change",
    color: "#36d6e7",
    deviations: 0,
  },
  {
    id: "IS-1893",
    name: "IS 1893:2016",
    scope: "Indian seismic zones II–V",
    detail: "Zone factors 0.10–0.36, importance factor I=1.5 for critical facilities",
    color: "#a78bfa",
    deviations: 0,
  },
  {
    id: "DESIGN-BASIS",
    name: "Design Basis (OPR)",
    scope: "Owner requirements — 40 MW, 8 data halls",
    detail: "Project Meghdoot specific: set-points, redundancy targets, equipment specs",
    color: "#8a96a8",
    deviations: 2,
  },
];

export default function StandardsKB() {
  return (
    <div className="standards-kb">
      <div className="standards-kb-grid">
        {STANDARDS.map((s) => (
          <div key={s.id} className="std-card" style={{ borderLeftColor: s.color }}>
            <div className="std-card-header">
              <span className="std-card-name" style={{ color: s.color }}>{s.name}</span>
              {s.deviations > 0 && (
                <span className="std-card-badge">
                  {s.deviations} {s.deviations === 1 ? "finding" : "findings"}
                </span>
              )}
            </div>
            <div className="std-card-scope">{s.scope}</div>
            <div className="std-card-detail">{s.detail}</div>
          </div>
        ))}
      </div>
      <div className="standards-kb-note">
        All standard content is paraphrased summaries — no copyrighted text reproduced.
        Real data sourced from public secondary references and verified against official publications.
      </div>
    </div>
  );
}
