import { SupplyChainAnalysis, Shipment } from "../lib/api";

// Zero-dependency equirectangular world map (no map lib, no tile token, SSR-safe).
// Projection is linear: x=(lon+180)/360·W, y=(90-lat)/180·H. Shipments render as
// origin→site Bezier arcs colored by delivery-risk band, over a graticule. A
// shipment table is the always-on semantic fallback.

const MW = 820;
const MH = 410;

// Representative coordinates by country (decimal degrees; W/S negative).
const COUNTRY: Record<string, [number, number]> = {
  US: [39.0, -77.5], USA: [39.0, -77.5], Germany: [50.1, 8.7], China: [31.2, 121.5],
  India: [19.1, 72.9], Norway: [59.9, 10.7], UAE: [25.2, 55.3], Japan: [35.7, 139.7],
  Australia: [-33.9, 151.2], Brazil: [-23.5, -46.6], UK: [51.5, -0.1], Canada: [43.7, -79.4],
  Ireland: [53.3, -6.3], Netherlands: [52.4, 4.9], Singapore: [1.35, 103.8],
};
const BAND_COLOR: Record<string, string> = {
  green: "var(--ok)", amber: "var(--warn)", red: "var(--fault)",
};

const xAt = (lon: number) => ((lon + 180) / 360) * MW;
const yAt = (lat: number) => ((90 - lat) / 180) * MH;

function coordsFor(place: string): [number, number] | null {
  if (!place) return null;
  if (COUNTRY[place]) return COUNTRY[place];
  const country = place.split(",").pop()?.trim() ?? "";
  return COUNTRY[country] ?? null;
}

function Arc({ s }: { s: Shipment }) {
  const o = coordsFor(s.origin_country);
  const d = coordsFor(s.destination_site);
  if (!o || !d) return null;
  const [x0, y0] = [xAt(o[1]), yAt(o[0])];
  const [x1, y1] = [xAt(d[1]), yAt(d[0])];
  const mx = (x0 + x1) / 2;
  const my = (y0 + y1) / 2;
  const cx = mx - (y1 - y0) * 0.18;
  const cy = my + (x1 - x0) * 0.18;
  const color = BAND_COLOR[s.delivery_risk.band] ?? "var(--muted)";
  return (
    <g>
      <path d={`M ${x0} ${y0} Q ${cx} ${cy} ${x1} ${y1}`} fill="none"
        stroke={color} strokeWidth={s.at_risk ? 2 : 1.2} opacity={0.8}
        strokeDasharray={s.at_risk ? "5 3" : undefined} />
      <circle cx={x0} cy={y0} r={3} fill="var(--muted)" />
      <circle cx={x1} cy={y1} r={4.5} fill={color} stroke="var(--bg, #0b0e13)" strokeWidth={1} />
    </g>
  );
}

