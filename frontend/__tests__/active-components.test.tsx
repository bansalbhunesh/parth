import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AnalyzePanel from "../components/AnalyzePanel";
import ResolutionWorkflow from "../components/ResolutionWorkflow";
import ThemeToggle from "../components/ThemeToggle";
import { getOcrCheck, streamAnalyze, streamUploadAnalyze } from "../lib/api";

vi.mock("../lib/api", async (importOriginal) => {
  const original = await importOriginal<typeof import("../lib/api")>();
  return {
    ...original,
    getOcrCheck: vi.fn(),
    streamAnalyze: vi.fn(),
    streamUploadAnalyze: vi.fn(),
  };
});

const mockedOcrCheck = vi.mocked(getOcrCheck);
const mockedStreamAnalyze = vi.mocked(streamAnalyze);
const mockedStreamUploadAnalyze = vi.mocked(streamUploadAnalyze);

beforeEach(() => {
  mockedOcrCheck.mockResolvedValue({
    ocr_available: false,
    image_ocr_supported: false,
    status: "disabled",
    tesseract_version: null,
  });
  mockedStreamAnalyze.mockReset();
  mockedStreamUploadAnalyze.mockReset();
});

describe("ThemeToggle", () => {
  it("reads the current theme and persists a deliberate change", async () => {
    document.documentElement.dataset.theme = "dark";
    const user = userEvent.setup();
    render(<ThemeToggle />);

    const toggle = await screen.findByRole("button", { name: "Switch to light theme" });
    await user.click(toggle);

    expect(document.documentElement.dataset.theme).toBe("light");
    expect(localStorage.getItem("pramaan-theme")).toBe("light");
    expect(toggle).toHaveAccessibleName("Switch to dark theme");
  });

  it("defaults to the light theme when no valid theme is present", async () => {
    delete document.documentElement.dataset.theme;
    render(<ThemeToggle />);
    expect(await screen.findByRole("button", { name: "Switch to dark theme" })).toBeInTheDocument();
  });
});

