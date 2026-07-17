import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AnalyzeResolutionWorkflow from "../components/analyze/AnalyzeResolutionWorkflow";
import type { AnalyzeResult } from "../components/analyze/model";
import { analyzeOnce } from "../lib/api";
import {
  addFinding,
  createCase,
  deleteCase,
  draftAndIssueRfi,
  getAuditCount,
  updateFinding,
  updateRfi,
} from "../lib/case-api";

vi.mock("../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../lib/api")>()),
  analyzeOnce: vi.fn(),
}));

vi.mock("../lib/case-api", () => ({
  addFinding: vi.fn(),
  createCase: vi.fn(),
  deleteCase: vi.fn(),
  draftAndIssueRfi: vi.fn(),
  getAuditCount: vi.fn(),
  updateFinding: vi.fn(),
  updateRfi: vi.fn(),
}));

const RESULT: AnalyzeResult = {
  system: "UPS",
  input_hash: "analysis-hash",
  count: 1,
  elapsed_ms: 1_200,
  mode: "llm",
  deviations: [{
    component: "UPS-02",
    parameter: "battery_runtime_min",
    required_value: 10,
    provided_value: 8,
    unit: "min",
    severity: "Critical",
    rationale: "Runtime is below the requirement.",
    standard_ref: "UPTIME-TIER4",
    spec_clause: "DB-4.3",
    predicted_cx_test: "IST-07",
    lead_time_weeks: 27,
  }],
};

const CLEARED: AnalyzeResult = {
  ...RESULT,
  input_hash: "verification-hash",
  count: 0,
  deviations: [],
};

const credentials = { caseId: "case-1", secret: "secret-1" };

beforeEach(() => {
  vi.clearAllMocks();
  sessionStorage.clear();
  vi.mocked(createCase).mockResolvedValue(credentials);
  vi.mocked(addFinding).mockResolvedValue("finding-1");
  vi.mocked(updateFinding).mockResolvedValue(undefined);
  vi.mocked(draftAndIssueRfi).mockResolvedValue("rfi-1");
  vi.mocked(updateRfi).mockResolvedValue(undefined);
  vi.mocked(getAuditCount).mockResolvedValue(7);
  vi.mocked(deleteCase).mockResolvedValue(undefined);
  vi.mocked(analyzeOnce).mockResolvedValue(CLEARED);
});

async function reachIssuedStage(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: "Persist the highest-priority finding" }));
  await user.click(await screen.findByRole("button", { name: "Assign owner and accept" }));
  await user.click(await screen.findByRole("button", { name: "Draft and issue the RFI" }));
  expect(await screen.findByRole("button", { name: "Re-analyze revision and close" })).toBeEnabled();
}

