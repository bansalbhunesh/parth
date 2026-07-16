import type { UploadExtraction } from "../../lib/api";
import AnalyzeResolutionWorkflow from "./AnalyzeResolutionWorkflow";
import RiskRemediation from "./RiskRemediation";
import { formatElapsed, isModelBacked, provenance, timingTitle, type AnalyzeResult } from "./model";

interface AnalyzeResultsProps {
  result: AnalyzeResult;
  extraction: UploadExtraction | null;
  specText: string;
  submittalText: string;
}

export default function AnalyzeResults({ result, extraction, specText, submittalText }: AnalyzeResultsProps) {
  const source = provenance(result.mode);
  const usedOcr = extraction?.spec.ocr_used || extraction?.submittal.ocr_used;
  const evidenceByTarget = new Map((result.evidence?.findings ?? []).map((finding) => [finding.target, finding]));
  return (
    <div className="analyze-results" aria-live="polite">
      <div className="analyze-results-header">
        <span className="analyze-results-count">
          {result.count} deviation{result.count !== 1 ? "s" : ""} found
        </span>
        <span className="analyze-results-meta">
          <span className={`analyze-prov ${source.cls}`} title={source.title}>{source.label}</span>
          {result.cached ? (
            <span
              className="analyze-prov prov-cache"
              title={`Reused a verified result for the same documents, system, prompt and model configuration${result.input_hash ? ` (input ${result.input_hash})` : ""}.`}
            >
              Verified cache replay
            </span>
          ) : null}
          {usedOcr ? (
            <span className="analyze-prov prov-ocr" title="At least one document was read through best-effort OCR.">
              OCR text extraction
            </span>
          ) : null}
          <span className="analyze-results-time" title={timingTitle(result.timing)}>{formatElapsed(result.elapsed_ms)}</span>
          {result.input_hash ? <span className="analyze-results-hash" title={result.input_hash}>Input {result.input_hash.slice(0, 10)}</span> : null}
        </span>
      </div>

      <RiskRemediation
        compoundRisk={result.compound_risk}
        remediation={result.remediation}
        deviations={result.deviations}
      />

      {result.deviations.length === 0 ? (
        isModelBacked(result.mode) ? (
          <div className="analyze-no-devs">No deviations detected — the submittal meets all identified requirements.</div>
        ) : (
          <div className="analyze-no-devs inconclusive">
            No deviations found by the <strong>deterministic rule floor</strong> — the live model was unavailable,
            and this floor is low-recall by design, so this is <strong>not</strong> a clean bill of health. Re-run
            when the live model is reachable for a full check.
          </div>
        )
      ) : (
        <div className="analyze-devs">
          {result.deviations.map((deviation, index) => {
            const strength = evidenceByTarget.get(`${deviation.component || "?"}/${deviation.parameter || "?"}`);
            return (
            <article key={`${deviation.component}-${deviation.parameter}-${index}`} className={`analyze-dev analyze-dev-${deviation.severity.toLowerCase()}`}>
              <div className="analyze-dev-header">
                <span className="analyze-dev-component">{deviation.component || "—"}</span>
                <span className={`sev ${deviation.severity}`}>{deviation.severity || "—"}</span>
              </div>
              <div className="analyze-dev-param">{deviation.parameter.replaceAll("_", " ")}</div>
              <div className="analyze-dev-values">
                <span className="analyze-dev-req">Required: {deviation.required_value} {deviation.unit}</span>
                <span className="analyze-dev-prov">Provided: {deviation.provided_value} {deviation.unit}</span>
              </div>
              {deviation.rationale ? <div className="analyze-dev-rationale">{deviation.rationale}</div> : null}
              <div className="analyze-dev-refs">
                {deviation.standard_ref ? <span className="analyze-dev-ref">{deviation.standard_ref}</span> : null}
                {deviation.spec_clause ? <span className="analyze-dev-ref">{deviation.spec_clause}</span> : null}
                {deviation.predicted_cx_test ? <span className="analyze-dev-ref">Cx: {deviation.predicted_cx_test}</span> : null}
                {deviation.lead_time_weeks && deviation.lead_time_weeks > 0 ? <span className="analyze-dev-ref">{deviation.lead_time_weeks}w lead</span> : null}
                {strength ? (
                  <span className="analyze-dev-ref" title={strength.signals.join(", ") || "no corroborating signals"}>
                    Evidence: {strength.band}
                  </span>
                ) : null}
              </div>
            </article>
            );
          })}
        </div>
      )}

      {result.deviations.length > 0 && specText && submittalText ? (
        <AnalyzeResolutionWorkflow result={result} specText={specText} submittalText={submittalText} />
      ) : result.deviations.length > 0 ? (
        <p className="resolution-unavailable">
          To demonstrate verified closure, switch to Paste Text so the revised vendor document can be re-analyzed in this browser.
        </p>
      ) : null}
    </div>
  );
}
