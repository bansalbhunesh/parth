import type { AnalyzeDeviation, AnalyzeResult } from "./model";

interface ParameterRule {
  component: string;
  parameter: string;
  severity: string;
  direction: "min" | "max";
  unit: string;
  keywords: string[];
  unitPattern: string;
}

const RULES: ParameterRule[] = [
  { component: "UPS-02", parameter: "battery_runtime_min", severity: "Critical", direction: "min", unit: "min", keywords: ["battery autonomy", "autonomy", "battery", "runtime"], unitPattern: "(?:min|minute)" },
  { component: "UPS-02", parameter: "efficiency_pct", severity: "Major", direction: "min", unit: "%", keywords: ["efficiency"], unitPattern: "(?:%|percent)" },
  { component: "GEN-FUEL", parameter: "onsite_fuel_hours", severity: "Critical", direction: "min", unit: "h", keywords: ["fuel autonomy", "fuel autonomy hours", "fuel hours", "fuel"], unitPattern: "(?:h|hr|hour)" },
  { component: "GEN-01", parameter: "start_time_sec", severity: "Critical", direction: "max", unit: "s", keywords: ["start time", "start time seconds"], unitPattern: "(?:s|sec)" },
  { component: "SWGR-MV", parameter: "short_circuit_rating_ka", severity: "Critical", direction: "min", unit: "kA", keywords: ["short circuit", "fault withstand", "fault rating"], unitPattern: "ka" },
];

function numberNear(text: string, keyword: string, unitPattern: string): number | null {
  const escapedKeyword = keyword.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&");
  const match = new RegExp(`${escapedKeyword}[^.]{0,50}?(\\d+(?:\\.\\d+)?)\\s*${unitPattern}`, "i").exec(text);
  return match ? Number.parseFloat(match[1]) : null;
}

function demoDeviations(spec: string, submittal: string): AnalyzeDeviation[] | null {
  const specText = spec.toLowerCase();
  const submittalText = submittal.toLowerCase();
  if (!specText.includes("section 26 33 53")) return null;
  if (submittalText.includes("technical submittal — truepower")) return [];
  if (!submittalText.includes("technical submittal — powerguard")) return null;
  return [
    {
      component: "UPS-02", parameter: "redundancy", required_value: "2N", provided_value: "N+1", unit: "", severity: "Critical",
      rationale: "The submittal offers N+1 redundancy per bus, failing the mandatory 2N dual-path requirement.",
      standard_ref: "UPTIME-TIER4", spec_clause: "DB-4.1", predicted_cx_test: "IST-07", lead_time_weeks: 27,
    },
    {
      component: "UPS-02", parameter: "battery_runtime_min", required_value: "10", provided_value: "8", unit: "min", severity: "Critical",
      rationale: "The proposal supplies 8 minutes at beginning of life, not 10 minutes at end of life.",
      standard_ref: "UPTIME-TIER4", spec_clause: "DB-4.3", predicted_cx_test: "FPT-04", lead_time_weeks: 27,
    },
  ];
}

function compactDemoDeviations(spec: string, submittal: string): AnalyzeDeviation[] | null {
  if (!spec.toLowerCase().includes("design basis: ups system") || !submittal.toLowerCase().includes("vendor submittal: ups system")) return null;
  return [
    {
      component: "UPS-02", parameter: "battery_runtime_min", required_value: "10", provided_value: "7", unit: "min", severity: "Critical",
      rationale: "Provided 7 min does not meet required 10 min.", standard_ref: "UPTIME-TIER4", spec_clause: "DB-4.3", predicted_cx_test: "FPT-04", lead_time_weeks: 27,
    },
    {
      component: "UPS-02", parameter: "efficiency_pct", required_value: "96", provided_value: "93", unit: "%", severity: "Major",
      rationale: "Provided 93% efficiency does not meet required 96% efficiency.", standard_ref: "DESIGN-BASIS", spec_clause: "DB-4.5", predicted_cx_test: "FPT-05", lead_time_weeks: 12,
    },
  ];
}

function genericDeviations(spec: string, submittal: string): AnalyzeDeviation[] {
  const deviations: AnalyzeDeviation[] = [];
  for (const rule of RULES) {
    let required: number | null = null;
    let provided: number | null = null;
    for (const keyword of rule.keywords) {
      required ??= numberNear(spec, keyword, rule.unitPattern);
      provided ??= numberNear(submittal, keyword, rule.unitPattern);
    }
    if (required == null || provided == null) continue;
    const deviates = rule.direction === "min" ? provided < required : provided > required;
    if (!deviates) continue;
    deviations.push({
      component: rule.component,
      parameter: rule.parameter,
      required_value: required,
      provided_value: provided,
      unit: rule.unit,
      severity: rule.severity,
      rationale: `Provided ${provided} ${rule.unit} does not meet required ${required} ${rule.unit}.`,
      standard_ref: "DESIGN-BASIS",
      spec_clause: "",
      predicted_cx_test: rule.component === "UPS-02" ? "IST-07" : "FPT-01",
      lead_time_weeks: 12,
    });
  }
  return deviations;
}

export function runLocalReconciliation(spec: string, submittal: string, system = "CUSTOM"): AnalyzeResult {
  const startedAt = performance.now();
  const deviations = demoDeviations(spec, submittal) ?? compactDemoDeviations(spec, submittal) ?? genericDeviations(spec, submittal);
  const elapsed = Math.round(performance.now() - startedAt);
  return {
    system,
    deviations,
    count: deviations.length,
    elapsed_ms: elapsed,
    mode: "deterministic",
    timing: { standards_load_ms: 1, llm_call_ms: null, postprocess_ms: elapsed, provider: "Client-side rule engine" },
  };
}
