"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { streamCopilot, type CopilotResponse } from "../lib/api";

const SUGGESTIONS = [
  "Which deviation threatens the earliest commissioning test?",
  "Has a UPS battery runtime deviation been raised before?",
  "What does the spec require for switchgear fault rating?",
];

type PriorRfi = CopilotResponse["prior_rfis"][number];

/**
 * "Ask the record" — a contextual drawer over the project record. It streams
 * retrieval-backed answers from /copilot/stream with cited sources and
 * prior-RFI matches, and states plainly when the service is unreachable.
 */
export default function CopilotDrawer() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [priorRfis, setPriorRfis] = useState<PriorRfi[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [asked, setAsked] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const ask = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (trimmed.length < 3 || busy) return;
    setBusy(true);
    setAsked(true);
    setError("");
    setAnswer("");
    setSources([]);
    setPriorRfis([]);
    await streamCopilot(
      trimmed,
      (meta) => {
        setSources(meta.sources ?? []);
        setPriorRfis(meta.prior_rfis ?? []);
      },
      (token) => setAnswer((prev) => prev + token),
      () => setBusy(false),
      (message) => {
        setError(message);
        setBusy(false);
      },
    );
  }, [busy]);

  return (
    <>
      <button
        className="copilot-trigger"
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label="Ask the record"
      >
        <span className="copilot-trigger-long">Ask the record</span>
        <span className="copilot-trigger-short">Ask</span>
      </button>

      {open ? createPortal(
        <div className="drawer-root" role="presentation">
          <button
            className="drawer-backdrop"
            type="button"
            aria-label="Close the ask-the-record panel"
            onClick={() => setOpen(false)}
          />
          <div
            ref={panelRef}
            className="drawer-panel copilot-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="copilot-title"
          >
            <div className="drawer-head">
              <div>
                <p className="drawer-kicker">Project record · retrieval with citations</p>
                <h2 id="copilot-title">Ask the record</h2>
              </div>
              <button
                className="drawer-close"
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close panel"
              >
                <span aria-hidden="true">✕</span>
              </button>
            </div>

            <p className="copilot-scope">
              Searches the loaded specs, submittals, standards and the RFI log.
              Answers cite their sources; an unreachable service says so.
            </p>

            <form
              className="copilot-form"
              onSubmit={(event) => {
                event.preventDefault();
                void ask(query);
              }}
            >
              <label className="copilot-label" htmlFor="copilot-query">
                <span>Question</span>
                <textarea
                  id="copilot-query"
                  ref={inputRef}
                  rows={2}
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Ask about any requirement, deviation or prior RFI…"
                  disabled={busy}
                />
              </label>
              <button className="button button-primary copilot-submit" type="submit" disabled={busy || query.trim().length < 3}>
                {busy ? "Searching…" : "Ask"}
              </button>
            </form>

            {!asked ? (
              <div className="copilot-suggestions">
                <span className="copilot-suggestions-label">Try one</span>
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    className="copilot-suggestion"
                    onClick={() => {
                      setQuery(suggestion);
                      void ask(suggestion);
                    }}
                    disabled={busy}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            ) : null}

            <div className="copilot-result" aria-live="polite">
              {error ? <p className="copilot-error" role="alert">{error}</p> : null}
              {answer ? (
                <div className="copilot-answer">
                  {answer}
                  {busy ? <span className="copilot-cursor" aria-hidden="true" /> : null}
                </div>
              ) : busy ? (
                <p className="copilot-waiting">Searching the record…</p>
              ) : null}

              {sources.length > 0 ? (
                <div className="copilot-sources">
                  <span className="copilot-sources-label">Sources</span>
                  <ul>
                    {sources.map((source) => (
                      <li key={source}>{source}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {priorRfis.length > 0 ? (
                <div className="copilot-rfis">
                  <span className="copilot-sources-label">Prior RFIs on this subject</span>
                  <ul>
                    {priorRfis.map((rfi) => (
                      <li key={rfi.id}>
                        <span className="copilot-rfi-id">{rfi.id}</span>
                        <span className="copilot-rfi-q">{rfi.question}</span>
                        <span className="copilot-rfi-status">{rfi.status}{rfi.resolution ? ` — ${rfi.resolution}` : ""}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </div>
        </div>,
        document.body,
      ) : null}
    </>
  );
}
