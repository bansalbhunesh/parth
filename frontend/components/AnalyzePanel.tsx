"use client";
import { useEffect, useRef, useState } from "react";
import { streamAnalyze, streamUploadAnalyze, getOcrCheck } from "../lib/api";
import type { OcrStatus, UploadExtraction } from "../lib/api";
import AnalyzeResults from "./analyze/AnalyzeResults";
import DropZone from "./analyze/DropZone";
import { runLocalReconciliation } from "./analyze/local-reconciliation";
import { friendlyError, type AnalyzeResult, type InputMode } from "./analyze/model";

const EXAMPLE_SPEC = `# Design Basis: UPS System
- **UPS-02** — battery runtime min: shall be **10 min** (ref: UPTIME-TIER4; clause DB-4.3)
- **UPS-02** — redundancy: shall be **2N topology** (ref: UPTIME-TIER4; clause DB-4.1)
- **UPS-02** — efficiency pct: shall be **96 %** (ref: DESIGN-BASIS; clause DB-4.5)`;

const EXAMPLE_SUBMITTAL = `# Vendor Submittal: UPS System
- **UPS-02** — battery runtime min: **7 min** (vendor datasheet)
- **UPS-02** — redundancy: **2N topology** (vendor datasheet)
- **UPS-02** — efficiency pct: **93 %** (vendor datasheet)`;

// A realistic design basis + vendor datasheet written in natural prose + tables
// (nothing like the structured corpus). Proves the reasoning generalises to a
// document a vendor would actually send. Buried deviations: redundancy (2N
// required vs N+1 offered) and battery autonomy (10 min EoL required vs 8 min
// BoL offered). Compliant rows (efficiency, THD, noise) must NOT be flagged.
const REAL_SPEC = `SECTION 26 33 53 — STATIC UPS · Project Helios (Tier IV) · Issued for Construction

2. PERFORMANCE REQUIREMENTS
The Contractor shall provide a double-conversion UPS meeting these minimums.
A proposal differing from these values is non-conforming unless a formal
deviation is approved in writing.

  2.1 System configuration ......... Distributed redundant, 2N across two paths
  2.2 Module rated power ........... 1000 kW per module, minimum
  2.3 Battery autonomy at full load  Not less than 10 minutes, at END OF LIFE,
                                     minimum design temperature, one string out
  2.4 Efficiency at 100% load ...... >= 96.0%
  2.5 Input THDi at full load ...... <= 3%
  2.6 Acoustic noise at 1 m ........ <= 72 dB(A)

3. REDUNDANCY
Any single module, static switch or path must be removable for maintenance
without dropping the critical load. A 2N topology is mandatory; N+1 does not
satisfy this requirement. Runtime quoted at beginning of life only shall not
be accepted as evidence of compliance.`;

const REAL_SUBMITTAL = `TECHNICAL SUBMITTAL — PowerGuard ePX-1000 UPS
Submitted by Apex Critical Power · Submittal APX-EL-0241 · For Approval

The ePX-1000 is a field-proven transformer-free double-conversion system trusted
by leading hyperscale operators.

1. System Overview
Modular UPS units arranged in an N+1 redundant configuration on each power bus,
delivering excellent availability while optimising capital cost for the client.

2. Guaranteed Technical Particulars
  2.1 Topology ......................... Double conversion (VFI-SS-111)
  2.2 Module rated active power ........ 1000 kW
  2.3 System redundancy (per bus) ...... N+1
  2.4 Battery autonomy at full load .... 8 minutes (VRLA, beginning of life @ 25C)
  2.5 Online efficiency at 100% load ... 96.5%
  2.6 Input current THD ................ < 3%
  2.7 Audible noise at 1 m ............. 71 dB(A)

4. Compliance Statement
Apex Critical Power confirms the ePX-1000 meets or exceeds all applicable
performance requirements and is offered as fully compliant with the project
specification.`;

// Clean-negative demo: a submittal that MEETS or EXCEEDS every requirement in
// REAL_SPEC (2N, 1000 kW, 10 min EoL autonomy, >=96% eff, THD <=3%, <=72 dB).
// The correct answer is ZERO deviations — it demonstrates the low false-alert
// behaviour the benchmark measures (0 false alerts on 64 clean-negative controls),
// not just the ability to find faults.
const CLEAN_SUBMITTAL = `TECHNICAL SUBMITTAL — TruePower DCX-1000 UPS
Submitted by Meridian Power Systems · Submittal MPS-EL-0117 · For Approval

1. System Overview
Modular double-conversion UPS arranged in a full 2N configuration across two
independent power paths. Any single module, static switch or path can be removed
for maintenance without dropping the critical load.

2. Guaranteed Technical Particulars
  2.1 Topology ......................... Double conversion (VFI-SS-111)
  2.2 Module rated active power ........ 1000 kW
  2.3 System redundancy ................ 2N (two independent paths)
  2.4 Battery autonomy at full load .... 11 minutes at END OF LIFE, minimum
                                         design temperature, one string out
  2.5 Online efficiency at 100% load ... 96.4%
  2.6 Input current THD ................ 2.7%
  2.7 Audible noise at 1 m ............. 70 dB(A)

3. Compliance Statement
Meridian confirms the DCX-1000 meets or exceeds every performance requirement in
Section 26 33 53, including the 2N topology and end-of-life autonomy provisions.`;

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
  };

  const loadRealSample = () => {
    setMode("text");
    setSpec(REAL_SPEC);
    setSubmittal(REAL_SUBMITTAL);
    setResult(null);
    setError("");
    setStreamText("");
    setSystemId("UPS");
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
