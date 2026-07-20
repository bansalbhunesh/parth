"use client";
import { useEffect, useRef, useState } from "react";
import { streamAnalyze, streamUploadAnalyze, getOcrCheck } from "../lib/api";
import type { OcrStatus, UploadExtraction } from "../lib/api";
import AnalyzeResults from "./analyze/AnalyzeResults";
import DropZone from "./analyze/DropZone";
import { runLocalReconciliation } from "./analyze/local-reconciliation";
import { friendlyError, type AnalyzeResult, type InputMode } from "./analyze/model";
import { EXAMPLE_SPEC, EXAMPLE_SUBMITTAL, REAL_SPEC, REAL_SUBMITTAL, CLEAN_SUBMITTAL } from "./analyze/demo-fixtures";
import AnalyzeStages from "./analyze/AnalyzeStages";


const API = process.env.NEXT_PUBLIC_API ?? "http://127.0.0.1:8000";

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
  const [ocr, setOcr] = useState<OcrStatus | null>(null);
  const [extraction, setExtraction] = useState<UploadExtraction | null>(null);
  const [localMode, setLocalMode] = useState(false);
  const [preview, setPreview] = useState<AnalyzeResult | null>(null);
  const [systemId, setSystemId] = useState("CUSTOM");
  const abortRef = useRef<AbortController | null>(null);

  // Probe whether THIS deployment can OCR, so the UI reflects reality instead of
  // implying a capability the backend may not have. null = unknown → claim nothing.
  useEffect(() => {
    let alive = true;
    getOcrCheck().then((s) => { if (alive) setOcr(s); });
    return () => { alive = false; };
  }, []);

  useEffect(() => () => abortRef.current?.abort(), []);

  // Only offer image upload when the backend can actually OCR images.
  const imageOcrOk = ocr?.image_ocr_supported ?? false;
  const acceptTypes = imageOcrOk ? ".pdf,.md,.txt,.png,.jpg,.jpeg,.tiff,.webp" : ".pdf,.md,.txt";
  const dropHint = imageOcrOk
    ? "Drop PDF/image/MD/TXT here or click to browse"
    : "Drop PDF/MD/TXT here or click to browse";

  // Show the OCR caveat when either uploaded document was read via OCR.
  const ocrWarning =
    extraction && (extraction.spec.ocr_used || extraction.submittal.ocr_used)
      ? extraction.submittal.warning ?? extraction.spec.warning
      : null;



  const resetState = (): AbortController => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setStreaming(true);
    setError("");
    setResult(null);
    setStreamText("");
    setSpecPreview("");
    setSubPreview("");
    setExtraction(null);
    
    // Render free-tier cold-start UX gracefully
    setTimeout(() => {
      if (!controller.signal.aborted) {
        setStatus((prev) => {
          if (prev === "Connecting to analysis engine..." || prev === "Uploading documents...") {
            return "Waking up the analysis engine (free-tier cold start, ~15-30s)...";
          }
          return prev;
        });
      }
    }, 4000);
    
    return controller;
  };

  const finalize = (controller?: AbortController) => {
    if (controller && abortRef.current !== controller) return;
    setLoading(false);
    setStreaming(false);
    setStatus("");
    abortRef.current = null;
  };

  const handleAnalyzePdf = async () => {
    if (localMode) {
      setError("Local Engine runs pasted text only. Switch to Paste Text or turn off Local Engine to upload documents.");
      return;
    }
    if (!specFile || !submittalFile) return;
    const controller = resetState();
    setStatus("Uploading documents...");

    const formData = new FormData();
    formData.append("spec_file", specFile);
    formData.append("submittal_file", submittalFile);
    formData.append("system_id", systemId);

    await streamUploadAnalyze(formData, {
      onStatus: setStatus,
      onPreview: (p) => { setSpecPreview(p.spec || ""); setSubPreview(p.submittal || ""); },
      onExtraction: setExtraction,
      onToken: (token) => { if (!controller.signal.aborted) setStreamText((prev) => prev + token); },
      onResult: (res: any) => {
        setResult(res as AnalyzeResult);
        setPreview(null);
        setStreamText("");
        setStreaming(false);
      },
      onError: (err) => {
        if (err !== "Analysis cancelled.") setError(err);
        finalize(controller);
      },
      onDone: () => finalize(controller),
    }, controller.signal);
  };

  const handleAnalyzeText = async () => {
    if (spec.length < 10 || submittal.length < 10) {
      setError("Both spec and submittal must be at least 10 characters.");
      return;
    }
    const controller = resetState();

    if (localMode) {
      setStatus("Running client-side rule engine (instant)...");
      setTimeout(() => {
        if (controller.signal.aborted) return;
        const localResult = runLocalReconciliation(spec, submittal);
        setResult(localResult);
        setPreview(null);
        finalize(controller);
      }, 400);
      return;
    }

    setStatus("Connecting to analysis engine...");

    try {
      await streamAnalyze(
        spec,
        submittal,
        setStatus,
        (token) => { if (!controller.signal.aborted) setStreamText((prev) => prev + token); },
        (res: any) => {
          setResult(res as AnalyzeResult);
          setPreview(null);
          setStreamText("");
          setStreaming(false);
        },
        () => finalize(controller),
        async (err) => {
          if (controller.signal.aborted || err === "Analysis cancelled.") {
            finalize(controller);
            return;
          }
          try {
            const r = await fetch(`${API}/analyze`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ spec_text: spec, submittal_text: submittal, system_id: systemId }),
              signal: controller.signal,
            });
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            const data = await r.json();
            setResult(data);
            setPreview(null);
          } catch (e) {
            if (!controller.signal.aborted) setError(e instanceof Error ? e.message : err);
          }
          finalize(controller);
        },
        controller.signal,
        systemId,
      );
    } catch (e) {
      if (!controller.signal.aborted) setError(e instanceof Error ? e.message : "Analysis failed");
      finalize(controller);
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
    setSystemId("UPS");
    setPreview(runLocalReconciliation(EXAMPLE_SPEC, EXAMPLE_SUBMITTAL));
  };

  const loadRealSample = () => {
    setMode("text");
    setSpec(REAL_SPEC);
    setSubmittal(REAL_SUBMITTAL);
    setResult(null);
    setError("");
    setStreamText("");
    setSystemId("UPS");
    setPreview(runLocalReconciliation(REAL_SPEC, REAL_SUBMITTAL));
  };

  // Clean-negative: same spec, a fully compliant submittal → expect 0 deviations.
  const loadCleanSample = () => {
    setMode("text");
    setSpec(REAL_SPEC);
    setSubmittal(CLEAN_SUBMITTAL);
    setResult(null);
    setError("");
    setStreamText("");
    setSystemId("UPS");
    setPreview(runLocalReconciliation(REAL_SPEC, CLEAN_SUBMITTAL));
  };

  const cancelAnalysis = () => {
    abortRef.current?.abort();
    setError("");
    setStatus("Analysis cancelled. Your documents are still here.");
    setLoading(false);
    setStreaming(false);
    abortRef.current = null;
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
          onClick={() => { setMode("pdf"); setSystemId("CUSTOM"); setError(""); }}
          disabled={loading}
          aria-pressed={mode === "pdf"}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          Upload PDFs
        </button>
        <button
          className={`analyze-mode-btn ${mode === "text" ? "active" : ""}`}
          onClick={() => { setMode("text"); setError(""); }}
          disabled={loading}
          aria-pressed={mode === "text"}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="4 7 4 4 20 4 20 7" />
            <line x1="9" y1="20" x2="15" y2="20" />
            <line x1="12" y1="4" x2="12" y2="20" />
          </svg>
          Paste Text
        </button>
        <button className="analyze-example-btn" onClick={loadRealSample} disabled={loading} aria-label="Load deviation demo ★: realistic demo with hidden non-compliances">
          Load deviation demo ★
        </button>
        <button className="analyze-example-btn" onClick={loadCleanSample} disabled={loading} aria-label="Load compliant demo ✓: with zero expected deviations">
          Load compliant demo ✓
        </button>
        <button className="analyze-example-btn" onClick={loadExample} disabled={loading}>
          Load compact example
        </button>
        <label className="local-mode-toggle">
          <input
            type="checkbox"
            checked={localMode}
            onChange={(e) => { setLocalMode(e.target.checked); if (e.target.checked && mode === "pdf") setMode("text"); }}
            id="local-mode-chk"
          />
          <span>Local Engine (Instant)</span>
        </label>
      </div>

      {mode === "pdf" && ocr && (
        <div className={`ocr-status ${ocr.ocr_available ? "is-ready" : "is-unavailable"}`}>
          <span className="ocr-status-dot" aria-hidden="true" />
          <span>
            {ocr.ocr_available
              ? `OCR ready — scanned PDFs & images supported${ocr.tesseract_version ? ` (Tesseract ${ocr.tesseract_version})` : ""}`
              : ocr.status === "disabled"
                ? "OCR disabled in this deployment — upload text-based PDFs or paste the text"
                : "OCR unavailable in this deployment — upload text-based PDFs or paste the text"}
          </span>
        </div>
      )}

      {mode === "pdf" ? (
        <div className="analyze-editors">
          <div className="analyze-editor">
            <div className="analyze-editor-label">Design Basis (Spec PDF)</div>
            <DropZone
              label="Spec document"
              file={specFile}
              onFile={setSpecFile}
              accept={acceptTypes}
              hint={dropHint}
              disabled={loading}
            />
          </div>
          <div className="analyze-editor">
            <div className="analyze-editor-label">Vendor Submittal (PDF)</div>
            <DropZone
              label="Submittal document"
              file={submittalFile}
              onFile={setSubmittalFile}
              accept={acceptTypes}
              hint={dropHint}
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
              aria-label="Design basis specification text"
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
              aria-label="Vendor submittal text"
              value={submittal}
              onChange={(e) => setSubmittal(e.target.value)}
              placeholder={"Paste vendor submittal here...\n\nExample format:\n- **UPS-02** — battery runtime min: **7 min** (vendor datasheet)"}
              rows={10}
            />
          </div>
        </div>
      )}

      <div className="analyze-actions">
        <button
          className="analyze-submit"
          onClick={handleAnalyze}
          disabled={loading}
        >
          {loading ? "Analyzing..." : mode === "pdf" ? "Upload & Analyze" : "Analyze for deviations"}
        </button>
        {loading ? <button className="analyze-cancel" type="button" onClick={cancelAnalysis}>Cancel analysis</button> : null}
      </div>

      {error && <div className="analyze-error" role="alert">{friendlyError(error)}</div>}

      {ocrWarning && (
        <div className="ocr-warning" role="status">
          <span aria-hidden="true">⚠</span>
          <span>{ocrWarning}</span>
        </div>
      )}

      {loading && (
        <div className="analyze-loading">
          <div className="analyze-loading-bar" />
          <span>{status || "Cross-referencing against 7 governing standards..."}</span>
          <AnalyzeStages status={status} streamingTokens={streaming && streamText.length > 0} />
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
          <div className="analyze-stream-label">Structured extraction trace</div>
          <pre className="analyze-stream-text">
            {streamText}
            <span className="copilot-cursor" />
          </pre>
        </div>
      )}

      {preview && !result ? (
        <section className="instant-preview" aria-label="Deterministic preview">
          <div className="instant-preview-banner" role="status">
            <strong>Deterministic preview</strong> — client-side rule engine, instant, no model call.
            {loading ? " The live model is upgrading this result now…" : " Click Analyze for the live model read."}
          </div>
          <AnalyzeResults
            result={preview}
            extraction={null}
            specText={mode === "text" ? spec : ""}
            submittalText={mode === "text" ? submittal : ""}
          />
        </section>
      ) : null}

      {result ? (
        <AnalyzeResults
          result={result}
          extraction={extraction}
          specText={mode === "text" ? spec : ""}
          submittalText={mode === "text" ? submittal : ""}
        />
      ) : null}
    </div>
  );
}
