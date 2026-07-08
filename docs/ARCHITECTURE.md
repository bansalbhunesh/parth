# Pramaan — Architecture One-Pager

**EPC Deviation Intelligence for hyperscale data centres.** Pramaan cross-references
a design basis, a vendor submittal, and the governing standards; flags every
deviation the day the submittal lands; and maps each one to the commissioning
test it will fail and how many weeks early it was caught.

The runtime is **one compliance reasoning graph, a set of connected deterministic
intelligence services, and a reliability layer** — not five autonomous agents.
This page describes what actually runs. Every claim here is checkable against
`backend/orchestrator.py`, `backend/main.py`, and the endpoints below.

Live: **frontend** parth-tan.vercel.app · **API** parth-1-ma30.onrender.com
(`/health` shows the deployed commit · `/llm-check` reports the live provider
chain · `/ocr-check` reports whether OCR runs in that deployment).

---

## The shape in one picture

```
 Documents / text / image input  (PDF · MD · pasted text · datasheet image)
        │
        ▼  extraction / OCR / text parsing
 ┌──────────────────────────────────────────────────────────────────────┐
 │  COMPLIANCE REASONING GRAPH   (LangGraph StateGraph, conditional      │
 │  routing, two bounded cycles — falls back to a sequential runner)     │
 │                                                                      │
 │   ingest ─▶ load_standards ─▶ validate ─(no docs)─▶ format_output    │
 │                                   │ (docs)                            │
 │                                   ▼                                   │
 │                              reconcile ◀──────────────┐  ◀────────┐   │
 │                             (LLM core)                │           │   │
 │                                   ▼                   │           │   │
 │                               retrieve ──(fetched a   │ cycle 1   │   │
 │                                   │      missing cited │ tool-call │   │
 │                                   │      standard)─────┘           │   │
 │                                   ▼ (ok)                           │   │
 │                               critique ──(self-check fails,────────┘   │
 │                                   │        budget left)  cycle 2       │
 │                                   ▼ (ok / budget spent)  reflexion     │
 │                              cx_predict ─▶ format_output               │
 └──────────────────────────────────────────────────────────────────────┘
        │  evidence-grounded deviation register + Cx test + lead-time + citations
        ▼
 CONNECTED DETERMINISTIC SERVICES      RELIABILITY LAYER
  · commissioning-test mapping          · LLM provider failover (availability)
    (rule table, L1–L5)                 · deterministic rule fallback (no silent 0s)
  · schedule risk (CPM + Monte Carlo)   · OCR runtime availability (/ocr-check)
  · supply-chain risk                   · rate limits + optional demo auth
  · project graph (blast radius)        · upload validation (MIME/magic-byte/caps)
  · RFI / copilot (TF-IDF retrieval)    · benchmark evidence (ps4_external_v1)
        │
        ▼
 Judge-facing explanation  (Next.js dashboard + Judge Mode /judge + Evidence /evidence)
```

## The reasoning graph, node by node

The graph is a real agent, not a straight pipeline: it has a validation gate and
**two bounded cycles**. Exactly one node calls an LLM to *reason*; the rest are
deterministic.

| Node | What it does | LLM? |
|------|--------------|------|
| `ingest` | PDF/MD/image → normalized text per system | No — pdfplumber + PyMuPDF (+ Tesseract OCR fallback) |
| `load_standards` | Loads the governing-standards corpus into context | No — local KB read |
| `validate` | Routing gate: skip reasoning when a document is missing | No |
| **`reconcile`** | **Extraction + cross-document deviation reasoning — the core.** Design basis authoritative; standards interpret-only; confidence + citation-faithfulness check | **Yes — the single LLM reasoning core** |
| `retrieve` | **Cycle 1 (tool-call):** if a finding cites a standard absent from context, fetch it from the local KB and loop back to re-reason | No — deterministic local lookup |
| `critique` | **Cycle 2 (reflexion):** verify the reconciler's own output; drop equality false-positives and duplicates; loop back on a failed self-check | No by default — deterministic verifier (opt-in LLM critic via `PRAMAAN_LLM_CRITIQUE=1`) |
| `cx_predict` | Deviation → commissioning test (L1–L5) + scheduled week + lead-time + risk score | Rule table → standards graph first (deterministic); an **LLM fallback** fires only for equipment classes in neither (`cx_source` records `rule`/`graph`/`llm`/`fallback`) |
| `format_output` | Attach system id, defaults, emit JSON/SSE | No |

Both cycles are **bounded** (`PRAMAAN_MAX_RETRIEVALS`, `PRAMAAN_MAX_REVISIONS`)
so the graph always terminates. If LangGraph isn't installed, an equivalent
sequential runner drives the same nodes and cycles.

> **Why not "five agents"?** An earlier framing called ingest / extract /
> reconcile / cx-predict / copilot "five agents" — wording we retired. In the real runtime the
> reconcile step is the **single LLM reasoning core** (extraction happens inside
> it — there is no separate extract node); ingestion, retrieval and self-critique
> are deterministic. Two nodes touch an LLM only at the edges: `cx_predict` is
> rule/graph-first and calls an LLM **fallback** only for equipment classes it
> can't map, and the RFI copilot uses an LLM only to *phrase* a deterministically
> retrieved answer. Calling them all "AI agents" overstates what runs, so we
> describe the truth: **one LLM reasoning core inside a deterministic compliance
> graph, plus deterministic services.**

