"use client";

import { useState } from "react";
import { askCopilot, CopilotResponse } from "../lib/api";

const PRESETS = [
  "Has the UPS battery runtime issue come up before?",
  "What is the required cooling redundancy for Tier IV?",
  "Which deviations will fail during IST testing?",
  "What are the seismic requirements for the structural system?",
  "Summarize all critical findings and their lead times",
];

export default function CopilotPanel() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(q: string) {
    const actualQuery = q || query;
    if (!actualQuery.trim()) return;
    setLoading(true);
    setQuery(actualQuery);
    setResponse(null);
    try {
      const res = await askCopilot(actualQuery);
      setResponse(res);
    } catch {
      setResponse({
        answer: "Error connecting to backend. Ensure the API is running at localhost:8000.",
        sources: [],
        prior_rfis: [],
      });
    }
    setLoading(false);
  }

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
          {loading ? "Searching..." : "Ask"}
        </button>
      </div>

      {loading && (
        <div className="copilot-loading">
          <div className="copilot-loading-bar" />
          <span>Searching across specs, submittals, standards, and RFI log...</span>
        </div>
      )}

      {response && !loading && (
        <div className="copilot-response">
          <div className="copilot-answer">{response.answer}</div>
          {response.sources.length > 0 && (
            <div className="copilot-sources">
              <span className="copilot-sources-label">Sources:</span>
              {response.sources.map((s) => (
                <span key={s} className="copilot-source">
                  [{s}]
                </span>
              ))}
            </div>
          )}
          {response.prior_rfis.length > 0 && (
            <div className="copilot-rfis">
              <div className="copilot-rfis-title">Related prior RFIs:</div>
              {response.prior_rfis.map((r) => (
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
