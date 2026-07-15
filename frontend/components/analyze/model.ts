export interface AnalyzeDeviation {
  component: string;
  parameter: string;
  required_value: string | number;
  provided_value: string | number;
  unit: string;
  severity: string;
  rationale: string;
  standard_ref?: string;
  spec_clause?: string;
  predicted_cx_test?: string;
  lead_time_weeks?: number;
}

export interface CompoundCluster {
  kind: string;
  key: string | number;
  member_count: number;
  members: string[];
  compound_risk: number;
  earliest_week_fail: number | null;
}

export interface ScheduleCliff {
  week_fail: number;
  converging_deviations: number;
  compound_risk: number;
  deviations: string[];
}

export interface CompoundRisk {
  project_compound_risk: number;
  risk_band: "Critical" | "High" | "Moderate" | "Low";
  deviation_count: number;
  converged_cx_tests: Array<string | number>;
  schedule_cliff: ScheduleCliff | null;
  clusters: CompoundCluster[];
  method: string;
}

export interface RemediationAction {
  kind: "fix_deviation" | "clear_cluster";
  target: string;
  resolves: string[];
  risk_reduction: number;
  residual_project_risk: number;
  clears_schedule_cliff: boolean;
  new_schedule_cliff_week: number | null;
}

export interface Remediation {
  actions: RemediationAction[];
  highest_leverage: RemediationAction | null;
  has_convergence: boolean;
  note: string;
  method: string;
}

export interface AnalyzeResult {
  system: string;
  deviations: AnalyzeDeviation[];
  count: number;
  elapsed_ms: number;
  mode: string;
  compound_risk?: CompoundRisk;
  remediation?: Remediation;
  timing?: {
    standards_load_ms: number;
    llm_call_ms: number | null;
    postprocess_ms: number;
    provider: string | null;
  };
}

export type InputMode = "text" | "pdf";

export function formatElapsed(ms: number | undefined | null): string {
  if (ms == null || Number.isNaN(ms)) return "—";
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)} ms`;
}

export function timingTitle(timing: AnalyzeResult["timing"]): string {
  if (!timing) return "Total analysis time.";
  const parts = [`Standards load: ${formatElapsed(timing.standards_load_ms)}`];
  if (timing.llm_call_ms != null) parts.push(`LLM call: ${formatElapsed(timing.llm_call_ms)}`);
  parts.push(`Post-processing: ${formatElapsed(timing.postprocess_ms)}`);
  if (timing.provider) parts.push(`Provider: ${timing.provider}`);
  return parts.join(" · ");
}

export function provenance(mode: string): { label: string; cls: string; title: string } {
  switch (mode) {
    case "llm":
      return {
        label: "Live LLM reasoning",
        cls: "prov-llm",
        title: "A configured LLM provider answered. Availability failover is scored the same regardless of provider.",
      };
    case "vision":
      return {
        label: "Vision (image) reasoning",
        cls: "prov-llm",
        title: "The configured vision provider read values directly from the uploaded image.",
      };
    case "vision-unavailable":
      return {
        label: "Vision unavailable",
        cls: "prov-rule",
        title: "The vision provider could not be reached; no findings were fabricated.",
      };
    case "deterministic":
    case "rule":
      return {
        label: "Deterministic rule floor",
        cls: "prov-rule",
        title: "No model provider was reachable, so the deterministic rule engine answered from the submitted documents. It is a low-recall availability floor, never seeded data.",
      };
    default:
      return {
        label: "Provenance unknown",
        cls: "prov-rule",
        title: "This result did not report how it was produced; treat it cautiously.",
      };
  }
}

export function isModelBacked(mode: string): boolean {
  return mode === "llm" || mode === "vision";
}

export function friendlyError(raw: string): string {
  const value = (raw || "").toLowerCase();
  if (value.includes("429") || value.includes("rate limit")) {
    return "Rate limit reached — the public demo caps requests per IP. Wait a moment and try again.";
  }
  if (value.includes("401") || value.includes("403") || value.includes("auth")) {
    return "This deployment requires an access token for analysis. Use the public demo or provide valid credentials.";
  }
  if (value.includes("413") || value.includes("too large")) {
    return "That upload is over the 15 MB limit. Try a smaller PDF or paste the text instead.";
  }
  if (value.includes("415") || value.includes("unsupported") || value.includes("mime")) {
    return "That file type was rejected. Use a PDF, image, MD, or TXT — or paste the text.";
  }
  if (/http 5\d\d/.test(value) || value.includes("temporarily unavailable")) {
    return "The analysis service is temporarily unavailable. Retry, or use the local text engine.";
  }
  if (value.includes("not connected") || value.includes("failed to fetch") || value.includes("networkerror")) {
    return "Backend not reachable — a cold service can take about 30 seconds to wake. Retry, or use the local text engine.";
  }
  return raw;
}
