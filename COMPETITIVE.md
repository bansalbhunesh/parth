# Competitive Positioning — Pramaan

> Honest landscape analysis. We don't claim to be the only system that reads
> submittals; we claim a specific, defensible edge and back every number.

## 1. The visible hackathon field (refreshed 2026-07-14)

The all-track public scan is now broader than the original PS4-only sweep.
Pramaan should be positioned as **dominant on verifiable engineering**, not as an
automatic overall favorite. The strongest public all-track threats are strong
for different reasons:

| Threat | Why it can beat us in a judge room | Pramaan's answer |
|---|---|---|
| [`sanskar9999/prahari`](https://github.com/sanskar9999/prahari) | Public-safety/fraud story is emotionally immediate; its current README links a phone-capable GitHub Pages demo, documents a 3–4 minute guided flow, and the repository now includes a GitHub Pages deployment workflow. It does not currently document a test suite. | We cannot out-drama digital-arrest scams. We out-verify: backend + frontend deploys, 839 backend tests, 43 frontend tests, 145 browser journeys, a frozen benchmark, claims register, explicit provenance, and no hidden eval. |
| [`Agent-A345/PlantIQ`](https://github.com/Agent-A345/PlantIQ) | Industrial domain is close to ours; the current public repository documents 5 specialist agents, 22+ implemented features, 6 real government PDFs, a knowledge graph, Docker, and a useful honest disclosure that operating telemetry is simulated. It does not currently document a public deployment or test suite. | We avoid feature fog: one LLM reasoning core, deterministic services, a benchmark card, CI, and a judge path that proves one consequential workflow end to end. |
| [`Exyons/ET-GenAI-Hackathon`](https://github.com/Exyons/ET-GenAI-Hackathon) | Agriculture has broad social impact; the current repository links a live Vercel frontend and documents multilingual web/SMS/WhatsApp access plus a drone simulation. It does not currently document a test suite. | We make the business consequence concrete: a vendor deviation becomes a dated commissioning failure and an owned resolution, with citations and reproducible checks. |

Do **not** claim "best overall all-track project." The defensible claim is:
**among visible public submissions, Pramaan is the strongest evidence and
reproducibility package I found, and the strongest visible PS4 project.** That is
more persuasive than pretending emotional/social-impact tracks do not exist.

## 1a. What changed since the earlier snapshot

The earlier 2026-07-03 sweep is retained in git history, but its aggregate
counts are no longer used as current evidence. Public repositories changed:
Prahari now visibly contains a GitHub Actions deployment workflow, and commit
counts, deployment availability, and documentation continue to move. A one-time
"0 CI pipelines" or "3 deployments" count ages too quickly to support a durable
claim.

The current comparison therefore uses only checkable, repository-level facts and
states the visibility limit plainly: private submissions are not observable, and
"not documented" is not the same as "does not exist." The defensible position is
that Pramaan's public package is unusually deep on reproducibility and claim
boundaries; it is not proof of overall competition rank.

### Patterns worth adopting from the fresh scan

1. **A guided story beats a feature index.** Prahari documents one timed demo
   sequence. Pramaan now uses a 90-second evidence → consequence → owner → RFI →
   closure journey instead of a 22-section dashboard.
2. **Honest data labels create trust.** PlantIQ explicitly separates real
   regulatory documents from simulated telemetry. Pramaan now keeps live,
   deterministic, bundled-reference, benchmark, and scenario states visually
   distinct.
3. **Reach matters, but only where it serves the user.** Kisan AI's multi-channel
   story is compelling because it matches low-connectivity users. Pramaan should
   not imitate channel breadth; its equivalent is a printable/exportable evidence
   record and an API-backed case workflow for CxAs and owner's engineers.

## 2. The commercial landscape (and where we differ)

AI submittal-review tools already exist — **BuildSync, Part3, Spec-ID,
InspectMind, and Document Crunch**. BuildSync and Part3 now publicly document
requirement-by-requirement review, direct source navigation, and a human final
decision; Document Crunch reasons across whole project document sets and can
generate RFIs. So "AI reads a submittal vs a spec," "shows citations," and
"drafts an RFI" are **not** novel, and we do not claim they are.

| Capability | Commercial submittal-review tools | **Pramaan** |
|---|---|---|
| Spec ⇄ submittal deviation detection | ✅ | ✅ |
| Cross-reference governing **standards** (Uptime/EN 50600/GB/NFPA…) | partial | ✅ 25+ standards, 11 countries |
| **Predict which commissioning test each deviation fails** | ✗ | ✅ L1–L5 Cx twin |
| **Lead-time-to-failure** (weeks early, quantified) | ✗ | ✅ per-deviation `lead_time_weeks` |
| Open, reproducible **eval harness** (P/R/F1 + ground truth) | ✗ (closed SaaS) | ✅ 3 paths + real-LLM |
| **Graceful degradation** when the LLM is down (no silent zero) | n/a | ✅ rule-based fallback + 60s cap |
| **Reads scanned / image-only submittals** (the paper EPCs actually email) | partial | ◑ OCR where Tesseract is installed (Docker image); honest "OCR unavailable" message on the default hosted demo |
| Self-hostable / inspectable (MIT, full source) | ✗ | ✅ |

**Our moat is the commissioning-risk twin + lead-time quantification + an open,
reproducible eval** — turning "this submittal deviates" into "this will fail
IST-07 at Week 44; you have 27 weeks to act."

### 2a. Market validation + the agentic tier (2026)

The thesis is no longer speculative: in **April 2026 Trimble completed its
acquisition of Document Crunch** — a construction "AI risk-intelligence" platform that compares documents
to standards, flags deviations, and cites sources — to fold it into its project-
delivery ecosystem. Trunk Tools (CNBC, Aug 2025) raised on adjacent document-QA.
That a $15B contractor-software vendor paid to own *exactly* the
deviation-vs-standards-with-citations capability is the strongest possible
external signal that Pramaan is building in the right place. It also sets the bar:
these are funded, production, field-data products. Trimble reports Document
Crunch has been deployed on 10,000+ projects. We do **not** out-scale them.

The bar moved again on **9 June 2026**: Document Crunch (now a Trimble company)
launched a project-level risk-intelligence platform that answers questions
across all source documents, surfaces scope gaps, and auto-generates
deliverables — redlines, notices, submittals, and **RFIs**. Two consequences we
state plainly: (1) pre-drafted RFI copy is now commercial table stakes — our
case-scoped webhooks are a secured integration boundary, not a moat; (2) the moat
claim below therefore rests entirely on the commissioning-risk join, which
their public feature set still does not include.

### 2b. Commercial patterns adopted in this redesign

- **Part3:** its April 2026 Submittal Assistant presents the spec requirement,
  submitted evidence, exact gap, notes, and direct page links; it then recommends
  a status while explicitly leaving the professional in control. Pramaan's active
  workflow now mirrors that decision shape: evidence is immutable, ownership and
  status changes are separate, and closure requires recorded resolution evidence.
- **BuildSync:** its current product surface emphasizes side-by-side verification,
  pass/fail/unknown-style outcomes, and a complete audit trail. Pramaan now keeps
  the evidence chain adjacent to the finding and refuses to label a fallback as
  live. BuildSync's public 95%+ figure remains a vendor claim, not a directly
  comparable open benchmark.
- **Document Crunch:** project-level context and generated deliverables have moved
  the baseline beyond single-document Q&A. Pramaan's defensible response is not
  more chat; it is the commissioning-test/schedule/supply join plus a case state
  machine that carries an RFI response through closure.
- **What we deliberately did not copy:** broad agent counts, dense dashboard
  grids, and channel proliferation. They add surface area without strengthening
  Pramaan's one buyer-critical workflow.

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

1. **Third-party-derived document** — a Vertiv Liebert datasheet built from
   Vertiv's published figures, outside the seeded corpus, analysed live: 8 genuine
   deviations incl. derived arithmetic (3 kVA × 0.8 PF → 2.4 kW) and a value
   omission. See
   [`data/samples/REAL_DOCUMENT_RESULT.md`](data/samples/REAL_DOCUMENT_RESULT.md).
2. **Real-LLM eval** — a frontier model reasons over raw documents and recovers
   the seeded deviations (semantic + strict scoring).
3. **Extraction-robustness eval** — recovers 50/50 deviations from raw markdown
   across 12 differently-formatted projects (integrity check on our own corpus).
4. **Structured baseline** — 1.000 by construction; plumbing check, not a flex.

We label (3) and (4) as integrity checks, not capability proofs — because they
are. Judges reward that honesty.

## 4. Where a judge could still push — and our answer

- *"A perfect score looks too clean."* On the **synthetic** seeded corpus it is —
  those are integrity checks confirming the harness recovers what it seeded, not a
  capability claim. The number we actually report is the frozen ps4_external_v1
  benchmark (v1.2): **recall 0.862, precision 0.953, FAR 0.000** on frozen labels
  with adversarial clean negatives — deliberately not 1.000.
- *"Is this just GPT-wrapping?"* No: one compliance reasoning graph (a single LLM
  reasoning core wrapped in deterministic ingest/retrieval/critique/Cx-mapping
  services), a deterministic rule-based fallback, an open frozen eval harness, and
  a commissioning-impact model that commercial tools don't expose.
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
3. **Open, reproducible eval + benchmark result.** A public test harness, 839
   backend tests, 43 frontend tests, 145 browser journeys, and a frozen **53-pair / 129-label / 17-system** benchmark with
   repeat-run model results, clean-negative controls, and a rule baseline
   ([`benchmarks/ps4_external_v1/METHODOLOGY.md`](benchmarks/ps4_external_v1/METHODOLOGY.md)).
   Closed SaaS asks you to trust the marketing; we ship the harness and its limits.
4. **No-silent-zero resilience.** A deterministic detector that still returns the
   headline deviations when the LLM is rate-limited or absent — a property a
   cloud-only black box cannot offer on-prem or air-gapped sites.
5. **Reads the documents that actually arrive.** Real submittals are stamped paper
   scanned to image-only PDFs. Pramaan OCRs them where Tesseract is installed (the
   `Dockerfile.backend` image — [`eval/OCR_SCANNED_PDF.md`](eval/OCR_SCANNED_PDF.md));
   the default hosted demo does not bundle Tesseract and says so plainly instead of
   returning a silent zero.

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

### Why naming that gap is itself a strength — auditability beats opacity

The two caveats above are stated plainly on purpose. In *this* market the honesty
is not a weakness we tolerate — it is the strongest card we hold. Two things are
both true, and we say both:

1. **The incumbents have real field data; we do not.** Document Crunch (acquired
   by Trimble, April 2026), BuildSync, InspectMind, and Trunk Tools have run on
   live projects for years and have accumulated real submittals, real engineer
   corrections, and real commissioning outcomes. Pramaan is a weeks-old build
   evaluated on **team-authored fixtures** (§2a, §3); it is **not** field-validated,
   and every benchmark surface says so. On accumulated field evidence, they lead —
   full stop, no asterisk.

2. **We are the only one you can actually check.** Every number Pramaan reports
   ships with the means to reproduce it: a frozen 53-pair / 129-label benchmark,
   the eval scripts, the labels, the deterministic rule baseline, and a **claims
   register that enumerates its own limits** ([`docs/CLAIMS_REGISTER.md`](docs/CLAIMS_REGISTER.md))
   — enforced by a test that fails the build if any surface overstates. The
   commercial tools are closed SaaS: you get a marketing accuracy figure and a
   login. You cannot see their eval, run it, inspect one label, or discover where
   the tool is *weak*.

For most software, "less field data" is just a deficit. Here it is a smaller
deficit than it looks, because of *who signs*. The buyer of commissioning-risk
intelligence is the owner's engineer or commissioning agent (CxA) — a licensed
professional who puts their name on the deviation register and carries personal
liability if a missed non-conformance surfaces at Level-4/5 commissioning. For that
buyer the decisive property is not the vendor's accuracy claim; it is *whether they
can audit the tool before they stake their stamp on it.* A system that ships its
eval and openly marks where it is not yet validated is more defensible to sign
against than a black box that asks for trust — precisely because the liability sits
with the professional, not the vendor.

That reframes the gap as one of **timing, not architecture:**

- **Their field-data lead is a head start we close by running.** The data flywheel
  (item 2 above) is built and waiting; the moment real deployments begin, every
  correction a CxA makes labels the deviation→Cx→lead-time mapping. The gap narrows
  with our usage.
- **Their opacity never becomes auditable.** It is structural to a closed product.
  A judge — or a liability-bearing buyer — can run *our* eval this afternoon; they
  cannot run the incumbents' at all, ever.

So "we do not have their field data" is not a hedge we merely tolerate — it is the
setup for the sentence that follows it: **Pramaan is the only entrant, commercial
or hackathon, whose every claim you can verify yourself before you trust it.**
Naming our own gap is what makes that credible; a tool that hides its limits has
already shown you it will hide the next one.

> The claims register is not a confession — it is a due-diligence artifact the
> closed incumbents cannot produce. For a buyer whose signature is on the line, it
> is the most persuasive object in the repository.
