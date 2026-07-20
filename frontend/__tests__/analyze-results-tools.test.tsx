import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AnalyzeResults from "../components/analyze/AnalyzeResults";
import type { AnalyzeResult } from "../components/analyze/model";

const withConsequence = {
  component: "UPS-02",
  parameter: "battery_runtime_min",
  required_value: "10",
  provided_value: "8",
  unit: "min",
  severity: "Critical",
  rationale: "Autonomy quoted at beginning of life only.",
  standard_ref: "UPTIME-TIER4",
  spec_clause: "DB-4.3",
  predicted_cx_test: "IST-07",
  lead_time_weeks: 27,
};

const withoutConsequence = {
  component: "SWGR-MV",
  parameter: "short_circuit_rating_ka",
  required_value: "50",
  provided_value: "40",
  unit: "kA",
  severity: "Major",
  rationale: "Below prospective fault level.",
  standard_ref: "IEC-62271",
  spec_clause: "DB-9.1",
};

const result = {
  count: 2,
  mode: "llm",
  elapsed_ms: 16600,
  deviations: [withConsequence, withoutConsequence],
} as unknown as AnalyzeResult;

describe("analyze result tools", () => {
  it("restates findings in Hindi on demand and returns to English", async () => {
    const user = userEvent.setup();
    render(<AnalyzeResults result={result} extraction={null} specText="" submittalText="" />);

    const toggle = screen.getByRole("button", { name: "हिंदी में देखें" });
    expect(toggle).toHaveAttribute("aria-pressed", "false");

    await user.click(toggle);
    expect(screen.getByText(/आवश्यक 10 min/)).toBeInTheDocument();
    expect(screen.getByText(/कमीशनिंग टेस्ट IST-07/)).toBeInTheDocument();
    // A finding without a commissioning test carries no consequence clause.
    expect(screen.queryByText(/IEC-62271 में विफल/)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "English" }));
    expect(screen.queryByText(/आवश्यक 10 min/)).not.toBeInTheDocument();
  });

  it("prints the dossier through the browser print dialog", async () => {
    const user = userEvent.setup();
    const print = vi.fn();
    vi.stubGlobal("print", print);
    render(<AnalyzeResults result={result} extraction={null} specText="" submittalText="" />);

    await user.click(screen.getByRole("button", { name: "Print dossier" }));
    expect(print).toHaveBeenCalledOnce();
    vi.unstubAllGlobals();
  });
});
