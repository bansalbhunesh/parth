# Pramaan — Validation Dossier

> We don't have a signed customer yet (honest). What we *do* have is **independent
> third-party evidence** that the problem is real, expensive, and industry-acknowledged
> — and a product that already works on real equipment from the vendors involved.
> This is the evidence a judge can check.

## 1. The problem is real and expensive (independent sources)

- **9 in 10 large infrastructure projects run over schedule** — Oxford megaproject
  research (Bent Flyvbjerg). Data-centre builds are textbook megaprojects.
- **Commissioning is *the* schedule risk.** Industry analysis frames it as
  "the $30–150M problem" — the gap between "construction complete" and "ready for
  operations" is where projects slip (Exto; DatacenterDynamics).
- **A commissioning slip on a 60 MW build ≈ $14.2M/month** in lost revenue
  (~$180/kW·month lease) (Exto / DCD).
- **Long-lead gear locks in late catches.** Generators, transformers, **switchgear**
  carry **12–18 month** lead times — a deviation found at commissioning can't be
  swapped; it slips the schedule.

→ Pramaan attacks the single most expensive, most-acknowledged failure mode in the
industry, at the one moment it's still free to fix.

## 2. The market is real and large (independent sources)

- India data-centre market **doubling to ~$22B by 2030** (IBEF; Business Standard).
- **~$30B invested toward 2 GW by 2026**; **$60–70B announced over five years**;
  **>700 MW under construction now** (JLL; BusinessToday).
- Global data-centre capex runs into the **hundreds of billions per year** — the
  problem is not India-specific; India is the fastest-growing wedge.

## 3. The deviation *types* we catch are live industry issues (not invented)

- **Refrigerant / clean-agent GWP phase-down is happening now.** EU F-Gas + the
  US **AIM Act** are phasing down high-GWP HFCs — R-410A (2,088), R-134a (1,430),
  **FM-200/HFC-227ea (3,220)**. Specifying these today creates real recharge/cost/
  compliance risk over a 15–20 yr life (Control Fire Systems; Firetrace). **Pramaan
  flags exactly these**, recalling the GWP the datasheet omits.
- **EPA Tier 4 vs Tier 2 gensets, NFPA 110 10-second start, IEC 61439 withstand,
  EUROBAT battery life** — all are standard acceptance criteria a CxA checks today,
  by hand.

## 4. The product already works on the real vendors' equipment

Eight sourced pairs — **Vertiv, Cummins, STULZ, ABB, FM-200/Novec, Carrier-class,
EUROBAT, IEC 60076-11 transformer, NFPA 75 cabling** — **17 genuine deviations +
0 false positives, all LLM-verified in a single batch, every value cited**
([`../data/samples/real/PROVENANCE.md`](../data/samples/real/PROVENANCE.md)). The
model did arithmetic (4,000 ÷ 103 = 38.8 h) and recalled three refrigerant/agent
GWPs the datasheets never stated. This is reality, not a synthetic benchmark.

## 5. The one thing left — and how to close it fast

The remaining gap is a **named practitioner's "yes."** Outreach (send to 3–5
data-centre / MEP / commissioning contacts on LinkedIn; ask for one quotable line,
not a meeting):

> *"You've lived the commissioning side. We built a tool that reads a design basis,
> a vendor submittal, and the standard together and flags where the submittal falls
> short — predicting which commissioning test it'll fail and how many weeks early.
> On a real Vertiv UPS + Cummins genset it caught a 7-vs-10-min battery, an
> EPA-Tier-2-vs-Tier-4 engine, and derived a 38.8h-vs-48h fuel shortfall itself.
> Does this match a real pain you've seen — and would catching it on submittal day
> be worth anything? One honest line is all I need."*

One reply ("yes, this is real") — screenshotted into the deck — converts modeled
impact into validated impact.

---

### Sources
Oxford/Flyvbjerg megaproject overrun research · Exto, *"The $30–150M Problem"* ·
DatacenterDynamics, *financial impact of time* · IBEF / Business Standard, India
DC market · JLL / BusinessToday, India capacity & investment · Control Fire
Systems / Firetrace, FM-200 vs Novec 1230 GWP · EU F-Gas Reg. 517/2014 + 2024
revision · US AIM Act · EUROBAT battery service-life classification.
