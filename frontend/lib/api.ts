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

const API = process.env.NEXT_PUBLIC_API ?? "http://localhost:8000";

// Time-box server-rendered data fetches. A cold Render free-tier backend can
// take 30s+ to wake; without a timeout the page render blocks on it. With one,
// we render instantly from the bundled fallback data if the API is slow.
const FETCH_TIMEOUT_MS = 2500;

function fetchOpts(opts: RequestInit = {}): RequestInit {
  try {
    return { ...opts, signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) };
  } catch {
    return opts; // AbortSignal.timeout unavailable (very old runtime) — skip
  }
}


async function consumeSSE(
  response: Response,
  handlers: Record<string, (data: string) => void>,
): Promise<void> {
  if (!response.body) return;
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        const handler = handlers[currentEvent];
        if (handler) handler(line.slice(6));
      }
    }
  }
}


export async function getRegister(): Promise<Deviation[]> {
  try {
    // Cacheable so the page can be ISR-rendered (instant reloads); refreshed
    // in the background every 10 min. Timeout still guards the background fetch.
    const r = await fetch(`${API}/deviations`, fetchOpts({ next: { revalidate: 600 } }));
    if (!r.ok) throw new Error(String(r.status));
    const data = await r.json();
    return data.register as Deviation[];
  } catch {
    return FALLBACK;
  }
}

export async function getCxPlan(): Promise<CxPlan | null> {
  try {
    const r = await fetch(`${API}/cx-plan`, fetchOpts({ next: { revalidate: 600 } }));
    if (!r.ok) throw new Error(String(r.status));
    return await r.json();
  } catch {
    return FALLBACK_CX_PLAN;
  }
}

export async function askCopilot(query: string): Promise<CopilotResponse> {
  try {
    const r = await fetch(`${API}/copilot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
      cache: "no-store",
    });
    if (!r.ok) throw new Error(String(r.status));
    return await r.json();
  } catch {
    return {
      answer: "Backend not connected. In production, the copilot searches across all project documents (specs, submittals, standards, RFI log) and returns cited answers with prior-RFI matching.",
      sources: [],
      prior_rfis: [],
    };
  }
}

export async function streamCopilot(
  query: string,
  onMeta: (meta: { sources: string[]; prior_rfis: CopilotResponse["prior_rfis"] }) => void,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: string) => void,
): Promise<void> {
  try {
    const r = await fetch(`${API}/copilot/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!r.ok || !r.body) throw new Error(`HTTP ${r.status}`);

    await consumeSSE(r, {
      meta: (data) => { try { onMeta(JSON.parse(data)); } catch {} },
      token: (data) => { try { onToken(JSON.parse(data)); } catch { onToken(data); } },
      done: () => { onDone(); },
    });
    onDone();
  } catch {
    onError("Backend not connected. Ensure the API is running at localhost:8000.");
  }
}

