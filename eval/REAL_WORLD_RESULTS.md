# Pramaan — Real-World LLM Eval Results

These are **honest, real-LLM results** — not the offline/structured baseline.
The model reads each system's raw spec + submittal + standards markdown and
reasons out deviations from scratch, scored against committed ground truth.

> **Why this matters:** the structured eval compares pre-extracted triples and
> is trivially 1.000. The numbers below come from an actual frontier model
> recovering deviations from raw documents — a score that exercises the full
> pipeline, not just the harness. Read it with the caveats under the headline:
> the ground truth is self-authored, and the precision figure is post-tuning.

## Headline

| Eval | Projects | Deviations | Recall | Precision | F1 |
|------|----------|-----------|--------|-----------|-----|
| Single-project (Meghdoot) | 1 | 14 | **1.000** | **1.000** | **1.000** |
| Multi-project (full portfolio) | 12 | 50 | **1.000** | **1.000** | **1.000** |

- **Model:** `gemini-2.5-pro` (also verified all-14 recall on `gemini-2.5-flash`)
- **Method:** real LLM reasoning over raw markdown, semantic scoring
- **Date:** 2026-06-27
- **False negatives:** 0 — the engine never missed a seeded deviation in any of
  the 12 projects (11 countries, 6 tier standards).

> **Read these numbers honestly (don't over-read the 1.000s):**
> 1. **Recall is partly structural.** The deviations are graded against *our own*
>    seeded ground truth, so a recall near 1.000 reflects "the model re-finds the
>    differences we planted," not detection on an independent labeled set. The
>    real-world generalization signal is the third-party datasheet pairs in
>    `REAL_PAIRS_EVAL.md` (4/4 reproducible offline; the rest need a key).
> 2. **Precision 1.000 is post-tuning.** The first 12-project run scored
>    **P=0.962** (2 false positives in Sakura). We then scoped the reconciliation
>    prompt to fix that exact failure (see "What broke" below) → 1.000. That is an
>    improvement made *in response to the eval set*, so treat 0.962→1.000 as the
>    honest before/after, not a from-scratch perfect sweep. As this repo says
>    elsewhere: a perfect score is a flag to investigate, not a brag.

## How to reproduce

```bash
# point at any LLM provider:
#   native Google:   export GEMINI_API_KEY=AIza...
#   OpenAI-compatible gateway:
export PRAMAAN_LLM=openai
export OPENAI_API_KEY=<your key>
export OPENAI_BASE_URL=<gateway /v1 root>
export OPENAI_MODEL=google/gemini-2.5-pro

# single project (14 deviations)
python3 eval/run_eval.py --detector llm

# full portfolio (50 deviations across 12 projects)
python3 eval/multi_project_eval.py --detector llm
```

## Scoring honesty

The harness reports **two** matching modes (see `eval/run_eval.py`):

- **Semantic (primary):** a deviation is "caught" if the model reports the same
  required→provided discrepancy on the same system, regardless of the parameter
  label it chose. This measures detection, not labeling. Different models
  paraphrase parameter names (`delta_t_c` vs `delta t c`, `FLOOR/height_mm` vs
  `Raised Floor System/finished_floor_height`); semantic matching scores the
  fact, not the wording. A genuine hallucination (a value transition that
  exists in no ground-truth deviation) still counts as a false positive — the
  matcher is robust, not lenient (guarded by tests in `tests/test_eval.py`).
- **Strict:** exact `(component, parameter)` string match, always reported
  alongside for full transparency.

## What we learned along the way (and fixed)

Real runs surfaced two issues that mocking never could:

1. **`gemini-2.5-flash` scored 0.786 strict on Meghdoot** despite finding all
   14 deviations — it labeled 3 differently. Root cause: brittle exact-string
   scoring. Fix: semantic matching (above) + a prompt that pins canonical
   `component` / snake_case `parameter` naming.

2. **2 false positives in Sakura (JEITA Class 4, Tokyo)** on the first
   12-project run (P=0.962). The model flagged `COOL-01` (N+2) and `GEN-01`
   (N+1) redundancy because JEITA Class 4 calls for 2N — but those values
   **match the design basis**. The submittal correctly delivered the spec; the
   model was second-guessing the design itself. Fix: scoped the reconciliation
   prompt so standards only *interpret* ambiguous design-basis requirements,
   never override design-basis values the submittal satisfies. Result: clean
   1.000 sweep. (The model's instinct — noticing the design is below the
   standard — is a valid *design-audit* capability, just a different mode from
   submittal review.)

Both fixes are committed; both numbers above are post-fix and reproducible.
