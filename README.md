# Pramaan — EPC Deviation Intelligence

**Spec-to-Site Deviation Sentinel + Commissioning Risk Twin** for hyperscale
data-centre EPC delivery. Built for ET AI Hackathon 2026, Problem Statement 4.

Pramaan reasons across the three documents humans keep in three different
systems — the **design basis**, the **vendor submittal**, and the **governing
standard** — catches the contradiction the day the submittal arrives, and
predicts the exact **commissioning test** it will cause to fail months later.
The headline metric is **lead time**: how many weeks early you caught it.

```
specs ─┐
submittals ─┤→ Extraction → Reconciliation (brain) → Cx Risk Predictor → Deviation Register
standards ─┘                         ↑
                              Standards KB (RAG)        RFI / Project Copilot
```

## What's in here

| Path | What it is |
|------|------------|
| `data/generate_corpus.py` | Generates the labelled **Project Meghdoot** corpus (deterministic, no LLM) |
| `data/corpus/` | Generated specs, submittals, standards, Cx plan, RFIs, **ground_truth.json** |
| `backend/agents/reconciliation.py` | **The brain** — cross-document deviation reasoning (Gemini) |
| `backend/agents/commissioning.py` | Maps deviation → Cx test + **lead time** |
| `backend/agents/extraction.py` | Raw doc → structured triples |
| `backend/agents/rfi_copilot.py` | RAG copilot with citations + prior-RFI surfacing |
| `backend/orchestrator.py` | LangGraph pipeline (graceful fallback if not installed) |
| `backend/main.py` | FastAPI: `/ingest`, `/deviations`, `/copilot`, `/export/audit` |
| `eval/run_eval.py` | **Precision / recall / F1** vs ground truth + Cx-prediction accuracy |
| `eval/baseline_reconciler.py` | Deterministic baseline (proves plumbing; the "vs baseline" story) |
| `frontend/` | Next.js 15 — the Sentinel firing card + deviation register |

## Quick start

```bash
# 1. generate the labelled corpus
python3 data/generate_corpus.py

# 2. prove the pipeline + eval harness (no key needed)
python3 eval/run_eval.py --detector baseline      # expect P/R/F1 = 1.0

# 3. the real run (recovers deviations from RAW docs)
export GEMINI_API_KEY=...        # or PRAMAAN_LLM=claude + ANTHROPIC_API_KEY
pip install -r backend/requirements.txt
python3 eval/run_eval.py --detector llm           # the score that matters

# 4. API + UI
uvicorn backend.main:app --reload                 # :8000
cd frontend && npm install && npm run dev         # :3000
```

## Why the baseline scores 1.0 and the LLM run is the real test

The baseline compares **already-structured** triples — it proves the register
schema, the Cx mapping, and the eval harness are correct. The hard task is
recovering the same six deviations from **unstructured** spec + submittal text,
reasoning against paraphrased standards. That's `--detector llm`, and that
number — plus citation faithfulness — is your Technical Excellence story.

## The metric that wins

Lead time. Every deviation carries `lead_time_weeks`. The UPS-02 hero is **27
weeks** — caught Week 11, would have failed integrated systems test IST-07 at
Week 38. Put that number on screen, in the deck title, in the closing line.
