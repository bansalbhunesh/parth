"use client";
import { useState, useRef } from "react";
import { streamAnalyze } from "../lib/api";

const EXAMPLE_SPEC = `# Design Basis: UPS System
- **UPS-02** — battery runtime min: shall be **10 min** (ref: UPTIME-TIER4; clause DB-4.3)
- **UPS-02** — redundancy: shall be **2N topology** (ref: UPTIME-TIER4; clause DB-4.1)
- **UPS-02** — efficiency pct: shall be **96 %** (ref: DESIGN-BASIS; clause DB-4.5)`;

const EXAMPLE_SUBMITTAL = `# Vendor Submittal: UPS System
- **UPS-02** — battery runtime min: **7 min** (vendor datasheet)
- **UPS-02** — redundancy: **2N topology** (vendor datasheet)
- **UPS-02** — efficiency pct: **93 %** (vendor datasheet)`;

interface AnalyzeResult {
  system: string;
  deviations: Array<{
    component: string;
    parameter: string;
    required_value: string | number;
    provided_value: string | number;
    unit: string;
    severity: string;
    rationale: string;
    standard_ref?: string;
    spec_clause?: string;
    predicted_cx_test?: string;
    lead_time_weeks?: number;
  }>;
  count: number;
  elapsed_ms: number;
  mode: string;
}

const API = process.env.NEXT_PUBLIC_API ?? "http://localhost:8000";

export default function AnalyzePanel() {
  const [spec, setSpec] = useState("");
  const [submittal, setSubmittal] = useState("");
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [streamText, setStreamText] = useState("");
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef(false);

  const handleAnalyze = async () => {
    if (spec.length < 10 || submittal.length < 10) {
      setError("Both spec and submittal must be at least 10 characters.");
      return;
    }
    abortRef.current = false;
    setLoading(true);
    setStreaming(true);
    setError("");
    setResult(null);
    setStreamText("");
    setStatus("Connecting to analysis engine...");

    try {
      await streamAnalyze(
        spec,
        submittal,
        (s) => setStatus(s),
        (token) => {
          if (!abortRef.current) {
            setStreamText((prev) => prev + token);
          }
        },
        (res) => {
          setResult(res as AnalyzeResult);
          setStreamText("");
          setStreaming(false);
        },
        () => {
          setLoading(false);
          setStreaming(false);
          setStatus("");
        },
        async (err) => {
          try {
            const r = await fetch(`${API}/analyze`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ spec_text: spec, submittal_text: submittal }),
            });
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            const data = await r.json();
            setResult(data);
          } catch (e) {
            setError(e instanceof Error ? e.message : err);
          }
          setLoading(false);
          setStreaming(false);
          setStatus("");
        },
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
      setLoading(false);
      setStreaming(false);
    }
  };

  const loadExample = () => {
    setSpec(EXAMPLE_SPEC);
    setSubmittal(EXAMPLE_SUBMITTAL);
    setResult(null);
    setError("");
    setStreamText("");
  };

  return (
    <div className="analyze-panel">
      <div className="analyze-header">
        <div className="analyze-badge">LIVE ANALYSIS</div>
        <div className="analyze-desc">
          Paste any design-basis spec and vendor submittal below. Pramaan will cross-reference
          them against 7 governing standards and identify deviations in real time.
        </div>
      </div>

      <div className="analyze-actions">
        <button className="analyze-example-btn" onClick={loadExample}>
          Load example (UPS system)
        </button>
      </div>

      <div className="analyze-editors">
        <div className="analyze-editor">
          <div className="analyze-editor-label">Design Basis (Spec)</div>
          <textarea
            className="analyze-textarea"
            value={spec}
            onChange={(e) => setSpec(e.target.value)}
            placeholder={"Paste design basis requirements here...\n\nExample format:\n- **UPS-02** — battery runtime min: shall be **10 min** (ref: UPTIME-TIER4; clause DB-4.3)"}
            rows={10}
          />
        </div>
        <div className="analyze-editor">
          <div className="analyze-editor-label">Vendor Submittal</div>
          <textarea
            className="analyze-textarea"
            value={submittal}
            onChange={(e) => setSubmittal(e.target.value)}
            placeholder={"Paste vendor submittal here...\n\nExample format:\n- **UPS-02** — battery runtime min: **7 min** (vendor datasheet)"}
            rows={10}
          />
        </div>
      </div>

      <button
        className="analyze-submit"
        onClick={handleAnalyze}
        disabled={loading || spec.length < 10 || submittal.length < 10}
      >
        {loading ? "Analyzing..." : "Analyze for deviations"}
      </button>

      {error && <div className="analyze-error">{error}</div>}

      {loading && (
        <div className="analyze-loading">
          <div className="analyze-loading-bar" />
          <span>{status || "Cross-referencing against 7 governing standards..."}</span>
        </div>
      )}

      {streaming && streamText && (
        <div className="analyze-stream">
          <div className="analyze-stream-label">AI reasoning</div>
          <pre className="analyze-stream-text">
            {streamText}
            <span className="copilot-cursor" />
          </pre>
        </div>
      )}

      {result && (
        <div className="analyze-results">
          <div className="analyze-results-header">
            <span className="analyze-results-count">
              {result.count} deviation{result.count !== 1 ? "s" : ""} found
            </span>
            <span className="analyze-results-meta">
              {result.elapsed_ms}ms · {result.mode} mode
            </span>
          </div>

          {result.deviations.length === 0 ? (
            <div className="analyze-no-devs">
              No deviations detected — submittal meets all identified requirements.
            </div>
          ) : (
            <div className="analyze-devs">
              {result.deviations.map((d, i) => (
                <div key={i} className={`analyze-dev analyze-dev-${d.severity.toLowerCase()}`}>
                  <div className="analyze-dev-header">
                    <span className="analyze-dev-component">{d.component}</span>
                    <span className={`sev ${d.severity}`}>{d.severity}</span>
                  </div>
                  <div className="analyze-dev-param">{d.parameter.replace(/_/g, " ")}</div>
                  <div className="analyze-dev-values">
                    <span className="analyze-dev-req">Required: {d.required_value} {d.unit}</span>
                    <span className="analyze-dev-prov">Provided: {d.provided_value} {d.unit}</span>
                  </div>
                  {d.rationale && <div className="analyze-dev-rationale">{d.rationale}</div>}
                  <div className="analyze-dev-refs">
                    {d.standard_ref && <span className="analyze-dev-ref">{d.standard_ref}</span>}
                    {d.spec_clause && <span className="analyze-dev-ref">{d.spec_clause}</span>}
                    {d.predicted_cx_test && <span className="analyze-dev-ref">Cx: {d.predicted_cx_test}</span>}
                    {d.lead_time_weeks && <span className="analyze-dev-ref">{d.lead_time_weeks}w lead</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
