"use client";
import { useEffect, useState } from "react";

/** Live system-status strip for Judge Mode.
 *
 * One cheap `/health` fetch (no LLM call, not rate-limited) so a judge can
 * see — before they click Analyze — that the deployed backend is up, which
 * LLM legs are configured, and that the deterministic floor is armed. Doubles
 * as the cold-start handler: free-tier hosting can take ~50 s to wake, and
 * this strip says so instead of leaving a silent, dead-looking panel.
 */

type Health = {
  ok?: boolean;
  commit?: string;
  analysis_mode?: string;
  ocr_available?: boolean;
  llm?: { provider?: string; chain?: string[]; ready?: boolean };
  security?: { deterministic_fallback_available?: boolean };
};

type StripState = "checking" | "waking" | "live" | "down";

const DOT: Record<StripState, string> = {
  checking: "#8896ab",
  waking: "#ffb020",
  live: "#35c98b",
  down: "#ff4d4d",
};

export default function SystemStatusStrip({ apiBase }: { apiBase: string }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [state, setState] = useState<StripState>("checking");

  useEffect(() => {
    let cancelled = false;
    let attempts = 0;

    const wakeTimer = setTimeout(() => {
      setState((s) => (s === "checking" ? "waking" : s));
    }, 2500);

    async function ping() {
      attempts += 1;
      try {
        const r = await fetch(`${apiBase}/health`, { cache: "no-store" });
        const h = (await r.json()) as Health;
        if (!cancelled) {
          setHealth(h);
          setState("live");
        }
        return true;
      } catch {
        if (!cancelled) setState((s) => (s === "checking" ? s : "down"));
        return false;
      }
    }

    // Poll until live: quick first check, then every 15 s (max ~4 min) to
    // ride out a free-tier cold start without hammering anything.
    let interval: ReturnType<typeof setInterval> | null = null;
    ping().then((ok) => {
      if (ok || cancelled) return;
      interval = setInterval(async () => {
        if (attempts >= 16 || (await ping())) {
          if (interval) clearInterval(interval);
        }
      }, 15000);
    });

    return () => {
      cancelled = true;
      clearTimeout(wakeTimer);
      if (interval) clearInterval(interval);
    };
  }, [apiBase]);

  const chain = health?.llm?.chain?.length
    ? health.llm.chain.join(" → ")
    : null;
  const floor = health?.security?.deterministic_fallback_available;

  const text =
    state === "live" ? (
      <>
        Live API up{health?.commit ? <> · commit <code>{health.commit}</code></> : null}
        {chain ? <> · LLM chain {chain}</> : null}
        {floor ? <> · deterministic floor armed</> : null}
        {health?.ocr_available ? <> · OCR on</> : null}
      </>
    ) : state === "waking" ? (
      <>Waking the live API — free-tier hosting can take ~50 s on the first hit. This strip flips green when it answers.</>
    ) : state === "down" ? (
      <>Live API not answering yet — retrying every 15 s. The demo buttons below fall back to bundled fixtures, and analysis degrades to the deterministic rule floor rather than failing.</>
    ) : (
      <>Checking the live API&hellip;</>
    );

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        background: "#0d131b",
        border: "1px solid #1f2937",
        borderRadius: 8,
        padding: "10px 14px",
        margin: "0 0 14px",
        fontSize: 12,
        color: "#9ca3af",
        fontFamily: "var(--font-mono)",
        lineHeight: 1.5,
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: 9,
          height: 9,
          borderRadius: "50%",
          flexShrink: 0,
          background: DOT[state],
          boxShadow: state === "live" ? "0 0 6px rgba(53,201,139,.7)" : undefined,
        }}
      />
      <span>{text}</span>
    </div>
  );
}
