import type { AnalyzeDeviation } from "../components/analyze/model";

/**
 * Deterministic Hindi restatement of a finding.
 *
 * Template-only on purpose: no model call, no translation service, so the
 * Hindi line cannot drift from the English one or invent a value. Every
 * number, unit, component id and commissioning-test id is carried through
 * verbatim in ASCII — only the connective language is translated.
 */

const PARAMETER_HI: Record<string, string> = {
  redundancy: "रिडंडंसी",
  battery_runtime_min: "बैटरी बैकअप",
  system_configuration: "सिस्टम कॉन्फ़िगरेशन",
  efficiency_pct: "दक्षता",
  onsite_fuel_hours: "ऑनसाइट फ़्यूल",
  start_time_sec: "स्टार्ट समय",
  short_circuit_rating_ka: "शॉर्ट-सर्किट रेटिंग",
};

const SEVERITY_HI: Record<string, string> = {
  Critical: "गंभीर",
  Major: "बड़ा",
  Minor: "छोटा",
};

export function parameterHi(parameter: string): string {
  const key = parameter.trim();
  return PARAMETER_HI[key] ?? key.replaceAll("_", " ");
}

export function severityHi(severity: string): string {
  return SEVERITY_HI[severity] ?? severity;
}

/** One-sentence Hindi summary: what was required, what was offered. */
export function deviationSummaryHi(d: AnalyzeDeviation): string {
  const unit = d.unit ? ` ${d.unit}` : "";
  const param = parameterHi(d.parameter);
  const sev = d.severity ? `${severityHi(d.severity)} — ` : "";
  return (
    `${sev}${d.component} की ${param} में विचलन: ` +
    `आवश्यक ${d.required_value}${unit}, प्रस्तावित ${d.provided_value}${unit}।`
  );
}

/** Optional consequence clause — only when both facts are present. */
export function consequenceHi(d: AnalyzeDeviation): string | null {
  if (!d.predicted_cx_test || !d.lead_time_weeks || d.lead_time_weeks <= 0) return null;
  return (
    `बिना सुधारे यह कमीशनिंग टेस्ट ${d.predicted_cx_test} में विफल होगा — ` +
    `कार्रवाई के लिए ${d.lead_time_weeks} सप्ताह शेष।`
  );
}
