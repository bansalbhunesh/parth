"use client";

// The real pipeline order, surfaced as live progress while an analysis runs.
// Stage inference is presentational only — every stage shown here corresponds
// to an actual step in backend/orchestrator.py; nothing is invented.
const STAGES = ["Ingest", "Validate", "Reason (model)", "Map to Cx", "Audit"] as const;

interface Props {
  status: string;
  streamingTokens: boolean;
}

function activeIndex(status: string, streamingTokens: boolean): number {
  if (streamingTokens) return 2;
  const s = status.toLowerCase();
  if (/upload|read|ocr|extract|waking|connect/.test(s)) return 0;
  if (/valid|pars|normal/.test(s)) return 1;
  if (/reason|model|llm|analyz/.test(s)) return 2;
  return 0;
}

export default function AnalyzeStages({ status, streamingTokens }: Props) {
  const active = activeIndex(status, streamingTokens);
  return (
    <ol className="analyze-stages" aria-label="Analysis pipeline progress">
      {STAGES.map((label, i) => (
        <li
          key={label}
          className={`analyze-stage ${i < active ? "is-done" : ""} ${i === active ? "is-active" : ""}`}
          aria-current={i === active ? "step" : undefined}
        >
          <span className="analyze-stage-dot" aria-hidden="true" />
          {label}
        </li>
      ))}
    </ol>
  );
}
