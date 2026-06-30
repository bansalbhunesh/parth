import { ProjectGraph } from "../lib/api";

// Columnar node-link view of the unified project graph: deviations -> standards/
// equipment -> Cx tests -> schedule tasks -> milestone -> suppliers. Hand-rolled
// SVG, server-rendered. Columns are capped for legibility; the stat header carries
// the full scale.

const COLS = ["deviation", "standard", "equipment", "cx_test", "schedule_task", "milestone", "supplier"];
const KIND_COLOR: Record<string, string> = {
  deviation: "var(--fault)", standard: "var(--muted)", equipment: "var(--accent)",
  cx_test: "var(--lead)", schedule_task: "var(--warn)", milestone: "var(--ok)", supplier: "var(--accent)",
};
const KIND_LABEL: Record<string, string> = {
  deviation: "Deviations", standard: "Standards", equipment: "Equipment", cx_test: "Cx tests",
  schedule_task: "Schedule", milestone: "Milestone", supplier: "Suppliers",
};
const CAP = 12;
const W = 980;
const NODE_W = 112;
const NODE_H = 20;
const GAP = 6;
const TOP = 40;

export default function ProjectGraphView({ graph }: { graph: ProjectGraph }) {
  const kinds = COLS.filter((k) => graph.graph.nodes.some((n) => n.kind === k));
  const colW = W / Math.max(kinds.length, 1);
  const pos: Record<string, { x: number; y: number; color: string }> = {};
  let maxRows = 0;
  kinds.forEach((k, ci) => {
    const nodes = graph.graph.nodes.filter((n) => n.kind === k).slice(0, CAP);
    maxRows = Math.max(maxRows, nodes.length);
    nodes.forEach((n, i) => {
      pos[n.id] = {
        x: ci * colW + colW / 2,
        y: TOP + i * (NODE_H + GAP) + NODE_H / 2,
        color: KIND_COLOR[k] ?? "var(--muted)",
      };
    });
  });
  const H = TOP + maxRows * (NODE_H + GAP) + 16;
  const edges = graph.graph.edges.filter((e) => pos[e.from] && pos[e.to]);

  return (
    <div className="pg">
      <div className="pg-stats">
        <span className="pg-kind"><b>{graph.stats.nodes}</b> nodes</span>
        <span className="pg-kind"><b>{graph.stats.edges}</b> edges</span>
        {Object.entries(graph.stats.by_kind).map(([k, c]) => (
          <span className="pg-kind" key={k}><b>{c}</b> {KIND_LABEL[k] ?? k}</span>
        ))}
      </div>
      <svg className="pg-svg" viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label={`Unified project graph: ${graph.stats.nodes} nodes and ${graph.stats.edges} relationships across ${kinds.length} domains`}>
        {kinds.map((k, ci) => (
          <text key={k} x={ci * colW + colW / 2} y={18} fill="var(--muted)" fontSize={12} textAnchor="middle">
            {(KIND_LABEL[k] ?? k).toUpperCase()}
          </text>
        ))}
        {edges.map((e, i) => {
          const a = pos[e.from];
          const b = pos[e.to];
          return (
            <line key={i} x1={a.x + NODE_W / 2} y1={a.y} x2={b.x - NODE_W / 2} y2={b.y}
              stroke="var(--line)" strokeWidth={0.7} opacity={0.55} />
          );
        })}
        {graph.graph.nodes.filter((n) => pos[n.id]).map((n) => {
          const p = pos[n.id];
          return (
            <g key={n.id}>
              <rect x={p.x - NODE_W / 2} y={p.y - NODE_H / 2} width={NODE_W} height={NODE_H} rx={4}
                fill="var(--panel)" stroke={p.color} strokeWidth={1} />
              <text x={p.x} y={p.y + 3.5} fill="var(--muted)" fontSize={10} textAnchor="middle">
                {(n.label || n.id).slice(0, 17)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
