# IS 1893 (Part 1):2016 — Detailed Technical Reference

**Standard:** IS 1893 (Part 1):2016 — Criteria for Earthquake Resistant Design of Structures, Part 1: General Provisions and Buildings
**Version:** 2016 (6th Revision)
**Issuing Body:** Bureau of Indian Standards (BIS)
**Scope:** Provides seismic zoning map, design spectra, importance factors, response reduction factors, soil classification, and analysis methods for earthquake-resistant design of buildings and structures across India. This is the principal Indian standard governing seismic design for all construction including data centres.

---

## 1. Seismic Zone Classification and Zone Factors

India is divided into four seismic zones (Zone I was merged into Zone II in 2002). The zone factor Z represents the peak ground acceleration as a fraction of g.

| Zone | Seismic Intensity | Zone Factor (Z) | Peak Ground Acceleration |
|------|-------------------|-----------------|--------------------------|
| Zone II | Low | 0.10 | 0.10g |
| Zone III | Moderate | 0.16 | 0.16g |
| Zone IV | Severe | 0.24 | 0.24g |
| Zone V | Very Severe | 0.36 | 0.36g |

### 1.1 Notable Zone Assignments for Data Centre Locations

| Location | Zone | Z Factor | Notes |
|----------|------|----------|-------|
| Chennai | III | 0.16 | Major data centre hub |
| Mumbai (city) | III | 0.16 | Financial hub |
| Navi Mumbai | III | 0.16 | Emerging hyperscale corridor |
| Pune | III | 0.16 | IT/data centre growth area |
| Hyderabad | II | 0.10 | Major IT hub, lowest seismic risk |
| Bangalore | II | 0.10 | Major IT hub |
| Delhi-NCR | IV | 0.24 | National capital, high seismic risk |
| Noida / Greater Noida | IV | 0.24 | Data centre development zone |
| Northeast India | V | 0.36 | Highest seismic risk |
| Parts of J&K, Himachal, Uttarakhand | V | 0.36 | Himalayan seismic belt |
| Kutch (Gujarat) | V | 0.36 | Post-2001 earthquake reclassification |

---

## 2. Importance Factor (I)

The importance factor accounts for the consequences of failure and the need for post-disaster functionality.

| Category | Importance Factor (I) | Examples |
|----------|----------------------|----------|
| Critical / Post-disaster facilities | 1.5 | Hospitals, fire stations, emergency communication centres, data centres housing essential/lifeline services, nuclear facilities |
| Important / Business continuity structures | 1.2 | Commercial buildings, industrial structures, multi-storey residential, data centres (general) |
| General / Standard occupancy | 1.0 | Standard residential buildings, ordinary occupancy |

**Data Centre Application:**
- Tier III/IV data centres housing critical national infrastructure should use I = 1.5.
- General commercial data centres typically use I = 1.2.
- The choice of I = 1.5 vs 1.2 increases the design base shear by 25%, with proportional impact on structural member sizing and foundation design.

---

## 3. Response Reduction Factor (R)

The response reduction factor accounts for the inherent overstrength, ductility, and redundancy of the structural system. Higher R values indicate greater ductility and energy dissipation capacity, allowing lower design forces.

### 3.1 R Values for Common Structural Systems (Table 9 of IS 1893:2016)

| Structural System | R Value |
|-------------------|---------|
| **RC Moment Resisting Frames** | |
| Ordinary Moment Resisting Frame (OMRF) | 3.0 |
| Special Moment Resisting Frame (SMRF) | 5.0 |
| **RC Shear Wall Systems** | |
| Ordinary shear wall | 3.0 |
| Ductile shear wall | 4.0 |
| **Dual Systems (Frame + Shear Wall)** | |
| OMRF + shear wall | 3.0 |
| SMRF + shear wall | 4.0 |
| OMRF + ductile shear wall | 4.5 |
| SMRF + ductile shear wall | 5.0 |
| **Steel Frames** | |
| Steel OMRF | 3.0 |
| Steel SMRF | 5.0 |
| Steel braced frame (concentric) | 4.0 |
| Steel braced frame (eccentric) | 5.0 |