export default function SupplyChainPanel({ analysis }: { analysis: SupplyChainAnalysis }) {
  const s = analysis.summary;
  const graticule: number[] = [];
  for (let lon = -150; lon <= 150; lon += 30) graticule.push(lon);
  const latLines: number[] = [];
  for (let lat = -60; lat <= 60; lat += 30) latLines.push(lat);

  // Label the real shipment endpoints (origins + the destination site) so the
  // arcs are legible without any fabricated coastlines. Dedupe by pixel position
  // since several shipments share the same origin/destination.
  const labels = new Map<string, { x: number; y: number; text: string; dest: boolean }>();
  for (const sh of analysis.shipments) {
    const o = coordsFor(sh.origin_country);
    const d = coordsFor(sh.destination_site);
    if (o) {
      const x = xAt(o[1]), y = yAt(o[0]);
      labels.set(`${Math.round(x)},${Math.round(y)}`, { x, y, text: sh.origin_country, dest: false });
    }
    if (d) {
      const x = xAt(d[1]), y = yAt(d[0]);
      const short = sh.destination_site.split(",")[0].trim() || sh.destination_site;
      labels.set(`${Math.round(x)},${Math.round(y)}`, { x, y, text: short, dest: true });
    }
  }

  return (
    <div className="sc">
      <div className="sc-summary">
        <div className="sc-pill"><span className="sc-pill-val">{s.total}</span>
          <span className="sc-pill-label">Long-lead items</span></div>
        <div className="sc-pill"><span className="sc-pill-val" style={{ color: "var(--fault)" }}>{s.at_risk}</span>
          <span className="sc-pill-label">At risk of slip</span></div>
        <div className="sc-pill"><span className="sc-pill-val" style={{ color: "var(--warn)" }}>{s.worst_score}</span>
          <span className="sc-pill-label">Worst delivery-risk</span></div>
      </div>

      {analysis.narrative && <p className="sr-narrative">{analysis.narrative.narrative}</p>}

      <svg className="sc-map" viewBox={`0 0 ${MW} ${MH}`} role="img"
        aria-label={`Supply-chain map: ${s.at_risk} of ${s.total} shipments at risk`}>
        {graticule.map((lon) => (
          <line key={`v${lon}`} x1={xAt(lon)} y1={0} x2={xAt(lon)} y2={MH} stroke="var(--line)" strokeWidth={0.5} opacity={0.5} />
        ))}
        {latLines.map((lat) => (
          <line key={`h${lat}`} x1={0} y1={yAt(lat)} x2={MW} y2={yAt(lat)} stroke="var(--line)" strokeWidth={0.5} opacity={0.5} />
        ))}
        {analysis.shipments.map((sh) => <Arc key={sh.id} s={sh} />)}
        {[...labels.values()].map((p) => (
          <text key={`${p.x},${p.y}`} x={p.x} y={p.y - 9}
            fill={p.dest ? "var(--lead)" : "var(--muted)"}
            fontSize={11} fontWeight={p.dest ? 700 : 500}
            textAnchor={p.x > MW - 90 ? "end" : p.x < 90 ? "start" : "middle"}>
            {p.text}
          </text>
        ))}
        {/* legend — risk bands + at-risk styling, so the arcs read at a glance */}
        <g transform={`translate(14 ${MH - 20})`} fontSize={11}>
          <rect x={-8} y={-16} width={344} height={26} rx={6} fill="var(--panel)" opacity={0.65} />
          <circle cx={2} cy={0} r={4} fill="var(--ok)" />
          <text x={11} y={4} fill="var(--muted)">low risk</text>
          <circle cx={78} cy={0} r={4} fill="var(--warn)" />
          <text x={87} y={4} fill="var(--muted)">medium</text>
          <circle cx={150} cy={0} r={4} fill="var(--fault)" />
          <text x={159} y={4} fill="var(--muted)">high</text>
          <line x1={210} x2={236} y1={0} y2={0} stroke="var(--muted)" strokeWidth={2} strokeDasharray="5 3" />
          <text x={242} y={4} fill="var(--muted)">at-risk shipment</text>
        </g>
      </svg>

      {/* Horizontal scroll container: on phones the table is wider than the
          viewport, and body{overflow-x:hidden} would otherwise clip the right
          columns with no way to reach them (same pattern as .register-wrap). */}
      <div className="sc-table-wrap">
      <table className="sc-table">
        <thead>
          <tr>
            <th>Equipment</th><th>Supplier</th><th>Origin</th>
            <th>ETA P80</th><th>Need-by</th><th>Slack</th><th>P(late)</th><th>Delivery risk</th>
          </tr>
        </thead>
        <tbody>
          {analysis.shipments.map((sh) => (
            <tr key={sh.id}>
              <td>{sh.description}{sh.on_critical_path && <span title="on critical path"> ★</span>}</td>
              <td>{sh.supplier}{sh.supplier_risk.band !== "green" &&
                <span title="elevated supplier risk"> ⚠</span>}</td>
              <td>{sh.origin_country}</td>
              <td>wk {sh.eta_p80}</td>
              <td>wk {sh.required_on_site_week}</td>
              <td style={{ color: sh.slack_weeks < 0 ? "var(--fault)" : "var(--muted)" }}>
                {sh.slack_weeks > 0 ? "+" : ""}{sh.slack_weeks} wk</td>
              <td>{Math.round(sh.p_late * 100)}%</td>
              <td><span className={`sc-badge ${sh.delivery_risk.band}`}>{sh.delivery_risk.score}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
