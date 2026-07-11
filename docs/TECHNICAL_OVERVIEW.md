# Pramaan — Technical Overview (runtime truth & how to verify it)

A companion to [`ARCHITECTURE.md`](ARCHITECTURE.md). This page exists so a
reviewer can confirm that **every architecture claim matches what actually runs**
— with the file, endpoint, or command that proves it. Nothing here is aspirational;
where something is a prototype limitation it says so.

## 1. The LLM ↔ deterministic boundary

The single most important truth about Pramaan's runtime: **one step *reasons*
with an LLM — `reconcile`; the decision/numeric path everywhere else is
deterministic.** An LLM is used at only two edges beyond the core — a Cx-mapping
**fallback** for equipment classes the rule table + graph don't cover, and
*phrasing* the copilot's deterministically-retrieved answer. Get this right and
the rest follows.

| Concern | Runs on | Source of truth |
|---------|---------|-----------------|
| Deviation detection & reasoning | **LLM** (failover chain) | `backend/agents/reconciliation.py`, `node_reconcile` in `backend/orchestrator.py` |
| Document ingestion / OCR | Deterministic | `backend/agents/ingestion.py`, `backend/agents/ocr_util.py` |
| Standards retrieval (tool-call cycle) | Deterministic local KB | `backend/agents/retrieval.py`, `node_retrieve` |
| Self-critique / reflexion cycle | Deterministic verifier (opt-in LLM critic) | `_self_check` / `node_critique` in `backend/orchestrator.py` |
| Commissioning-test mapping + lead-time | Rule table → standards graph (deterministic); LLM **fallback** only for unmapped classes | `backend/agents/commissioning.py` (`predict_cx_impact`) |
| Schedule risk (CPM + Monte Carlo) | Deterministic | `backend/agents/schedule_risk.py` |
| Supply-chain risk scoring | Deterministic | `backend/agents/supply_chain.py` |
| Project graph / blast radius | Deterministic | `backend/agents/project_graph.py` |
| RFI copilot retrieval | Deterministic BM25 (TF-IDF-family) ranking + LLM only to phrase the answer | `backend/agents/rfi_copilot.py` |

**Consequence:** an LLM outage degrades *detection recall* (to the rule floor)
but does **not** disable the schedule / supply-chain / graph services — those keep
computing from the deviation register. Narratives that an LLM writes carry a
`mode` field so you can tell live text from a rule-based fallback.

## 2. The graph is a real agent (two bounded cycles)

`build_graph()` in `backend/orchestrator.py` compiles a LangGraph `StateGraph`:

- **Validation gate** — `route_after_validate` sends a system with a missing spec
  or submittal straight to `format_output` (no wasted LLM call).
- **Cycle 1 — retrieval tool-call** — when a finding cites a governing standard
  that isn't in context, `node_retrieve` fetches it from the local KB and routes
  back to `reconcile`. Bounded by `PRAMAAN_MAX_RETRIEVALS` (default 1).
- **Cycle 2 — self-critique / reflexion** — `node_critique` verifies the
  reconciler's own findings, drops provable false positives (a value that already
  meets spec) and duplicates, and on a failed check routes back to `reconcile`
  with the critique as feedback. Bounded by `PRAMAAN_MAX_REVISIONS` (default 1).
  The verifier never drops a value merely for not being verbatim in the docs —
  the best findings are *derived* (4000/103 = 38.8 h) or *recalled* (R-410A GWP
  2088).
- **Best-so-far retention** — a revision pass that returns fewer findings than the
  prior pass is discarded, so a degraded retry can't silently erase legitimate
  findings.
- **Fallback** — if `langgraph` is absent, `run_pipeline` drives the identical
  nodes and both cycles with a plain loop.

## 3. Reliability: failover is availability, not accuracy

`backend/llm.py` implements the provider chain. Order (only *configured* providers
are attempted): `gemini → Qwen/OpenAI-compatible gateway → Groq → Claude → local
Ollama → deterministic rule engine`. The hosted demo runs `gemini,qwen,groq` —
the gateway leg is funded (aicredits.in) and pinned to the benchmark-featured
`gemini-3.1-flash-lite`, so the first failover lands on the featured
configuration; Claude has no key and is left out of the order.

- Every leg is scored the same in the benchmark — **failover never improves
  accuracy**, it only keeps the demo answering.
- The terminal leg is the deterministic rule engine (the "floor"): low recall by
  design (0.111 on the benchmark), computed from the real documents, never from
  seeded labels.
- The Qwen gateway must be a genuinely separate quota, not Google's endpoint.

Verify live: `GET /llm-check` (tiny probe + live chain), `GET /llm-check?deep=1`
(reconcile-sized probe — a tiny probe can pass while demo-sized calls 429 on
token-weighted quotas), `GET /llm-check?probe_all=1` (per-provider).

## 4. Endpoint map (what a judge can hit)

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Running commit, analysis mode, OCR availability, security + scalability status |
| `GET /ocr-check` | Ground-truth OCR capability for this deployment (booleans/ints only) |
| `GET /llm-check` | Real LLM call + live failover chain + last failover reason |
| `POST /analyze` · `/analyze/stream` | Text spec+submittal → deviations (SSE token stream) |
| `POST /analyze/upload` · `/analyze/upload/stream` | PDF/image upload → extraction meta + deviations |
| `POST /analyze/vision` | Datasheet image → Gemini vision reads values (separate from OCR) |
| `POST /jobs/analyze` · `GET /jobs/{id}` | Async job flow + input-hash cache (scale path) |
| `GET /projects/{id}/schedule` · `/supply-chain` · `/graph` | Deterministic services |
| `GET /export/audit/html` | Standalone evidence pack (HTML) |
| `POST /cases` · `/cases/{id}/findings` · `/cases/{id}/export/itp.pdf` | Persisted, tenant-isolated case workflow — finding → drafted RFI → printable HTML/PDF export → audit log |

Full list: `backend/main.py`.

## 5. Behaviour-changing environment flags

| Flag | Default | Effect |
|------|---------|--------|
| `PRAMAAN_LLM` | `gemini` | Primary provider (`gemini`/`openai`→gateway/`claude`/`ollama`) |
| `PRAMAAN_RETRIEVAL` | `1` | Cycle 1 (retrieval tool-call) on/off |
| `PRAMAAN_MAX_RETRIEVALS` | `1` | Cycle 1 bound |
| `PRAMAAN_MAX_REVISIONS` | `1` | Cycle 2 (reflexion) bound |
| `PRAMAAN_LLM_CRITIQUE` | `0` | Opt-in deeper LLM critic in Cycle 2 |
| `PRAMAAN_LLM_TIMEOUT` | — | Bounds the non-streaming LLM wait before the rule fallback |
| `PRAMAAN_OCR` / `PRAMAAN_OCR_ENABLED` | on | OCR enable/disable (binary still required) |
| `PRAMAAN_VISION` | `1` | Image-via-LLM vision path |

## 6. What this is not

- **Not five autonomous agents** — one LLM reasoning core + deterministic nodes/services (§1).
- **Not fully autonomous / not production-grade** — a hackathon prototype; security is demo hardening, rate limiting is single-instance/in-memory.
- **Not field- or customer-validated** — see the benchmark limitations in [`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md).
- **OCR is not always available** — it depends on the tesseract binary; `/ocr-check` is authoritative.
- **Benchmark labels are single-author frozen** — two-person human adjudication is pending; the automated consistency audit (123/129 consistent, 6 flagged) is machine QA, not a second human reviewer.
