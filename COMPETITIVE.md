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
