# Pramaan — 3-Minute Pitch Script

> The words you actually say. Built around the live real-document demo and the
> "regex finds 0, reasoning finds 8" kill shot. Rehearse the demo until it's
> muscle memory; everything else flexes around it.

---

## Pre-flight (do this 5 minutes before)
- Open **`/judge`** in the browser (parth-tan.vercel.app/judge).
- Hit **`/health`** — confirm `"ready": true`. (If not, fix the key first — see README.)
- Have the two PDFs ready: a design basis + the **real Vertiv datasheet**.
- Do one warm-up Analyze so the backend is awake (no cold-start mid-pitch).
- Speak **slower** than feels natural. Let the 8-deviation result land in silence.

---

## [0:00–0:20] — The problem (make them feel it)

> "On a hyperscale data-centre build, the design spec, the vendor's submittal, and
> the governing standard live in three different documents, written by three
> different parties. A vendor quotes a UPS at 7-minute battery backup; the spec
> needs 10. Nobody catches it — until commissioning, Week 38, when the test fails.
> Now it's a six-month delay and a seven-figure overrun. This happens on *every*
> large build."

## [0:20–0:45] — What it is + the numbers

> "Pramaan is a multi-agent AI system that reads all three documents and catches
> that deviation **the day the submittal lands**. We've proven it across 12
> real-world projects, 11 countries, 6 tier standards — **50 deviations, 1,024
> weeks of lead time saved, F1 of 1.000 with a real LLM, zero false positives.**
> But numbers on a slide are cheap. Let me show you it work on a document it has
> never seen."

## [0:45–1:45] — The live demo (the star)

*(On `/judge` → Live Analysis. Show the two PDFs.)*

> "This is a **real Vertiv UPS datasheet** — downloaded from their website. This is
> a data-centre design basis. Neither was in our training or test data."

*(Click Analyze. Let it stream.)*

> "Watch it read the raw PDFs and reason from scratch."

*(Results appear — point at them.)*

> "**Eight deviations.** And look — it didn't just match strings. The spec needs
> 6 kW; the datasheet says 3 kVA — so it did the math: 3 kVA × 0.8 power factor =
> 2.4 kW, and flagged it. It caught **88% efficiency** — but only because it read
> the *online-mode* number, not the higher ECO-mode headline the vendor leads with.
> And here — input THD: the value is simply **missing**, and it flagged the
> omission. Every finding cites the standard, predicts the commissioning test it'll
> fail, and the lead time. Oh — and the vendor stamped this datasheet **'fully
> compliant.'**"

## [1:45–2:10] — The kill shot

*(Show the "before" screenshot, or describe it.)*

> "Now — is this just keyword matching? **Same two PDFs, AI turned off** — our
> deterministic fallback finds **zero**. It can't parse real prose. Turn reasoning
> back on: **eight**. That gap — zero to eight on *identical* documents — **that is
> the product.** Pattern-matching can't do this. Reasoning can."

## [2:10–2:35] — Rigor (pre-empt the skeptic)

> "And we kept ourselves honest. Our eval scores **two ways** — exact-match and
> semantic — so we never inflate a number. We seed clean systems as **true
> negatives** to prove we don't over-flag. When our model once got *too* strict —
> applying a Japanese seismic standard the design basis didn't require — we caught
> it, scoped it, and documented it. **258 tests, three eval paths, graceful
> degradation everywhere.** This is a system, not a demo."

## [2:35–3:00] — Business + close

> "On an 800-crore project, catching these early avoids roughly **₹1,788 lakhs** of
> rework. One reviewer, weeks of work — replaced by minutes, with a full audit
> trail. And it **generalises**: 12 projects across 11 countries, every one at F1
> 1.000, on standards we never tuned for. Pramaan turns the most expensive question
> in construction — *'did the vendor actually build what we specified?'* — into a
> five-minute answer. Thank you."

---

## Q&A defence — the four hard questions

**"Is your data synthetic?"**
> "Our *benchmark* is — deliberately. 12 rigorously-built project archetypes so we
> can measure honestly across geographies. But you just watched it work on a **real
> Vertiv datasheet we'd never seen**. The benchmark proves breadth; the live demo
> proves reality."

**"Isn't this just a Gemini wrapper?"**
> "The model is one component. The system is the orchestration, the cross-document
> reconciliation, the commissioning-test prediction, the citation-faithfulness
> check, and an eval harness that proves it. And we showed you the difference
> reasoning makes — **zero versus eight** on the same documents. A wrapper doesn't
> earn that."

**"What does it cost to run at scale?"**
> "A few paise per analysis on a flash model, after an 85% prompt-token reduction.
> At enterprise scale: batch ingest, response caching, and a vector store over the
> project corpus."

**"What happens when the LLM is down, or there's no key?"**
> "It degrades gracefully — every endpoint still returns 200, the dashboard renders
> from cached data, and a `/llm-check` endpoint reports the exact status. We
> designed for the bad day, not just the demo."

---

## The 10-second version (elevator / hallway)
> "Pramaan reads the spec, the submittal, and the standard — and catches the
> deviation the day the document lands, not six months later in commissioning.
> Real documents, real reasoning, full audit trail."

## Three things to never skip
1. The **live real-document** analysis (not the seeded example).
2. The **zero-vs-eight** kill shot.
3. One **honesty** beat (semantic scoring, or the Sakura over-reach we fixed) — it builds more trust than a perfect score does.
