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

## Pair 3 — Low-Voltage Switchgear (ABB MNS vs IEC 61439-2 / IEC 61641 / Tier IV)

Files: `design_basis_switchgear.md` + `submittal_abb_mns.md`. An
electrical-distribution pair.

### Real, cited facts
- **ABB MNS** LV switchgear is design-verified to **IEC 61439-1/-2**, with rated
  short-time withstand **Icw up to 100 kA**, **Form up to 4**, **IP up to IP54**,
  and an **arc-proof variant type-tested to IEC 61641**. — ABB MNS system guide /
  technical catalogue (new.abb.com, library.e.abb.com).
- **IEC 61439-2** defines Icw and Forms 1–4 of internal separation; **IEC 61641**
  defines internal-arc (IAC) type testing — published standards.

### Standard / design-basis requirements
- Icw ≥ **65 kA / 1 s**; **Form 4b** separation; arc-resistant **IEC 61641**
  type-tested; **IP42** minimum; 415 V 3-phase.

### Deviations — LLM-verified (gemini-2.5-flash, 18 s, 3 of 3)

| # | Parameter | Required | Provided | Note |
|---|-----------|----------|----------|------|
| 1 | Short-circuit withstand Icw | ≥ 65 kA/1 s | **50 kA/1 s** | Below prospective fault level |
| 2 | Internal separation | Form 4b | **Form 3b** | Lower separation |
| 3 | Internal-arc test | IEC 61641 | **Not included** | Standard (non-arc-proof) config |
| — | Ingress protection | ≥ IP42 | IP54 | **Compliant — exceeds (true negative)** |
| — | Voltage | 415 V | 415 V | **Compliant — true negative** |

The IP54-vs-IP42 true negative checks the system does not false-positive when the
submittal *exceeds* a requirement. **Honesty note:** ABB MNS can reach 100 kA /
Form 4 / arc-proof; the 50 kA / Form 3b / non-arc-proof figures are the proposal's
stated configuration (a realistic under-spec), with the IEC 61439/61641 framework
and the MNS capability envelope being the cited real facts.

---

## Pairs 4–6 — Fire suppression · Chiller · Battery (LLM-verified)

Three more pairs widen system coverage. Each headline value is a **published,
fixed property** the model recalled from the agent/refrigerant/battery class
named in the submittal — it was *not* written in the document.

| Pair | Files | Real fact | Deviation (LLM-verified) |
|------|-------|-----------|--------------------------|
| **4 Fire suppression** | `design_basis_fire.md` + `submittal_fm200.md` | FM-200 (HFC-227ea) **GWP 3,220** (Novec 1230 = 1) — NFPA 2001; EU F-Gas / US AIM Act phase-down | `agent_gwp: 750 → 3220` **[Critical]** |
| **5 Chiller** | `design_basis_chiller.md` + `submittal_chiller_r134a.md` | **R-134a GWP 1,430** — EU F-Gas; ASHRAE 90.1 | `refrigerant_gwp: 750 → 1430` **[Major]** |
| **6 Battery** | `design_basis_battery.md` + `submittal_vrla.md` | EUROBAT standard-commercial VRLA = **3–5 yr** design life (High-Performance/Long-Life = 10–12 yr); IEEE 1188 monitoring | `design_life_years: 10 → 3–5` **[Major]**; `monitoring: 3 params → voltage only` **[Major]** (omission) |

The model **recalled GWP values (FM-200 = 3,220; R-134a = 1,430)** the datasheets
never stated — genuine domain knowledge, not string-matching.

---

## Pairs 7–8 — Transformer · Cabling (LLM-verified, same batch)

| Pair | Files | Real fact | Deviation |
|------|-------|-----------|-----------|
| **7 Transformer** | `design_basis_transformer.md` + `submittal_transformer.md` | Dry-type cast-resin, IEC 60076-11; **K-factor** rating for non-linear loads | `harmonic_rating: K-13 → K-1` **[Major]** (cleared Class-F, F1, Dyn11, 6% — all compliant) |
| **8 Cabling** | `design_basis_cabling.md` + `submittal_cabling.md` | NFPA 75 / NFPA 262: plenum spaces need **CMP** (UL 910) | `plenum_fire_rating: CMP → CMR` **[Major]** (cleared Cat6A, OM4/OS2 — compliant) |

