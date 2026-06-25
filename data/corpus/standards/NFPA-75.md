# NFPA 75 — Standard for the Fire Protection of Information Technology Equipment (paraphrased summary)

NFPA 75 (2025 edition) establishes fire protection requirements for IT equipment areas. Materials in IT and plenum spaces must meet fire performance requirements for the room classification.

## Cable fire ratings
Cable fire-rating must satisfy the plenum or room classification. NFPA 75 references the cable hierarchy defined by the NEC and tested per UL/NFPA standards:

| Rating | Full Name                        | Test Standard     | Use               |
|--------|----------------------------------|-------------------|-------------------|
| CMP    | Communications Multipurpose Plenum | UL 910 / NFPA 262 | Plenum spaces    |
| CMR    | Communications Multipurpose Riser  | UL 1666           | Riser / vertical |
| CM     | Communications Multipurpose        | UL 1685           | General purpose  |
| CMX    | Communications Multipurpose Ltd    | UL 1581           | Residential      |

### Key rule: CMP is mandatory in plenum-classified spaces.
CMR cable is NOT acceptable as a substitute for CMP in plenums. The hierarchy is strictly CMP > CMR > CM > CMX — a higher-rated cable may substitute for a lower rating, but never the reverse.

### UL 910 / NFPA 262 plenum test criteria
- Peak optical smoke density: <= 0.50
- Average optical smoke density: <= 0.15
- Maximum flame spread distance: <= 1.52 m (5 ft)

## Fire detection
- VESDA (Very Early Smoke Detection Apparatus) recommended for high-value IT rooms
- Aspirating smoke detection provides earliest warning tier (Alert → Action → Fire levels)
- Spot-type smoke detectors as secondary detection layer

## Fire suppression
- Clean-agent suppression required for rooms with active IT equipment
- FM-200 (HFC-227ea): most widely installed halocarbon agent, GWP 3500, atmospheric lifetime 33-36 years
- Novec 1230 (FK-5-1-12): fluoroketone, GWP 1, atmospheric lifetime 0.014 years (5 days), zero ODP
- Inert gas systems (IG-541 Inergen, IG-55) as alternative
- Design concentration per agent manufacturer's listing (NFPA 2001)
- 10-minute minimum hold time verified by annual door fan test
- Pre-action sprinkler acceptable in support spaces only

## Room construction
- IT equipment rooms: minimum 1-hour fire-resistance-rated construction
- Door openings: minimum 3/4-hour fire-resistance-rated assemblies
- Raised-floor plenum classified as plenum space per mechanical code
- All cable penetrations fire-stopped to match wall rating
- Documented risk analysis required for each IT equipment area


---

## Supplementary: NFPA-75_detailed

# NFPA 75 / NFPA 262 — Detailed Technical Reference

**Standards:**
- NFPA 75 — Standard for the Fire Protection of Information Technology Equipment (2020 Edition)
- NFPA 262 — Standard Method of Test for Flame Travel and Smoke of Wires and Cables for Use in Air-Handling Spaces
- NFPA 2001 — Standard on Clean Agent Fire Extinguishing Systems (referenced for suppression)
**Scope:** Fire detection, cable fire ratings, suppression systems, and room construction requirements for data centre and IT equipment spaces.

---

## 1. Cable Fire Rating Hierarchy (NFPA 262 / NEC Article 800)

Cable ratings form a strict hierarchy. A higher-rated cable may substitute for a lower rating, but NOT the reverse.

### 1.1 Rating Summary Table

| Rating | Test Standard | Application | Flame Travel Limit | Smoke Limits | Substitution |
|--------|--------------|-------------|--------------------|--------------|----|
| CMP (Plenum) | UL 910 / NFPA 262 | Air-handling (plenum) spaces | ≤ 1.52 m (5 ft) | Peak OD ≤ 0.5; Average OD ≤ 0.15 | Highest — can replace all below |
| CMR (Riser) | UL 1666 | Vertical shafts, floor-to-floor risers | Must self-extinguish within test parameters | Limited by vertical tray test | Can replace CM, CMX |
| CM (General Purpose) | UL 1685 | Horizontal runs, general building areas | Must self-extinguish | Limited by test | Can replace CMX |
| CMX (Residential/Limited Use) | UL 1581 VW-1 | Low-risk residential, single-family | Limited flame spread | N/A | Lowest rating |

