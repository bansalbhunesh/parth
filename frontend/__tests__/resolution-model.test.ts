import { describe, expect, it } from "vitest";

import type { AnalyzeDeviation, AnalyzeResult } from "../components/analyze/model";
import {
  buildRevisedSubmittal,
  findingCleared,
  humanActionLabel,
  humanSystemLabel,
  humanizeRiskTarget,
  primaryDeviation,
} from "../components/analyze/resolution-model";

const FIRST: AnalyzeDeviation = {
  component: "UPS-02",
  parameter: "battery_runtime_min",
  required_value: 10,
  provided_value: 8,
  unit: "min",
  severity: "Critical",
  rationale: "Below requirement",
  predicted_cx_test: "IST-07",
};

const SECOND: AnalyzeDeviation = {
  ...FIRST,
  component: "UPS-03",
  parameter: "redundancy",
  required_value: "2N",
  provided_value: "N+1",
};

function result(deviations = [FIRST, SECOND]): AnalyzeResult {
  return {
    system: "CUSTOM",
    deviations,
    count: deviations.length,
    elapsed_ms: 10,
    mode: "llm",
    remediation: {
      actions: [],
      highest_leverage: {
        kind: "fix_deviation",
        target: "UPS-03/redundancy",
        resolves: ["UPS-03/redundancy"],
        risk_reduction: 0.4,
        residual_project_risk: 0.2,
        clears_schedule_cliff: false,
        new_schedule_cliff_week: null,
      },
      has_convergence: false,
      note: "",
      method: "deterministic",
    },
  };
}

describe("resolution model", () => {
  it("selects the highest-leverage finding and writes a human action", () => {
    expect(primaryDeviation(result())).toEqual(SECOND);
    expect(humanActionLabel(result())).toBe("Resolve UPS-03 redundancy before IST-07");
  });

  it("uses real components instead of CUSTOM internals", () => {
    expect(humanSystemLabel(result([FIRST]))).toBe("UPS-02");
    expect(humanSystemLabel(result())).toBe("UPS-02 + 1 more");
    expect(humanizeRiskTarget("CUSTOM (system)", [FIRST])).toBe("UPS-02 system");
    expect(humanizeRiskTarget("CUSTOM (system)", [FIRST, SECOND])).toBe("submitted systems");
    expect(humanizeRiskTarget("UPS-02/battery_runtime_min", [FIRST])).toBe("UPS-02 · battery runtime min");
  });

  it("falls back to the reported system or submitted-system label", () => {
    expect(humanSystemLabel({ ...result([]), system: "UPS" })).toBe("UPS");
    expect(humanSystemLabel(result([]))).toBe("submitted system");
  });

  it("builds an editable revision and appends explicit supersession evidence", () => {
    const revised = buildRevisedSubmittal("Runtime is 8 min.", FIRST);
    expect(revised).toContain("Runtime is 10 min.");
    expect(revised).toContain("REVISION C — FORMAL VENDOR RESPONSE");
    expect(revised).toContain("supersedes the earlier 8 min");
  });

  it("adds the correction note even when the old value was not found", () => {
    expect(buildRevisedSubmittal("No value here.", SECOND)).toContain("UPS-03 redundancy: 2N min");
    expect(buildRevisedSubmittal("", FIRST)).toBe("");
  });

  it("only clears the exact component/parameter target", () => {
    expect(findingCleared(result([SECOND]), FIRST)).toBe(true);
    expect(findingCleared(result([FIRST]), FIRST)).toBe(false);
  });

  it("keeps safe human fallbacks for incomplete provider output", () => {
    const incomplete: AnalyzeDeviation = {
      ...FIRST,
      component: "",
      parameter: "runtime",
      required_value: "",
      provided_value: "",
      predicted_cx_test: undefined,
    };
    const withoutRemediation = { ...result([FIRST]), remediation: undefined };
    expect(primaryDeviation(withoutRemediation)).toEqual(FIRST);
    expect(humanActionLabel(result([incomplete]))).toBe("Resolve  runtime");
    expect(humanizeRiskTarget("CUSTOM", [incomplete])).toBe("submitted systems");
    expect(buildRevisedSubmittal("Original vendor text", incomplete)).toBe("Original vendor text");
    expect(findingCleared(result([{ ...incomplete, parameter: "" }]), { ...incomplete, parameter: "" })).toBe(false);

    const missingProvided = { ...FIRST, provided_value: null } as unknown as AnalyzeDeviation;
    const missingRequired = { ...FIRST, required_value: null } as unknown as AnalyzeDeviation;
    expect(buildRevisedSubmittal("Original vendor text", missingProvided)).toBe("Original vendor text");
    expect(buildRevisedSubmittal("Original vendor text", missingRequired)).toBe("Original vendor text");
  });
});
