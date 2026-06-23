# ASHRAE TC 9.9 — Detailed Technical Reference

**Standard:** ASHRAE TC 9.9 — Thermal Guidelines for Data Processing Environments
**Version:** 5th Edition (2021)
**Issuing Body:** ASHRAE Technical Committee 9.9 (Mission Critical Facilities, Data Centers, Technology Spaces and Electronic Equipment)
**Scope:** Defines recommended and allowable environmental envelopes (temperature, humidity, altitude) for air-cooled and liquid-cooled IT equipment in data centres. Measurements are taken at server air inlet, not room ambient.

---

## 1. Air-Cooled Equipment Classes — Allowable Envelopes

### 1.1 Temperature Ranges (Dry-Bulb, Measured at Server Inlet)

| Class | Allowable Low | Allowable High | Typical Equipment |
|-------|--------------|----------------|-------------------|
| A1 | 15 C (59 F) | 32 C (89.6 F) | Enterprise servers, mission-critical storage |
| A2 | 10 C (50 F) | 35 C (95 F) | Volume servers, rack-mount, standard IT |
| A3 | 5 C (41 F) | 40 C (104 F) | Extended temperature — economiser-friendly |
| A4 | 5 C (41 F) | 45 C (113 F) | Maximum flexibility — free-air cooling capable |

### 1.2 Humidity Ranges (Allowable)

| Class | Minimum Humidity | Maximum Relative Humidity | Maximum Dew Point |
|-------|-----------------|--------------------------|-------------------|
| A1 | Higher of -12 C dew point or 8% RH | 80% RH | 17 C DP |
| A2 | Higher of -12 C dew point or 8% RH | 80% RH | 21 C DP |
| A3 | Higher of -12 C dew point or 8% RH | 85% RH | 24 C DP |
| A4 | Higher of -12 C dew point or 8% RH | 90% RH | 24 C DP |

### 1.3 Altitude Limits (Allowable)

| Class | Maximum Altitude |
|-------|-----------------|
| A1 | 3,050 m (10,000 ft) |
| A2 | 3,050 m (10,000 ft) |
| A3 | 3,050 m (10,000 ft) |
| A4 | 3,050 m (10,000 ft) |

**Note:** Operation above 3,050 m requires consultation with the IT equipment supplier for each specific piece of equipment. Reduced air density at altitude affects cooling capacity and may require derating.

---

## 2. Recommended Envelope (All A-Classes)

The recommended envelope applies to ALL classes (A1 through A4) and represents the range for optimal equipment reliability and energy efficiency.

| Parameter | Recommended Range |
|-----------|-------------------|
| Dry-bulb temperature | 18-27 C (64.4-80.6 F) |
| Dew point (low) | -9 C DP (approximately equivalent to 20% RH at 25 C) |
| Dew point (high) | 15 C DP |
| Maximum relative humidity | 60% RH |
| Minimum relative humidity | Higher of -9 C dew point or 8% RH |

### 2.1 Recommended vs Allowable — Key Distinction

- **Recommended:** The operating range that provides the best balance of equipment reliability, energy efficiency, and operational cost. Equipment manufacturers typically provide full warranty coverage within this range.
- **Allowable:** The wider range within which equipment is designed to function. Operating in the allowable-but-not-recommended zone may increase failure rates, reduce equipment life, or void certain warranty terms. The A2 allowable range often supports reliable operation even if the OEM warranty specifies A1.

---

## 3. Rate of Change Limits

| Parameter | Limit |
|-----------|-------|
| Recommended rate of change | Maximum 5 C per hour at server inlet |
| Rationale | Rapid temperature changes risk condensation on cold surfaces (chilled water piping, cold aisle barriers) and thermal stress on electronic components |
| ASHRAE guidance | Temperature change rate of no more than 5 C per 20-minute period (equivalent to 15 C/hr maximum, but 5 C/hr recommended for sustained operations) |

---

## 4. Moisture and Corrosion Considerations

| Parameter | Guidance |
|-----------|----------|
| Corrosion risk threshold | Above 70% RH, pollutant-driven corrosion risk increases significantly |
| ESD risk threshold | Below -9 C dew point (approximately 20% RH at 25 C), electrostatic discharge risk increases |
| Gaseous contamination | ASHRAE TC 9.9 references ANSI/ISA-71.04 severity level G1 for data centre environments |
| Condensation prevention | Dew point upper limits ensure chilled water piping and cold aisle surfaces do not develop condensation |

---

## 5. Liquid Cooling Classes

The 5th edition (2021) expanded liquid cooling guidance with updated water temperature classes.

### 5.1 Original W-Classes (Pre-2022)

| Class | Facility Water Supply Temperature Range |
|-------|----------------------------------------|
| W1 | 2-17 C |
| W2 | 2-27 C |
| W3 | 2-32 C |
| W4 | 2-45 C |
| W5 | Greater than 45 C |