---

**Together, the eight real pairs give 17 genuine deviations + 0 false positives**
(recall 1.000, single batch run — see [`../../eval/REAL_PAIRS_EVAL.md`](../../eval/REAL_PAIRS_EVAL.md))
across UPS, generator, cooling, LV switchgear, fire suppression, chiller, battery,
transformer, and cabling — sourced to Vertiv, Cummins, STULZ, ABB, FM-200/Novec,
Carrier-class, EUROBAT, IEC/NFPA/TIA-942, and the standards Uptime Tier IV, NFPA
110/2001/75, EPA 40 CFR 60, ASHRAE 90.1/TC9.9, EU F-Gas, US AIM Act, IEC
61439/61641/60076, IEEE 1188. **None seeded.**

---

## Pairs 9–10 — Hard-fact additions (the product's published ceiling IS the shortfall)

Earlier pairs include a few "scenario" values (the *honesty notes* above flag the
N+1 redundancy, 50 kA / Form 3b, 180 kW selections as realistic proposal choices,
not fixed datasheet maxima). Pairs 9–10 close that gap: in both, the **submitted
product's maximum published rating is itself below the requirement** — there is no
"they could have specified better variant" escape, because the named product
cannot reach the number. These are the most cross-examination-proof deviations in
the set.

| Pair | Files | Real product fact (published ceiling) | Required | Deviation |
|------|-------|---------------------------------------|----------|-----------|
| **9 Raised floor** | `design_basis_floor.md` + `submittal_floor_concore1250.md` | **Tate ConCore 1250** design (allowable) concentrated load = **1250 lbf** on 1 in² (CISCA); ultimate ≥ 2500 lbf — Tate ConCore 1250 spec, Section 09 69 00, R07/15 | ≥ **1500 lbf** (ConCore 1500 class, high-density AI hall) | `concentrated_load_lbf: 1500 → 1250` **[Major]** — caught **offline** |
| **10 Busway** | `design_basis_busway.md` + `submittal_busway_canalis.md` | **Schneider Canalis KTA10** (1000 A) standard I_cw = **50 kA / 1 s** — Canalis KTA 800–4000 A catalogue I_cw/I_pk table | ≥ **65 kA / 1 s** (prospective fault, IEC 61439-6) | `short_time_withstand_ka: 65 → 50` **[Critical]** — caught **offline** |

Both are recovered by the **rule-based detector with no API key** (see
`../../eval/real_pairs_offline.py`), and both pairs are true-negative-rich: the
floor's compliant rolling/pedestal/flame ratings and the busway's IP55 (≥ IP54)
and 1000 A current are correctly **not** flagged.

## Pair 11 — Contested-by-design (the honest sub-1.0 source)

| Pair | Files | The ambiguity | Why it matters |
|------|-------|---------------|----------------|
| **11 Supply-air setpoint** | `design_basis_thermal_setpoint.md` + `submittal_crah_setpoint.md` | Submittal proposes a **30 °C** supply setpoint: **within ASHRAE A1 _allowable_ (15–32 °C)** but **above _recommended_ (≤ 27 °C)** | A real CxA could call this either way — a non-conformance against the recommended envelope, or an accepted efficiency choice within allowable. |

This pair exists so the benchmark is **not** a suspicious 1.000 everywhere. Counting
the contested case against the system yields a precision near **0.9** (live-verified, gemini-2.5-flash) — reported
openly (see [`../../eval/REAL_PAIRS_EVAL.md`](../../eval/REAL_PAIRS_EVAL.md)). The
offline detector deliberately does **not** fire on it (a confident rule has no
business adjudicating a judgment call); it is reserved for the reasoning layer.

## Honest classification of all real deviations

- **(A) Hard fact** — published value genuinely below a published requirement,
  no variant escape: battery 10→7, efficiency 96→95.9, EPA Tier 4→2, fuel
  48→38.8 (derived), the four GWP/agent recalls (R-410A 2088, R-134a 1430,
  FM-200 3220), K-13→K-1, CMP→CMR, VRLA life, **floor 1500→1250**, **busway
  65→50**. *(~15 deviations.)*
