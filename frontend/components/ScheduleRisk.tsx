import { ScheduleAnalysis } from "../lib/api";

// Hand-rolled SVG/CSS (no chart lib), server-rendered from props. Shows the
// deviation→schedule "slip card" money-shot, the Monte-Carlo finish-week
// distribution with P50/P80/P90 + deadline markers, and the sensitivity tornado.

const W = 820;
const H = 210;
const PAD_L = 10;
const PAD_R = 10;
const PAD_T = 34; // headroom for up to two rows of staggered percentile labels
const PAD_B = 30;

function pct(p: number | null | undefined): string {
  return p === null || p === undefined ? "—" : `${Math.round(p * 100)}%`;
}

export default function ScheduleRisk({ analysis }: { analysis: ScheduleAnalysis }) {
  const mc = analysis.monte_carlo;
  const base = analysis.baseline;
  const imp = analysis.deviation_impact;
  const bins = mc.histogram ?? [];
  const deadline = mc.deadline_week ?? analysis.deadline_week ?? null;

  const xs = [
    ...bins.map((b) => b.x0), ...bins.map((b) => b.x1),
    mc.p50, mc.p80, mc.p90, ...(deadline !== null ? [deadline] : []),
  ];
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const span = xMax - xMin || 1;
  const plotW = W - PAD_L - PAD_R;
  const plotH = H - PAD_T - PAD_B;
  const xAt = (w: number) => PAD_L + ((w - xMin) / span) * plotW;
  const maxCount = Math.max(...bins.map((b) => b.count), 1);

  const drivers = Object.entries(mc.sensitivity ?? {})
    .map(([id, v]) => ({ id, name: analysis.cpm.tasks[id]?.name ?? id, v: Math.abs(v) }))
    .sort((a, b) => b.v - a.v)
    .slice(0, 5);
  const maxSens = Math.max(...drivers.map((d) => d.v), 0.01);

  const markers: Array<[string, number, string]> = [
    ["P50", mc.p50, "var(--ok)"],
    ["P80", mc.p80, "var(--warn)"],
    ["P90", mc.p90, "var(--fault)"],
  ];

  // Stagger the percentile labels into up to two rows so close percentiles
  // (e.g. P80 70.2 vs P90 71.55) don't print on top of each other. Greedy:
  // prefer the upper row; drop to the lower row only when too near the last
  // label placed on the upper row.
  const LABEL_MIN_GAP = 58;
  const ROW_Y = [PAD_T - 22, PAD_T - 8];
  const rowLastX = [-Infinity, -Infinity];
  const markerLayout = markers
    .map(([lbl, wk, c]) => ({ lbl, wk, c, x: xAt(wk) }))
    .sort((a, b) => a.x - b.x)
    .map((m) => {
      let row = m.x - rowLastX[0] < LABEL_MIN_GAP ? 1 : 0;
      if (row === 1 && m.x - rowLastX[1] < LABEL_MIN_GAP) row = 0;
      rowLastX[row] = m.x;
      return { ...m, y: ROW_Y[row] };
    });

  return (
    <div className="sr">
      <div className="sr-slip">
        <div className="sr-stat">
          <div className="sr-stat-label">On-time probability · baseline</div>
          <div className="sr-stat-val ok">{pct(base.on_time_probability)}</div>
        </div>
        <div className="sr-arrow" aria-hidden>→</div>
        <div className="sr-stat">
          <div className="sr-stat-label">If {analysis.n_risks} deviations uncaught</div>
          <div className="sr-stat-val fault">{pct(imp?.at_risk_on_time)}</div>
        </div>
        <div className="sr-stat sr-stat-slip">
          <div className="sr-stat-label">{imp ? "Ready-for-service slip" : "Milestone slip"}</div>
          <div className="sr-stat-val warn">
            +{imp?.slip_weeks ?? 0}<span className="sr-unit"> wk</span>
          </div>
        </div>
      </div>

      {analysis.narrative && <p className="sr-narrative">{analysis.narrative.narrative}</p>}

      <div className="sr-chart-title">
        Monte-Carlo finish-week distribution ·{" "}
        {bins.reduce((s, b) => s + b.count, 0).toLocaleString()} trials
      </div>
      <svg className="sr-hist" viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label={`Finish-week distribution: P50 week ${mc.p50}, P80 week ${mc.p80}, P90 week ${mc.p90}${deadline !== null ? `, deadline week ${deadline}` : ""}`}>
        {bins.map((b, i) => {
          const x = xAt(b.x0);
          const w = Math.max(1, xAt(b.x1) - xAt(b.x0) - 1.5);
          const h = (b.count / maxCount) * plotH;
          const late = deadline !== null && b.x0 >= deadline;
          return (
            <rect key={i} x={x} y={PAD_T + plotH - h} width={w} height={h}
              fill={late ? "var(--fault)" : "var(--lead)"} opacity={late ? 0.85 : 0.55} rx={1} />
          );
        })}
        {markerLayout.map(({ lbl, wk, c, x, y }) => (
          <g key={lbl}>
            <line x1={x} x2={x} y1={PAD_T} y2={PAD_T + plotH}
              stroke={c} strokeWidth={1.5} strokeDasharray="4 3" />
            {/* faint connector from the staggered label down to the line top */}
            <line x1={x} x2={x} y1={y + 3} y2={PAD_T} stroke={c} strokeWidth={0.75} opacity={0.45} />
            <text x={x} y={y} fill={c} fontSize={12} textAnchor="middle">{lbl} · {wk}</text>
          </g>
        ))}
        {deadline !== null && (
          <g>
            <line x1={xAt(deadline)} x2={xAt(deadline)} y1={PAD_T} y2={H - PAD_B}
              stroke="var(--muted)" strokeWidth={1.5} />
            <text x={xAt(deadline)} y={H - PAD_B + 16} fill="var(--muted)" fontSize={12} textAnchor="middle">
              Deadline · wk {deadline}
            </text>
          </g>
        )}
      </svg>

      <div className="sr-chart-title">What drives the date · schedule sensitivity</div>
      <div className="sr-tornado">
        {drivers.map((d) => (
          <div className="sr-tor-row" key={d.id}>
            <span className="sr-tor-label">{d.name}</span>
            <span className="sr-tor-track">
              <span className="sr-tor-fill" style={{ width: `${(d.v / maxSens) * 100}%` }} />
            </span>
            <span className="sr-tor-val">{d.v.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
