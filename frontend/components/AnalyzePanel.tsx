"use client";
import { useState, useRef, useCallback } from "react";
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

type InputMode = "text" | "pdf";

function DropZone({
  label,
  file,
  onFile,
  accept,
  disabled,
}: {
  label: string;
  file: File | null;
  onFile: (f: File) => void;
  accept: string;
  disabled: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) onFile(f);
    },
    [onFile],
  );

  return (
    <div
      className={`analyze-dropzone ${dragOver ? "drag-over" : ""} ${file ? "has-file" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        style={{ display: "none" }}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
        disabled={disabled}
      />
      {file ? (
        <div className="dropzone-file">
          <div className="dropzone-file-icon">PDF</div>
          <div className="dropzone-file-info">
            <div className="dropzone-file-name">{file.name}</div>
            <div className="dropzone-file-size">{(file.size / 1024).toFixed(1)} KB</div>
          </div>
        </div>
      ) : (
        <div className="dropzone-empty">
          <div className="dropzone-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <div className="dropzone-label">{label}</div>
          <div className="dropzone-hint">Drop PDF here or click to browse</div>
        </div>
      )}
    </div>
  );
}

export default function AnalyzePanel() {
  const [mode, setMode] = useState<InputMode>("pdf");
  const [spec, setSpec] = useState("");
  const [submittal, setSubmittal] = useState("");
  const [specFile, setSpecFile] = useState<File | null>(null);
  const [submittalFile, setSubmittalFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [streamText, setStreamText] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [specPreview, setSpecPreview] = useState("");
  const [subPreview, setSubPreview] = useState("");
  const abortRef = useRef(false);

  const canAnalyzeText = spec.length >= 10 && submittal.length >= 10;
  const canAnalyzePdf = specFile !== null && submittalFile !== null;
  const canAnalyze = mode === "text" ? canAnalyzeText : canAnalyzePdf;

  const handleAnalyzePdf = async () => {
    if (!specFile || !submittalFile) return;
    abortRef.current = false;
    setLoading(true);
    setStreaming(true);
    setError("");
    setResult(null);
    setStreamText("");
    setSpecPreview("");
    setSubPreview("");
    setStatus("Uploading documents...");

    try {
      const formData = new FormData();
      formData.append("spec_file", specFile);
      formData.append("submittal_file", submittalFile);

      const r = await fetch(`${API}/analyze/upload/stream`, {
        method: "POST",
        body: formData,
      });

      if (!r.ok || !r.body) {
        const fallbackR = await fetch(`${API}/analyze/upload`, {
          method: "POST",
          body: formData,
        });
        if (!fallbackR.ok) throw new Error(`HTTP ${fallbackR.status}`);
        const data = await fallbackR.json();
        setResult(data);
        if (data.spec_preview) setSpecPreview(data.spec_preview);
        if (data.submittal_preview) setSubPreview(data.submittal_preview);
        setLoading(false);
        setStreaming(false);
        setStatus("");
        return;
      }

      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7);
          } else if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (currentEvent === "status") {
              setStatus(data);
            } else if (currentEvent === "preview") {
              try {
                const p = JSON.parse(data);
                setSpecPreview(p.spec || "");
                setSubPreview(p.submittal || "");
              } catch {}
            } else if (currentEvent === "token") {
              if (!abortRef.current) {
                try {
                  setStreamText((prev) => prev + JSON.parse(data));
                } catch {
                  setStreamText((prev) => prev + data);
                }
              }
            } else if (currentEvent === "result") {
              try { setResult(JSON.parse(data)); } catch {}
              setStreamText("");
              setStreaming(false);
            } else if (currentEvent === "error") {
              setError(data);
            } else if (currentEvent === "done") {
              setLoading(false);
              setStreaming(false);
              setStatus("");
              return;
            }
          }
        }
      }
      setLoading(false);
      setStreaming(false);
      setStatus("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setLoading(false);
      setStreaming(false);
    }
  };

  const handleAnalyzeText = async () => {
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

  const handleAnalyze = mode === "pdf" ? handleAnalyzePdf : handleAnalyzeText;

  const loadExample = () => {
    setMode("text");
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
          Upload spec and submittal PDFs — or paste text — and Pramaan will cross-reference
          them against 7 governing standards and identify deviations in real time.
        </div>
      </div>

      <div className="analyze-mode-toggle">
        <button
          className={`analyze-mode-btn ${mode === "pdf" ? "active" : ""}`}
          onClick={() => setMode("pdf")}
          disabled={loading}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          Upload PDFs
        </button>
        <button
          className={`analyze-mode-btn ${mode === "text" ? "active" : ""}`}
          onClick={() => setMode("text")}
          disabled={loading}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="4 7 4 4 20 4 20 7" />
            <line x1="9" y1="20" x2="15" y2="20" />
            <line x1="12" y1="4" x2="12" y2="20" />
          </svg>
          Paste Text
        </button>
        <button className="analyze-example-btn" onClick={loadExample} disabled={loading}>
          Load example
        </button>
      </div>

      {mode === "pdf" ? (
        <div className="analyze-editors">
          <div className="analyze-editor">
            <div className="analyze-editor-label">Design Basis (Spec PDF)</div>
            <DropZone
              label="Spec document"
              file={specFile}
              onFile={setSpecFile}
              accept=".pdf,.md,.txt"
              disabled={loading}
            />
          </div>
          <div className="analyze-editor">
            <div className="analyze-editor-label">Vendor Submittal (PDF)</div>
            <DropZone
              label="Submittal document"
              file={submittalFile}
              onFile={setSubmittalFile}
              accept=".pdf,.md,.txt"
              disabled={loading}
            />
          </div>
        </div>
      ) : (
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
      )}

      <button
        className="analyze-submit"
        onClick={handleAnalyze}
        disabled={loading || !canAnalyze}
      >
        {loading ? "Analyzing..." : mode === "pdf" ? "Upload & Analyze" : "Analyze for deviations"}
      </button>

      {error && <div className="analyze-error">{error}</div>}

      {loading && (
        <div className="analyze-loading">
          <div className="analyze-loading-bar" />
          <span>{status || "Cross-referencing against 7 governing standards..."}</span>
        </div>
      )}

      {(specPreview || subPreview) && !result && (
        <div className="analyze-previews">
          <div className="analyze-preview-label">Extracted text preview</div>
          <div className="analyze-preview-grid">
            {specPreview && (
              <div className="analyze-preview-box">
                <div className="analyze-preview-title">Spec</div>
                <div className="analyze-preview-text">{specPreview}</div>
              </div>
            )}
            {subPreview && (
              <div className="analyze-preview-box">
                <div className="analyze-preview-title">Submittal</div>
                <div className="analyze-preview-text">{subPreview}</div>
              </div>
            )}
          </div>
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
