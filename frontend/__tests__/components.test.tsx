import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import ScheduleRisk from "../components/ScheduleRisk";
import SupplyChainPanel from "../components/SupplyChainPanel";
import ProjectGraphView from "../components/ProjectGraph";
import { highlightDeviations } from "../components/DocumentDiff";
import {
  FALLBACK_SCHEDULE, FALLBACK_SUPPLY, FALLBACK_GRAPH,
  Deviation, ScheduleAnalysis, SupplyChainAnalysis, ProjectGraph,
} from "../lib/api";

// Render to a string; assert it doesn't throw and contains no "NaN"/"undefined"
// (which would mean a division-by-zero or unguarded field reached the DOM).
function render(el: React.ReactElement): string {
  const html = renderToStaticMarkup(el);
  expect(html).not.toContain("NaN");
  expect(html).not.toContain(">undefined<");
  return html;
}

// ── adversarial fixtures (the inputs most likely to crash) ──
const EMPTY_SCHEDULE: ScheduleAnalysis = {
  available: true, deadline_week: null,
  cpm: { tasks: {}, project_duration: 0, critical_path: [] },
  monte_carlo: {
    p50: 0, p80: 0, p90: 0, mean_finish: 0, on_time_probability: null,
    deadline_week: null, histogram: [], criticality_index: {}, sensitivity: {}, milestones: {},
  },
  baseline: { p50: 0, p80: 0, p90: 0, on_time_probability: null },
  deviation_impact: null, n_risks: 0,
};
const EMPTY_SUPPLY: SupplyChainAnalysis = {
  available: true, shipments: [],
  summary: { total: 0, at_risk: 0, by_band: {}, worst_item: null, worst_score: 0 },
};
const EMPTY_GRAPH: ProjectGraph = {
  available: true,
  stats: { nodes: 0, edges: 0, by_kind: {}, relationship_types: [] },
  graph: { nodes: [], edges: [] },
};

describe("ScheduleRisk", () => {
  it("renders with fallback data", () => {
    const html = render(<ScheduleRisk analysis={FALLBACK_SCHEDULE} />);
    expect(html).toContain("%");
  });
  it("survives empty/degenerate data without NaN", () => {
    render(<ScheduleRisk analysis={EMPTY_SCHEDULE} />);
  });
});

describe("SupplyChainPanel", () => {
  it("renders with fallback data", () => {
    render(<SupplyChainPanel analysis={FALLBACK_SUPPLY} />);
  });
  it("survives empty shipments without NaN", () => {
    render(<SupplyChainPanel analysis={EMPTY_SUPPLY} />);
  });
});

describe("ProjectGraphView", () => {
  it("renders with fallback data", () => {
    render(<ProjectGraphView graph={FALLBACK_GRAPH} />);
  });
  it("survives empty graph without NaN", () => {
    render(<ProjectGraphView graph={EMPTY_GRAPH} />);
  });
});

describe("DocumentDiff", () => {
  it("escapes document text while highlighting deviations", () => {
    const injected = '<img src=x onerror="alert(1)">';
    const deviation: Deviation = {
      component: "UPS-1",
      parameter: "battery_autonomy_min",
      required_value: 10,
      provided_value: injected,
      unit: "min",
      standard_ref: "Owner Basis",
      spec_clause: "UPS",
      severity: "Major",
      predicted_cx_test: "Integrated UPS autonomy test",
      predicted_cx_level: 4,
      week_caught: 8,
      week_fail: 32,
      lead_time_weeks: 24,
    };

    const html = render(highlightDeviations(`Vendor table: ${injected}`, [deviation], "submittal"));
    expect(html).toContain("diff-highlight-sub");
    expect(html).toContain("&lt;img");
    expect(html).not.toContain("<img src=");
    expect(html).not.toContain("dangerouslySetInnerHTML");
  });
});
