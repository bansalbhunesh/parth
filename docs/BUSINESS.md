# Pramaan — Business Case & Impact Model

> Every figure here is cited or a transparently-stated assumption. The point of
> the model is not a single number — it's that **catching one deviation before
> commissioning pays for the product many times over.**

---

## 1. The problem, in money

A spec deviation that slips through review doesn't surface on submittal day — it
surfaces **months later, during commissioning**, the gap between "construction
complete" and "ready for operations." That gap is where the cost lives:

- **9 in 10 large infrastructure projects run over schedule** (Oxford megaproject
  research).
- For a **60 MW** data centre, a commissioning delay costs developers up to
  **~$14.2M per month** in lost revenue (~$180/kW/month lease).¹
- A **3-month slip on a 50 MW** campus ≈ **$15–40M** financing on an idle $500M+
  build + **$10–60M** deferred revenue + **$5–30M** liquidated damages.¹
- Long-lead gear — generators, transformers, **switchgear** — carries **12–18
  month** lead times, so a deviation caught late can't be "swapped out"; it slips
  the whole schedule.

**Commissioning is the single biggest schedule risk in a data-centre build, and
a spec-vs-submittal deviation is one of its most common, most avoidable triggers.**

## 2. The impact model (one deviation)

Transparent, conservative, assumptions stated:

| Input | Value | Basis |
|-------|-------|-------|
| Project | 50 MW hyperscale build | mid-size Indian hyperscale campus |
| Revenue at risk per month of slip | **$9–14M** | 50,000 kW × ~$180/kW/mo lease¹ (India lower; order-of-magnitude) |
| Delay from one undetected deviation | **2–8 weeks** | conservative; commissioning rework + re-test |
| **Cost of one missed deviation** | **$4M – $25M+** | revenue + financing + liquidated damages |
| Cost to fix the *same* deviation on submittal day | **≈ one RFI** (hours of engineering) | caught before procurement/build |
| Pramaan analysis cost | **~paise per analysis** | flash model, 85% prompt-token cut |

> **A single prevented deviation-driven delay is worth millions; the analysis that
> catches it costs rupees.** That asymmetry is the entire business case.

Pramaan flags the deviation **the day the submittal lands** — when it's a one-line
clarification, not a seven-figure schedule event — and tells the team exactly
which commissioning test it would have failed and how many weeks early they caught
it.

## 3. Market

India is one of the fastest-growing data-centre markets in the world:

- Market **doubling to ~$22B by 2030** (from ~$10B in 2025).²
- Capacity to **1.7–2 GW by 2026**, backed by **~$30B in investment**; 4–5 GW by
  2030.³
- **>700 MW under construction now**, 1–2 GW in planning.³
- **$60–70B in announced investment over the next five years.**³

Every one of those builds runs spec-vs-submittal review today — manually, by
people, across thousands of pages. That is the addressable surface.

**Globally**, data-centre capex runs into the hundreds of billions per year; the
problem and the product are not India-specific — India is simply the sharpest,
fastest-growing wedge.

## 4. Who pays, and the model

| Buyer | Why they buy |
|-------|--------------|
| **Owner's engineer / project management consultant** | Catches vendor non-conformances before they sign off — their core mandate |
| **EPC contractor** | Avoids the rework and liquidated damages they're on the hook for |
| **Hyperscaler / colo operator** | Protects go-live date = protects revenue |
| **Commissioning authority (CxA)** | Pre-loads the Cx risk register; audit-ready evidence |

**Business model:** SaaS, priced **per project / per-MW** (or per-submittal for
high volume). Value-based anchoring is trivial: a **$100–500K** per-project licence
against a **$4–25M** avoided-delay exposure is a **10–100× ROI on a single prevented
incident** — an easy procurement decision for a project carrying a $500M+ budget.

## 5. Market sizing — TAM / SAM / SOM (bottom-up)

Sized from project volume × licence price, not top-down hand-waving. Assumptions
stated so the method survives scrutiny even if you swap the inputs.

| Layer | Definition | Estimate | Basis |
|-------|-----------|----------|-------|
| **TAM** | Global critical-infrastructure spec-vs-submittal QA across data centres + adjacent regulated builds (fabs, pharma, hospitals) | **~$1B+/yr** | tens of GW of new build/yr globally × ~$5–10K/MW licence, plus retrofits & per-submittal volume |
| **SAM** | India + APAC data-centre new builds, near-term | **~$10–30M/yr, growing** | ~0.5–1 GW added/yr near-term³ × ~$5–10K/MW; recurring as capacity compounds toward 4–5 GW by 2030 |
| **SOM (3-yr)** | What an early team can realistically capture via owner's-engineer / CxA / EPC accounts | **~$1–3M ARR** | 5–15 projects/yr × $100–300K/project licence |

> Per-MW pricing makes the model scale-invariant: a $250K licence on a 50 MW
> project is **$5K/MW** — immaterial against the $4–25M delay exposure on that same
> project (§2). The wedge is **new builds**; the durable expansion is **retrofits,
> ongoing submittal volume, and non-DC critical infrastructure** that run the same
> review process.

## 6. Unit economics

| Metric | Value | Note |
|--------|-------|------|
| Price per project | **$100–500K** (or $5–10K/MW) | value-anchored to avoided-delay exposure |
| Variable cost per analysis | **~rupees** | flash model + 85% prompt-token cut; OCR/compute negligible |
| Gross margin | **~95%+** | typical vertical SaaS; no per-seat human cost |
| ROI to buyer (single prevented incident) | **10–100×** | $100–500K licence vs $4–25M exposure |
| Payback | **first prevented deviation** | often within the first project |

The cost to *serve* an analysis is rupees; the cost of the deviation it catches is
millions. That gap is both the sales pitch and the margin profile.

## 7. Sensitivity — does the case survive pessimistic inputs?

The headline asymmetry is robust, not cherry-picked. Stress every input downward:

| Scenario | Lease rate | Delay prevented | Value of 1 catch | vs $100–500K licence |
|----------|-----------|-----------------|------------------|----------------------|
| Base (§2) | ~$180/kW/mo | 2–8 wks | $4–25M | **10–100×** |
| India-realistic (1/3 lease) | ~$60/kW/mo | 2–4 wks | $1.5–6M | **3–30×** |
| Deep-pessimist (1/5 lease, min delay) | ~$36/kW/mo | 2 wks | ~$0.9M | **2–9×** |

Even in the deep-pessimist row — a low Indian lease rate and the *shortest*
credible delay — one prevented deviation still returns several times the licence.
**There is no realistic input set where the product fails to pay for itself on a
single catch.**

## 8. The one-line narrative

> **India is pouring $30B+ into data centres, and 9 in 10 large builds slip
> schedule — most expensively at commissioning. Pramaan catches the vendor
> deviation that causes the slip on the day the document arrives, when fixing it
> costs an email instead of a seven-figure delay.**

---

### Sources
1. Exto, *"The $30–150M Problem: Why Commissioning Delays Are the Biggest Risk in
   Data Center Construction"*; DatacenterDynamics, *"Every day counts… the
   financial impact of time on data center construction."*
2. IBEF / Business Standard, *India data-centre market to reach ~$22B by 2030.*
3. BusinessToday / JLL, *India data-centre capacity to ~2 GW by 2026, ~$30B
   investment; $60–70B announced over five years; >700 MW under construction.*

> Note: lease and delay-cost figures above are US/global industry benchmarks used
> as order-of-magnitude; Indian lease rates are lower, but the asymmetry — millions
> per month of slip vs rupees per analysis — holds at any realistic rate.
