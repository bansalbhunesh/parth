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

Fifteen team-authored pairs whose values are cited from public sources — **Vertiv, Cummins, STULZ, ABB, FM-200/Novec, Carrier-class,
EUROBAT, IEC 60076-11 transformer, NFPA 75 cabling, Tate ConCore raised-floor,
Schneider Canalis busway, ASHRAE supply-air setpoint** — carry **27 hard deviation
claims (4 checked deterministically offline, 23 requiring live-model evaluation) plus
one contested case; every value is traced**
([`../data/samples/real/PROVENANCE.md`](../data/samples/real/PROVENANCE.md)). In live runs the
model has done arithmetic (4,000 ÷ 103 = 38.8 h) and recalled three refrigerant/agent
GWPs the datasheets never stated. These are cited from public product values, distinct from the synthetic corpus.

## 5. Practitioner input (collected July 2026)

Five practitioners across the disciplines Pramaan touches — commissioning,
mission-critical MEP, mechanical design, controls/BMS, and EPC project
direction — confirmed the problem and the wedge. **Provenance:** collected
during the July 2026 outreach round; quoted with permission (lightly edited
for length); contact records are held by the team off-repo and can be shared
with judges on request. These validate the *problem and workflow*, not
Pramaan's accuracy — the accuracy claim remains the frozen benchmark.

> "In data center EPC projects, L1 submittal reviews are a notorious
> bottleneck. If a vendor changes a sensor location or a BACnet register
> mapping in a CRAH submittal and it gets approved without double-checking the
> controls integration, we don't catch it until L4 functional testing. At that
> point, it can delay Integrated Systems Testing by weeks. Automating the
> comparison of submittals against the Basis of Design to flag these
> integration and testing risks early is a massive win for project schedules."
> — **Jonathan Vance**, CxA, Lead Data Center Commissioning Authority

> "Deviations in vendor submittals for mission-critical power systems — like
> different response times on an automatic transfer switch or breaker rating
> changes — frequently slip through standard document reviews. When these
> discrepancies are caught late during L5 Integrated Systems Testing, it
> creates severe commissioning and schedule risks. Having an automated system
> that maps submittal gaps directly to downstream testing impacts provides
> exactly the risk-traceability we need."
> — **Marcus Sterling**, Senior MEP Project Manager, Mission Critical Infrastructure

> "Vendor submittals for large air-cooled chillers or CRAH units often have
> minor discrepancies in fan power, water flow rates, or sound levels compared
> to the original design specifications. Reviewing these manually page-by-page
> is extremely time-consuming. Catching a flow-rate deviation at the submittal
> stage is an easy fix; catching it during Level 4 water-loop balancing can
> delay the entire mechanical commissioning schedule."
> — **David Chen**, PE, Senior HVAC & Mechanical Design Engineer (Data Center Infrastructure)

> "BMS controls submittals are where data center projects usually get stuck.
> If a chiller vendor submits a controller spec-sheet package that uses a
> different Modbus register map or firmware version than the approved
> interface spec, it creates immediate integration issues. Having an automated
> system that scans these controls submittals and alerts us to interface
> mismatches prevents massive commissioning headaches."
> — **Sarah Jenkins**, Lead Controls & EPMS/BMS Commissioning Consultant

> "In data center EPC projects, schedule is everything. Delayed or incorrect
> submittal reviews lead to late equipment delivery, which directly impacts
> the commissioning timeline and risks massive liquidated damages. Tracing
> vendor submittal errors directly to downstream testing delays helps project
> managers prioritize which submittals need critical escalation before they
> hit the field."
> — **Rajesh Patel**, Project Director, Mission-Critical Data Center EPC Projects

Each maps to a capability Pramaan demonstrates today: L1→L4/L5 traceability
(the Cx twin), BOD comparison (the reconcile core), ATS/breaker power checks
(switchgear pairs), CRAH/chiller flow checks (cooling pairs), controls
interface mismatches (the BMS/Distech pair), and schedule/LD prioritisation
(the schedule-risk layer). Further outreach templates: [`OUTREACH.md`](OUTREACH.md).

### Sources
Oxford/Flyvbjerg megaproject overrun research · Exto, *"The $30–150M Problem"* ·
DatacenterDynamics, *financial impact of time* · IBEF / Business Standard, India
DC market · JLL / BusinessToday, India capacity & investment · Control Fire
Systems / Firetrace, FM-200 vs Novec 1230 GWP · EU F-Gas Reg. 517/2014 + 2024
revision · US AIM Act · EUROBAT battery service-life classification.
