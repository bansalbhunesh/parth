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
}

const API = process.env.NEXT_PUBLIC_API ?? "http://localhost:8000";

export async function getRegister(): Promise<Deviation[]> {
  try {
    const r = await fetch(`${API}/deviations`, { cache: "no-store" });
    if (!r.ok) throw new Error(String(r.status));
    const data = await r.json();
    return data.register as Deviation[];
  } catch {
    // Fallback so the demo renders even before the backend is wired.
    return FALLBACK;
  }
}

// Mirrors the seeded corpus — lets the UI render standalone.
export const FALLBACK: Deviation[] = [
  {
    component: "UPS-02", parameter: "battery_runtime_min",
    required_value: 10, provided_value: 7, unit: "min",
    standard_ref: "UPTIME-TIER4", spec_clause: "DB-4.3", severity: "Critical",
    rationale:
      "Battery autonomy below Tier IV requirement; UPS cannot sustain load during concurrent maintenance.",
    predicted_cx_test: "IST-07", predicted_cx_level: 4,
    predicted_cx_name: "Load transfer under maintenance (battery autonomy)",
    week_caught: 11, week_fail: 38, lead_time_weeks: 27,
  },
  {
    component: "GEN-FUEL", parameter: "onsite_fuel_hours",
    required_value: 24, provided_value: 12, unit: "h",
    standard_ref: "UPTIME-TIER4", spec_clause: "DB-5.4", severity: "Critical",
    predicted_cx_test: "IST-11", predicted_cx_level: 4,
    predicted_cx_name: "Sustained utility-outage run (fuel autonomy)",
    week_caught: 11, week_fail: 41, lead_time_weeks: 30,
  },
  {
    component: "COOL-LOOP", parameter: "redundancy",
    required_value: "N+2", provided_value: "N+1", unit: "topology",
    standard_ref: "UPTIME-TIER4", spec_clause: "DB-6.1", severity: "Critical",
    predicted_cx_test: "IST-09", predicted_cx_level: 4,
    predicted_cx_name: "Cooling failover under fault + maintenance",
    week_caught: 11, week_fail: 39, lead_time_weeks: 28,
  },
  {
    component: "SWGR-MV", parameter: "short_circuit_rating_ka",
    required_value: 50, provided_value: 40, unit: "kA",
    standard_ref: "DESIGN-BASIS", spec_clause: "DB-7.2", severity: "Critical",
    predicted_cx_test: "FAT-03", predicted_cx_level: 3,
    predicted_cx_name: "Protection coordination / fault-withstand verification",
    week_caught: 11, week_fail: 30, lead_time_weeks: 19,
  },
  {
    component: "CABLE-DC", parameter: "fire_rating",
    required_value: "CMP", provided_value: "CMR", unit: "plenum-class",
    standard_ref: "NFPA-75", spec_clause: "DB-8.4", severity: "Major",
    predicted_cx_test: "ITP-02", predicted_cx_level: 2,
    predicted_cx_name: "Cable fire-rating / plenum compliance inspection",
    week_caught: 11, week_fail: 22, lead_time_weeks: 11,
  },
  {
    component: "BMS", parameter: "critical_alarm_points",
    required_value: "complete", provided_value: "missing:leak_detection",
    unit: "set", standard_ref: "DESIGN-BASIS", spec_clause: "DB-9.5",
    severity: "Major",
    predicted_cx_test: "IST-14", predicted_cx_level: 4,
    predicted_cx_name: "Monitoring & alarm verification",
    week_caught: 11, week_fail: 40, lead_time_weeks: 29,
  },
];
