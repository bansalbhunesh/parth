import { describe, expect, it } from "vitest";

import { runLocalReconciliation } from "../components/analyze/local-reconciliation";
import { formatElapsed, friendlyError, isModelBacked, provenance, timingTitle } from "../components/analyze/model";

describe("analysis presentation model", () => {
  it.each([
    [undefined, "—"],
    [Number.NaN, "—"],
    [499, "499 ms"],
    [1_250, "1.3s"],
  ])("formats elapsed time %s", (value, expected) => {
    expect(formatElapsed(value)).toBe(expected);
  });

  it("describes complete and missing timing without fabricating model latency", () => {
    expect(timingTitle(undefined)).toBe("Total analysis time.");
    expect(timingTitle({ standards_load_ms: 4, llm_call_ms: null, postprocess_ms: 6, provider: null }))
      .toBe("Standards load: 4 ms · Post-processing: 6 ms");
    expect(timingTitle({ standards_load_ms: 4, llm_call_ms: 1_200, postprocess_ms: 6, provider: "provider" }))
      .toContain("LLM call: 1.2s");
  });

  it.each([
    ["llm", "Live LLM reasoning", true],
    ["vision", "Vision (image) reasoning", true],
    ["vision-unavailable", "Vision unavailable", false],
    ["deterministic", "Deterministic rule floor", false],
    ["rule", "Deterministic rule floor", false],
    ["unexpected", "Provenance unknown", false],
  ])("keeps provenance for %s explicit", (mode, label, modelBacked) => {
    expect(provenance(mode).label).toBe(label);
    expect(isModelBacked(mode)).toBe(modelBacked);
  });

  it.each([
    ["HTTP 429", "Rate limit reached"],
    ["401 auth required", "requires an access token"],
    ["413 too large", "15 MB limit"],
    ["415 unsupported MIME", "file type was rejected"],
    ["Failed to fetch", "Backend not reachable"],
    ["Provider unavailable", "Provider unavailable"],
  ])("turns %s into actionable copy", (raw, expected) => {
    expect(friendlyError(raw)).toContain(expected);
  });
});

describe("local reconciliation", () => {
  it("detects compact fixture mismatches without treating matching topology as a deviation", () => {
    const result = runLocalReconciliation(
      "Design Basis: UPS System battery runtime 10 min efficiency 96 % 2N topology",
      "Vendor Submittal: UPS System battery runtime 7 min efficiency 93 % 2N topology",
    );
    expect(result.mode).toBe("deterministic");
    expect(result.deviations.map((item) => item.parameter)).toEqual(["battery_runtime_min", "efficiency_pct"]);
  });

  it("returns an explicitly deterministic empty result for the controlled clean fixture", () => {
    const result = runLocalReconciliation(
      "Section 26 33 53 requires 10 minutes and 2N",
      "Technical Submittal — TruePower provides 11 minutes and 2N",
    );
    expect(result).toMatchObject({ count: 0, deviations: [], mode: "deterministic" });
  });

  it("applies generic minimum and maximum rules to novel text", () => {
    const result = runLocalReconciliation(
      "Battery autonomy 10 min. Generator start time 10 sec.",
      "Battery autonomy 8 min. Generator start time 15 sec.",
    );
    expect(result.deviations).toEqual(expect.arrayContaining([
      expect.objectContaining({ parameter: "battery_runtime_min" }),
      expect.objectContaining({ parameter: "start_time_sec" }),
    ]));
  });
});
