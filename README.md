# Pramaan — EPC Deviation Intelligence

**Spec-to-Site Deviation Sentinel + Commissioning Risk Twin** for hyperscale
data-centre EPC delivery. Built for ET AI Hackathon 2026, Problem Statement 4.

> **The headline:** Pramaan caught a critical UPS battery shortfall **27 weeks**
> before it would have failed integrated systems testing. That's the difference
> between a one-line email and a seven-figure schedule slip.

## The Problem

In a 40 MW Tier IV data centre build, the design basis, vendor submittals, and
governing standards (Uptime Tier IV, TIA-942, BICSI-002, NFPA 75) live in three
different systems, reviewed by three different people. Subtle deviations — a
battery sized for 7 minutes instead of 10, cooling at N+1 instead of N+2, a
CMR cable in a CMP-required space — slip through and surface months later during
commissioning, causing rework, delays, and cost overruns.

## The Solution

Pramaan is an AI-powered cross-document reasoning engine that:

1. **Extracts** structured requirements from unstructured spec and submittal docs
2. **Reconciles** every requirement against the vendor submittal AND governing standards using LLM reasoning
3. **Predicts** the exact commissioning test (L1-L5) each deviation will cause to fail
4. **Computes lead time** — how many weeks early the deviation was caught
5. **Cites everything** — every finding links back to the spec clause, standard reference, and Cx test
6. **Surfaces prior RFIs** through a project copilot with RAG retrieval

```
specs ───┐
submittals ──┤→ Extraction → Reconciliation (brain) → Cx Risk Predictor → Deviation Register
standards ───┘                      ↑
                             Standards KB (RAG)        RFI / Project Copilot
```

## Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Extraction  │───>│ Reconcilia-  │───>│ Commissioning│
│    Agent     │    │ tion Agent   │    │  Predictor   │
│  (Gemini)    │    │  (THE BRAIN) │    │ (Rule+LLM)   │
└──────────────┘    └──────┬───────┘    └──────┬───────┘
                           │                    │
                    ┌──────▼────────────────────▼──────┐
                    │     Deviation Register            │
                    │  with citation chain + lead time  │
                    └──────────────┬───────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
     ┌────────▼──────┐   ┌────────▼──────┐    ┌────────▼──────┐
     │   Sentinel    │   │  Commissioning│    │    RFI        │
     │   Dashboard   │   │  Risk Twin    │    │   Copilot     │
     │   (Next.js)   │   │  (Timeline)   │    │   (RAG)       │
     └───────────────┘   └───────────────┘    └───────────────┘
```

**5 agents, narratable in 60 seconds:**
- **Extraction Agent** — raw documents → structured triples
- **Reconciliation Agent** — cross-document deviation reasoning (the brain)
- **Commissioning Predictor** — deviation → Cx test + lead time
- **RFI Copilot** — RAG over project corpus with citation
- **Orchestrator** — LangGraph pipeline wiring it all together

## What's in here

| Path | What it is |
|------|------------|
| `data/generate_corpus.py` | Generates the labelled **Project Meghdoot** corpus (deterministic, no LLM) |
| `data/corpus/` | 10 systems, 30+ requirements, 6 seeded deviations, Cx plan, RFI log, ground truth |
| `backend/agents/reconciliation.py` | **The brain** — cross-document deviation reasoning with confidence scoring |
| `backend/agents/commissioning.py` | Maps deviation → Cx test + lead time (rule table + LLM fallback) |
| `backend/agents/extraction.py` | Raw doc → structured triples with accuracy scoring |
| `backend/agents/rfi_copilot.py` | RAG copilot with TF-IDF retrieval + citations + prior-RFI surfacing |
| `backend/orchestrator.py` | LangGraph pipeline (graceful fallback if not installed) |
| `backend/main.py` | FastAPI: `/deviations`, `/copilot`, `/metrics`, `/export/audit`, `/export/audit/html` |
| `eval/run_eval.py` | Precision / recall / F1 + Cx-prediction accuracy + citation faithfulness |
| `eval/baseline_reconciler.py` | Deterministic baseline (proves plumbing; the "vs baseline" story) |
| `frontend/` | Next.js 15 — Sentinel card, system health grid, Cx twin, copilot panel, stats dashboard |

## Quick start

```bash
# 1. generate the labelled corpus (10 systems, 30+ requirements, 6 seeded deviations)
python3 data/generate_corpus.py

# 2. prove the pipeline + eval harness (no key needed)
python3 eval/run_eval.py --detector baseline      # expect P/R/F1 = 1.0

# 3. the real run (recovers deviations from RAW unstructured docs)
export GEMINI_API_KEY=...        # or PRAMAAN_LLM=claude + ANTHROPIC_API_KEY
pip install -r backend/requirements.txt
python3 eval/run_eval.py --detector llm           # the score that matters

# 4. API + UI
uvicorn backend.main:app --reload                 # :8000
cd frontend && npm install && npm run dev         # :3000

# 5. export evidence pack
curl http://localhost:8000/export/audit/html > evidence.html
```

## Key Metrics

| Metric | Baseline | LLM Agent |
|--------|----------|-----------|
| Precision | 1.000 | Target >= 0.85 |
| Recall | 1.000 | Target 1.000 |
| F1 | 1.000 | Target >= 0.92 |
| Cx prediction accuracy | 1.000 | Target >= 0.85 |
| Citation faithfulness | N/A | Target >= 0.95 |
| Max lead time | 30 weeks | 30 weeks |
| Mean lead time | 24 weeks | 24 weeks |

## The Metric That Wins: Lead Time

Every deviation carries `lead_time_weeks`. The UPS-02 hero is **27 weeks** —
caught Week 11, would have failed integrated systems test IST-07 at Week 38.
The total lead-time savings across all 6 deviations is **144 weeks** of avoided
commissioning rework. Put that number on screen, in the deck title, in the
closing line.

## Scale Story

The demo corpus models 10 systems with 30+ requirements. The architecture
scales to 14,000+ line items via:

- **Batch ingest**: POST `/ingest/{system_id}` processes one system at a time
- **Vector store**: swap the in-memory TF-IDF retriever for pgvector/Qdrant
- **Queue**: LangGraph orchestrator supports async execution
- **Multimodal**: Gemini handles PDFs, drawings, and tables natively
- **Incremental**: process only changed submittals (delta ingest)

## Rubric Mapping

| Rubric dimension | Pramaan feature |
|------------------|-----------------|
| **Innovation** | Cross-document AI reasoning across spec + submittal + standard — no commercial tool does this |
| **Business Impact** | 27-week early detection prevents 7-figure schedule slips; quantified lead-time per finding |
| **Technical Excellence** | Eval harness with P/R/F1, citation faithfulness, Cx prediction accuracy |
| **Scalability** | 10→14,000 line items via batch ingest + vector store + LangGraph pipeline |
| **UX** | One-screen firing moment: sentinel card → timeline → citation chain → risk twin → copilot |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/project` | Project metadata |
| GET | `/systems` | List modelled systems |
| POST | `/ingest/{system_id}` | Run pipeline for one system |
| GET | `/deviations` | Full deviation register |
| POST | `/copilot` | RFI/project copilot Q&A |
| GET | `/cx-plan` | Commissioning plan with test schedule |
| GET | `/rfi-log` | Full RFI log |
| GET | `/metrics` | Live eval metrics for the deck |
| GET | `/export/audit` | JSON compliance evidence pack |
| GET | `/export/audit/html` | Printable HTML evidence pack |
