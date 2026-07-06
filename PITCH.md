# Pramaan — 3–4 Minute Pitch Script

> The words you actually say, timed to ~3:30. Built for a panel that rewards
> *trust*: lead with the stakes, let one live catch carry the wow, and close on
> honest limitations. Rehearse the demo until it's muscle memory.
> Recording the video? The shoot is run by [`docs/VIDEO_RUNBOOK.md`](docs/VIDEO_RUNBOOK.md).

---

## Pre-flight (5 minutes before you present)

- Run **`make verify-live`** (or `python scripts/verify_live.py`) — the only green
  light that counts. It checks the deployed commit and runs a real pair through
  `/analyze` end-to-end. **Do not trust a bare `/llm-check`** — the tiny probe can
  pass while demo-sized calls 429 (that false-green killed the live AI path once);
  use `/llm-check?deep=1`.
- Open **`/judge`** (parth-tan.vercel.app/judge) and **`/evidence`** in a second tab.
- Do **one warm-up Analyze** so the path a judge sees is the path you just verified — no cold-start mid-pitch.
- If the model is down, that's fine — the deterministic floor and the honest
  provenance chip are part of the story. Do not fake a live result.
- Speak **slower** than feels natural. Let the derived-number moment land in silence.

---

## [0:00–0:20] — Problem / stakes

> "Billions are pouring into data-centre construction, and most large builds slip
> schedule. The most expensive slips happen at **commissioning** — when a vendor
> submittal that quietly failed the spec finally gets caught, after the gear is
> fabricated, shipped, and installed. It's the most expensive question in the
> project: *did the vendor actually deliver what we specified?*"

## [0:20–0:50] — What Pramaan does

> "Pramaan answers that question **the day the submittal lands.** It reconciles the
> owner's requirement, the vendor's submittal, and the governing standards, flags
> every deviation, and — this is the part no one else does — tells you exactly
> which **commissioning test** that deviation will fail and how many **weeks of lead
> time** you have to fix it first. Let me show you, live."

## [0:50–1:30] — Live demo flow

*(On `/judge` → Live Analysis. Hit **Load deviation demo ★**.)*

> "This is a realistic design basis against a vendor submittal, in natural prose —
> nothing pre-seeded. Watch it reason from the raw documents."

*(Click Analyze; let it stream. Point at the findings.)*

> "It surfaces the non-compliances a human skims past — a redundancy dropped from
> 2N to N+1, battery autonomy quoted at end-of-life below spec — each cited to the
> clause, mapped to the commissioning test it fails, with the lead time. And notice
> the **provenance chip**: it tells you honestly whether this came from the live
> model or the deterministic floor."

*(Hit **Load compliant demo ✓**.)*

> "Now a fully compliant submittal. The correct answer is **zero deviations** — and
> it doesn't cry wolf. That's the behaviour our 64 clean-negative controls measure."

## [1:30–2:00] — Evidence chain

> "So the chain is: **requirement → deviation → commissioning test → schedule
> risk.** A 7-minute battery against a 10-minute spec isn't just a compliance flag —
> Pramaan traces it to the integrated systems test it fails at Week 38, and the
> milestone that slips. Caught at submittal review in Week 11, that's a 27-week
> window to fix it — a one-line RFI instead of a seven-figure slip."

## [2:00–2:35] — Benchmark result

> "And this is measured, not asserted. On our frozen benchmark — **53
> spec–submittal pairs, 129 labels, 17 systems, 64 clean negatives** — the featured
> model over a 3-pass run reports **0.862 recall, 0.953 precision, 0.905 F1, and
> zero false alerts** on the clean negatives, versus a deterministic rule baseline
> of **0.111** on the same labels. The reasoning core clearly beats the floor — and
> you can reproduce the deterministic parts on your own laptop, no key required."

## [2:35–3:05] — Architecture and reliability

