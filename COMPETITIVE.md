# Competitive Positioning — Pramaan

> Honest landscape analysis. We don't claim to be the only system that reads
> submittals; we claim a specific, defensible edge and back every number.

## 1. There is no public peer benchmark (yet)

The ET AI Hackathon 2.0 is mid-competition — participant repositories are not
public, so there is no rival submission to benchmark against directly. The
meaningful comparison is therefore against (a) the **commercial state of the
art** and (b) the **judging rubric**.

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
| **Graceful degradation** when the LLM is down (no silent zero) | n/a | ✅ rule-based fallback + 18s cap |
| Self-hostable / inspectable (MIT, full source) | ✗ | ✅ |

**Our moat is the commissioning-risk twin + lead-time quantification + an open,
reproducible eval** — turning "this submittal deviates" into "this will fail
IST-07 at Week 44; you have 27 weeks to act."

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

## 5. Feature teardown — the four things only Pramaan does

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
   263-test suite, and a **17/17-recall result on real third-party datasheets**
   ([`eval/REAL_PAIRS_EVAL.md`](eval/REAL_PAIRS_EVAL.md)). Closed SaaS asks you to
   trust the marketing; we ship the proof.
4. **No-silent-zero resilience.** A deterministic detector that still returns the
   headline deviations when the LLM is rate-limited or absent — a property a
   cloud-only black box cannot offer on-prem or air-gapped sites.

The category proves the *demand* is real and buyers already pay for adjacent
tooling. Pramaan's wedge is the **commissioning-risk layer on top** — the part
that ties a document deviation to a dated, costed schedule event.
