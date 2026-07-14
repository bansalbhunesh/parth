import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import AnalyzeResults from "../components/analyze/AnalyzeResults";
import DropZone from "../components/analyze/DropZone";
import type { AnalyzeResult } from "../components/analyze/model";

const EMPTY_RESULT: AnalyzeResult = {
  system: "UPS",
  count: 0,
  deviations: [],
  elapsed_ms: 15,
  mode: "vision",
};

describe("AnalyzeResults", () => {
  it("distinguishes a model-backed clean result and reports OCR provenance", () => {
    render(
      <AnalyzeResults
        result={EMPTY_RESULT}
        extraction={{
          spec: { method: "ocr_pdf", chars: 10, ocr_used: true, truncated: false, warning: null },
          submittal: { method: "text_layer", chars: 10, ocr_used: false, truncated: false, warning: null },
        }}
      />,
    );
    expect(screen.getByText(/meets all identified requirements/)).toBeInTheDocument();
    expect(screen.getByText("Vision (image) reasoning")).toBeInTheDocument();
    expect(screen.getByText("OCR text extraction")).toBeInTheDocument();
  });

  it("renders optional evidence only when the finding supplies it", () => {
    render(
      <AnalyzeResults
        result={{
          ...EMPTY_RESULT,
          count: 2,
          mode: "unexpected",
          deviations: [
            { component: "UPS", parameter: "runtime", required_value: 10, provided_value: 7, unit: "min", severity: "Critical", rationale: "Below requirement", standard_ref: "DB", spec_clause: "4.3", predicted_cx_test: "IST-07", lead_time_weeks: 9 },
            { component: "", parameter: "noise", required_value: 72, provided_value: 71, unit: "dB", severity: "Minor", rationale: "" },
          ],
        }}
        extraction={null}
      />,
    );
    expect(screen.getByText("2 deviations found")).toBeInTheDocument();
    expect(screen.getByText("Provenance unknown")).toBeInTheDocument();
    expect(screen.getByText("Cx: IST-07")).toBeInTheDocument();
    expect(screen.getByText("9w lead")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});

describe("DropZone", () => {
  it("accepts drag/drop and clears the drag state", () => {
    const onFile = vi.fn();
    const file = new File(["content"], "basis.txt", { type: "text/plain" });
    const { rerender } = render(<DropZone label="Spec" file={null} onFile={onFile} accept=".txt" disabled={false} />);
    const zone = screen.getByRole("button", { name: /Spec: drop/ });

    fireEvent.dragOver(zone);
    expect(zone).toHaveClass("drag-over");
    fireEvent.dragLeave(zone);
    expect(zone).not.toHaveClass("drag-over");
    fireEvent.drop(zone, { dataTransfer: { files: [file] } });
    expect(onFile).toHaveBeenCalledWith(file);

    rerender(<DropZone label="Spec" file={file} onFile={onFile} accept=".txt" disabled={false} />);
    expect(zone).toHaveTextContent("basis.txt");
  });

  it("opens the picker from keyboard but remains inert when disabled", () => {
    const clickSpy = vi.spyOn(HTMLInputElement.prototype, "click").mockImplementation(() => undefined);
    const { rerender } = render(<DropZone label="Spec" file={null} onFile={vi.fn()} accept=".txt" disabled={false} />);
    const zone = screen.getByRole("button", { name: /Spec: drop/ });
    fireEvent.keyDown(zone, { key: "Enter" });
    fireEvent.keyDown(zone, { key: " " });
    fireEvent.click(zone);
    expect(clickSpy).toHaveBeenCalledTimes(3);

    rerender(<DropZone label="Spec" file={null} onFile={vi.fn()} accept=".txt" disabled />);
    fireEvent.keyDown(zone, { key: "Enter" });
    fireEvent.click(zone);
    expect(clickSpy).toHaveBeenCalledTimes(3);
    expect(zone).toHaveAttribute("aria-disabled", "true");
  });
});