**Note:** IS 1893:2016 specifies empirical R values based on the lateral force-resisting system type. The code does not explicitly account for storey height or geometric configuration in the R factor selection.

---

## 4. Soil Classification

IS 1893:2016 classifies foundation soil into three types based on Standard Penetration Test (SPT) N-values and soil characteristics. Soil type affects the shape of the design response spectrum.

| Soil Type | Description | SPT N-Value Range | Characteristics |
|-----------|-------------|-------------------|-----------------|
| Type I — Rock or Hard Soil | Rock, hard soil, stiff clay | N > 30 | Well-graded gravel or sand-gravel mixtures with or without clay binder; stiff to hard clays |
| Type II — Medium Soil | Medium stiff soil | 10 ≤ N ≤ 30 | Poorly graded sands; medium stiff clays; sand-clay mixtures |
| Type III — Soft Soil | Soft soil, loose sand | N < 10 | Soft to medium clays; poorly graded sands; loose fill; marine clays |

### 4.1 Spectral Acceleration Coefficient (Sa/g)

The spectral acceleration coefficient depends on the natural period of the structure (T) and soil type. Key plateau values for 5% damping:

| Soil Type | Sa/g Plateau Value | Plateau Period Range |
|-----------|--------------------|---------------------|
| Type I (Rock/Hard) | 2.5 | 0.10-0.40 s |
| Type II (Medium) | 2.5 | 0.10-0.55 s |
| Type III (Soft) | 2.5 | 0.10-0.67 s |

**Key difference:** While the plateau value is the same (2.5) for all soil types, the plateau extends to longer periods for softer soils, meaning taller/more flexible structures on soft soil experience higher spectral acceleration than the same structure on rock.

For periods beyond the plateau:
- Type I: Sa/g = 1.0/T (for T > 0.40 s)
- Type II: Sa/g = 1.36/T (for T > 0.55 s)
- Type III: Sa/g = 1.67/T (for T > 0.67 s)

---

## 5. Design Horizontal Seismic Coefficient

The design horizontal seismic coefficient (Ah) is the primary parameter for calculating the design base shear:

```
Ah = (Z x I x Sa/g) / (2 x R)
```

Where:
- Z = Zone factor (Table 3)
- I = Importance factor (Table 8)
- Sa/g = Spectral acceleration coefficient (depends on natural period T and soil type)
- R = Response reduction factor (Table 9)
- The factor of 2 in the denominator converts the zone factor from Maximum Considered Earthquake (MCE) to Design Basis Earthquake (DBE)

### 5.1 Example Calculations for Data Centres

**Example 1: Navi Mumbai Hyperscale Data Centre (Tier IV)**
- Zone III: Z = 0.16
- Critical facility: I = 1.5
- SMRF structure: R = 5.0
- Medium soil (Type II), T = 0.5 s: Sa/g = 2.5
- Ah = (0.16 x 1.5 x 2.5) / (2 x 5.0) = 0.06

**Example 2: Delhi-NCR Data Centre (Tier III)**
- Zone IV: Z = 0.24
- Important facility: I = 1.2
- SMRF structure: R = 5.0
- Soft soil (Type III), T = 0.6 s: Sa/g = 2.5
- Ah = (0.24 x 1.2 x 2.5) / (2 x 5.0) = 0.072

**Example 3: Hyderabad Data Centre (Tier III)**
- Zone II: Z = 0.10
- Important facility: I = 1.2
- SMRF structure: R = 5.0
- Rock (Type I), T = 0.4 s: Sa/g = 2.5
- Ah = (0.10 x 1.2 x 2.5) / (2 x 5.0) = 0.03

---

## 6. Seismic Design Requirements for Data Centre Infrastructure

### 6.1 Equipment Anchorage