## Connected deterministic intelligence services

These consume the deviation register and are **deterministic**, with one
disclosed exception: commissioning-test mapping falls back to an LLM to predict
the Cx test/level for equipment classes in neither the rule table nor the
standards graph (`cx_source="llm"`). Otherwise an LLM is used only to *narrate*
results (schedule, supply-chain, graph), and the narrative is labelled with its
`mode`.

- **Commissioning-test mapping** — rule table + a standards knowledge graph map each deviation to its L1–L5 test and the lead-time window; an LLM fallback covers only classes in neither (`backend/agents/commissioning.py`).
- **Schedule risk** — CPM + Monte Carlo over the project network; on-time probability, milestone slip (`/projects/{id}/schedule`).
- **Supply-chain risk** — long-lead shipment risk scoring (`/projects/{id}/supply-chain`).
- **Project graph** — deviation → equipment → Cx test → milestone → supplier blast-radius (`/projects/{id}/graph`, `/blast-radius/{dev}`). Edges carry a `basis` where one exists; some edges (e.g. `supplied-by`) are structural and carry none — so we do **not** claim "every edge is standards-cited".
- **RFI / copilot** — BM25 (TF-IDF-family) retrieval over the project corpus + prior-RFI match; an LLM only phrases the cited answer, streamed (`/copilot/stream`).

## Reliability layer

- **LLM provider failover (availability, not accuracy):** on quota/429/timeout the demo fails over `gemini → Qwen gateway → Groq → Claude → local Ollama → deterministic rule engine`. Only configured providers are tried (the hosted demo runs `gemini,qwen,groq` — Claude has no key and is left out). Every leg is scored the same — **failover buys uptime, never accuracy.** `/llm-check` shows the live chain and last failover reason.
- **Deterministic rule fallback (no silent zeros):** if no provider answers, the rule engine still returns the headline deviations with Cx mapping, computed from the real documents — never from seeded labels. It is deliberately low-recall (a floor).
- **OCR runtime availability:** OCR is text-first with a Tesseract fallback and needs the tesseract binary. `GET /ocr-check` is the ground truth for a given deployment; the UI reads it and never implies OCR where it isn't installed.
- **Public-demo security:** optional token auth, per-IP (single-instance, in-memory) rate limiting, MIME/magic-byte/size upload validation, prompt-injection-resistant prompts, no secret leakage in status endpoints. This is **demo hardening, not production security.**
- **Verifiability:** `/health` exposes the running commit and analysis mode; every endpoint returns 200 without a key (bundled ground-truth data).

## Evidence

Featured configuration `gemini-3.1-flash-lite` (via gateway), 3-pass, on the
frozen **ps4_external_v1 (v1.2)** benchmark: **53 spec–submittal pairs, 129
single-author-frozen labels, 17 systems, 64 clean negatives** → mean semantic
**recall 0.862 (0.841–0.873), precision 0.953, F1 0.905, 0 false alerts** on the
64 clean negatives, p50 ~2.5 s, vs a deterministic rule baseline of **0.111**.
Fixtures are team-authored (10 derived from public primary sources, 5 with
verified URLs); labels are single-author frozen with **two-person human
adjudication pending** and stored primary-source PDFs pending. This is a
benchmark result, **not** a real-world-accuracy or field-validation claim. Full
numbers, limitations and links: [`/evidence`](../frontend/app/evidence/page.tsx)
· [`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md) ·
[`benchmark_card.json`](../benchmarks/ps4_external_v1/reports/benchmark_card.json).

**605 tests · GitHub Actions CI.** Deeper runtime detail:
[`TECHNICAL_OVERVIEW.md`](TECHNICAL_OVERVIEW.md).

## Tech stack

| Layer | Technology |
|-------|-----------|
| Reasoning core | LLM via failover chain — featured `gemini-3.1-flash-lite` (gateway); native Gemini / Claude / Qwen-gateway / Groq / local Ollama all swappable |
| Orchestration | LangGraph (`StateGraph`, `add_conditional_edges`, two bounded cycles) → sequential fallback |
| Deterministic services | commissioning rule table · CPM + Monte Carlo schedule · supply-chain scoring · project graph · TF-IDF copilot |
| Backend | FastAPI (Python 3.11), SSE streaming — Render |
| Frontend | Next.js 15, React 19, TypeScript — Vercel |
| Extraction | pdfplumber (primary) + PyMuPDF (fallback) + Tesseract OCR (scanned/image, where installed) |
| Retrieval | TF-IDF (demo) → pgvector / Qdrant (scale path) |

## Scale path

`POST /ingest/{system}` is per-system and parallelisable → async job flow +
input-hash cache (already in `backend/jobs.py`); TF-IDF → pgvector/Qdrant over
the project corpus; delta-only re-checks on changed submittals; Gemini
multimodal for drawings/P&IDs. The demo models 10 systems / 33 requirements; the
architecture targets 500+ systems and 14,000+ line items per project. See
[`SCALABILITY_PROOF.md`](SCALABILITY_PROOF.md).
