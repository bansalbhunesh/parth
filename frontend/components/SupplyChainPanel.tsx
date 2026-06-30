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
      </svg>

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
  );
}