| Item | Requirement |
|------|-------------|
| Rack anchorage | Bolted to floor slab or structural framing; design for Z x I acceleration |
| Battery racks | Seismic restraint per zone factor x importance factor product; cross-bracing required |
| UPS systems | Floor-mounted with seismic isolation or rigid anchorage |
| Generator sets | Spring-mounted with snubbers; seismic stops to limit displacement |
| Cooling towers | Vibration isolators with seismic restraints |
| Piping | Sway bracing at maximum 3 m intervals; flexible connections at building joints |

### 6.2 Raised Floor Systems

| Requirement | Specification |
|-------------|---------------|
| Bracing | Diagonal bracing at perimeter and every 3 m grid |
| Pedestal anchorage | Mechanically fastened to structural slab |
| Seismic joints | Flexible joints where raised floor crosses building expansion joints |
| Load rating | Must maintain structural integrity under combined gravity + seismic loading |

### 6.3 Structural System Selection

| Zone | Recommended System for Data Centres |
|------|-------------------------------------|
| Zone II | OMRF or SMRF acceptable; standard design |
| Zone III | SMRF recommended; ductile detailing required |
| Zone IV | SMRF mandatory; seismic base isolation recommended for Tier IV |
| Zone V | SMRF mandatory; base isolation strongly recommended; special detailing per IS 13920 |

---

## 7. Relevance to Data Centre EPC Projects

- **Site selection:** Zone factor directly impacts structural cost. Moving from Zone IV (Delhi, Z=0.24) to Zone II (Hyderabad, Z=0.10) reduces seismic design loads by 58%.
- **Importance factor choice (1.2 vs 1.5):** A 25% increase in design base shear translates to approximately 10-15% increase in structural steel/concrete quantities and cost. This must be agreed with the client during conceptual design.
- **Soil investigation:** Geotechnical investigation must determine soil type (I, II, or III) early in the project — this directly affects spectral acceleration and foundation design.
- **Equipment procurement:** All mechanical and electrical equipment specifications must include seismic certification to the applicable zone factor x importance factor product.
- **Raised floor coordination:** Seismic bracing of raised floor systems (per BICSI 002) must be designed in conjunction with IS 1893 requirements for the specific zone.
- **IS 1893:2016 vs IS 1893:2025:** A draft revision (2025) introduces Zone VI and revised response spectra. EPC projects should confirm which edition applies per the contract and local building authority requirements.

---

## Sources

- [InfraLens — IS 1893 Part 1:2016 PDF Seismic Design Criteria](https://infralens.in/code/IS-1893-Part-1-2016)
- [Bentley STAAD.Pro Help — IS 1893 (Part 1) 2016 Codes: Lateral Seismic Load](https://docs.bentley.com/LiveContent/web/STAAD.Pro%20Help-v14/en/STD_DEFINE_IS1893_2016.html)
- [IJERT — Analytical Comparison of IS 1893:2016 and IS 1893:2025](https://www.ijert.org/an-analytical-comparison-of-seismic-design-provisions-of-is-18932016-and-is-18932025-and-its-implications-on-reinforced-concrete-building-design)
- [ResearchGate — Provisions for Geotechnical Aspects and Soil Classification in IS-1893](https://www.researchgate.net/publication/264003652_Provisions_for_Geotechnical_Aspects_and_Soil_Classification_in_Indian_Seismic_Design_Code_IS-1893)
- [Civil Engineering Web — Criteria for SBC and Types of Soil as per IS 1893](https://www.civilengineeringweb.com/2023/03/criteria-for-sbc-types-of-soil-as-per-is1893.html)
- [CivilEra — Understanding Response Reduction Factor (R) in IS 1893](https://www.civilera.com/post/earthquake-load-is-1893-response-reduction-factor)
- [IJRASET — Computation of R Factor for SMRF and OMRF Frames](https://www.ijraset.com/research-paper/computation-of-r-factor-for-smrf-and-omrf-frame)
- [IIT Kanpur NICEE — Explanatory Examples on IS 1893 (PDF)](https://www.iitk.ac.in/nicee/IITGN-WB/EQ03.pdf)
- [Internet Archive — IS 1893 Part 1:2016 Full Standard](https://archive.org/details/gov.in.is.1893.1.2016)
