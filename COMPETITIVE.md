# Competitive Positioning — Pramaan

> Honest landscape analysis. We don't claim to be the only system that reads
> submittals; we claim a specific, defensible edge and back every number.

## 1. The visible hackathon field (surveyed 2026-07-03)

A GitHub sweep (repo + code search on "ET AI Hackathon" and every
problem-statement keyword) catalogued **~70 public participant repositories
across all tracks**. Scored on hard, checkable signals, the visible field has:

| Signal | Visible field (~70 repos, all tracks) | Pramaan |
|---|---|---|
| CI pipeline | **0** | ✅ green (tests + 3 evals + tsc + build + Docker smoke + ruff) |
| Test suite | **1** (minimal) | ✅ 446 tests |
| Eval harness with ground truth | **0** | ✅ 4 paths + no-key real-pairs harness |
| Quantified impact model | **0** | ✅ `docs/BUSINESS.md`, every figure cited |
| Live deployment | 3 | ✅ 2 (Vercel + Render) |
| Real third-party documents in the loop | ~2 | ✅ 14 sourced datasheet pairs |

In our own track (PS4), the strongest visible rival is a FastAPI+Claude+ChromaDB
platform with an NCR workflow — real code, but no tests, no eval, no CI, no
deployment. The caveat cuts both ways: serious teams keep repos private until
submission (we did), so the visible field is a floor, not the field. The honest
claim is not "we beat everyone"; it is that **no publicly visible entry in any
track ships verifiable rigor** — reproducible numbers, an open eval, a test
suite a judge can run — which is precisely the axis Pramaan is built on.
Everything below benchmarks against the harder target: the **commercial state
of the art** and the **judging rubric**.

## 2. The commercial landscape (and where we differ)

AI submittal-review tools already exist — **BuildSync, Spec-ID, InspectMind,
SubmittalLink**. They extract product data from submittals and check it against
the spec. BuildSync publicly cites catching an air-handling unit that "would
have failed commissioning." So "AI reads a submittal vs a spec" is **not**
novel, and we no longer claim it is.

| Capability | Commercial submittal-review tools | **Pramaan** |
|---|---|---|
| Spec ⇄ submittal deviation detection | ✅ | ✅ |
| Cross-reference governing **standards** (Uptime/EN 50600/GB/NFPA…) | partial | ✅ 25+ standards, 11 countries |
| **Predict which commissioning test each deviation fails** | ✗ | ✅ L1–L5 Cx twin |
| **Lead-time-to-failure** (weeks early, quantified) | ✗ | ✅ per-deviation `lead_time_weeks` |
| Open, reproducible **eval harness** (P/R/F1 + ground truth) | ✗ (closed SaaS) | ✅ 3 paths + real-LLM |
| **Graceful degradation** when the LLM is down (no silent zero) | n/a | ✅ rule-based fallback + 60s cap |
| **Reads scanned / image-only submittals** (the paper EPCs actually email) | partial | ✅ OCR fallback + honest message when unavailable |
| Self-hostable / inspectable (MIT, full source) | ✗ | ✅ |

**Our moat is the commissioning-risk twin + lead-time quantification + an open,
reproducible eval** — turning "this submittal deviates" into "this will fail
IST-07 at Week 44; you have 27 weeks to act."

### 2a. Market validation + the agentic tier (2026)

The thesis is no longer speculative: in **April 2026 Trimble acquired Document
Crunch** — a construction "AI risk-intelligence" platform that compares documents
to standards, flags deviations, and cites sources — to fold it into its project-
delivery ecosystem. Trunk Tools (CNBC, Aug 2025) raised on adjacent document-QA.
That a $15B contractor-software vendor paid to own *exactly* the
deviation-vs-standards-with-citations capability is the strongest possible
external signal that Pramaan is building in the right place. It also sets the bar:
these are funded, production, field-data products. We do **not** out-scale them.

Where we are *not* a follower: none of the public agentic-risk or submittal tools
(Document Crunch, BuildSync, Trunk Tools, Part3, InspectMind) publicly unify a
spec deviation → the **commissioning test it fails** → the **schedule milestone it
slips** (CPM + beta-PERT Monte-Carlo) → the **long-lead supplier whose
re-procurement is the real cost** into **one standards-cited, offline-deterministic
graph** with a `blast_radius()` traversal. Schedule-delay AI exists (BuildOps,
CMiC, academic early-warning systems), and so does deviation detection — but the
**join** between them, every edge citation-backed and reproducible without an API
key, is the part we have not found in any public competitor. That is the wedge a
hackathon judge can see end-to-end in two minutes; the incumbents sell the pieces
separately and behind a login.

## 3. Evidence hierarchy (strongest first)

1. **Real third-party document** — a Vertiv Liebert datasheet the system never
   saw, analysed live: 8 genuine deviations incl. derived arithmetic
   (3 kVA × 0.8 PF → 2.4 kW) and a value omission. See
   [`data/samples/REAL_DOCUMENT_RESULT.md`](data/samples/REAL_DOCUMENT_RESULT.md).
