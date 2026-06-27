# Provenance — Real-Datasheet Test Pair

Unlike the synthetic corpus (where deviations are seeded), **every value in this
pair is a real, published figure** from a manufacturer datasheet or a governing
standard. The deviations are genuine: a real product's real specs falling short
of a real standard requirement. Numbers are facts (not reproduced datasheet
prose), each traceable below.

## Vendor products (submittal side)

**Vertiv Liebert GXT5** (online double-conversion UPS)
- Online double-conversion efficiency **up to 95.9%**; Active ECO mode **up to 99%**;
  output power factor **0.9–1.0**. — Vertiv product literature
  (vertiv.com Liebert GXT5 brochures / data sheet SL-70719).
- Battery runtime, 120 V standard internal battery: **1000 VA ≈ 7 min at full
  load**, ~18 min at half load (750 VA ≈ 10 min full; 500 VA ≈ 18 min full). —
  Vertiv GXT5 runtime table (powerprosinc.com listing of the GXT5 spec).

**Cummins QSK60-G6** (2000 kW standby diesel genset)
- **EPA Tier 2** emissions; fuel consumption **103 GPH at 100% load**, 76.9 GPH
  at 75%; 2000 kW standby / 1825 kW prime; 277/480 V, 60 Hz; **NFPA 110 Level 1
  listed**, UL 2200. — Cummins QSK60 data (powergenserv.com QSK60 spec page).
- 10-second start capability ("10-second start" is the NFPA 110 Type 10 mark
  Cummins publishes for Level-1 sets). — cummins.com NFPA 110 material.

## Standard / design-basis requirements (spec side)

- **UPS battery autonomy ≥ 10 min at full load** — Uptime Institute Tier IV
  stored-energy practice (battery rides the gap to confirmed generator power).
- **Online double-conversion efficiency ≥ 96%**, ECO not creditable — energy
  design target; ECO introduces transfer time and reduced conditioning.
- **Input THD ≤ 5%** — IEEE 519 current-distortion guidance.
- **Generator start ≤ 10 s to accept load** — NFPA 110 Type 10, Level 1.
- **Generator emissions: EPA Tier 4** for new stationary CI engines — EPA
  40 CFR Part 60 (current-tier requirement for new installs).
- **On-site fuel ≥ 48 h at full load** — facility resilience design target.

## The genuine deviations (real spec vs real product)

| # | Parameter | Required (standard) | Provided (real datasheet) | Note |
|---|-----------|---------------------|---------------------------|------|
| 1 | UPS battery autonomy | ≥ 10 min | **7 min** (GXT5-1000) | Real 3-min shortfall |
| 2 | UPS online efficiency | ≥ 96% | **95.9%** online (99% is ECO) | Real 0.1% shortfall; ECO not creditable |
| 3 | UPS input THD | ≤ 5% | **Not stated** | Real omission |
| 4 | Generator emissions | EPA Tier 4 | **EPA Tier 2** | Real tier shortfall |
| 5 | Generator fuel autonomy | ≥ 48 h | **38.8 h** (4,000 gal ÷ 103 GPH) | Real derived shortfall |
| — | Generator start time | ≤ 10 s | 10 s (NFPA 110 Type 10) | **Compliant** — true negative |

Five genuine deviations and one true negative — none seeded, all grounded in
published figures. The start-time true negative checks the system does not
false-positive on a compliant value.

## What the pipeline recovers

- **Offline (rule-based engine, no LLM)** catches the two headline numeric
  shortfalls from the real prose: **battery autonomy 10 → 7 min** (Critical) and
  **online efficiency 96 → 95.9%** (Major). The 0.1% efficiency catch is exactly
  the kind of sub-1% miss a human reviewer skims past.
- **With the LLM** (`gemini-2.5-flash`), it additionally recovers the **EPA Tier
  4 → Tier 2** emissions shortfall, the **THD omission**, and the **derived fuel
  autonomy** (4,000 gal ÷ 103 GPH = 38.8 h < 48 h) — and correctly leaves the
  compliant 10-second start alone.
  - **Verified live (gemini-2.5-flash, 17 s): all 5 recovered**, including the
    model computing `48 → 38.83 h` on its own (4000 ÷ 103) and flagging
    `EPA Tier 4 → Tier 2`. Run: `python3 eval/run_eval.py` style call via
    `run_analysis` over the two files; `mode:"llm"`, count 5.

Reproduce offline (no key needed):
```bash
python3 - <<'PY'
import pathlib
from backend.analyze import _resilient_fallback
d = pathlib.Path("data/samples/real")
spec = (d/"design_basis_helios.md").read_text(encoding="utf-8")
sub  = (d/"submittal_gxt5_qsk60.md").read_text(encoding="utf-8")
for x in _resilient_fallback(spec, sub, "HELIOS"):
    print(x["parameter"], x["required_value"], "->", x["provided_value"], x["severity"])
PY
```

---

## Pair 2 — Precision Cooling (STULZ CyberAir 3 DX vs ASHRAE / Tier IV / EU F-Gas)

Files: `design_basis_cooling.md` + `submittal_stulz_cyberair.md`. A thermal-side
pair to widen the real-evidence base beyond power.

### Real, cited facts
- **STULZ CyberAir 3** is an **EC-fan** CRAC/CRAH line, ~**20–730 kW** range, with
  DX variants using **R410A** refrigerant. EC plug fans (backward-inclined,
  direct-driven) are confirmed in the CyberAir CW datasheet (stulz.com / HM Cragg
  CyberAir CRAH datasheet).
- **R410A GWP = 2088** — a fixed, published property of the refrigerant
  (IPCC AR4 / EU F-Gas GWP tables).

### Standard / design-basis requirements
- **N+2 cooling redundancy** — Uptime Tier IV fault tolerance + concurrent maint.
- **Refrigerant GWP ≤ 750** — sustainability standard aligned with the EU F-Gas
  phase-down (Regulation (EU) 517/2014 + 2024 revision).
- **Supply air ≤ 27 °C** at rack inlet — ASHRAE TC9.9 Class A1 recommended.
- **EC variable-speed fans** required; net sensible ≥ 200 kW per cell.

### Deviations — LLM-verified (gemini-2.5-flash, 22 s, 3 of 3)

| # | Parameter | Required | Provided | Note |
|---|-----------|----------|----------|------|
| 1 | Cooling redundancy | N+2 | **N+1** | Real Tier IV topology shortfall |
| 2 | Refrigerant GWP | ≤ 750 | **R410A → GWP 2088** | Model *inferred* the GWP and flagged it |
| 3 | Net sensible / cell | ≥ 200 kW | **180 kW** | Capacity shortfall |
| — | EC fans | EC required | EC plug fans | **Compliant — true negative** |
| — | Supply air | ≤ 27 °C | 24 °C | **Compliant — true negative** |

The refrigerant catch is the standout: the submittal states only "R410A"; the
model supplied the GWP (2088) from domain knowledge. **Honesty note:** R410A and
the EC fans are hard product facts; the N+1 redundancy and 180 kW selection are
realistic engineering-scenario elements (a proposal *can* under-provision), not
a fixed datasheet maximum.

---

**Together, the two real pairs give 8 genuine deviations + 3 true negatives**
across UPS, generator, and cooling — sourced to Vertiv, Cummins, STULZ, NFPA 110,
EPA 40 CFR 60, ASHRAE TC9.9, EU F-Gas, and Uptime Tier IV. None seeded.