> "Under the hood it's **one compliance reasoning graph, not five AI agents.**
> Exactly one step reasons with an LLM; ingestion, retrieval, self-critique, and
> commissioning mapping are deterministic and inspectable, plus deterministic
> schedule and supply-chain services. And it's built for the bad day: when a
> provider is rate-limited it **fails over for availability** — gemini, Groq,
> gateway, Claude, local — and if none answer, a rule engine still returns the headline
> deviations. Failover buys uptime, never accuracy. Every leg is scored the same."

## [3:05–3:30] — Limitations, roadmap, close

> "I'll be straight about what this is. **Pramaan is not claiming field-validated
> ROI yet. It is a benchmarked prototype that proves a reliable first-pass deviation
> detection workflow across EPC document pairs.** The fixtures are team-authored,
> the labels are single-author frozen with a second human reviewer still pending,
> and the automated cross-check is machine QA, not a human review — and the app says
> so, everywhere. Next is stored primary sources, two-person adjudication, and
> production hardening. Everything I just claimed is on the **/evidence** page with
> its limitation. Evidence before confidence. Thank you."

---

## Q&A defence — the hard questions

**"Is your data real?"**
> "The benchmark fixtures are **team-authored** — 10 derived from public primary
> sources, 5 with a verified URL — and stored primary-source PDFs are a pending
> roadmap item. We deliberately don't call them real datasheets. The benchmark
> measures a reliable first-pass workflow; it is not a real-world-accuracy claim."

**"Isn't this just a Gemini wrapper?"**
> "One node reasons with an LLM; the system around it is the cross-document
> reconciliation graph with retrieval and self-critique cycles, the deterministic
> commissioning and schedule services, the citation check, and a frozen,
> reproducible benchmark. A wrapper doesn't clear a 0.111 rule floor to 0.862 on
> frozen labels."

**"Is your benchmark independently reviewed?" — Not yet.**
> "Not yet — and we're explicit about it. Labels are single-author frozen. There's
> an automated consistency audit (123 of 129 consistent, 6 flagged), but that is
> machine QA, **not** a second human reviewer. Two-person adjudication is the next
> validation milestone."

**"What does it miss?" — know the two weak classes cold.**
> "Two classes, and they're published in the error analysis. **Omission
> detection: 3 of 8** (recall 0.375) — deviations where the submittal silently
> *leaves out* something the spec requires; noticing absence is harder than
> comparing two stated values, and it's the top item on the improvement
> roadmap. **Unit conversion: 0 of 2** — the two labels that require a
> multi-step unit conversion before comparing. Every other class — direct
> values, categorical reasoning, derived arithmetic, domain recall,
> adversarial noise, scanned/image — runs at or near 1.0 on the featured
> passes. We haven't retuned the engine against the frozen set to fix these —
> that would turn the FAR 0.000 story into overfitting; they're future work on
> a new benchmark version."

**"Your benchmark features `gemini-3.1-flash-lite` but the live demo runs `gemini-2.5-flash` — why?"**
> "The featured benchmark configuration is the one that completed a clean,
> repeatable 3-pass run — that's what we headline. The hosted demo pins
> `gemini-2.5-flash`, which is on the same benchmark card as the ablation — it
> peaked *higher* (0.9524 recall) but didn't complete a clean 3-pass, so we
> don't headline it. The demo may answer from any configured provider in the
> failover chain, and `/llm-check` reports exactly which model answered. We
> never re-attribute one model's benchmark numbers to another."

**"What if the LLM is down during judging?"**
> "Every endpoint still returns 200, the deterministic rule engine still finds the
> headline deviations, and the UI labels that result as the low-recall floor — not a
> clean bill of health. `/llm-check` reports the true provider status."

---

## The 10-second version (hallway / elevator)
> "Pramaan reads the spec, the submittal, and the standard, and catches the vendor
> deviation the day the document lands — then names the commissioning test it'll
> fail and how many weeks early you caught it. Benchmarked, honest about its limits,
> and reproducible."

## Three things to never skip
1. **Lead with the stakes** — the seven-figure commissioning slip.
2. **The live catch + provenance chip** — it reasons, and it tells you how it answered.
3. **One honesty beat** — reviewer-2 pending, or "no silent zeros when the AI is down." Trust beats a perfect score.
