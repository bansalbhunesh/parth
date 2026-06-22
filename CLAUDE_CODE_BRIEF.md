# Pramaan — Claude Code Execution Brief

Drop-in build prompts in dependency order. Each block is "read it, own it, win
it" — paste one, let it run to green, then move to the next. The scaffold in
this repo already implements the spine; these prompts take it from scaffold to
demo-ready and harden the parts that win rubric points.

**Rule for every prompt:** build the vertical slice (UPS-02) to a working
"27-weeks-early" moment FIRST. Do not go wide until that one path is green.

---

## P0 — Orient (run once)

```
Read README.md, then data/generate_corpus.py, backend/agents/reconciliation.py,
backend/agents/commissioning.py, and eval/run_eval.py. Summarise in plain
language: the data flow from a raw submittal to a deviation register row, where
the LLM is actually called, and what the eval harness measures. Then run:
  python3 data/generate_corpus.py
  python3 eval/run_eval.py --detector baseline
Confirm precision/recall = 1.0 and report the six seeded deviations. Do not
change code yet.
```

## P1 — Make the LLM brain real (the core win)

```
Goal: eval/run_eval.py --detector llm should recover all six seeded deviations
from the RAW markdown in data/corpus/specs and data/corpus/submittals, scored
against data/corpus/ground_truth.json.

1. Set GEMINI_API_KEY in the environment. Install backend/requirements.txt.
2. Run `python3 eval/run_eval.py --detector llm`. Record precision/recall/F1 and
   the Cx-prediction accuracy.
3. If recall < 1.0, the reconciliation prompt in backend/agents/reconciliation.py
   is missing subtle deviations. Improve the prompt (do NOT hardcode answers):
   add explicit instruction to compare numeric thresholds and redundancy levels,
   and to treat "below the required value" as a deviation. Re-run until recall is
   1.0 with precision >= 0.85.
4. Add a citation-faithfulness check: for each finding, verify spec_clause and
   standard_ref actually appear in the source docs; report a faithfulness %.
Output the final metrics table. This table goes straight into the deck.
```

## P2 — Extraction as its own scored stage

```
Wire backend/agents/extraction.py into the pipeline so reconciliation consumes
EXTRACTED triples (not raw text). Then measure extraction accuracy: compare the
agent's triples against data/corpus/extracted/requirements.json and
submittals.json (field-level precision/recall). Report it. This proves the
foundation is solid and gives a second rubric-grade metric.
```

## P3 — Commissioning twin + lead time on every row

```
Confirm backend/agents/commissioning.py attaches predicted_cx_test, level,
week_fail and lead_time_weeks to every deviation. For any deviation whose
(component,parameter) is not in the rule table, call the LLM to map it to the
most likely Cx test from data/corpus/commissioning/cx_plan.json and flag it
"LLM-estimated, needs Cx review". Add a /export/audit assertion that no Critical
row is missing a lead_time.
```

## P4 — Frontend: the firing moment

```
Run the frontend (cd frontend && npm install && npm run dev). It renders from
the API, with a local fallback. Wire NEXT_PUBLIC_API to the FastAPI URL and
confirm the Sentinel card shows UPS-02 at 27 weeks with the live timeline strip.
Then add the React Flow commissioning twin: nodes for equipment → requirement →
standard → Cx test, with the at-risk test node pulsing red. Keep it to the six
deviations. One screen, no scrolling needed for the hero.
```

## P5 — RFI copilot demo beat

```
Confirm POST /copilot answers "has the UPS battery runtime issue come up before?"
by citing RFI-014 from data/corpus/rfi/rfi_log.json. Add a copilot panel to the
frontend with 3 preset questions for the demo. Every answer must show its [source]
citations.
```

## P6 — Evidence pack + scale story

```
Make GET /export/audit produce a clean compliance evidence pack (JSON + a
printable HTML view) grouped by severity with the citation chain per finding.
Then add a /metrics endpoint returning the eval numbers so the deck can pull
live: detection P/R/F1, extraction accuracy, citation faithfulness, mean lead
time. Document in README how the architecture scales from 8 systems to 14,000
line items (batch ingest + vector store + queue).
```

## P7 — Demo rehearsal + deck

```
Produce: (a) a 90-second demo script keyed to the screen (drop UPS submittal →
Sentinel fires → 27w → citation chain → twin lights IST-07 → copilot cites
RFI-014 → export evidence pack); (b) an architecture diagram (mermaid) from
backend/orchestrator.py; (c) a 6-slide deck outline mapping each feature to the
rubric (Innovation / Business Impact / Tech Excellence / Scalability / UX) with
the live metrics from /metrics.
```

---

## De-risk order (do not reorder)

1. Corpus + eval green on baseline ✅ (done in repo)
2. LLM brain recovers deviations from raw docs (P1) ← the make-or-break
3. Lead-time on every row (P3)
4. One polished screen with the firing moment (P4)
5. Everything else (P2, P5, P6, P7)

If you run out of time, a flawless UPS-02 vertical slice with a real eval table
beats six half-working systems. Depth on the moment wins.

## Guardrails

- Never hardcode deviation answers. The reasoning must be real; the eval proves it.
- Never reproduce copyrighted standard text — paraphrased summaries only.
- Keep the agent count at 5 and narratable. Legible beats clever for this jury.
- The lead-time number is the story. If a change buries it, revert.