describe("AnalyzeResolutionWorkflow", () => {
  it("moves the actual analyzed finding through read-back closure", async () => {
    const user = userEvent.setup();
    render(<AnalyzeResolutionWorkflow result={RESULT} specText="Runtime shall be 10 min." submittalText="Runtime is 8 min." />);

    expect(screen.getByText("Resolve UPS-02 battery runtime min before IST-07")).toBeInTheDocument();
    expect(screen.getByText("27 weeks")).toBeInTheDocument();
    await reachIssuedStage(user);
    expect(
      (screen.getByLabelText("Vendor revision to verify") as HTMLTextAreaElement).value,
    ).toContain("Runtime is 10 min.");
    await user.click(screen.getByRole("button", { name: "Re-analyze revision and close" }));

    expect(await screen.findByText("Closed with read-back evidence.")).toBeInTheDocument();
    expect(screen.getByText(/7 audit events/)).toBeInTheDocument();
    expect(analyzeOnce).toHaveBeenCalledWith(
      "Runtime shall be 10 min.",
      expect.stringContaining("REVISION C"),
      "UPS",
      expect.any(AbortSignal),
    );
    expect(updateRfi).toHaveBeenCalledTimes(2);
    expect(updateFinding).toHaveBeenLastCalledWith(credentials, "finding-1", expect.objectContaining({ status: "resolved" }));
  });

  it("does not close a finding when re-analysis still detects it", async () => {
    vi.mocked(analyzeOnce).mockResolvedValue(RESULT);
    const user = userEvent.setup();
    render(<AnalyzeResolutionWorkflow result={RESULT} specText="Runtime shall be 10 min." submittalText="Runtime is 8 min." />);
    await reachIssuedStage(user);
    await user.click(screen.getByRole("button", { name: "Re-analyze revision and close" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("still fails this requirement");
    expect(updateRfi).not.toHaveBeenCalled();
    expect(screen.queryByText("Closed with read-back evidence.")).not.toBeInTheDocument();
  });

  it("keeps owner assignment explicit and blocks an empty owner", async () => {
    const user = userEvent.setup();
    render(<AnalyzeResolutionWorkflow result={RESULT} specText="spec" submittalText="Runtime is 8 min." />);
    await user.click(screen.getByRole("button", { name: "Persist the highest-priority finding" }));
    const owner = await screen.findByLabelText("Accountable owner");
    await user.clear(owner);
    expect(screen.getByRole("button", { name: "Assign owner and accept" })).toBeDisabled();
    await user.type(owner, "Asha Rao, CxA");
    await user.click(screen.getByRole("button", { name: "Assign owner and accept" }));
    expect(updateFinding).toHaveBeenCalledWith(credentials, "finding-1", { status: "accepted", owner: "Asha Rao, CxA" });
  });

  it("restores an issued case after refresh and can finish it", async () => {
    sessionStorage.setItem("pramaan-resolution:analysis-hash", JSON.stringify({
      stage: "issued",
      credentials,
      findingId: "finding-1",
      rfiId: "rfi-1",
      owner: "Priya Menon",
      revisedSubmittal: "Runtime is 10 min.",
      auditCount: 0,
      remainingFindings: null,
      verificationHash: "",
      verificationMode: "",
    }));
    const user = userEvent.setup();
    render(<AnalyzeResolutionWorkflow result={RESULT} specText="spec content" submittalText="Runtime is 8 min." />);
    await user.click(await screen.findByRole("button", { name: "Re-analyze revision and close" }));
    expect(await screen.findByText("Closed with read-back evidence.")).toBeInTheDocument();
    expect(createCase).not.toHaveBeenCalled();
  });

  it("deletes a started demo case and returns to a clean state", async () => {
    const user = userEvent.setup();
    render(<AnalyzeResolutionWorkflow result={RESULT} specText="spec" submittalText="Runtime is 8 min." />);
    await user.click(screen.getByRole("button", { name: "Persist the highest-priority finding" }));
    await user.click(await screen.findByRole("button", { name: "Delete this demo case and restart" }));
    expect(deleteCase).toHaveBeenCalledWith(credentials);
    expect(await screen.findByRole("button", { name: "Persist the highest-priority finding" })).toBeInTheDocument();
    expect(sessionStorage.getItem("pramaan-resolution:analysis-hash")).toBeNull();
  });

  it("recovers from corrupt session state and reports case creation failures", async () => {
    sessionStorage.setItem("pramaan-resolution:analysis-hash", "not-json");
    vi.mocked(createCase).mockRejectedValue(new Error("Case store unavailable"));
    const user = userEvent.setup();
    render(<AnalyzeResolutionWorkflow result={RESULT} specText="spec" submittalText="Runtime is 8 min." />);
    await waitFor(() => expect(sessionStorage.getItem("pramaan-resolution:analysis-hash")).toBeNull());
    await user.click(screen.getByRole("button", { name: "Persist the highest-priority finding" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Case store unavailable");
  });

  it("restarts locally even when the old hosted case has disappeared", async () => {
    vi.mocked(deleteCase).mockRejectedValue(new Error("No such case"));
    const user = userEvent.setup();
    render(<AnalyzeResolutionWorkflow result={RESULT} specText="spec" submittalText="Runtime is 8 min." />);
    await user.click(screen.getByRole("button", { name: "Persist the highest-priority finding" }));
    await user.click(await screen.findByRole("button", { name: "Delete this demo case and restart" }));
    expect(await screen.findByRole("button", { name: "Persist the highest-priority finding" })).toBeInTheDocument();
  });

  it("does not throw when unmounted during an async advance", async () => {
    // Make createCase hang so the advance is in-flight when we unmount
    let resolveCreate!: (value: typeof credentials) => void;
    vi.mocked(createCase).mockImplementation(() => new Promise((resolve) => { resolveCreate = resolve; }));
    const user = userEvent.setup();
    const { unmount } = render(<AnalyzeResolutionWorkflow result={RESULT} specText="spec" submittalText="Runtime is 8 min." />);
    await user.click(screen.getByRole("button", { name: "Persist the highest-priority finding" }));
    // Unmount while advance() is still awaiting createCase
    unmount();
    // Resolve the hanging promise after unmount — should not throw
    resolveCreate(credentials);
    // If we reach here without an unhandled rejection, the abort guard works.
  });

  it("blocks verification if the revised submittal text is cleared", async () => {
    const user = userEvent.setup();
    render(<AnalyzeResolutionWorkflow result={RESULT} specText="spec" submittalText="Runtime is 8 min." />);
    
    // Idle -> Opened
    await user.click(screen.getByRole("button", { name: "Persist the highest-priority finding" }));
    
    // Opened -> Owned
    await user.type(screen.getByLabelText("Accountable owner"), "Eng");
    await user.click(screen.getByRole("button", { name: "Assign owner and accept" }));
    
    // Owned -> Issued
    await user.click(screen.getByRole("button", { name: "Draft and issue the RFI" }));
    
    // Clear the revision textarea
    const textarea = await screen.findByRole("textbox", { name: "Vendor revision to verify" });
    await user.clear(textarea);
    
    // Try to advance and verify the error message appears
    await user.click(screen.getByRole("button", { name: "Re-analyze revision and close" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Paste the full design basis and revised vendor text before verification.");
  });
});
