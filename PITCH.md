# Pramaan — 3-Minute Pitch Script

> The words you actually say, timed to ~3:00. Built for a *business* panel:
> lead with the money, let one live real-document catch carry the wow, close on
> impact. Rehearse the demo until it's muscle memory — everything flexes around it.

---

## Pre-flight (5 minutes before you present)

- Open **`/judge`** (parth-tan.vercel.app/judge).
- Hit **`/llm-check`** — confirm `"ok": true`. If it's 429, swap in a fresh key
  first (README). The rule-based fallback covers you, but you want the live AI.
- Have one **real pair** ready from `data/samples/real/` — the **Vertiv GXT5 +
  Cummins QSK60** power pair is the richest (5 findings, incl. the arithmetic).
- Do **one warm-up Analyze** so the backend is awake — no cold-start mid-pitch.
- Speak **slower** than feels natural. Let the derived-number moment land in silence.

---

## [0:00–0:20] — The stakes (make a business judge feel it)

> "**Thirty billion dollars** is pouring into Indian data centres on the way to
> **two gigawatts by 2026** — and **nine out of ten** large builds slip schedule.
> The most expensive slips happen at **commissioning**: on a 50-megawatt build, a
> single month of delay runs **ten to forty million dollars** in lost revenue,
> financing, and penalties. One of the most common — and most avoidable — triggers
> is a vendor submittal that quietly fails the spec. It's the most expensive
> question in construction: *did the vendor actually deliver what we specified?*"

## [0:20–0:40] — Why it's hard

> "Because the design spec, the vendor's submittal, and the governing standard live
> in **three different documents**, written by three different parties, reviewed by
> people who are human. A 7-minute battery where the spec needs 10 hides in
> thousands of pages — until a commissioning test fails at Week 38."

## [0:40–0:55] — What Pramaan is

> "Pramaan is a multi-agent AI system that reads all three documents and catches
> that deviation **the day the submittal lands** — and tells you exactly which
> commissioning test it will fail, and how many weeks early you caught it. Let me
> show you, live, on **real manufacturer datasheets**."

## [0:55–1:50] — The live demo (the star)

*(On `/judge` → Live Analysis. Load the Vertiv GXT5 + Cummins QSK60 pair.)*

> "This is a real **Vertiv UPS** and a real **Cummins generator**, against a
> Tier IV design basis. Watch it reason from the raw documents."

*(Click Analyze. Let it stream token-by-token. Then point at the findings.)*

> "Five deviations — and this is **reasoning, not keyword matching.** Look here:
> the generator's day tank is 4,000 gallons, it burns 103 gallons an hour — Pramaan
> **did the division itself: 38.8 hours of fuel, against the 48 required.** It
> flagged the engine as **EPA Tier 2** where the site needs **Tier 4**. It caught
> the battery at **7 minutes against 10** — and an efficiency miss of **96 versus
> 95.9 percent**, a tenth of a percent a human skims straight past. Every finding
> cites the standard, names the commissioning test, and the lead time."

## [1:50–2:15] — It's real, and it's honest

> "And it's not our data. We built **three** of these from actual published
> spec sheets — **Vertiv, Cummins, STULZ, ABB** — against real standards: Uptime,
> NFPA, EPA, ASHRAE, IEC. On the cooling unit it even **knew R410A's global-warming
> potential is 2,088** and flagged it against the limit — the datasheet never said
> the number. And it doesn't cry wolf: on the switchgear it **cleared** an IP-54
> rating that *exceeds* the requirement. Every value we used is citable. Nothing
> seeded."

## [2:15–2:35] — Built for the bad day (production-grade)

> "This isn't a demo that works once. The eval scores two ways so we never inflate
> a number; clean systems are seeded as true negatives to prove we don't over-flag;
> 263 tests, CI green. And when the AI model is rate-limited — which *will* happen —
> a rule-based engine still catches the headline shortfalls. **No silent zeros.**
> We engineered for the bad day, not just the stage."

## [2:35–3:00] — Impact + close

> "What does that buy? Manual cross-checking is **weeks** of one engineer's time.
> Pramaan does it in **minutes**, with a full audit trail you can hand to the
> commissioning authority. On an 800-crore project, catching these early avoids
> **crores** of rework — and protects a schedule where every week of delay is real
> revenue lost. Pramaan turns *'did they build what we specified?'* into a
> five-minute, evidence-backed answer — on the day it still costs nothing to fix.
> Thank you."

---

## Q&A defence — the hard questions

**"Is your data synthetic?"**
> "Our 12-project *benchmark* is — deliberately, so we can measure breadth across
> geographies. But you just watched it work on **real Vertiv and Cummins
> datasheets**, and we ship three such pairs with every number sourced. Benchmark
> for breadth; real datasheets for reality."

**"Isn't this just a Gemini wrapper?"**
> "A wrapper doesn't divide 4,000 by 103 and reason about fuel autonomy, or recall
> a refrigerant's GWP, or *not* flag a value that exceeds spec. The model is one
> component — the system is the cross-document reconciliation, the commissioning
> prediction, the citation check, and an open eval that proves it."

**"Hasn't this been done — BuildSync, Spec-ID?"**
> "Submittal review exists. What no one else does is **predict the commissioning
> test each deviation will fail and the lead-time-to-failure** — turning 'this
> deviates' into 'this fails IST-07 at Week 44, you have 27 weeks.' That, plus an
> open reproducible eval, is the moat."

**"What does it cost, and what if the LLM is down?"**
> "A few paise per analysis on a flash model after an 85% prompt-token cut. If the
> model's down, every endpoint still returns 200, the rule-based engine still
> finds the headline deviations, and `/llm-check` reports the true status."

---

## The 10-second version (hallway / elevator)
> "Pramaan reads the spec, the submittal, and the standard, and catches the vendor
> deviation the day the document lands — not six months later in commissioning.
> Real datasheets, real reasoning, and it tells you which test it'll fail."

## Three things to never skip
1. **Lead with the money** — Indian data-centre capex and the seven-figure slip.
2. **The arithmetic moment** — "it divided 4,000 by 103 itself." That's the proof it reasons.
3. **One honesty beat** — true negatives, or "no silent zeros when the AI is down." Trust beats a perfect score.