describe("AnalyzePanel", () => {
  it("starts with an honest upload state and reports unavailable OCR", async () => {
    render(<AnalyzePanel />);

    expect(screen.getByRole("button", { name: "Upload PDFs" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Upload & Analyze" })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Spec document:/ })).toHaveAttribute("aria-disabled", "false");
    expect(await screen.findByText(/OCR disabled in this deployment/)).toBeInTheDocument();
  });

  it("advertises image inputs only when the deployment actually supports them", async () => {
    mockedOcrCheck.mockResolvedValue({
      ocr_available: true,
      image_ocr_supported: true,
      status: "ready",
      tesseract_version: "5.5.0",
    });
    render(<AnalyzePanel />);

    expect(await screen.findByText(/OCR ready.*Tesseract 5.5.0/)).toBeInTheDocument();
    expect(document.querySelector('input[type="file"]')).toHaveAttribute("accept", expect.stringContaining(".png"));
    expect(screen.getAllByText(/Drop PDF\/image\/MD\/TXT/)).toHaveLength(2);
  });

  it("switches modes and accepts manually entered text", async () => {
    const user = userEvent.setup();
    render(<AnalyzePanel />);
    await user.click(screen.getByRole("button", { name: "Paste Text" }));
    await user.type(screen.getByLabelText("Design basis specification text"), "runtime must be 10 minutes");
    await user.type(screen.getByLabelText("Vendor submittal text"), "runtime provided is 7 minutes");
    expect(screen.getByRole("button", { name: "Analyze for deviations" })).toBeEnabled();

    await user.click(screen.getByRole("button", { name: "Upload PDFs" }));
    expect(screen.getByRole("button", { name: "Upload & Analyze" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Paste Text" }));
    expect(screen.getByLabelText("Design basis specification text")).toHaveValue("runtime must be 10 minutes");
  });

  it("runs the compliant fixture locally without presenting it as a clean bill of health", async () => {
    const user = userEvent.setup();
    render(<AnalyzePanel />);

    await user.click(screen.getByRole("button", { name: /Load compliant demo/ }));
    await user.click(screen.getByRole("checkbox", { name: "Local Engine (Instant)" }));
    await user.click(screen.getByRole("button", { name: "Analyze for deviations" }));

    expect(await screen.findByText("0 deviations found", {}, { timeout: 2_000 })).toBeInTheDocument();
    expect(document.querySelector(".analyze-no-devs")).toHaveTextContent("not a clean bill of health");
    expect(screen.getByText("Deterministic rule floor")).toBeInTheDocument();
  });

  it("runs the realistic deviation fixture through the local rule floor", async () => {
    const user = userEvent.setup();
    render(<AnalyzePanel />);
    await user.click(screen.getByRole("button", { name: /Load deviation demo/ }));
    await user.click(screen.getByRole("checkbox", { name: "Local Engine (Instant)" }));
    await user.click(screen.getByRole("button", { name: "Analyze for deviations" }));
    expect(await screen.findByText(/deviation(s)? found/, {}, { timeout: 2_000 })).toBeInTheDocument();
    expect(screen.getByText("Deterministic rule floor")).toBeInTheDocument();
  });

  it("accepts files through both keyboard-operable drop zones", async () => {
    render(<AnalyzePanel />);
    const [specZone, submittalZone] = screen.getAllByRole("button", { name: /drop a PDF/ });
    const inputs = document.querySelectorAll<HTMLInputElement>('input[type="file"]');

    fireEvent.change(inputs[0], { target: { files: [new File(["spec"], "spec.txt", { type: "text/plain" })] } });
    fireEvent.change(inputs[1], { target: { files: [new File(["submittal"], "submittal.txt", { type: "text/plain" })] } });

    expect(specZone).toHaveTextContent("spec.txt");
    expect(submittalZone).toHaveTextContent("submittal.txt");
    expect(screen.getByRole("button", { name: "Upload & Analyze" })).toBeEnabled();
  });

  it("renders streamed model findings with explicit live provenance", async () => {
    mockedStreamAnalyze.mockImplementation(async (_spec, _submittal, onStatus, onToken, onResult, onDone) => {
      onStatus("Comparing requirements");
      onToken("Reasoning from cited values");
      onResult({
        system: "UPS",
        count: 1,
        elapsed_ms: 1_200,
        mode: "llm",
        timing: { standards_load_ms: 4, llm_call_ms: 1_100, postprocess_ms: 96, provider: "test-provider" },
        deviations: [{
          component: "UPS-02", parameter: "battery_runtime_min", required_value: 10, provided_value: 7,
          unit: "min", severity: "Critical", rationale: "Runtime is below the cited minimum.",
          standard_ref: "UPTIME-TIER4", spec_clause: "DB-4.3", predicted_cx_test: "IST-07", lead_time_weeks: 27,
        }],
      });
      onDone();
    });
    const user = userEvent.setup();
    render(<AnalyzePanel />);

    await user.click(screen.getByRole("button", { name: "Load compact example" }));
    await user.click(screen.getByRole("button", { name: "Analyze for deviations" }));

    expect(await screen.findByText("1 deviation found")).toBeInTheDocument();
    expect(screen.getByText("Live LLM reasoning")).toBeInTheDocument();
    expect(screen.getByText("Runtime is below the cited minimum.")).toBeInTheDocument();
  });

  it("falls back to the non-streaming endpoint when streaming reports an error", async () => {
    mockedStreamAnalyze.mockImplementation(async (_spec, _submittal, _onStatus, _onToken, _onResult, _onDone, onError) => {
      onError("stream interrupted");
    });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ system: "UPS", count: 0, elapsed_ms: 8, mode: "llm", deviations: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<AnalyzePanel />);

    await user.click(screen.getByRole("button", { name: "Load compact example" }));
    await user.click(screen.getByRole("button", { name: "Analyze for deviations" }));

    expect(await screen.findByText("0 deviations found")).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledWith(expect.stringContaining("/analyze"), expect.objectContaining({ method: "POST" }));
  });

  it("shows a safe fallback error when both streaming and HTTP analysis fail", async () => {
    mockedStreamAnalyze.mockImplementation(async (_spec, _submittal, _onStatus, _onToken, _onResult, _onDone, onError) => {
      await onError("stream interrupted");
    });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("unavailable", { status: 503 }));
    const user = userEvent.setup();
    render(<AnalyzePanel />);
    await user.click(screen.getByRole("button", { name: "Load compact example" }));
    await user.click(screen.getByRole("button", { name: "Analyze for deviations" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/temporarily unavailable/i);
  });

  it("surfaces a direct streaming client failure and restores the controls", async () => {
    mockedStreamAnalyze.mockRejectedValue(new Error("network disconnected"));
    const user = userEvent.setup();
    render(<AnalyzePanel />);
    await user.click(screen.getByRole("button", { name: "Load compact example" }));
    await user.click(screen.getByRole("button", { name: "Analyze for deviations" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("network disconnected");
    expect(screen.getByRole("button", { name: "Analyze for deviations" })).toBeEnabled();
  });

  it("shows upload extraction status and OCR warnings without claiming a result", async () => {
    mockedStreamUploadAnalyze.mockImplementation(async (_form, handlers) => {
      handlers.onStatus("Extracting submitted documents");
      handlers.onPreview({ spec: "Extracted specification", submittal: "Extracted proposal" });
      handlers.onExtraction?.({
        spec: { method: "ocr_pdf", chars: 24, ocr_used: true, truncated: false, warning: "OCR text should be checked." },
        submittal: { method: "text_layer", chars: 25, ocr_used: false, truncated: false, warning: null },
      });
      handlers.onToken("partial reasoning");
      handlers.onDone();
    });
    const user = userEvent.setup();
    render(<AnalyzePanel />);
    const inputs = document.querySelectorAll<HTMLInputElement>('input[type="file"]');
    await user.upload(inputs[0], new File(["spec"], "spec.pdf", { type: "application/pdf" }));
    await user.upload(inputs[1], new File(["sub"], "sub.pdf", { type: "application/pdf" }));
    await user.click(screen.getByRole("button", { name: "Upload & Analyze" }));

    expect(await screen.findByText("OCR text should be checked.")).toBeInTheDocument();
    expect(screen.getByText("Extracted specification")).toBeInTheDocument();
    expect(screen.getByText("Extracted proposal")).toBeInTheDocument();
  });

  it("renders upload results, submittal warnings, and empty preview fallbacks", async () => {
    mockedStreamUploadAnalyze.mockImplementation(async (_form, handlers) => {
      handlers.onPreview({ spec: "", submittal: "" });
      handlers.onExtraction?.({
        spec: { method: "text_layer", chars: 30, ocr_used: false, truncated: false, warning: null },
        submittal: { method: "ocr_pdf", chars: 20, ocr_used: true, truncated: true, warning: "Submittal OCR is truncated." },
      });
      handlers.onResult({ system: "UPS", count: 0, elapsed_ms: 3, mode: "llm", deviations: [] });
      handlers.onDone();
    });
    const user = userEvent.setup();
    render(<AnalyzePanel />);
    const inputs = document.querySelectorAll<HTMLInputElement>('input[type="file"]');
    await user.upload(inputs[0], new File(["spec"], "spec.pdf", { type: "application/pdf" }));
    await user.upload(inputs[1], new File(["sub"], "sub.pdf", { type: "application/pdf" }));
    await user.click(screen.getByRole("button", { name: "Upload & Analyze" }));
    expect(await screen.findByText("0 deviations found")).toBeInTheDocument();
    expect(screen.getByText("Submittal OCR is truncated.")).toBeInTheDocument();
  });

  it("keeps an upload-stream failure explicit", async () => {
    mockedStreamUploadAnalyze.mockImplementation(async (_form, handlers) => {
      handlers.onError("Upload stream rejected");
      handlers.onDone();
    });
    const user = userEvent.setup();
    render(<AnalyzePanel />);
    const inputs = document.querySelectorAll<HTMLInputElement>('input[type="file"]');
    await user.upload(inputs[0], new File(["spec"], "spec.pdf", { type: "application/pdf" }));
    await user.upload(inputs[1], new File(["sub"], "sub.pdf", { type: "application/pdf" }));
    await user.click(screen.getByRole("button", { name: "Upload & Analyze" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Upload stream rejected");
  });

  it("does not silently run the local text engine against uploaded files", async () => {
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => undefined);
    const user = userEvent.setup();
    render(<AnalyzePanel />);
    const inputs = document.querySelectorAll<HTMLInputElement>('input[type="file"]');
    await user.upload(inputs[0], new File(["spec"], "spec.pdf", { type: "application/pdf" }));
    await user.upload(inputs[1], new File(["sub"], "sub.pdf", { type: "application/pdf" }));
    await user.click(screen.getByRole("checkbox", { name: "Local Engine (Instant)" }));
    await user.click(screen.getByRole("button", { name: "Upload & Analyze" }));

    expect(alertSpy).toHaveBeenCalledWith(expect.stringContaining("optimized for pasted text"));
    expect(mockedStreamUploadAnalyze).not.toHaveBeenCalled();
  });
});

describe("ResolutionWorkflow", () => {
  it("moves a protected case through finding, RFI, and audited closure", async () => {
    const responses = [
      { case_id: "case-1", secret: "case-secret" },
      { finding_id: "finding-1" },
      {},
      { rfi_id: "rfi-1" },
      {},
      {},
      {},
      {},
      { audit_log: [{}, {}, {}, {}, {}] },
    ];
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      new Response(JSON.stringify(responses.shift() ?? {}), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<ResolutionWorkflow />);

    await user.click(screen.getByRole("button", { name: "Open a protected case" }));
    await user.click(await screen.findByRole("button", { name: "Assign and accept" }));
    await user.click(await screen.findByRole("button", { name: "Draft and issue RFI" }));
    await user.click(await screen.findByRole("button", { name: "Record response and close" }));

    expect(await screen.findByText("Closed with evidence.")).toBeInTheDocument();
    expect(screen.getByText("5 immutable audit events recorded for this case.")).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(9);
  });

  it("keeps a failed step retryable and never labels it successful", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Case store unavailable" }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<ResolutionWorkflow />);

    await user.click(screen.getByRole("button", { name: "Open a protected case" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Case store unavailable");
    expect(screen.getByRole("button", { name: "Retry this step" })).toBeEnabled();
    await waitFor(() => expect(screen.getByText("Ready")).toBeInTheDocument());
  });

  it("translates an aborted request into an actionable timeout", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("request aborted"));
    const user = userEvent.setup();
    render(<ResolutionWorkflow />);
    await user.click(screen.getByRole("button", { name: "Open a protected case" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("did not respond within 20 seconds");
  });
});
