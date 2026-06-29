"use client";

import { useState, useRef, useCallback } from "react";
import { askCopilot, streamCopilot, CopilotResponse } from "../lib/api";

const PRESETS = [
  "Has the UPS battery runtime issue come up before?",
  "What is the required cooling redundancy for Tier IV?",
  "Which deviations will fail during IST testing?",
  "What are the seismic requirements for the structural system?",
  "Summarize all critical findings and their lead times",
];

export default function CopilotPanel() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [priorRfis, setPriorRfis] = useState<CopilotResponse["prior_rfis"]>([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef(false);

  const handleSubmit = useCallback(async (q: string) => {
    const actualQuery = q || query;
    if (!actualQuery.trim()) return;
    abortRef.current = false;
    setLoading(true);
    setStreaming(true);
    setQuery(actualQuery);
    setAnswer("");
    setSources([]);
    setPriorRfis([]);

    try {
      await streamCopilot(
        actualQuery,
        (meta) => {
          setSources(meta.sources);
          setPriorRfis(meta.prior_rfis);
        },
        (token) => {
          if (!abortRef.current) {
            setAnswer((prev) => prev + token);
          }
        },
        () => {
          setStreaming(false);
          setLoading(false);
        },
        async (err) => {
          try {
            const res = await askCopilot(actualQuery);
            setAnswer(res.answer);
            setSources(res.sources);
            setPriorRfis(res.prior_rfis);
          } catch {
            setAnswer(err);
          }
          setStreaming(false);
          setLoading(false);
        },
      );
    } catch {
      setStreaming(false);
      setLoading(false);
    }
  }, [query]);

  return (
    <div className="copilot">
      <div className="copilot-presets">
        {PRESETS.map((p) => (
          <button
            key={p}
            className="copilot-preset"
            onClick={() => handleSubmit(p)}
            disabled={loading}
          >
            {p}
          </button>
        ))}
      </div>

      <div className="copilot-input-row">
        <input
          className="copilot-input"
          aria-label="Ask the project copilot a question"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about specs, submittals, standards, or RFIs..."
          onKeyDown={(e) => e.key === "Enter" && handleSubmit(query)}
          disabled={loading}
        />
        <button
          className="copilot-submit"
          onClick={() => handleSubmit(query)}
          disabled={loading}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>

      {loading && !answer && (
        <div className="copilot-loading">
          <div className="copilot-loading-bar" />
          <span>Searching across specs, submittals, standards, and RFI log...</span>
        </div>
      )}

      {answer && (
        <div className="copilot-response">
          <div className="copilot-answer">
            {answer}
            {streaming && <span className="copilot-cursor" />}
          </div>
          {sources.length > 0 && (
            <div className="copilot-sources">
              <span className="copilot-sources-label">Sources:</span>
              {sources.map((s) => (
                <span key={s} className="copilot-source">
                  [{s}]
                </span>
              ))}
            </div>
          )}
          {priorRfis.length > 0 && (
            <div className="copilot-rfis">
              <div className="copilot-rfis-title">Related prior RFIs:</div>
              {priorRfis.map((r) => (
                <div key={r.id} className="copilot-rfi">
                  <span className="copilot-rfi-id">{r.id}</span>
                  <span className={`copilot-rfi-status ${r.status}`}>
                    {r.status}
                  </span>
                  <div className="copilot-rfi-q">{r.question}</div>
                  {r.resolution && (
                    <div className="copilot-rfi-a">{r.resolution}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
