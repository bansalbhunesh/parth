import { describe, expect, it } from "vitest";
import { consequenceHi, deviationSummaryHi, parameterHi, severityHi } from "../lib/hindi";
import type { AnalyzeDeviation } from "../components/analyze/model";

const base: AnalyzeDeviation = {
  component: "UPS-02",
  parameter: "battery_runtime_min",
  required_value: "10",
  provided_value: "8",
  unit: "min",
  severity: "Critical",
  rationale: "",
  standard_ref: "UPTIME-TIER4",
  spec_clause: "DB-4.3",
  predicted_cx_test: "IST-07",
  lead_time_weeks: 27,
};

describe("hindi restatement", () => {
  it("carries every number, unit and identifier through verbatim", () => {
    const line = deviationSummaryHi(base);
    expect(line).toContain("UPS-02");
    expect(line).toContain("10 min");
    expect(line).toContain("8 min");
  });

  it("translates known parameters and falls back to readable text", () => {
    expect(parameterHi("battery_runtime_min")).toBe("बैटरी बैकअप");
    expect(parameterHi("unknown_param_name")).toBe("unknown param name");
  });

  it("translates known severities and passes unknown ones through", () => {
    expect(severityHi("Critical")).toBe("गंभीर");
    expect(severityHi("Unlabelled")).toBe("Unlabelled");
  });

  it("states the commissioning consequence with its test id and weeks", () => {
    const line = consequenceHi(base);
    expect(line).toContain("IST-07");
    expect(line).toContain("27");
  });

  it("omits the consequence when the facts are not present", () => {
    expect(consequenceHi({ ...base, predicted_cx_test: undefined })).toBeNull();
    expect(consequenceHi({ ...base, lead_time_weeks: 0 })).toBeNull();
  });

  it("renders without a unit when the finding has none", () => {
    const line = deviationSummaryHi({ ...base, unit: "", parameter: "redundancy",
      required_value: "2N", provided_value: "N+1" });
    expect(line).toContain("2N");
    expect(line).not.toContain("undefined");
  });
});
