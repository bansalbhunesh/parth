import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import RiskRemediation from "../components/analyze/RiskRemediation";
import type { CompoundRisk, Remediation } from "../components/analyze/model";

const FULL_RISK: CompoundRisk = {
  project_compound_risk: 0.84,
  risk_band: "Critical",
  deviation_count: 3,
  converged_cx_tests: ["IST-07"],
  schedule_cliff: {
    week_fail: 38,
    converging_deviations: 2,
    compound_risk: 0.84,
    deviations: ["A/x", "B/y"],
  },
  clusters: [
    { kind: "cx_test", key: "IST-07", member_count: 2, members: ["A/x", "B/y"], compound_risk: 0.84, earliest_week_fail: 38 },
  ],
  method: "deterministic compound-risk aggregation; no LLM",
};

const FULL_REMEDIATION: Remediation = {
  actions: [],
  highest_leverage: {
    kind: "clear_cluster",
    target: "IST-07 (cx_test)",
    resolves: ["A/x", "B/y"],
    risk_reduction: 0.84,
    residual_project_risk: 0.0,
    clears_schedule_cliff: true,
    new_schedule_cliff_week: null,
  },
  has_convergence: true,
  note: "clearing the whole cluster reduces risk more than any single fix",
  method: "deterministic marginal optimisation; no LLM",
};

describe("RiskRemediation", () => {
  it("renders nothing without a compound-risk block", () => {
    const { container } = render(<RiskRemediation />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when there are no deviations", () => {
    const { container } = render(
      <RiskRemediation compoundRisk={{ ...FULL_RISK, deviation_count: 0 }} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows band, schedule cliff, clusters and the highest-leverage fix", () => {
    render(<RiskRemediation compoundRisk={FULL_RISK} remediation={FULL_REMEDIATION} />);
    expect(screen.getByText(/Critical/)).toHaveClass("rr-band-critical");
    expect(screen.getByText(/2 findings fail together/)).toBeInTheDocument();
    expect(screen.getByText("IST-07")).toBeInTheDocument();
    expect(screen.getByText("Fix this first")).toBeInTheDocument();
    expect(screen.getByText("IST-07 (cx test)")).toBeInTheDocument();
    expect(screen.getByText(/clears the cliff/)).toBeInTheDocument();
    expect(screen.getByText(/no LLM/)).toBeInTheDocument();
  });

  it("falls back to the low-risk band styling for an unexpected band and hides absent sections", () => {
    render(
      <RiskRemediation
        compoundRisk={{
          ...FULL_RISK,
          risk_band: "Elevated" as CompoundRisk["risk_band"],
          project_compound_risk: 0.2,
          schedule_cliff: null,
          clusters: [],
        }}
      />,
    );
    expect(screen.getByText(/Elevated/)).toHaveClass("rr-band-low");
    expect(screen.queryByText(/fail together/)).not.toBeInTheDocument();
    expect(screen.queryByText("Fix this first")).not.toBeInTheDocument();
  });

  it("omits the cliff note on a fix that does not clear the cliff", () => {
    render(
      <RiskRemediation
        compoundRisk={FULL_RISK}
        remediation={{
          ...FULL_REMEDIATION,
          highest_leverage: { ...FULL_REMEDIATION.highest_leverage!, risk_reduction: 0.24, clears_schedule_cliff: false },
        }}
      />,
    );
    expect(screen.getByText(/−24% risk/)).toBeInTheDocument();
    expect(screen.queryByText(/clears the cliff/)).not.toBeInTheDocument();
  });

  it("handles a remediation block with no leading action", () => {
    render(
      <RiskRemediation
        compoundRisk={FULL_RISK}
        remediation={{ ...FULL_REMEDIATION, highest_leverage: null }}
      />,
    );
    expect(screen.queryByText("Fix this first")).not.toBeInTheDocument();
  });
});
