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

## 5. The one-line narrative

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