2. **Real-LLM eval** — a frontier model reasons over raw documents and recovers
   the seeded deviations (semantic + strict scoring).
3. **Extraction-robustness eval** — recovers 50/50 deviations from raw markdown
   across 12 differently-formatted projects (integrity check on our own corpus).
4. **Structured baseline** — 1.000 by construction; plumbing check, not a flex.

We label (3) and (4) as integrity checks, not capability proofs — because they
are. Judges reward that honesty.

## 4. Where a judge could still push — and our answer

- *"F1 = 1.000 looks too clean."* It is — on **synthetic** seeded data. The
  honest number is the real-document run and the real-LLM eval; the perfect
  scores are the harness confirming it recovers what it seeded.
- *"Is this just GPT-wrapping?"* No: 5-agent LangGraph pipeline, deterministic
  rule-based fallback, an open eval harness, and a commissioning-impact model
  that commercial tools don't expose.
- *"Does it work without your API key / under load?"* Yes — `/llm-check` reports
  true status, and the rule-based fallback returns Cx-mapped deviations in <1s
  when the model is rate-limited (free-tier reality), instead of a silent zero.

## 5. Feature teardown — the five things only Pramaan does

Submittal-review tools extract product data and check it against the spec. None
of the following is in their public feature set — and together they are the moat:

1. **Commissioning-failure prediction.** Each deviation maps to the *specific*
   L1–L5 commissioning test it will fail (e.g. battery shortfall → IST-07).
   Commercial tools tell you *that* it deviates; Pramaan tells you *what breaks,
   and when*.
2. **Lead-time-to-failure.** A quantified "you caught this N weeks before the test
   fails" — the number that converts a finding into a dated, prioritised action
   and a board-level schedule-risk metric.
3. **Open, reproducible eval + real-world result.** A public test harness, a
   446-test suite, and a **26/26-recall result on real third-party datasheets**
   ([`eval/REAL_PAIRS_EVAL.md`](eval/REAL_PAIRS_EVAL.md)). Closed SaaS asks you to
   trust the marketing; we ship the proof.
4. **No-silent-zero resilience.** A deterministic detector that still returns the
   headline deviations when the LLM is rate-limited or absent — a property a
   cloud-only black box cannot offer on-prem or air-gapped sites.
5. **Reads the documents that actually arrive.** Real submittals are stamped paper
   scanned to image-only PDFs. Pramaan OCRs them ([`eval/OCR_SCANNED_PDF.md`](eval/OCR_SCANNED_PDF.md));
   when OCR isn't available it says so plainly instead of returning a silent zero.

The category proves the *demand* is real and buyers already pay for adjacent
tooling. Pramaan's wedge is the **commissioning-risk layer on top** — the part
that ties a document deviation to a dated, costed schedule event.

## 6. The durable moat — what compounds with use

Features can be copied; the items below get *harder* to catch the longer Pramaan
runs, which is what makes them a moat rather than a checklist:

1. **The commissioning-knowledge graph.** The proprietary asset isn't the LLM —
   it's the curated mapping of *deviation → which L1–L5 commissioning test it
   fails → typical lead-time-to-failure*. This ships **today as a real,
   traversable, standards-cited graph** — [`data/commissioning_graph.json`](data/commissioning_graph.json),
   served at `/cx-graph`: 16 deviation→test edges over a 5-level Cx taxonomy,
   each edge carrying its failure mode and governing standard (ASHRAE Guideline 0,
   BICSI-002, Uptime Tier Cx, NFPA 110, IEC 61439, CISCA, …). It encodes domain
   expertise a generic submittal-checker can't scrape, and **extends by one cited
   edge per equipment class** (the real raised-floor and busway pairs were added
   exactly this way) — it deepens with every system type and standard added.
2. **A data flywheel.** Every analysis a customer runs — and every correction a
   commissioning engineer makes ("no, that maps to IST-09, not IST-07") — labels
   the deviation→Cx→lead-time mapping. Accuracy on *real* submittals compounds
   with usage; a new entrant starts from zero on that labelled data.
3. **System-of-record switching cost.** Once Pramaan's output *is* the project's
   Cx risk register — audit-ready, dated, cited — ripping it out mid-build means
   re-deriving the schedule-risk evidence the owner's engineer signs against.
   That stickiness grows over a multi-year build.
4. **Distribution wedge.** Land with the owner's engineer / CxA (whose mandate
   *is* catching non-conformances), expand to the EPC and operator on the same
   project. The buyer with the strongest "this is literally my job" pull is the
   cheapest to win first.

### What is *not* yet a moat (so we don't oversell)

- **The reasoning model is rented**, not owned — any team can call the same LLM.
  The defensibility is the knowledge graph + labelled data around it, not the model.
- **The data flywheel needs real deployments to spin** — today it's an
  architecture, not yet accumulated proprietary data. The honest current moat is
  the commissioning-risk layer + open-eval credibility (≈ a strong head start),
  not yet network-effect lock-in. Closing the practitioner-validation gap
  ([`docs/OUTREACH.md`](docs/OUTREACH.md)) is what starts the flywheel.
