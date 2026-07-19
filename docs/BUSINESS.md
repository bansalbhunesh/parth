# Pramaan — Business Case & Impact Model

> Every figure here is cited or a transparently-stated assumption, and marked
> as one or the other. The point of the model is not a single number — it's an
> **expected-value case that clears a real return in the base scenario, is
> negative in the pessimistic one, and says so** (§7).

---

## 0. The national stakes

India is in the middle of a data-centre construction boom, and the documents
that govern that construction are the weakest link:

- **US$126B+ in cumulative investment commitments** to Indian data centres, with
  **US$16.4B deployed in 2025 alone**; CBRE projects capacity to grow **~30% in
  2026** (≈500 MW of new supply on a ~1.3–1.5 GW operational base), toward
  **4–5 GW by 2030** (CBRE, via BusinessToday, Apr 2026; KPMG, *India Data
  Centre Opportunity*, Jul 2026).
- Construction industry studies put **direct rework at ~5% of construction
  cost** (CII) and total **avoidable error at 10–25% of project cost** once
  indirect effects are counted (Get It Right Initiative, UK — ~£25B/yr lost);
  peer-reviewed field studies measure 2.4–6% of contract value (Love & Li;
  Josephson & Hammarlund).
- GIRI's estimate: **error-prevention effort pays back 5–10×** in avoided rework.

On a single 100 MW campus (₹8,000+ crore class), even the conservative 5%
direct-rework rate is a **₹400-crore class exposure** — and in EPC delivery,
avoidable error begins life as an unread or unreconciled document. That is the
document layer Pramaan audits.

*(Scope note: rework percentages are industry-wide construction figures, not
data-centre-specific measurements; they are cited here as the best available
published base rates.)*

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

## 2. The impact model — expected value, not gross exposure

§1's $14.2M/month (60 MW) — ~$9M/month at 50 MW and the same $180/kW/mo rate —
is the **size of the risk on the table**, not what Pramaan captures. Nobody
prevents 100% of deviations, catches them all earlier than a
human would have anyway, or converts every catch into avoided calendar time.
An honest model has to multiply through every one of those probabilities —
not present the whole risk as the product's attributable value.

**Formula** (per project, expected value):

```
eligible submittals × deviation prevalence × incremental recall
  (over current human review) × adoption
  × P(catch is critical-path) × months avoided (if critical-path)
  × local contribution margin at risk
  − false-alert review cost − software & change-management cost
```

Two of these terms are structurally different from a simple product: the
number of *critical-path* catches isn't a count you multiply straight through
(a 50 MW build has one schedule, not fifteen independent ones), so the model
computes **P(at least one critical-path catch)** = 1 − (1 − p)ⁿ, where *n* is
the expected number of incremental catches and *p* is the per-catch chance
one of them sits on the critical path — then multiplies that single
probability by months avoided.

| Input | Low | Base | High | Basis |
|---|---:|---:|---:|---|
| Eligible submittals / project | 400 | 800 | 1,500 | Assumption — typical MEP + controls submittal register size on a hyperscale build. **Not sourced; needs a real submittal log to calibrate.** |
| Deviation prevalence | 8% | 15% | 25% | Assumption — share of submittals carrying a genuine spec-vs-vendor deviation (not typos/formatting). **Not sourced; construction QA literature reports rejection/RFI rates in a much wider 10–40% band that isn't specific to "spec deviation."** |
| Incremental recall over current human review | 10% | 20% | 35% | **The single largest unvalidated assumption.** An experienced OE/CxA reviewer already catches the obvious deviations; Pramaan's benchmark recall (86.2%) is against a team-authored fixture, not against what a human misses in practice. This band is a placeholder until the pilot in §9 produces a real number. |
| Adoption / utilization | 40% | 65% | 90% | Assumption — fraction of eligible submittals actually routed through the tool given rollout friction. |
| P(catch sits on critical path) | 5% | 12% | 25% | Assumption — most caught deviations are non-critical-path (redundant equipment, float in the schedule). General PM risk-register heuristic, not project-specific data. |
| Months avoided, if critical-path | 0.5 | 1.0 | 3.0 | Derived from the 2–8 week commissioning-rework range in §1¹; High case allows more than one workstream (power / cooling / controls each commission separately) to be schedule-critical. |
| Local contribution margin at risk | $9/kW·mo (25% of $36) | $21/kW·mo (35% of $60) | $90/kW·mo (50% of $180) | The lease-rate bands from §7's sensitivity table, haircut to **contribution margin**, not gross revenue — some of a slip's revenue is deferred rather than lost, and fixed costs continue regardless of the slip. |
| Software + change-management cost | $120K | $285K | $550K | $100–500K licence (§6) + $20–50K assumed onboarding/change-management. |
| False-alert review cost | ~negligible | ~$800 | ~negligible | Flags × (1 − precision)/precision × 2 hrs × $75/hr loaded engineer rate, using benchmark precision 0.953. Small relative to the other terms, shown for completeness rather than because it moves the answer. |

