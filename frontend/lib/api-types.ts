export interface Deviation {
  component: string;
  parameter: string;
  required_value: string | number;
  provided_value: string | number;
  unit: string;
  standard_ref: string;
  spec_clause: string;
  severity: "Critical" | "Major" | "Minor";
  rationale?: string;
  predicted_cx_test: string | null;
  predicted_cx_level: number | null;
  predicted_cx_name?: string | null;
  week_caught: number;
  week_fail: number | null;
  lead_time_weeks: number | null;
  confidence?: number;
  citation_faithful?: boolean;
  cx_source?: string;
}

export type RegisterProvenanceKind =
  | "live"
  | "deterministic"
  | "cached"
  | "bundled_reference"
  | "unavailable";

export interface RegisterProvenance {
  kind: RegisterProvenanceKind;
  label: string;
  description: string;
  live: boolean;
  sourceDocuments?: number;
}

export interface RegisterSnapshot {
  rows: Deviation[];
  analysisMode: string;
  provenance: RegisterProvenance;
}

export interface CxTest {
  id: string;
  level: number;
  name: string;
  scheduled_week: number;
  acceptance: string;
}

export interface CxPlan {
  project: string;
  cx_authority: string;
  levels: Record<string, string>;
  tests: CxTest[];
}

export interface CopilotResponse {
  answer: string;
  sources: string[];
  prior_rfis: Array<{
    id: string;
    system: string;
    status: string;
    question: string;
    resolution: string | null;
  }>;
}

export interface ProjectSummary {
  id: string;
  name: string;
  tier: string;
  location: string;
  capacity_mw: number;
  deviations: number;
  systems: number;
}

export interface MultiProjectEval {
  aggregate: {
    projects: number;
    total_deviations: number;
    aggregate_precision: number;
    aggregate_recall: number;
    aggregate_f1: number;
    aggregate_cx_accuracy: number;
    total_lead_time_weeks: number;
    max_lead_time_weeks: number;
  };
  per_project: Record<string, {
    name: string;
    tier: string;
    location: string;
    capacity_mw: number;
    deviations: number;
    precision: number;
    recall: number;
    f1: number;
    cx_accuracy: number;
    total_lead_weeks: number;
  }>;
}

export interface ScheduleTaskCPM {
  name: string; is_milestone: boolean; cx_level: number | null;
  es: number; ef: number; ls: number; lf: number;
  total_float: number; free_float: number; critical: boolean;
}
export interface ScheduleAnalysis {
  available: boolean;
  project_id?: string;
  deadline_week?: number | null;
  cpm: {
    tasks: Record<string, ScheduleTaskCPM>;
    project_duration: number;
    critical_path: string[];
  };
  monte_carlo: {
    p50: number; p80: number; p90: number; mean_finish: number;
    on_time_probability: number | null; deadline_week: number | null;
    histogram: Array<{ x0: number; x1: number; count: number }>;
    criticality_index: Record<string, number>;
    sensitivity: Record<string, number>;
    milestones: Record<string, { p50: number; p80: number }>;
  };
  baseline: { p50: number; p80: number; p90: number; on_time_probability: number | null };
  deviation_impact: {
    milestone: string; baseline_p80: number | null; at_risk_p80: number | null;
    slip_weeks: number | null; baseline_on_time: number | null; at_risk_on_time: number | null;
  } | null;
  n_risks: number;
  narrative?: { narrative: string; mode: string };
}

export interface Shipment {
  id: string; equipment_type: string; description: string; supplier: string;
  origin_country: string; destination_site: string; current_stage: string;
  required_on_site_week: number; eta_p50: number; eta_p80: number; sigma: number;
  p_late: number; slack_weeks: number;
  supplier_risk: { score: number; band: string; contributions: Record<string, number> };
  delivery_risk: { score: number; band: string; consequence: number };
  on_critical_path: boolean; at_risk: boolean; linked_task_id: string | null;
}
export interface SupplyChainAnalysis {
  available: boolean;
  project_id?: string; current_week?: number;
  shipments: Shipment[];
  summary: {
    total: number; at_risk: number; by_band: Record<string, number>;
    worst_item: string | null; worst_score: number;
  };
  narrative?: { narrative: string; mode: string };
}

export interface GraphNode { id: string; kind: string; label: string }
export interface GraphEdge { from: string; to: string; rel: string; basis?: string | null }
export interface ProjectGraph {
  available: boolean;
  stats: { nodes: number; edges: number; by_kind: Record<string, number>; relationship_types: string[] };
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
}
export interface BlastRadius {
  available: boolean;
  deviation?: string; component?: string;
  cx_tests_at_risk: Array<{ id: string; label: string }>;
  equipment: string[];
  suppliers: Array<{ id: string; label: string; lead_time_weeks: number | null }>;
  milestones: Array<{ id: string; label: string; planned_week: number | null; slip_weeks: number }>;
  weeks_at_risk: number; cx_planned_week: number; fix_complete_week: number;
  worst_milestone_slip: number; caught_in_time: boolean; reach_size: number;
}

export interface RemediationScenario { catch_week: number; slip_weeks: number; cost_lakh: number }
export interface RemediationSim {
  available: boolean;
  deviation?: string; component?: string;
  fix_lead_weeks: number; cx_planned_week: number; zero_slip_deadline_week: number;
  long_lead_trap: boolean; cost_per_week_lakh: number;
  scenarios: { design_review: RemediationScenario; pramaan: RemediationScenario; commissioning: RemediationScenario };
  slip_avoided_weeks: number; cost_avoided_lakh: number;
  curve: RemediationScenario[]; assumption: string;
}

export interface ExtractionMeta {
  method: string;          // text_layer | ocr_pdf | ocr_image | plain_text | none
  chars: number;
  ocr_used: boolean;
  truncated: boolean;
  warning: string | null;
}
export interface UploadExtraction {
  spec: ExtractionMeta;
  submittal: ExtractionMeta;
}

export interface OcrStatus {
  ocr_available: boolean;
  ocr_enabled: boolean;
  tesseract_installed: boolean;
  tesseract_version: string | null;
  image_ocr_supported: boolean;
  pdf_ocr_supported: boolean;
  max_pdf_pages: number;
  max_image_pixels: number;
  status: "ready" | "disabled" | "tesseract_not_installed";
}

export interface HealthStatus {
  ok: boolean;
  project: string;
  version: string;
  commit: string;
  llm: {
    provider: string;
    key_set: boolean;
    model?: string;
    chain: string[];
    ready: boolean;
  };
  analysis_mode: string;
  ocr_available: boolean;
  security: {
    auth_required: boolean;
    rate_limit_enabled: boolean;
    rate_limits_per_hour: Record<string, number> | null;
    max_upload_mb: number;
    max_pdf_pages: number;
    max_image_pixels: number;
    cors_locked: boolean;
    ocr_available: boolean;
  };
  scalability?: Record<string, unknown>;
}