### 1.2 Critical Rules

- **CMP is mandatory** for any cable routed through plenum air-handling spaces (above drop ceilings or below raised floors used as return air plenums).
- **CMR is NOT an acceptable substitute for CMP** — the tests measure fundamentally different fire behaviours.
- NFPA 70 (National Electrical Code) Article 800.179 specifies where each rating is required.
- NEC hierarchy: CMP > CMR > CM > CMX (downward substitution only).

---

## 2. UL 910 / NFPA 262 — Steiner Tunnel Test

### 2.1 Test Apparatus

| Parameter | Specification |
|-----------|---------------|
| Tunnel length | 25 feet (7.62 m) — horizontal Steiner tunnel |
| Observation | Windows at 1-foot intervals for flame spread measurement |
| Smoke measurement | Optical density sensor in exhaust duct |
| Sample mounting | Cable samples mounted in a single layer on a cable tray inside the tunnel |
| Ignition source | Two circular methane burners mounted vertically at intake end |
| Air flow | Forced draft at 240 ft/min (1.22 m/s) through the tunnel |
| Test duration | 20 minutes of active flame exposure |

### 2.2 Pass/Fail Criteria

| Criterion | Limit |
|-----------|-------|
| Maximum flame travel distance | ≤ 1.52 m (5 ft) from ignition point |
| Peak optical smoke density | ≤ 0.50 |
| Average optical smoke density | ≤ 0.15 |

Cables passing all three criteria are classified as CMP (Communications Plenum) grade.

---

## 3. Clean Agent Suppression Systems (NFPA 2001)

### 3.1 Agent Comparison Table

| Property | FM-200 (HFC-227ea) | Novec 1230 (FK-5-1-12) | Inergen (IG-541) |
|----------|--------------------|-----------------------|------------------|
| Chemical type | Halocarbon (HFC) | Fluoroketone | Inert gas blend (52% N2, 40% Ar, 8% CO2) |
| Suppression mechanism | Chemical interruption of combustion chain | Chemical interruption + cooling | Oxygen displacement (reduces O2 to ~12-12.5%) |
| Design concentration (typical) | 7.0-8.0% by volume | 4.2-5.6% by volume | 34.2-43.0% by volume |
| Discharge time | ≤ 10 seconds (per NFPA 2001 Section 5.4.2.1) | ≤ 10 seconds | ≤ 60 seconds (120 seconds in some designs) |
| Ozone Depletion Potential (ODP) | 0 | 0 | 0 |
| Global Warming Potential (GWP) | 3,220 (high) | 1 (negligible) | 0 |
| Atmospheric lifetime | 34.2 years | 5 days | N/A (natural gases) |
| Residue | None | None | None |
| Safe for occupied spaces | Yes, at design concentration | Yes, at design concentration | Yes — O2 maintained at ~12.5% (above 10% hypoxia threshold) |
| Regulatory status | Phase-down under AIM Act (85% reduction by 2036) | Preferred replacement for FM-200 | Fully compliant, no phase-down |
| Maximum exposure (human) | Up to 10.5% concentration, 5-minute maximum | Up to design concentration limits | Safe at design O2 levels |
| Storage pressure | 25 bar (360 psi) or 42 bar (600 psi) | 25 bar (360 psi) | 150 bar (2,175 psi) or 200 bar (2,900 psi) |

### 3.2 Agent Selection Guidance for Data Centres

- **FM-200:** Most widely installed globally; proven track record but facing regulatory phase-down under the AIM Act (US) and F-gas regulations (EU). Not recommended for new installations where alternatives are available.
- **Novec 1230:** Preferred replacement for FM-200 in new data centre builds. Near-zero GWP, rapid discharge, safe for electronics and personnel.
- **Inergen:** Best choice where chemical agents are undesirable. Higher cylinder count and storage space due to inert gas volumes. Longer discharge time (60s vs 10s) but no chemical residue or environmental concerns.