**Worked base case (50 MW project):** n ≈ 15.6 expected incremental catches
→ P(≥1 critical-path catch) ≈ 86% → EV(months avoided) ≈ 0.86 → EV(gross
benefit) ≈ **$907K** → net of a $285K licence+onboarding cost ≈ **$621K net
expected value**, a **~3.2× gross-benefit-to-cost ratio** — a real number, not
the "$4–25M / 10–100×" figure the deterministic version of this model used to
print. See §7 for the low/high cases, one of which is **negative**.

Pramaan still flags the deviation **the day the submittal lands** — when it's
a one-line clarification, not a seven-figure schedule event — and tells the
team exactly which commissioning test it would have failed and how many weeks
early they caught it. What changed here is not the product; it's refusing to
present the size of the industry's risk as the size of the product's proven
value.

### The in-app scenario, reconciled (₹, scenario — not a measured saving)

The product itself shows a deterministic single-deviation scenario on
`/war-room` (demo project Meghdoot, deviation DEV-001 — UPS battery autonomy),
computed live by `/projects/{id}/remediation/{dev}` under one stated
assumption: **₹2 crore (200 lakh) per week of ready-for-service slip**.

| Catch moment | Week | Modeled slip | Modeled cost |
|---|---:|---:|---:|
| Design review | 4 | 6 wk | ₹12 cr |
| **Pramaan, at submittal review** | **11** | **13 wk** | **₹26 cr** |
| Commissioning discovery | 38 | 40 wk | ₹80 cr |

**Avoided by catching this one deviation at week 11 instead of week 38:
27 weeks ≈ ₹54 crore** — in the scenario, under the stated assumption.

**Is ₹2 cr/week honest?** Cross-checking against §1's cited lease benchmarks:
$180/kW·mo on a 50 MW build ≈ ₹17 cr/week of gross revenue at risk; typical
Indian colocation rates ($80–110/kW·mo) give ₹8–11 cr/week; applying §2's
25–50% contribution-margin haircut yields a defensible band of roughly
**₹2–5 cr per slip week**. The app's ₹2 cr/week sits at the *bottom* of that
band — a deliberately conservative conversion, not an inflated one.

**How this relates to §2:** the in-app number is the *deterministic,
single-deviation* view — the "months avoided × margin at risk" term shown for
one catch, before probability weighting. §2 is the honest per-project expected
value across all the probabilities (prevalence, incremental recall, adoption,
critical-path odds). Both are labeled scenarios; neither is a measured
customer saving. Against a $100–500K per-project licence, the base-case
expected value clears **~3.2×** (§7) — and the low case is negative, which we
say out loud.

## 3. Market

India is one of the fastest-growing data-centre markets in the world. Three
different numbers get quoted for this, and they are **not the same thing** —
market revenue, capacity, and committed capex have different denominators and
should never be added together:

- **Market size (services/revenue):** ~$1.7B in FY26, growing to **~$6.8B by
  FY30**, taking India from ~2–3% to ~5% of the global data-centre market.²
  *(This replaces an earlier ~$22B-by-2030 figure from an IBEF/Business
  Standard estimate whose methodology we could not verify; KPMG's July 2026
  report is the more recent, better-documented source and is used here
  instead — a corrected number, not a new claim stacked on the old one.)*
- **Capacity:** ~1.9 GW installed as of FY26, more than tripled since FY19,
  with a further **~4.5 GW in the pipeline over the next five years**.²
- **Committed investment:** **>$120B** already committed by hyperscalers and
  global/Indian data-centre operators.²

Every one of those builds runs spec-vs-submittal review today — manually, by
people, across thousands of pages. That is the addressable surface — sized
against **capacity added per year**, not against the revenue or capex totals
above (§5).

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
high volume). Value-based anchoring against the §2 expected-value model: a
**$100–500K** per-project licence against a **base-case ~$907K expected gross
benefit** (~3.2×) is a defensible procurement case for a project carrying a
$500M+ budget — without needing the low-probability, high-severity tail
($4–25M) to be doing the work.

## 5. Market sizing — TAM / SAM / SOM (bottom-up)

Sized from project volume × licence price, not top-down hand-waving. Assumptions
stated so the method survives scrutiny even if you swap the inputs.

| Layer | Definition | Estimate | Basis |
|-------|-----------|----------|-------|
| **TAM** | Global critical-infrastructure spec-vs-submittal QA across data centres + adjacent regulated builds (fabs, pharma, hospitals) | **~$1B+/yr** | tens of GW of new build/yr globally × ~$5–10K/MW licence, plus retrofits & per-submittal volume |
| **SAM** | India + APAC data-centre new builds, near-term | **~$10–30M/yr, growing** | ~0.9 GW added/yr near-term² (4.5 GW pipeline ÷ 5 yrs) × ~$5–10K/MW; recurring as capacity compounds |
| **SOM (3-yr)** | What an early team can realistically capture via owner's-engineer / CxA / EPC accounts | **~$1–3M ARR** | 5–15 projects/yr × $100–300K/project licence |

