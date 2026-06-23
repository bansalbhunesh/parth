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

const API = process.env.NEXT_PUBLIC_API ?? "http://localhost:8000";

export async function getRegister(): Promise<Deviation[]> {
  try {
    const r = await fetch(`${API}/deviations`, { cache: "no-store" });
    if (!r.ok) throw new Error(String(r.status));
    const data = await r.json();
    return data.register as Deviation[];
  } catch {
    return FALLBACK;
  }
}

export async function getCxPlan(): Promise<CxPlan | null> {
  try {
    const r = await fetch(`${API}/cx-plan`, { cache: "no-store" });
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

export async function getMetrics(): Promise<Record<string, unknown> | null> {
  try {
    const r = await fetch(`${API}/metrics`, { cache: "no-store" });
    if (!r.ok) throw new Error(String(r.status));
    return await r.json();
  } catch {
    return null;
  }
}

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
    { id: "FAT-01", level: 3, name: "UPS module load-bank test", scheduled_week: 24, acceptance: "Full load sustained 4 hours" },
    { id: "FAT-02", level: 3, name: "Generator load-bank test", scheduled_week: 26, acceptance: "110% load for 2 hours" },
    { id: "FAT-03", level: 3, name: "Protection coordination / fault-withstand verification", scheduled_week: 30, acceptance: "Fault withstand >= prospective fault" },
    { id: "IST-01", level: 4, name: "Utility failure simulation", scheduled_week: 34, acceptance: "Zero IT load impact" },
    { id: "IST-07", level: 4, name: "Load transfer under maintenance (battery autonomy)", scheduled_week: 38, acceptance: "Battery sustains load during transfer" },
    { id: "IST-09", level: 4, name: "Cooling failover under fault + maintenance", scheduled_week: 39, acceptance: "Temperature maintained within ASHRAE" },
    { id: "IST-11", level: 4, name: "Sustained utility-outage run (fuel autonomy)", scheduled_week: 41, acceptance: "Full design-duration outage" },
    { id: "IST-14", level: 4, name: "Monitoring & alarm verification", scheduled_week: 40, acceptance: "All critical alarms fire" },
    { id: "IST-15", level: 4, name: "Full-facility failover drill", scheduled_week: 44, acceptance: "Zero downtime during drill" },
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
];
