# Pramaan — Architecture One-Pager

**EPC Deviation Intelligence for hyperscale data centres.** A multi-agent AI
system that cross-references a design basis, a vendor submittal, and the
governing standards — flags every deviation the day the submittal lands, and
predicts which commissioning test it will fail and how many weeks early.

Live: **frontend** parth-tan.vercel.app · **API** parth-3puc.onrender.com
(`/health` shows the deployed commit; `/llm-check` reports live model status).

---

## System diagram

```
 Documents (PDF / MD / pasted text)
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│  FastAPI backend (Render)  —  22 endpoints · SSE streaming     │
│                                                                │
│   LangGraph pipeline (StateGraph + conditional routing):       │
│                                                                │
│   1 Ingest ─▶ 2 Extract ─▶ [validate?]─▶ 3 Reconcile ─▶        │
│                                  │  (no docs → END)            │
│                                  ▼                             │
│                         4 Cx-Predict ─▶ 5 RFI Copilot          │
│                                                                │
│   LLM layer: native Gemini (gemini-2.5-flash) · swappable to   │
│   OpenAI-compatible gateway or Claude · JSON validation ·      │
│   citation-faithfulness check · 503-retry                      │
│                                                                │
│   Resilience: 60s timeout → rule-based fallback (no silent     │
│   zeros) · graceful 200s without a key                         │
└───────────────────────────────────────────────────────────────┘
        │  deviations + Cx test + lead-time + citations (JSON / SSE)
        ▼
┌───────────────────────────────────────────────────────────────┐
│  Next.js 15 frontend (Vercel) — dashboard + Judge Mode (/judge)│
│  Live Analysis (token-by-token) · ROI · risk matrix · export   │
└───────────────────────────────────────────────────────────────┘
```

## The 5 agents

| # | Agent | Role | Tech |
|---|-------|------|------|
| 1 | **Ingestion** | PDF/MD/text → normalized text per system | pdfplumber + PyMuPDF |
| 2 | **Extraction** | Raw docs → structured (component, parameter, value, clause) | Gemini |
| 3 | **Reconciliation** *(the brain)* | Cross-document deviation detection; design basis authoritative, standards interpret-only | Gemini + confidence + citation check |
| 4 | **Cx Predictor** | Deviation → commissioning test (L1–L5) + week + lead-time | Rule table (no LLM) + LLM fallback |
| 5 | **RFI Copilot** | RAG Q&A over the project corpus + prior-RFI match | TF-IDF retrieval + streaming |

Orchestrated with **LangGraph** `StateGraph` + `add_conditional_edges`
(a validation gate skips reconciliation when a document is missing). Falls back
to a sequential runner if LangGraph isn't installed.

## Data

- **Benchmark (breadth):** a deterministic 12-project synthetic corpus — 11
  countries, 6 tier standards — for honest, repeatable measurement.
- **Real evidence (reality):** **3 fully-sourced real pairs** in
  [`../data/samples/real/`](../data/samples/real/) — Vertiv GXT5 + Cummins QSK60,
  STULZ CyberAir 3 DX, ABB MNS — vs Uptime / NFPA 110 / EPA 40 CFR 60 / ASHRAE
  TC9.9 / EU F-Gas / IEC 61439 / IEC 61641. Every value cited in `PROVENANCE.md`.
  **11 deviations + 5 true negatives, none seeded**, all LLM-verified.

## Evaluation

Four paths against the same ground truth, different inputs:
1. **Structured baseline** — integrity check (1.000 by construction; labelled as such).
2. **Text extraction** — robustness over raw markdown across 12 projects.
3. **Multi-project** — breadth across geographies/standards.
4. **Real-LLM + real pairs** — capability (the number that matters).

Two-way scoring (exact + semantic) so numbers are never inflated; true negatives
prove low false-positive rate. **263 tests · GitHub Actions CI green.**

## Resilience & ops

- **No silent zeros:** if the LLM is rate-limited, a rule-based detector still
  returns the headline deviations with Cx mapping. `PRAMAAN_LLM_TIMEOUT` bounds
  the wait; the streaming path is uncapped for the full LLM result.
- **Verifiable:** `/health` exposes the running commit; `/llm-check` makes a real
  model call and reports the true error (429/404/auth) instead of a false green.
- **Graceful:** every endpoint returns 200 without a key (cached/ground-truth data).

## Security

No secrets in the repo (env-only keys); request validation (`Field` length caps);
**15 MB upload cap**; CORS scoped for a public demo API; no `eval`/shell/subprocess.

## Tech stack

| Layer | Technology |
|-------|-----------|
| LLM | Gemini 2.5 Flash (native) · swappable to OpenAI-compat gateway / Claude |
| Orchestration | LangGraph (StateGraph, conditional edges) |
| Backend | FastAPI (Python 3.11), SSE streaming — Render |
| Frontend | Next.js 15, React 19, TypeScript — Vercel |
| PDF | pdfplumber (primary) + PyMuPDF (fallback) |
| Retrieval | TF-IDF (demo) → pgvector / Qdrant (scale) |
| Eval / CI | 4 eval paths · 263 tests · GitHub Actions |

## Scale path

`POST /ingest/{system}` is per-system and parallelisable → async + task queue;
TF-IDF → pgvector/Qdrant over the project corpus; delta-only re-checks on changed
submittals; Gemini multimodal for drawings/P&IDs. Demo models 10 systems / 33
requirements; the architecture targets 500+ systems and 14,000+ line items per
project.