> Per-MW pricing makes the model scale-invariant: a $250K licence on a 50 MW
> project is **$5K/MW** — small against the §2 base-case ~$907K expected gross
> benefit on that same project, and smaller still against the tail risk it's
> priced to hedge. The wedge is **new builds**; the durable expansion is
> **retrofits, ongoing submittal volume, and non-DC critical infrastructure**
> that run the same review process.

## 6. Unit economics

| Metric | Value | Note |
|--------|-------|------|
| Price per project | **$100–500K** (or $5–10K/MW) | value-anchored to the §2 expected-value model, not gross exposure |
| Variable cost per analysis | **~rupees** | flash model + 85% prompt-token cut; OCR/compute negligible |
| Gross margin | **~95%+** | typical vertical SaaS; no per-seat human cost |
| Expected gross-benefit-to-cost (base case) | **~3.2×** | §2 worked base case: ~$907K EV benefit vs $285K licence+onboarding |
| Payback | **not guaranteed in year one** | negative in the §7 low case; see below |

The cost to *serve* an analysis is rupees regardless of scenario. What is no
longer claimed is that the buyer's payback is guaranteed — §7 shows a
realistic scenario where it isn't.

> **Honesty note:** the price points, margin, and expected-value figures above
> are **modeled pricing hypotheses over unvalidated inputs** — not validated by
> a paid pilot, LOI, or customer. §9 lays out how each unvalidated input gets
> replaced with a measured one.

## 7. Sensitivity — does the case survive pessimistic inputs?

Applying the full §2 formula (not just lease rate) across low/base/high input
bands, on the reference 50 MW project:

| Scenario | Expected incremental catches (n) | P(≥1 critical-path catch) | EV gross benefit | Cost | **Net EV** | Gross-benefit / cost |
|---|---:|---:|---:|---:|---:|---:|
| **Low** | 1.28 | 6.3% | ~$14K | $120K | **−$106K** | 0.1× |
| **Base** | 15.6 | 86.4% | ~$907K | $285K | **+$621K** | 3.2× |
| **High** | 118 | ~100% | ~$13.5M | $550K | **+$12.95M** | 24.5× |

**The honest range is wide, and the low case is negative.** Five of the eight
§2 inputs are unvalidated assumptions (flagged in the table), and the model is
multiplicative — small pessimism in each of five inputs compounds into a
project where the licence doesn't clearly pay back in year one. That is a
materially different claim than "no realistic input set fails to pay back,"
and it is the more defensible one: it says where the model is fragile instead
of asserting it isn't. §9 is the plan to narrow this range with real data
instead of assumption bands.

## 8. The one-line narrative

> **India has committed $120B+ to data-centre build-out, and 9 in 10 large
> infrastructure builds slip schedule — most expensively at commissioning.
> Pramaan catches the vendor deviation that causes the slip on the day the
> document arrives. Our own expected-value model — not a deterministic
> best case — still clears a ~3× return in the base scenario, and we say so
> when it doesn't clear one.**

## 9. Narrowing the range — what a pilot would measure

The two inputs that move the answer most are **incremental recall over
current human review** and **deviation prevalence**, and neither can be
sourced from a desk review — they require a live submittal register. A pilot
with one owner's-engineer, EPC QA lead, or CxA would:

1. Run Pramaan alongside (not instead of) the existing human review process on
   one project's real submittal package.
2. Record, per submittal: did the human reviewer flag it, did Pramaan flag it,
   and — via a domain-practitioner adjudication, not our own team — was the
   flag a genuine deviation.
3. Compute realized incremental recall, realized false-alert rate, and (after
   the project reaches commissioning) how many flagged deviations would
   actually have caused a critical-path delay.
4. Publish the realized numbers next to this assumption table, replacing the
   low/base/high bands with a single measured value and a confidence interval.

Until that exists, every figure above is disclosed as a modeled hypothesis,
not a field result — consistent with [`docs/CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md).

---

### Sources
1. Exto, *"The $30–150M Problem: Why Commissioning Delays Are the Biggest Risk in
   Data Center Construction"*; DatacenterDynamics, *"Every day counts… the
   financial impact of time on data center construction."* McKinsey/Flyvbjerg,
   *"Don't cancel or coddle at-risk capital projects"* — of a 16,000-project
   database, 8.5% met both cost and schedule targets.
2. KPMG India, *"India data centre opportunity — from emerging demand hub to
   integrated data centre powerhouse,"* July 2026: ~$1.7B (FY26) → ~$6.8B
   (FY30) market size; ~1.9 GW installed capacity (FY26) + ~4.5 GW five-year
   pipeline; >$120B committed investment.

> Note: lease and delay-cost figures in §1 are US/global industry benchmarks
> used as order-of-magnitude; §2's contribution-margin bands haircut them for
> India rates and for the fact that not all at-risk revenue is fully lost in
> a slip. The asymmetry is real but it is a multiplicative, probability-weighted
> case now — not a deterministic one.
