"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

// Presenter mode for the live finale: big-type guided sequence over the same
// claims the rest of the product makes (benchmark exacts + floor-style counts).
// No new claims; every number here also lives on /evidence with its limitation.
const SLIDES = [
  {
    k: "title",
    kicker: "ET AI Hackathon 2.0 · Problem Statement 4",
    head: "Pramaan/",
    sub: "The proof engine for construction documents.",
    note: "Live: parth-tan.vercel.app · open /judge in the next tab now",
  },
  {
    k: "stakes",
    kicker: "The problem",
    head: "Construction runs on promised documents. Some promises are quietly broken.",
    sub: "2N becomes N+1. Ten minutes becomes eight. Nobody reads page 47 — until commissioning fails.",
    note: "Say: 'every week of delay costs crores'",
  },
  {
    k: "live",
    kicker: "Live demo — no staging",
    head: "Load ★ → instant rule verdict → live model upgrade.",
    sub: "Deterministic preview in one second; the real model streams in with a provenance chip.",
    cta: { href: "/judge", label: "Run it live → /judge" },
    note: "Watch the pipeline stages advance. Never call a replay fresh.",
  },
  {
    k: "converge",
    kicker: "What nobody else shows",
    head: "Two findings. One commissioning gate. Week 36.",
    sub: "Fix either alone and the gate still fails — Pramaan ranks the converged cluster.",
    cta: { href: "/war-room", label: "Consequence view → /war-room" },
    note: "Copilot beat: Ask the record — 'Which deviation threatens Week 36?'",
  },
  {
    k: "money",
    kicker: "Priced, honestly",
    head: "27 weeks of exposure ≈ ₹54 crore.",
    sub: "Modelled, not measured — the assumptions and the negative case are published.",
    note: "BUSINESS.md §0: $126B+ India DC commitments · 5–25% rework base rates (cited)",
  },
  {
    k: "closure",
    kicker: "A flag is not a workflow",
    head: "Persist → Owner → RFI → Re-check → Closed with read-back evidence.",
    sub: "The case closes only when re-analysis finds no gap — audit trail + verification hash.",
    note: "Run it against the API live if asked — it is not a staged animation.",
  },
  {
    k: "evidence",
    kicker: "Frozen benchmark · public protocol",
    head: "0.862 recall · 0.953 precision · 0/64 false alerts.",
    sub: "Versus a 0.111 rule-floor baseline. Behind it: 900+ tests, 160+ browser journeys, public CI.",
    cta: { href: "/evidence", label: "Every number + its limitation → /evidence" },
    note: "One command reproduces it: make verify",
  },
  {
    k: "close",
    kicker: "Limits, on purpose",
    head: "Team-authored fixtures. Reviewer-2 pending. All published.",
    sub: "Evidence before confidence. This is Pramaan — proof.",
    note: "Q&A ready: PITCH.md defence answers",
  },
] as const;

export default function PitchPage() {
  const [i, setI] = useState(0);
  const step = useCallback((d: number) => {
    setI((cur) => Math.min(SLIDES.length - 1, Math.max(0, cur + d)));
  }, []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") step(1);
      if (e.key === "ArrowLeft" || e.key === "PageUp") step(-1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [step]);
  const s = SLIDES[i];
  return (
    <main className="pitch-stage" aria-label="Presenter mode">
      <div className="pitch-kicker">{s.kicker}</div>
      <h1 className="pitch-head">{s.head}</h1>
      <p className="pitch-sub">{s.sub}</p>
      {"cta" in s && s.cta ? (
        <Link className="button button-primary pitch-cta" href={s.cta.href} target="_blank">
          {s.cta.label}
        </Link>
      ) : null}
      <div className="pitch-note">{s.note}</div>
      <div className="pitch-nav" aria-label="Slide navigation">
        <button className="pitch-nav-btn" onClick={() => step(-1)} disabled={i === 0} aria-label="Previous slide">←</button>
        <span className="pitch-count">{i + 1} / {SLIDES.length}</span>
        <button className="pitch-nav-btn" onClick={() => step(1)} disabled={i === SLIDES.length - 1} aria-label="Next slide">→</button>
      </div>
    </main>
  );
}
