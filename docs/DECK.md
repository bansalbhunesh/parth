# Pramaan — Pitch Deck Outline

> 11 slides for a 3-minute pitch + appendix. Business-led; the live demo (Slide 5)
> is the centre of gravity. Speaker notes map to [`PITCH.md`](../PITCH.md).
> Keep ≤ 6 words per bullet on screen — you say the rest.

---

### Slide 1 — Title
- **PRAMAAN** · EPC Deviation Intelligence for Data Centres
- *"Did the vendor build what we specified?" — answered the day the document lands.*
- Live: **parth-tan.vercel.app/judge** · ET AI Hackathon 2026
- **Speaker note:** name + one-line value prop. Don't over-explain; move to stakes.

### Slide 2 — The stakes (lead with money)
- India: **gigawatts** of new data-centre capacity, **billions in capex**
- One missed deviation → **multi-month delay + seven-figure overrun**
- Happens on *every* large build
- **Visual:** a rising data-centre capex curve; a red "₹" delay marker at Week 38.
- **Speaker note:** make a business judge feel the money in 15 seconds.

### Slide 3 — Why it's hard
- Spec · Submittal · Standard = **3 documents, 3 parties**
- Deviations hide in thousands of pages
- Surface at **commissioning — too late**
- **Visual:** three disconnected document icons; a deviation slipping through the gap.
- **Speaker note:** the 7-min-vs-10-min battery example, said out loud.

### Slide 4 — The solution
- Reads **all three documents** together
- Flags the deviation **on upload day**
- Predicts the **commissioning test it fails** + **weeks of lead time**
- **Visual:** the 5-agent pipeline (use `docs/pipeline-diagram.svg`).
- **Speaker note:** one sentence, then "let me show you live."

### Slide 5 — LIVE DEMO (the star) ★
- *Real Vertiv UPS + Cummins genset → 5 deviations*
- **It did the math: 4,000 gal ÷ 103 GPH = 38.8 h vs 48 required**
- EPA Tier 2 vs Tier 4 · battery 7 vs 10 min · efficiency 96 vs 95.9%
- **Visual:** the live `/judge` stream (record it; do NOT use a static slide if you can demo live).
- **Speaker note:** stop talking for 1 second after the 38.8h finding lands.

### Slide 6 — It's real, and it's honest
- **3 sourced real pairs:** Vertiv · Cummins · STULZ · ABB
- vs real standards: Uptime · NFPA · EPA · ASHRAE · IEC
- **11 deviations + 5 true negatives — none seeded**
- Knew R410A's GWP (2,088); *cleared* IP54 that exceeds spec
- **Visual:** the PROVENANCE.md source table.
- **Speaker note:** "every value is citable" — this is the anti-vaporware slide.

### Slide 7 — How it works
- **5 agents, LangGraph:** Ingest → Extract → Reconcile → Cx-Predict → RFI Copilot
- Gemini reasoning · citation-faithfulness check · rule-table Cx mapping
- **Visual:** the architecture one-pager diagram ([`ARCHITECTURE.md`](ARCHITECTURE.md)).
- **Speaker note:** 15 seconds — depth on demand, not a lecture.

### Slide 8 — The moat
- Submittal review exists (BuildSync, Spec-ID, InspectMind)
- **No one predicts the commissioning failure + lead-time-to-failure**
- + an **open, reproducible eval** — not a closed SaaS
- **Visual:** the comparison table from `COMPETITIVE.md`.
- **Speaker note:** honest positioning earns trust; name the competitors first.

### Slide 9 — Business impact
- Manual review: **weeks** of one engineer → Pramaan: **minutes**
- **Crores** of rework avoided per project; every delayed week = revenue lost
- Full audit trail → hand straight to the Cx authority
- **Visual:** the ROI calculator screenshot; before/after timeline.
- **Speaker note:** tie back to Slide 2's money.

### Slide 10 — Production-grade
- **No silent zeros** — rule-based fallback when the AI is rate-limited
- **263 tests · CI green · deployed** (Vercel + Render)
- Two-way scoring · true negatives · `/llm-check` live status
- **Visual:** green CI badge + the resilience flow.
- **Speaker note:** "engineered for the bad day, not just the stage."

### Slide 11 — Vision + ask
- Every data-centre build, every submittal, day one
- Scale: batch ingest · vector store · delta-only re-checks
- *The most expensive question in construction → a 5-minute answer*
- **Visual:** map of Indian data-centre hubs; the live URL.
- **Speaker note:** close on the vision; thank the panel.

---

## Appendix (for live Q&A, not the 3-min run)
- **A1 — Metrics:** benchmark P/R/F1, lead-time saved, true-negative rate; the 3 real-pair results (5/5, 3/3, 3/3, all LLM-verified).
- **A2 — Eval methodology:** structured baseline (integrity), text extraction (robustness), multi-project (breadth), real-LLM (capability); two-way scoring.
- **A3 — Cost & scale:** ~paise/analysis on a flash model after 85% prompt-token cut; async + queue + pgvector at scale.
- **A4 — Security/ops:** no secrets in repo, input validation, 15 MB upload cap, graceful degradation, deploy-commit visible at `/health`.
- **A5 — The four hard questions:** see `PITCH.md` Q&A defence.
