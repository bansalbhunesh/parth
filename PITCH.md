# Pramaan — 2:50 Pitch Script

> The words you actually say, timed to 2:50. Built for a panel that rewards
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

## [0:00–0:12] — Stakes

> "A vendor deviation found at commissioning is already late: the equipment is
> fabricated, shipped, and installed. Pramaan answers the expensive question on
> submittal day: did the vendor deliver what the owner specified?"

## [0:12–0:25] — Promise

> "Pramaan reconciles the requirement, submittal, and standards; cites the gap;
> maps it to the commissioning test; and shows the decision window to fix it."

## [0:25–0:55] — Live finding

*(On `/judge` → Live Analysis. Hit **Load deviation demo ★**.)*

> "These are two controlled natural-language documents, not a seeded result."

*(Click Analyze; let it stream. Point at the findings.)*

> "It catches 2N reduced to N+1 and ten minutes reduced to eight, with clause,
> commissioning gate, and lead time. The provenance chips say whether this was a
> model result, deterministic floor, or a verified replay of identical inputs."

## [0:55–1:25] — Consequence to closure

*(Persist the top finding, keep the named owner, issue the RFI, then re-analyze Revision C.)*

> "A flag is not a workflow. This is the exact finding we analyzed—persisted with
> its evidence, assigned to a named owner, converted to an RFI, and checked again
> against Revision C. It closes only when read-back analysis no longer finds the
> same gap. The audit count and verification hash make that closure inspectable."

## [1:25–1:50] — Measured evidence

> "On our frozen benchmark—**53
> spec–submittal pairs, 129 labels, 17 systems, 64 clean negatives** — the featured
> model over a 3-pass run reports **0.862 recall, 0.953 precision, 0.905 F1, and
> zero false alerts** on clean negatives, versus **0.111 recall** for the rule
> floor. These are benchmark results, not field-ROI claims."

## [1:50–2:15] — Architecture and reliability

> "This is one compliance graph, not an agent swarm. One step reasons with an LLM;
> ingestion, validation, commissioning mapping, cache identity, and audit are
> deterministic. Providers fail over for availability, and the low-recall rule
> floor is labelled honestly. Failover buys uptime, never accuracy."

## [2:15–2:38] — Boundaries

> "The boundaries matter: this is a benchmarked prototype, not field-validated ROI.
> Fixtures are team-authored; labels are single-author with reviewer two pending;
> omission recall is 3 of 8 and unit conversion 0 of 2. Those limits are published."

## [2:38–2:50] — Close

> "Pramaan turns a buried document mismatch into an owned, verified decision before
> commissioning makes it expensive. Evidence before confidence."

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