export async function streamAnalyze(
  specText: string,
  submittalText: string,
  onStatus: (status: string) => void,
  onToken: (token: string) => void,
  onResult: (result: unknown) => void,
  onDone: () => void,
  onError: (err: string) => void,
): Promise<void> {
  try {
    const r = await fetch(`${API}/analyze/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ spec_text: specText, submittal_text: submittalText }),
    });
    if (!r.ok || !r.body) throw new Error(`HTTP ${r.status}`);

    await consumeSSE(r, {
      status: (data) => onStatus(data),
      token: (data) => { try { onToken(JSON.parse(data)); } catch { onToken(data); } },
      result: (data) => { try { onResult(JSON.parse(data)); } catch {} },
      done: () => { onDone(); },
    });
    onDone();
  } catch {
    onError("Analysis failed — backend not connected.");
  }
}

export async function streamUploadAnalyze(
  formData: FormData,
  handlers: {
    onStatus: (status: string) => void;
    onPreview: (preview: { spec: string; submittal: string }) => void;
    onToken: (token: string) => void;
    onResult: (result: unknown) => void;
    onError: (err: string) => void;
    onDone: () => void;
  },
): Promise<void> {
  try {
    const r = await fetch(`${API}/analyze/upload/stream`, {
      method: "POST",
      body: formData,
    });
    if (!r.ok || !r.body) throw new Error(`HTTP ${r.status}`);

    await consumeSSE(r, {
      status: (data) => handlers.onStatus(data),
      preview: (data) => { try { handlers.onPreview(JSON.parse(data)); } catch {} },
      token: (data) => {
        try { handlers.onToken(JSON.parse(data)); } catch { handlers.onToken(data); }
      },
      result: (data) => { try { handlers.onResult(JSON.parse(data)); } catch {} },
      error: (data) => handlers.onError(data),
      done: () => { handlers.onDone(); },
    });
    handlers.onDone();
  } catch (e) {
    handlers.onError(e instanceof Error ? e.message : "Upload failed");
  }
}

export async function getMetrics(): Promise<Record<string, unknown> | null> {
  try {
    const r = await fetch(`${API}/metrics`, fetchOpts({ cache: "no-store" }));
    if (!r.ok) throw new Error(String(r.status));
    return await r.json();
  } catch {
    return null;
  }
}

export async function getProjects(): Promise<ProjectSummary[]> {
  try {
    const r = await fetch(`${API}/projects`, fetchOpts({ cache: "no-store" }));
    if (!r.ok) throw new Error(String(r.status));
    const data = await r.json();
    return data.projects as ProjectSummary[];
  } catch {
    return FALLBACK_PROJECTS;
  }
}

export async function getMultiProjectEval(): Promise<MultiProjectEval | null> {
  try {
    const r = await fetch(`${API}/projects/eval/aggregate`, fetchOpts({ cache: "no-store" }));
    if (!r.ok) throw new Error(String(r.status));
    return await r.json();
  } catch {
    return FALLBACK_MULTI_EVAL;
  }
}

const FALLBACK_PROJECTS: ProjectSummary[] = [
  { id: "meghdoot", name: "Project Meghdoot", tier: "Uptime Tier IV", location: "Navi Mumbai, India", capacity_mw: 40, deviations: 14, systems: 10 },
  { id: "vajra", name: "Project Vajra", tier: "Uptime Tier III", location: "Pune, India", capacity_mw: 20, deviations: 4, systems: 8 },
  { id: "nordic", name: "Project Nordic Edge", tier: "EN 50600 Class 3", location: "Oslo, Norway", capacity_mw: 10, deviations: 5, systems: 7 },
  { id: "sahara", name: "Project Sahara", tier: "Uptime Tier II", location: "Dubai, UAE", capacity_mw: 5, deviations: 3, systems: 6 },
  { id: "cascade", name: "Project Cascade", tier: "Uptime Tier IV", location: "Hillsboro, Oregon, USA", capacity_mw: 30, deviations: 4, systems: 8 },
  { id: "yangtze", name: "Project Yangtze", tier: "GB 50174 Grade A", location: "Shanghai, China", capacity_mw: 50, deviations: 3, systems: 8 },
  { id: "athena", name: "Project Athena", tier: "EN 50600 Class 4", location: "Frankfurt, Germany", capacity_mw: 15, deviations: 4, systems: 8 },
  { id: "sakura", name: "Project Sakura", tier: "JEITA Class 4", location: "Tokyo, Japan", capacity_mw: 25, deviations: 3, systems: 8 },
  { id: "outback", name: "Project Outback", tier: "Uptime Tier III", location: "Sydney, Australia", capacity_mw: 8, deviations: 3, systems: 7 },
  { id: "maple", name: "Project Maple", tier: "Uptime Tier III", location: "Toronto, Canada", capacity_mw: 12, deviations: 3, systems: 7 },
  { id: "pampas", name: "Project Pampas", tier: "Uptime Tier II", location: "São Paulo, Brazil", capacity_mw: 6, deviations: 2, systems: 6 },
  { id: "thames", name: "Project Thames", tier: "Uptime Tier IV", location: "London, United Kingdom", capacity_mw: 35, deviations: 2, systems: 8 },
];

const FALLBACK_MULTI_EVAL: MultiProjectEval = {
  aggregate: {
    projects: 12,
    total_deviations: 50,
    aggregate_precision: 1.0,
    aggregate_recall: 1.0,
    aggregate_f1: 1.0,
    aggregate_cx_accuracy: 1.0,
    total_lead_time_weeks: 1024,
    max_lead_time_weeks: 36,
  },
  per_project: {
    meghdoot: { name: "Project Meghdoot", tier: "Uptime Tier IV", location: "Navi Mumbai, India", capacity_mw: 40, deviations: 14, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 267 },
    vajra: { name: "Project Vajra", tier: "Uptime Tier III", location: "Pune, India", capacity_mw: 20, deviations: 4, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 95 },
    nordic: { name: "Project Nordic Edge", tier: "EN 50600 Class 3", location: "Oslo, Norway", capacity_mw: 10, deviations: 5, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 113 },
    sahara: { name: "Project Sahara", tier: "Uptime Tier II", location: "Dubai, UAE", capacity_mw: 5, deviations: 3, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 38 },
    cascade: { name: "Project Cascade", tier: "Uptime Tier IV", location: "Hillsboro, Oregon, USA", capacity_mw: 30, deviations: 4, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 80 },
    yangtze: { name: "Project Yangtze", tier: "GB 50174 Grade A", location: "Shanghai, China", capacity_mw: 50, deviations: 3, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 98 },
    athena: { name: "Project Athena", tier: "EN 50600 Class 4", location: "Frankfurt, Germany", capacity_mw: 15, deviations: 4, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 80 },
    sakura: { name: "Project Sakura", tier: "JEITA Class 4", location: "Tokyo, Japan", capacity_mw: 25, deviations: 3, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 58 },
    outback: { name: "Project Outback", tier: "Uptime Tier III", location: "Sydney, Australia", capacity_mw: 8, deviations: 3, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 53 },
    maple: { name: "Project Maple", tier: "Uptime Tier III", location: "Toronto, Canada", capacity_mw: 12, deviations: 3, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 58 },
    pampas: { name: "Project Pampas", tier: "Uptime Tier II", location: "São Paulo, Brazil", capacity_mw: 6, deviations: 2, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 34 },
    thames: { name: "Project Thames", tier: "Uptime Tier IV", location: "London, United Kingdom", capacity_mw: 35, deviations: 2, precision: 1.0, recall: 1.0, f1: 1.0, cx_accuracy: 1.0, total_lead_weeks: 50 },
  },
};

export const FALLBACK_CX_PLAN: CxPlan = {
  project: "Project Meghdoot",
  cx_authority: "DCx International (India)",
  levels: {
    "1": "Factory inspections & witness tests (ITP)",
    "2": "Installation verification & inspection (ITP)",
    "3": "Functional / factory acceptance test (FAT)",
    "4": "Integrated systems test (IST)",
    "5": "Owner acceptance & sustained operations",
  },
  tests: [
    { id: "ITP-01", level: 1, name: "Equipment receipt inspection", scheduled_week: 16, acceptance: "Visual + documentation check" },
    { id: "ITP-02", level: 2, name: "Cable fire-rating / plenum compliance inspection", scheduled_week: 22, acceptance: "Cable marking matches CMP" },
    { id: "ITP-03", level: 2, name: "Arc flash labeling and PPE verification", scheduled_week: 20, acceptance: "Arc flash labels match incident energy calculations" },
    { id: "ITP-04", level: 2, name: "Pathway fill and cable management inspection", scheduled_week: 18, acceptance: "Bundle sizes within BICSI-002 fill limits" },
    { id: "ITP-05", level: 1, name: "Structural load test and floor deflection", scheduled_week: 19, acceptance: "Floor deflection within L/360 under design load" },
    { id: "FAT-01", level: 3, name: "UPS module load-bank test", scheduled_week: 24, acceptance: "Full load sustained 4 hours" },
    { id: "FAT-02", level: 3, name: "Generator load-bank test", scheduled_week: 26, acceptance: "110% load for 2 hours" },
    { id: "FAT-03", level: 3, name: "Protection coordination / fault-withstand verification", scheduled_week: 30, acceptance: "Fault withstand >= prospective fault" },
    { id: "IST-01", level: 4, name: "Utility failure simulation", scheduled_week: 34, acceptance: "Zero IT load impact" },
    { id: "IST-05", level: 4, name: "Single-path maintenance simulation", scheduled_week: 36, acceptance: "Full load on single path" },
    { id: "IST-07", level: 4, name: "Load transfer under maintenance (battery autonomy)", scheduled_week: 38, acceptance: "Battery sustains load during transfer" },
    { id: "IST-09", level: 4, name: "Cooling failover under fault + maintenance", scheduled_week: 39, acceptance: "Temperature maintained within ASHRAE" },
    { id: "IST-11", level: 4, name: "Sustained utility-outage run (fuel autonomy)", scheduled_week: 41, acceptance: "Full design-duration outage" },
    { id: "IST-14", level: 4, name: "Monitoring & alarm verification", scheduled_week: 40, acceptance: "All critical alarms fire" },
    { id: "IST-15", level: 4, name: "Full-facility failover drill", scheduled_week: 44, acceptance: "Zero downtime during drill" },
    { id: "IST-16", level: 4, name: "Cooling performance and thermal verification", scheduled_week: 36, acceptance: "Delta-T and flow rates meet design criteria" },
    { id: "SAT-01", level: 5, name: "72-hour sustained operations test", scheduled_week: 48, acceptance: "No critical alarms for 72 hours" },
  ],
};

export const FALLBACK: Deviation[] = [
  {
    component: "UPS-02", parameter: "battery_runtime_min",
    required_value: 10, provided_value: 7, unit: "min",
    standard_ref: "UPTIME-TIER4", spec_clause: "DB-4.3", severity: "Critical",
    rationale: "Battery autonomy below Tier IV requirement; UPS cannot sustain load during concurrent maintenance of the alternate path.",
    predicted_cx_test: "IST-07", predicted_cx_level: 4,
    predicted_cx_name: "Load transfer under maintenance (battery autonomy)",
    week_caught: 11, week_fail: 38, lead_time_weeks: 27,
  },
  {
    component: "GEN-FUEL", parameter: "onsite_fuel_hours",
    required_value: 24, provided_value: 12, unit: "h",
    standard_ref: "UPTIME-TIER4", spec_clause: "DB-5.4", severity: "Critical",
    rationale: "On-site fuel autonomy below Tier IV minimum; generators cannot sustain a full design-duration outage.",
    predicted_cx_test: "IST-11", predicted_cx_level: 4,
    predicted_cx_name: "Sustained utility-outage run (fuel autonomy)",
    week_caught: 11, week_fail: 41, lead_time_weeks: 30,
  },
  {
    component: "COOL-LOOP", parameter: "redundancy",
    required_value: "N+2", provided_value: "N+1", unit: "topology",
    standard_ref: "UPTIME-TIER4", spec_clause: "DB-6.1", severity: "Critical",
    rationale: "N+1 cooling cannot maintain fault tolerance during concurrent maintenance as Tier IV demands.",
    predicted_cx_test: "IST-09", predicted_cx_level: 4,
    predicted_cx_name: "Cooling failover under fault + maintenance",
    week_caught: 11, week_fail: 39, lead_time_weeks: 28,
  },
  {
    component: "SWGR-MV", parameter: "short_circuit_rating_ka",
    required_value: 50, provided_value: 40, unit: "kA",
    standard_ref: "DESIGN-BASIS", spec_clause: "DB-7.2", severity: "Critical",
    rationale: "Switchgear withstand rating below calculated prospective fault level.",
    predicted_cx_test: "FAT-03", predicted_cx_level: 3,
    predicted_cx_name: "Protection coordination / fault-withstand verification",
    week_caught: 11, week_fail: 30, lead_time_weeks: 19,
  },
  {
    component: "CABLE-DC", parameter: "fire_rating",
    required_value: "CMP", provided_value: "CMR", unit: "plenum-class",
    standard_ref: "NFPA-75", spec_clause: "DB-8.4", severity: "Major",
    rationale: "Cable fire-rating below plenum class required per NFPA 75.",
    predicted_cx_test: "ITP-02", predicted_cx_level: 2,
    predicted_cx_name: "Cable fire-rating / plenum compliance inspection",
    week_caught: 11, week_fail: 22, lead_time_weeks: 11,
  },
  {
    component: "BMS", parameter: "critical_alarm_points",
    required_value: "complete", provided_value: "missing:leak_detection",
    unit: "set", standard_ref: "DESIGN-BASIS", spec_clause: "DB-9.5",
    severity: "Major",
    rationale: "Critical leak-detection alarm point absent; monitoring cannot confirm full alarm coverage.",
    predicted_cx_test: "IST-14", predicted_cx_level: 4,
    predicted_cx_name: "Monitoring & alarm verification",
    week_caught: 11, week_fail: 40, lead_time_weeks: 29,
  },
  {
    component: "FLOOR", parameter: "height_mm",
    required_value: 900, provided_value: 600, unit: "mm",
    standard_ref: "DESIGN-BASIS", spec_clause: "DB-13.3",
    severity: "Major",
    rationale: "Raised floor height 600 mm vs required 900 mm; insufficient clearance for under-floor chilled-air distribution, power cabling, and fire suppression piping.",
    predicted_cx_test: "ITP-01", predicted_cx_level: 1,
    predicted_cx_name: "Equipment receipt inspection",
    week_caught: 11, week_fail: 16, lead_time_weeks: 5,
  },
  {
    component: "GEN-01", parameter: "start_time_sec",
    required_value: 10, provided_value: 15, unit: "s",
    standard_ref: "UPTIME-TIER4", spec_clause: "DB-5.3",
    severity: "Critical",
    rationale: "Generator start time exceeds Tier IV 10-second requirement; during utility failure, the additional 5-second delay risks UPS battery depletion on the concurrent maintenance path.",
    predicted_cx_test: "IST-01", predicted_cx_level: 4,
    predicted_cx_name: "Utility failure simulation",
    week_caught: 11, week_fail: 34, lead_time_weeks: 23,
  },
  {
    component: "COOL-LOOP", parameter: "delta_t_c",
    required_value: 10, provided_value: 7, unit: "C",
    standard_ref: "ASHRAE-TC9.9", spec_clause: "DB-6.4",
    severity: "Major",
    rationale: "Chilled water delta-T of 7°C vs required 10°C indicates low delta-T syndrome; pumps must increase flow 43% to meet heat rejection.",
    predicted_cx_test: "IST-16", predicted_cx_level: 4,
    predicted_cx_name: "Cooling performance and thermal verification",
    week_caught: 11, week_fail: 36, lead_time_weeks: 25,
  },
  {
    component: "UPS-02", parameter: "efficiency_pct",
    required_value: 96, provided_value: 93, unit: "%",
    standard_ref: "DESIGN-BASIS", spec_clause: "DB-4.5",
    severity: "Major",
    rationale: "UPS efficiency 93% vs required 96% adds 36 kW heat load per module at rated load; cooling plant not sized for additional heat rejection.",
    predicted_cx_test: "FAT-01", predicted_cx_level: 3,
    predicted_cx_name: "UPS module load-bank test",
    week_caught: 11, week_fail: 24, lead_time_weeks: 13,
  },
  {
    component: "SWGR-MV", parameter: "arc_flash_rating",
    required_value: "Type_2B", provided_value: "Type_2", unit: "class",
    standard_ref: "DESIGN-BASIS", spec_clause: "DB-7.3",
    severity: "Major",
    rationale: "Switchgear Type 2 vs required Type 2B exposes operators to incident energy above 40 cal/cm²; PPE category exceeds safe working practice limits.",
    predicted_cx_test: "ITP-03", predicted_cx_level: 2,
    predicted_cx_name: "Arc flash labeling and PPE verification",
    week_caught: 11, week_fail: 20, lead_time_weeks: 9,
  },
  {
    component: "CABLE-DC", parameter: "max_bundle_size",
    required_value: 48, provided_value: 72, unit: "cables",
    standard_ref: "BICSI-002", spec_clause: "DB-8.5",
    severity: "Minor",
    rationale: "Bundle size of 72 exceeds BICSI-002 pathway fill limit of 48; thermal derating reduces current capacity.",
    predicted_cx_test: "ITP-04", predicted_cx_level: 2,
    predicted_cx_name: "Pathway fill and cable management inspection",
    week_caught: 11, week_fail: 18, lead_time_weeks: 7,
  },
  {
    component: "BMS", parameter: "monitoring_redundancy",
    required_value: "dual", provided_value: "single", unit: "topology",
    standard_ref: "UPTIME-TIER4", spec_clause: "DB-9.1",
    severity: "Critical",
    rationale: "Single monitoring path creates single point of failure; Tier IV requires concurrent maintainability of all monitoring systems.",
    predicted_cx_test: "IST-15", predicted_cx_level: 4,
    predicted_cx_name: "Full-facility failover drill",
    week_caught: 11, week_fail: 44, lead_time_weeks: 33,
  },
  {
    component: "FLOOR", parameter: "load_rating_kpa",
    required_value: 12, provided_value: 8, unit: "kPa",
    standard_ref: "IS-1893", spec_clause: "DB-13.1",
    severity: "Critical",
    rationale: "Floor load capacity 8 kPa vs required 12 kPa; high-density racks will exceed floor bearing capacity under seismic Zone IV conditions.",
    predicted_cx_test: "ITP-05", predicted_cx_level: 1,
    predicted_cx_name: "Structural load test and floor deflection",
    week_caught: 11, week_fail: 19, lead_time_weeks: 8,
  },
];