---

## 4. NFPA 75 Key Requirements for IT Equipment Rooms

### 4.1 Detection

| Requirement | Specification |
|-------------|---------------|
| Detection type | Very Early Warning Fire Detection (VEWFD) — typically air-sampling smoke detection (VESDA or equivalent) |
| Sensitivity | Air-sampling systems provide detection sensitivity far below conventional spot detectors |
| Coverage | Full coverage of IT equipment space including under raised floors and above drop ceilings |

### 4.2 VESDA (Very Early Smoke Detection Apparatus)

| Parameter | Specification |
|-----------|---------------|
| Technology | Aspirating (air-sampling) smoke detection — continuously draws air through a network of sampling pipes |
| Sensitivity range | 0.001% to 20.0% obscuration per metre (VESDA-E VEU ultra-wide range) |
| Alarm thresholds | Four levels: Alert, Action, Fire1, Fire2 |
| Typical Alert threshold | 0.03% obs/m (very early warning — pre-combustion pyrolysis) |
| Typical Action threshold | 0.06% obs/m (investigation required) |
| Typical Fire1 threshold | 0.12% obs/m (fire condition imminent or started) |
| Fire2 threshold | Configurable (e.g., 10% obs/m) — triggers suppression system activation |
| Sampling | Continuous air sampling through pipe network with laser-based particle detection |
| Response time | Significantly faster than conventional spot-type smoke detectors |

### 4.3 Suppression

| Requirement | Specification |
|-------------|---------------|
| Preferred system | Clean agent (NFPA 2001) or pre-action sprinkler — NOT wet-pipe sprinkler in IT spaces |
| Agent hold time | Minimum 10 minutes for enclosed rooms |
| Room integrity | Door fan test (room integrity test) per NFPA 2001 Annex C required before agent charge |
| Cross-zoning | Recommended: two detection zones must alarm before agent release (prevents accidental discharge) |

### 4.4 Room Construction

| Requirement | Specification |
|-------------|---------------|
| Door fire rating | Minimum 3/4-hour (45-minute) fire rating for IT room boundaries |
| Wall construction | Fire-rated construction as determined by occupancy classification |
| Penetration sealing | All cable and pipe penetrations through fire-rated barriers must be firestopped |
| Automatic power disconnect | Interlock with suppression system (optional but recommended by NFPA 75) |

### 4.5 Additional NFPA 75 Provisions

- Documented risk analysis required for each IT equipment area
- Risk analysis informs the required level of fire protection (room construction, detection, suppression)
- Emergency Power Off (EPO) system required — accessible without entering the IT room
- Portable fire extinguishers: clean agent type (CO2 or halotron) within IT spaces; ABC dry chemical prohibited inside IT rooms
- Under-floor smoke detection required when raised floor is used as air distribution plenum

---

## 5. Relevance to Data Centre EPC Projects

- Cable specification (CMP vs CMR) must be decided at design stage based on air distribution architecture — raised floor plenum vs overhead ducted.
- Clean agent system selection (FM-200 vs Novec 1230 vs Inergen) drives room volume calculations, floor loading (cylinder weight), and storage room sizing.
- VESDA pipe routing must be coordinated with cable tray and HVAC ductwork at the BIM coordination stage.
- Room integrity (door fan) testing is a commissioning milestone that must be scheduled after all penetrations are sealed.
- 10-minute agent hold time requires tight room envelope — all penetrations, dampers, and door seals must be validated.
- EPO system design must be integrated with the electrical distribution system and coordinated with the building management system (BMS).

---

## Sources