### 5.2 Updated Classes (2022 Nomenclature)

| Class | Maximum Allowable Supply Fluid Temperature | Notes |
|-------|-------------------------------------------|-------|
| W17 | 17 C | Chilled water — traditional cooling |
| W27 | 27 C | Moderate — some economiser use possible |
| W32 | 32 C | Warm water — significant economiser potential |
| W40 | 40 C | New class — heat recovery optimised |
| W45 | 45 C | Hot water — maximum heat reuse potential |
| W+ | Greater than 45 C | Extended range for specialised applications |

**Note on W40:** This class was added in response to growing interest in heat recovery and reuse from data centres, with several manufacturers designing liquid-cooled solutions that operate around 40 C inlet water temperature.

### 5.3 H1 Class (5th Edition Addition)

The 5th edition introduced the H1 class for hybrid air/liquid cooled environments, expanding the liquid cooling envelope to accommodate modern high-density GPU/AI workloads.

---

## 6. Summary Psychrometric Chart Reference Points

| Boundary | A1 | A2 | A3 | A4 | Recommended |
|----------|-----|-----|-----|-----|-------------|
| Dry-bulb low | 15 C | 10 C | 5 C | 5 C | 18 C |
| Dry-bulb high | 32 C | 35 C | 40 C | 45 C | 27 C |
| DP low | -12 C | -12 C | -12 C | -12 C | -9 C |
| DP high | 17 C | 21 C | 24 C | 24 C | 15 C |
| RH max | 80% | 80% | 85% | 90% | 60% |
| RH min | 8% | 8% | 8% | 8% | 8% |

---

## 7. Relevance to Data Centre EPC Projects

- **HVAC design basis:** Class A1 recommended envelope (18-27 C inlet, 60% RH max) is the default HVAC design criterion for enterprise data centres in India.
- **Economiser feasibility:** Classes A2-A4 enable direct or indirect air-side economisation in Indian climates. A2 (up to 35 C allowable) is practical for most of India except peak summer in northern plains.
- **Liquid cooling for AI/HPC:** W32 and W40 classes are the design basis for modern GPU clusters. Warm water (W40) enables heat recovery for district heating or process use.
- **Humidity control in India:** Coastal sites (Mumbai, Chennai) require active dehumidification to stay below 60% RH recommended; arid sites (Rajasthan) may need humidification to stay above -9 C dew point.
- **Altitude considerations:** Sites above 1,000 m (Bangalore at ~920 m is borderline) may need cooling capacity derating calculations.
- **Rate of change monitoring:** BMS should alarm if inlet temperature changes exceed 5 C/hr — important during cooling system transitions and economiser mode changeovers.

---

## Sources

- [CKY — ASHRAE TC 9.9 Thermal Guidelines (5th Ed.) A1-A4 Limits](https://www.cky.com.tw/en/insights/ashrae-tc9-datacenter-thermal-guidelines)
- [Envigilance — ASHRAE TC 9.9: Data Center Thermal Guide 2026](https://envigilance.com/compliance/ashrae-tc-9-9/)
- [Alliance Chemical — ASHRAE TC 9.9 Thermal Guidelines for AI Data Center Cooling](https://alliancechemical.com/blogs/articles/ashrae-tc-9-9-thermal-guidelines-ai-data-center-cooling)
- [ASHRAE — 2021 Equipment Thermal Guidelines Reference Card (PDF)](https://www.ashrae.org/file%20library/technical%20resources/bookstore/supplemental%20files/therm-gdlns-5th-r-e-refcard.pdf)
- [Uptime Institute Journal — New ASHRAE Guidelines Challenge Efficiency Drive](https://journal.uptimeinstitute.com/new-ashrae-guidelines-challenge-efficiency-drive/)
- [Upsite Technologies — Difference Between Recommended and Allowable Limits (Part 4)](https://www.upsite.com/blog/what-is-the-difference-between-ashraes-recommended-and-allowable-data-center-environmental-limits-part-4/)
- [Upsite Technologies — Major Changes to ASHRAE 5th Edition: Liquid Cooling Updates](https://www.upsite.com/blog/major-changes-to-ashraes-fifth-edition-of-thermal-guidelines-part-3-liquid-cooling-chapter-updates/)
- [CIBSE Journal — Module 254: Liquid Cooling in Data Centre Applications](https://www.cibsejournal.com/cpd/modules/2025-09-lcdca/)
- [TechTarget — Data Center Temperature and Humidity Guidelines](https://www.techtarget.com/searchdatacenter/tip/Data-center-temperature-and-humidity-guidelines)
- [ASHRAE Journal (May 2022) — Data Center Thermal Guidelines Air-Cooled Evolution (PDF)](https://attom.tech/wp-content/uploads/2023/10/ASHRAE%E2%80%99s-Data-Center-Thermal-Guidelines-Air-cooled-Evolution.pdf)