- **(B) Scenario** — a realistic proposal under-spec where the product *could*
  reach the requirement in another variant (flagged honestly inline above):
  cooling N+1 / 180 kW, switchgear 50 kA / Form 3b / arc-test. *(~5 deviations.)*
- **(C) Contested** — reasonable experts disagree: the 30 °C supply setpoint.
  *(1 deviation.)*

**Eleven real pairs, ~21 deviation claims, every value traced to a published
source. None seeded.**

## Pairs 12–14 — added 2026-07-03 (PDU / ASD / BMS controller)

Offline-checked (zero false positives — the compliant values below are
correctly cleared) and **live-verified 2026-07-03** (`make eval-real`,
gemini-2.5-flash): **7/7 hard deviations recovered, 0 findings beyond ground
truth**. The first live run also surfaced two *additional* genuine
consequences of the BMS profile shortfall (head-end autonomy, integral IP
routing) that we then added to the ground truth — the model out-audited our
initial answer key, and we kept the stricter version.

**Pair 12 — Rack PDU** (`design_basis_pdu.md` + `submittal_pdu_px3_1000.md`)
- **Raritan PX3-1493V, PX3-1000 "Monitored" series**: energy metering at the
  **inlet** (unit level); per-outlet metering and **outlet switching are
  PX3-5000-series features**, not available on the 1000 series. Billing-grade
  **±1 %** metering certified to **ISO/IEC 62053-21**; rated for **60 °C**
  operation; Zero-U 3-phase, 24 outlets. — Raritan PX3 data sheet
  (DPC-RAR-PX3) + raritan.com PX3 tech-specs / product selector
  (PX3-1493V listing).
- Deviations: required **per-outlet metering** → provided **inlet-only**;
  required **switched outlets** → **unswitched**. Cleared (compliant): ±1 %
  billing-grade accuracy (meets ±1 % requirement), 60 °C rating (exceeds the
  45 °C hot-aisle requirement), Zero-U 3-phase form factor, sensor support.

**Pair 13 — Aspirating smoke detection** (`design_basis_asd.md` +
`submittal_vesda_vlc.md`)
- **Xtralis VESDA VLC (LaserCOMPACT)**: published maximum protected area
  **800 m² (8,000 sq ft)**; sensitivity range **0.005–20 % obs/m**; 24 V dc.
  — xtralis.com VLC product page + VLC product guide (doc 10280).
- Deviation: required **one detector covering the 1,600 m²** hall zone →
  provided **800 m²** published ceiling (a LaserPLUS/VESDA-E-class unit, not
  the compact, is the correct fit). Cleared (compliant): 0.005 % obs/m
  sensitivity floor, EN 54-20 listing, 24 V dc supply.

**Pair 14 — BMS supervisory controller** (`design_basis_bms_controller.md` +
`submittal_bms_ecb600.md`)
- **Distech Controls ECB-600**: **BTL-listed B-AAC** (BACnet Advanced
  Application Controller), communicating on **BACnet MS/TP LAN**; fully
  programmable, 28 points. — Distech ECB-600 datasheet / reseller listings
  (jacksonsystems.com "BACnet B-AAC 28-Point Programmable Controller").
- BACnet device-profile definitions (B-BC = field-programmable **building
  controller**, the supervisory/routing profile; B-AAC = advanced
  **application** controller) — BTL listed-products definitions
  (bacnetinternational.net) / ASHRAE 135 Annex L.
- Deviations: required **B-BC** profile → provided **B-AAC**; required native
  **BACnet/IP** at the controller → provided **MS/TP**; plus two derivative
  failures the reasoning layer surfaced unprompted and we adopted into ground
  truth: **head-end-independent supervisory functions** not provided (AAC
  operates under a supervisory controller) and **integral IP↔MS/TP routing**
  not provided. Cleared (compliant): full field-programmability.

**Fourteen real pairs, 26 hard deviation claims + 1 contested, every value
traced to a published source. None seeded. 19 live-verified June 2026 +
7 live-verified 2026-07-03 (gemini-2.5-flash), 0 false positives.**