- [UL Code Authorities — NFPA 75 and Fire Protection and Suppression in Data Centers (White Paper)](https://code-authorities.ul.com/wp-content/uploads/sites/40/2015/12/NFPA-75-and-Fire-Protection-and-Suppression-in-Data-Centers-white-paper_final.pdf)
- [US Made Supply — NFPA 75: Fire Protection of IT Equipment](https://usmadesupply.com/resources/building-codes-standards/fire-suppression-standards/nfpa-75)
- [US Made Supply — NFPA 2001 Clean Agent Systems](https://usmadesupply.com/resources/building-codes-standards/fire-suppression-standards/nfpa-2001)
- [Kord Fire Protection — Best Clean Agent for Data Centers Compared](https://kordfire.com/best-clean-agent-for-data-centers-compared/)
- [Code Ready Safety — Clean Agent Fire Suppression](https://www.codereadysafety.com/clean-agent-fire-suppression/)
- [Fire Testing Equipment — UL 910/NFPA 262 Wire and Cable Fire Test](https://www.firetestingequipment.com/news/ul910nfpa-262-wire-and-cables-fire-test/)
- [FOCC Fiber — CMP Cable Explained: Plenum Rating and NFPA 262 Guide](https://www.focc-fiber.com/info/cmp-cable-explained-plenum-rating-103498029.html)
- [Motis Tech — Steiner Tunnel UL 910 NFPA 262](https://www.motistech.com/intrumentation/steiner-tunnel)
- [Firetron — Best Fire Suppression Systems for Data Centers 2026](https://firetron.com/fire-suppression-systems/best-fire-suppression-systems-data-centers-server-rooms/)
- [Oliver FPS — The Role of VESDA in High-Sensitivity Smoke Detection](https://oliverfps.com/2025/06/the-role-of-vesda-in-high-sensitivity-smoke-detection/)
- [Xtralis — VESDA-E Aspirating Smoke Detection Technology](https://xtralis.com/file/868)
- [TFP1 — Understanding NFPA Fire Protection Standards for Data Centers](https://www.tfp1.com/blog/nfpa-75-and-76-fire-protection-standards-for-data-centers/)


---

## Supplementary: NFPA-75_websearch_fire_protection

# Scraped: NFPA-75

Source: WebSearch — NFPA 75 fire protection and clean agent suppression

## NFPA 75 / NFPA 262 — Data Center Fire Protection (paraphrased)

### Cable Fire Ratings (NFPA 262 / UL 910)

| Rating | Test Standard | Application | Flame Travel | Smoke |
|--------|--------------|-------------|--------------|-------|
| CMP (Plenum) | UL 910 / NFPA 262 | Air-handling spaces | ≤ 1.52 m (5 ft) | Peak OD ≤ 0.5, Avg OD ≤ 0.15 |
| CMR (Riser) | UL 1666 | Vertical shafts | Must self-extinguish | Limited by test |
| CM (General) | UL 1685 | Horizontal runs | Must self-extinguish | Limited by test |
| CMX (Residential) | UL 1581 | Low-risk only | Limited spread | N/A |

- CMP is mandatory for any cable routed through plenum air-handling spaces
- CMR is NOT acceptable as CMP substitute — different test, different criteria
- NFPA 70 (NEC) Article 800.179 specifies where each rating is required

### Clean Agent Suppression Systems (NFPA 2001)

| Agent | Chemical | GWP | ODP | Discharge Time | Status |
|-------|----------|-----|-----|----------------|--------|
| FM-200 | HFC-227ea | 3500 | 0 | ≤ 10 seconds | Phase-down (AIM Act, 85% by 2036) |
| Novec 1230 | FK-5-1-12 | 1 | 0 | ≤ 10 seconds | Preferred replacement |
| Inergen | IG-541 (N₂/Ar/CO₂) | 0 | 0 | 60 seconds | Inert gas alternative |

### NFPA 75 Key Requirements for IT Rooms
- Clean agent or pre-action sprinkler (not wet-pipe) for IT equipment spaces
- Minimum 10-minute agent hold time for enclosed rooms
- VESDA (Very Early Smoke Detection Apparatus) or equivalent air-sampling detection
- Door fire rating: ¾-hour minimum for IT room boundaries
- Automatic power disconnect interlock with suppression (optional but recommended)
- Room integrity test (door fan test) per NFPA 2001 Annex C before agent charge
