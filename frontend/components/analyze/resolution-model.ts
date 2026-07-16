import type { AnalyzeDeviation, AnalyzeResult } from "./model";

function normalizedTarget(deviation: AnalyzeDeviation): string {
  return `${deviation.component || "?"}/${deviation.parameter || "?"}`.toLowerCase();
}

export function primaryDeviation(result: AnalyzeResult): AnalyzeDeviation {
  const resolvedTargets = result.remediation?.highest_leverage?.resolves ?? [];
  const targets = new Set(resolvedTargets.map((target) => target.toLowerCase()));
  return result.deviations.find((deviation) => targets.has(normalizedTarget(deviation)))
    ?? result.deviations[0];
}

export function humanSystemLabel(result: AnalyzeResult): string {
  const components = [...new Set(result.deviations.map((item) => item.component).filter(Boolean))];
  if (components.length === 1) return components[0];
  if (components.length > 1) return `${components[0]} + ${components.length - 1} more`;
  if (result.system && result.system.toUpperCase() !== "CUSTOM") return result.system;
  return "submitted system";
}

export function humanActionLabel(result: AnalyzeResult): string {
  const deviation = primaryDeviation(result);
  const parameter = deviation.parameter.replaceAll("_", " ");
  const cx = deviation.predicted_cx_test ? ` before ${deviation.predicted_cx_test}` : "";
  return `Resolve ${deviation.component} ${parameter}${cx}`;
}

export function humanizeRiskTarget(target: string, deviations: AnalyzeDeviation[]): string {
  const components = [...new Set(deviations.map((item) => item.component).filter(Boolean))];
  if (/custom|\(system\)/i.test(target)) {
    return components.length === 1 ? `${components[0]} system` : "submitted systems";
  }
  return target.replaceAll("_", " ").replace("/", " · ");
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function buildRevisedSubmittal(
  submittal: string,
  deviation: AnalyzeDeviation,
): string {
  const provided = String(deviation.provided_value ?? "").trim();
  const required = String(deviation.required_value ?? "").trim();
  if (!submittal.trim() || !provided || !required) return submittal;

  const valuePattern = new RegExp(escapeRegExp(provided), "i");
  const revised = valuePattern.test(submittal)
    ? submittal.replace(valuePattern, required)
    : submittal;
  const changeNote = [
    "",
    "REVISION C — FORMAL VENDOR RESPONSE",
    `${deviation.component} ${deviation.parameter.replaceAll("_", " ")}: ${required} ${deviation.unit}`.trim(),
    `This value supersedes the earlier ${provided} ${deviation.unit} submission and is offered for verification.`.trim(),
  ].join("\n");
  return `${revised.trimEnd()}\n${changeNote}\n`;
}

export function findingCleared(result: AnalyzeResult, target: AnalyzeDeviation): boolean {
  return !result.deviations.some(
    (deviation) => normalizedTarget(deviation) === normalizedTarget(target),
  );
}
