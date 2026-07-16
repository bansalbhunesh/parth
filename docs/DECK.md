# Pramaan — Pitch Deck Outline

> 12 slides. The rendered deck is [`../presentation.html`](../presentation.html)
> (export with `python scripts/export_deck.py` → [`Pramaan_Deck.pdf`](Pramaan_Deck.pdf)).
> Speaker notes map to [`../PITCH.md`](../PITCH.md). Keep ≤ 6 words per bullet on
> screen — you say the rest. **Every metric on a slide carries an evidence label:**
> benchmarked · live-model · deterministic baseline · team-authored · primary-source-derived · pending · scenario · limitation.

---

### Slide 1 — Title
- **PRAMAAN** · EPC Deviation Intelligence for Data-Centre Delivery
- A **benchmarked prototype**: deterministic numbers reproduce offline; live-model results reported honestly.
- Headline chips: recall **0.862** *(benchmarked v1.2)* · **53** pairs *(team-authored)* · **1** LLM reasoning core *(+ deterministic services)*.
- **Speaker note:** name + one-line value prop, then move to stakes.

### Slide 2 — The problem
- A late submittal deviation becomes a **commissioning + schedule failure**.
- Caught at commissioning (Weeks 16–44, *scenario*) vs caught at submittal review (Week 11).
- **Speaker note:** make a business judge feel the date: "this does not become a problem someday; it fails IST-07 in Week 38."

### Slide 3 — Why current review fails
- Owner requirement · vendor submittal · commissioning/schedule = **3 documents, 3 parties**.
- Deviations hide in the gaps until an integrated systems test fails.
- **Speaker note:** the 7-min-vs-10-min battery example, said out loud.

### Slide 4 — The solution
- **Requirement → deviation → commissioning test → action window.**
- Reconciles spec + submittal + standards; traces each deviation to the Cx test it fails and the lead time to fix it.
- **Speaker note:** one sentence, then "let me show you live."

### Slide 5 — Live product / Judge Mode ★
- `/judge`: **Load deviation demo ★** (hidden 2N→N+1, 10→8 min) and **Load compliant demo ✓** (zero deviations — no false alarm).
- Token-by-token reasoning; a truthful provenance chip on every result (live LLM · vision · rule floor · OCR).
- **Speaker note:** demo live if you can; let the failure timeline land before the metrics.

### Slide 6 — Architecture truth
- **One compliance reasoning graph + connected deterministic services + reliability layer.**
- Exactly one node reasons with an LLM (`reconcile`); ingest/retrieve/critique deterministic; two bounded cycles. RFI copilot is a **service, not a graph node**.
- **Visual:** [`pipeline-diagram.svg`](pipeline-diagram.svg) / the interactive diagram — they now tell the same story.
- **Speaker note:** "not five LLM agents — one reasoning core, the rest deterministic and inspectable."

### Slide 7 — Benchmark proof
- **ps4_external_v1 (v1.2)** — 53 pairs · 129 frozen labels · 17 systems · 64 clean negatives · 3-pass (`gemini-3.1-flash-lite`).
- **recall 0.862 · precision 0.953 · F1 0.905 · FAR 0.000 · p50 ~2.5 s** *(benchmarked)*; **rule baseline 0.111** *(deterministic)*; **892** tests.
- **Speaker note:** the LLM core clears the deterministic floor on the same frozen labels — a benchmark result, not field validation.

### Slide 8 — Trust & limitations
- Stand behind: 0 false alerts on 64 clean negatives · citations · reproducible.
- Do not claim: team-authored fixtures (10 primary-source-derived, 5 URLs; source files not stored yet) · **reviewer-2 pending** · automated cross-check is **machine QA, not human** · not field/customer-validated.
- **Speaker note:** the honesty beat — trust beats a perfect score.

### Slide 9 — Reliability (built for the bad day)
- **Provider failover for availability** (→ deterministic floor), **not accuracy** — live at `/llm-check`.
- No silent zeros; OCR ground truth at `/ocr-check`; demo hardening (auth/rate-limit/upload validation), *not production*.
- **Speaker note:** "engineered for the bad day, not just the stage."

### Slide 10 — Business impact
- The value is **time, caught early** — lead-time weeks, not a fabricated ROI.
- Any cost figure is an explicitly-labelled illustrative **scenario**; manual-hours reduction not yet measured.
- **Speaker note:** the asymmetry is the business case; do not overclaim.

### Slide 11 — Roadmap
- Evidence depth (archived source artifacts) · independent review (reviewer-2 adjudication) · production hardening (shared-store auth/rate-limit, pgvector, async).
- **Speaker note:** ordered by what most increases trust first.

### Slide 12 — Close
- **Evidence before confidence.** Benchmark v1.2 headline; one reasoning graph + deterministic services + reliability layer; reviewer-2 pending, and we say so.
- **All-track answer:** others may win the room with drama; Pramaan wins the technical bar by making every claim inspectable.
- Links: `/judge` · `/evidence` · GitHub · live demo.

---

## Appendix (live Q&A)
- **A1 — Benchmark card:** `benchmarks/ps4_external_v1/reports/benchmark_card.json` + `/evidence`.
- **A2 — Architecture:** `docs/ARCHITECTURE.md`, `docs/TECHNICAL_OVERVIEW.md` — verify against `backend/orchestrator.py`.
- **A3 — Reviewer status:** `benchmarks/ps4_external_v1/labels/REVIEW_STATUS.md` (single-author frozen; reviewer-2 pending).
- **A4 — Reliability/ops:** `/health`, `/llm-check`, `/ocr-check`; `docs/LLM_FAILOVER_RUNBOOK.md`, `docs/SECURITY_DEMO_RUNBOOK.md`.
- **A5 — Claims governance:** `docs/CLAIMS_REGISTER.md` (allowed vs banned wording, with limitations).
