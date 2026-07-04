# Label Review Packet — ps4_external_v1 (v1.2)
_For an external technical reviewer. Judge only whether each **label** (the benchmark ground truth) is correct and well-evidenced. This packet contains no model output and no scores._

44 labels selected. Verdict options: `accept` / `accept_with_minor_edit` / `modify` / `reject` / `contested` / `needs_more_evidence`.

---

**Label ID:** P001-L01
**Pair ID:** pair_001
**System:** ups
**Label type:** positive_deviation
**Difficulty:** direct_value
**Component:** battery autonomy
**Parameter:** runtime_minutes

**Owner requirement (excerpt):**
> at least 10 minutes at full design load (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Rated battery runtime: 8 minutes (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 10 min
- Submitted value: 8 min
- Expected finding: Submitted UPS battery autonomy (8 min) is below the owner requirement (10 min).
- Severity: high
- Expected commissioning test: UPS battery autonomy discharge test (IST)
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P002-L01
**Pair ID:** pair_002
**System:** metering_power_quality
**Label type:** positive_deviation
**Difficulty:** direct_value
**Component:** input current THD
**Parameter:** input_thd_percent

**Owner requirement (excerpt):**
> shall not exceed 5 percent (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> input current THD: 8 percent (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 5%
- Submitted value: 8%
- Expected finding: Submitted input THD (8%) exceeds the 5% owner limit.
- Severity: medium
- Expected commissioning test: Power-quality / harmonic acceptance test
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P003-L01
**Pair ID:** pair_003
**System:** switchgear
**Label type:** positive_deviation
**Difficulty:** direct_value
**Component:** short-circuit withstand
**Parameter:** icw_ka

**Owner requirement (excerpt):**
> at least 65 kA for 1 second (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> short-circuit withstand: 50 kA — …*Team-authored submittal fixture.* ## 1. Ratings - Rated short-circuit withstand: **50 kA** for 1 s.… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 65 kA
- Submitted value: 50 kA
- Expected finding: Submitted short-circuit withstand (50 kA) is below the required 65 kA.
- Severity: high
- Expected commissioning test: Switchgear type-test verification / factory test review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P004-L01
**Pair ID:** pair_004
**System:** generator
**Label type:** positive_deviation
**Difficulty:** categorical_reasoning
**Component:** emissions tier
**Parameter:** epa_tier

**Owner requirement (excerpt):**
> EPA Tier 4 Final — …n intent.* ## 1. Emissions - Engine emissions shall meet **EPA Tier 4 Final** for new stationary CI engines.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> EPA Tier 2 — ….* ## 1. Certification - Engine emissions certification: **EPA Tier 2**.… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: EPA Tier 4
- Submitted value: EPA Tier 2
- Expected finding: Submitted emissions certification (EPA Tier 2) does not meet the required EPA Tier 4.
- Severity: high
- Expected commissioning test: Emissions compliance documentation review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P005-L01
**Pair ID:** pair_005
**System:** crac_crah
**Label type:** positive_deviation
**Difficulty:** unit_conversion
**Component:** supply airflow
**Parameter:** airflow_cfm

**Owner requirement (excerpt):**
> at least 2,500 CFM (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> supply airflow: 4,000 m³/h (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 2500 CFM
- Submitted value: 4000 m3/h
- Expected finding: Submitted 4,000 m³/h (~2,354 CFM) is below the required 2,500 CFM once converted.
- Severity: medium
- Expected commissioning test: Airflow / capacity acceptance test
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P006-L01
**Pair ID:** pair_006
**System:** generator
**Label type:** positive_deviation
**Difficulty:** derived_arithmetic
**Component:** on-site fuel autonomy
**Parameter:** fuel_hours

**Owner requirement (excerpt):**
> at least 48 hours of runtime at 100% load (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> 4,000 US gallons ... 103 GPH (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 48 h
- Submitted value: 38.8 h
- Expected finding: Derived on-site fuel autonomy (4,000 gal / 103 GPH = 38.8 h) is below the 48 h requirement.
- Severity: high
- Expected commissioning test: Fuel-endurance / load-bank test
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P007-L01
**Pair ID:** pair_007
**System:** battery
**Label type:** positive_deviation
**Difficulty:** derived_arithmetic
**Component:** fire-area li-ion energy
**Parameter:** fire_area_kwh

**Owner requirement (excerpt):**
> shall not exceed 600 kWh (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> 24 racks, each 26.5 kWh (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 600 kWh
- Submitted value: 636 kWh
- Expected finding: Aggregate li-ion energy (24 × 26.5 kWh = 636 kWh) exceeds the 600 kWh per-fire-area cap.
- Severity: high
- Expected commissioning test: Fire-area energy / NFPA 855 documentation review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P008-L01
**Pair ID:** pair_008
**System:** refrigerant
**Label type:** positive_deviation
**Difficulty:** domain_recall
**Component:** refrigerant GWP
**Parameter:** refrigerant_gwp

**Owner requirement (excerpt):**
> GWP shall be ≤ 750 (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Refrigerant charge: R-410A (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 750
- Submitted value: R-410A (GWP 2088)
- Expected finding: R-410A has a GWP of ~2,088, above the 750 owner limit (value not stated in the submittal).
- Severity: high
- Expected commissioning test: Refrigerant / F-Gas compliance review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P009-L01
**Pair ID:** pair_009
**System:** cabling
**Label type:** positive_deviation
**Difficulty:** categorical_reasoning
**Component:** plenum cable fire rating
**Parameter:** cable_fire_rating

**Owner requirement (excerpt):**
> shall be CMP (plenum) rated (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> cable fire rating: CMR (riser) (vendor_submittal.md §1)

**Benchmark label:**
- Required value: CMP
- Submitted value: CMR
- Expected finding: Provided CMR-rated cable does not meet the CMP (plenum) requirement for plenum pathways.
- Severity: medium
- Expected commissioning test: Cable listing / fire-rating documentation review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P010-L01
**Pair ID:** pair_010
**System:** ups
**Label type:** omission
**Difficulty:** omission_detection
**Component:** input THD
**Parameter:** input_thd_percent

**Owner requirement (excerpt):**
> shall be stated in the submittal — …lity - Input current THD shall not exceed **5 percent** and shall be stated in the submittal.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> available upon request — …red submittal fixture.* ## 1. Input - Input current THD: **available upon request**.… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 5%
- Submitted value: Not stated
- Expected finding: The submittal omits the required input THD value ('available upon request').
- Severity: medium
- Expected commissioning test: Power-quality documentation completeness check
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P011-L01
**Pair ID:** pair_011
**System:** switchgear
**Label type:** omission
**Difficulty:** omission_detection
**Component:** short-circuit withstand
**Parameter:** icw_ka

**Owner requirement (excerpt):**
> shall be stated and at least 65 kA / 1 s — ….* ## 1. Ratings - Assembly short-circuit withstand rating shall be stated and at least **65 kA / 1 s**.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> not included in this submission — …fixture.* ## 1. Ratings - Short-circuit withstand rating: not included in this submission.… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 65 kA
- Submitted value: Not stated
- Expected finding: The submittal does not state the required short-circuit withstand rating.
- Severity: high
- Expected commissioning test: Ratings documentation completeness check
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P012-L01
**Pair ID:** pair_012
**System:** ups
**Label type:** clean_negative
**Difficulty:** direct_value
**Component:** battery autonomy
**Parameter:** runtime_minutes

**Owner requirement (excerpt):**
> at least 10 minutes (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Rated battery runtime: 10 minutes (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 10 min
- Submitted value: 10 min
- Expected finding: No deviation — submitted autonomy meets the requirement.
- Severity: none
- Expected commissioning test: UPS battery autonomy discharge test
- Schedule impact category: commissioning_delay_risk
- Source basis: synthetic negative

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P013-L01
**Pair ID:** pair_013
**System:** crac_crah
**Label type:** clean_negative
**Difficulty:** categorical_reasoning
**Component:** cooling redundancy
**Parameter:** redundancy

**Owner requirement (excerpt):**
> N+1 redundant — …er's design intent.* ## 1. Redundancy - Cooling shall be **N+1 redundant** at design load.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> configuration: N+1 (vendor_submittal.md §1)

**Benchmark label:**
- Required value: N+1
- Submitted value: N+1
- Expected finding: No deviation — N+1 redundancy provided as required.
- Severity: none
- Expected commissioning test: Concurrent-maintainability / redundancy review
- Schedule impact category: commissioning_delay_risk
- Source basis: synthetic negative

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P014-L01
**Pair ID:** pair_014
**System:** refrigerant
**Label type:** clean_negative
**Difficulty:** domain_recall
**Component:** refrigerant GWP
**Parameter:** refrigerant_gwp

**Owner requirement (excerpt):**
> GWP shall be ≤ 750 (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> R-1234ze (GWP < 1) (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 750
- Submitted value: R-1234ze (GWP <1)
- Expected finding: No deviation — R-1234ze GWP is well below the 750 limit.
- Severity: none
- Expected commissioning test: Refrigerant / F-Gas compliance review
- Schedule impact category: commissioning_delay_risk
- Source basis: synthetic negative

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P015-L01
**Pair ID:** pair_015
**System:** crac_crah
**Label type:** ambiguous_contested
**Difficulty:** categorical_reasoning
**Component:** supply-air setpoint
**Parameter:** supply_air_temp_c

**Owner requirement (excerpt):**
> should not exceed 27 °C (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> supply-air setpoint: 30 °C (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 27 C recommended
- Submitted value: 30 C
- Expected finding: Contested: 30 °C is above the 27 °C recommended but within the A1 allowable band; a CxA could rule either way.
- Severity: info
- Expected commissioning test: Thermal set-point review (judgment call)
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P016-L01
**Pair ID:** pair_016
**System:** ups
**Label type:** adversarial_instruction
**Difficulty:** adversarial_noise
**Component:** battery autonomy
**Parameter:** runtime_minutes

**Owner requirement (excerpt):**
> at least 10 minutes (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Rated battery runtime: 6 minutes (vendor_submittal.md §2)

**Benchmark label:**
- Required value: 10 min
- Submitted value: 6 min
- Expected finding: Despite the embedded compliance instruction, the submitted 6-minute autonomy is below the 10-minute requirement and must be flagged.
- Severity: high
- Expected commissioning test: UPS battery autonomy discharge test
- Schedule impact category: commissioning_delay_risk
- Source basis: adversarial (team-authored)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P017-L01
**Pair ID:** pair_017
**System:** transformer
**Label type:** positive_deviation
**Difficulty:** categorical_reasoning
**Component:** harmonic rating
**Parameter:** k_factor

**Owner requirement (excerpt):**
> shall be K-13 (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Harmonic rating: K-1 (vendor_submittal.md §1)

**Benchmark label:**
- Required value: K-13
- Submitted value: K-1
- Expected finding: Provided K-1 transformer is not rated for the non-linear loads that require K-13.
- Severity: high
- Expected commissioning test: Transformer harmonic type-test review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P017-L02
**Pair ID:** pair_017
**System:** transformer
**Label type:** omission
**Difficulty:** omission_detection
**Component:** basic impulse level
**Parameter:** bil_kv

**Owner requirement (excerpt):**
> BIL shall be stated (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> (BIL not provided) (vendor_submittal.md §1)

**Benchmark label:**
- Required value: stated
- Submitted value: Not stated
- Expected finding: Submittal omits the required BIL rating.
- Severity: medium
- Expected commissioning test: Insulation coordination review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P017-L03
**Pair ID:** pair_017
**System:** transformer
**Label type:** clean_negative
**Difficulty:** categorical_reasoning
**Component:** vector group
**Parameter:** vector_group

**Owner requirement (excerpt):**
> Dyn11 — …3** for non-linear DC-hall loads. - Vector group shall be **Dyn11**. - Impedance shall be **6%**. - Insulation shall be **Cla… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Dyn11 — …## 1. Ratings - Harmonic rating: **K-1**. - Vector group: **Dyn11**. - Impedance: **6%**. - Insulation: **Class F**. - Rated… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: Dyn11
- Submitted value: Dyn11
- Expected finding: No deviation — Dyn11 as required.
- Severity: none
- Expected commissioning test: documentation / acceptance review
- Schedule impact category: commissioning_delay_risk
- Source basis: synthetic negative

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P017-L04
**Pair ID:** pair_017
**System:** transformer
**Label type:** clean_negative
**Difficulty:** direct_value
**Component:** impedance
**Parameter:** impedance_pct

**Owner requirement (excerpt):**
> 6% — …. - Vector group shall be **Dyn11**. - Impedance shall be **6%**. - Insulation shall be **Class F**. - Rated frequency sha… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> 6% — …rating: **K-1**. - Vector group: **Dyn11**. - Impedance: **6%**. - Insulation: **Class F**. - Rated frequency: **50 Hz**.… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 6%
- Submitted value: 6%
- Expected finding: No deviation — 6% as required.
- Severity: none
- Expected commissioning test: documentation / acceptance review
- Schedule impact category: commissioning_delay_risk
- Source basis: synthetic negative

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P018-L01
**Pair ID:** pair_018
**System:** chiller
**Label type:** positive_deviation
**Difficulty:** direct_value
**Component:** cooling capacity
**Parameter:** capacity_kw

**Owner requirement (excerpt):**
> at least 1000 kW (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Rated cooling capacity: 850 kW — …l chiller *Team-authored submittal fixture.* ## 1. Data - Rated cooling capacity: **850 kW**. - Plant configuration: **N** (no standby). - Refrigera… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 1000 kW
- Submitted value: 850 kW
- Expected finding: Rated capacity 850 kW is below the 1000 kW requirement.
- Severity: high
- Expected commissioning test: Chiller capacity acceptance test
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P018-L02
**Pair ID:** pair_018
**System:** chiller
**Label type:** positive_deviation
**Difficulty:** categorical_reasoning
**Component:** chiller redundancy
**Parameter:** redundancy

**Owner requirement (excerpt):**
> N+1 redundant (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> configuration: N (no standby) (vendor_submittal.md §1)

**Benchmark label:**
- Required value: N+1
- Submitted value: N
- Expected finding: Plant is N (no standby); N+1 is required.
- Severity: high
- Expected commissioning test: Redundancy / concurrent-maint review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P018-L03
**Pair ID:** pair_018
**System:** chiller
**Label type:** positive_deviation
**Difficulty:** domain_recall
**Component:** refrigerant GWP
**Parameter:** refrigerant_gwp

**Owner requirement (excerpt):**
> GWP shall be <= 750 (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Refrigerant: R-134a (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 750
- Submitted value: R-134a (GWP 1430)
- Expected finding: R-134a GWP (~1430) exceeds the 750 limit (value not stated in the submittal).
- Severity: high
- Expected commissioning test: Refrigerant / F-Gas compliance review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P018-L04
**Pair ID:** pair_018
**System:** chiller
**Label type:** omission
**Difficulty:** omission_detection
**Component:** performance test report
**Parameter:** test_report

**Owner requirement (excerpt):**
> performance test report shall be provided — …*. - Chilled-water flow shall be **>= 40 L/s**. - A factory performance test report shall be provided.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> (no test report) (vendor_submittal.md §1)

**Benchmark label:**
- Required value: provided
- Submitted value: Not stated
- Expected finding: Submittal omits the required factory performance test report.
- Severity: medium
- Expected commissioning test: Factory test documentation review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P018-L05
**Pair ID:** pair_018
**System:** chiller
**Label type:** clean_negative
**Difficulty:** direct_value
**Component:** supply voltage
**Parameter:** voltage_v

**Owner requirement (excerpt):**
> 415 V — …gerant GWP shall be **<= 750**. - Supply voltage shall be **415 V**. - Chilled-water flow shall be **>= 40 L/s**. - A factory… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> 415 V — …no standby). - Refrigerant: **R-134a**. - Supply voltage: **415 V**. - Chilled-water flow: **45 L/s**.… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 415 V
- Submitted value: 415 V
- Expected finding: No deviation — 415 V as required.
- Severity: none
- Expected commissioning test: documentation / acceptance review
- Schedule impact category: commissioning_delay_risk
- Source basis: synthetic negative

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P019-L03
**Pair ID:** pair_019
**System:** pdu_rpp
**Label type:** positive_deviation
**Difficulty:** table_or_layout
**Component:** branch B1 load
**Parameter:** branch_load_a

**Owner requirement (excerpt):**
> not exceed its 32 A rating (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> B1 | 32 A | 40 A — …edule | Branch | Rating | Connected load | |---|---|---| | B1 | 32 A | 40 A | | B2 | 32 A | 22 A | | B3 | 32 A | 18 A |… (vendor_submittal.md §2)

**Benchmark label:**
- Required value: 32 A
- Submitted value: 40 A
- Expected finding: Per the load schedule, branch B1 connected load (40 A) exceeds its 32 A rating.
- Severity: high
- Expected commissioning test: Branch-circuit load verification
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P019-L04
**Pair ID:** pair_019
**System:** pdu_rpp
**Label type:** clean_negative
**Difficulty:** categorical_reasoning
**Component:** form factor
**Parameter:** form_factor

**Owner requirement (excerpt):**
> Zero-U 3-phase 415 V — …ll not exceed its **32 A** rating. - Form factor shall be **Zero-U 3-phase 415 V**. - Environmental sensor ports shall be provided.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Zero-U 3-phase 415 V — …t-level only**. - Outlets: **unswitched**. - Form factor: **Zero-U 3-phase 415 V**. - Environmental sensor ports: **provided**. ## 2. Branc… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: Zero-U 3-phase 415 V
- Submitted value: Zero-U 3-phase 415 V
- Expected finding: No deviation — form factor as required.
- Severity: none
- Expected commissioning test: documentation / acceptance review
- Schedule impact category: commissioning_delay_risk
- Source basis: synthetic negative

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P020-L03
**Pair ID:** pair_020
**System:** bms
**Label type:** positive_deviation
**Difficulty:** table_or_layout
**Component:** Modbus support
**Parameter:** modbus_support

**Owner requirement (excerpt):**
> both Modbus and BACnet — …nsport shall be **BACnet/IP**. - Controller shall support **both Modbus and BACnet**. - Minimum **28** hardware points. - Supply shall be **24… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Modbus | No — …trix | Protocol | Supported | |---|---| | BACnet | Yes | | Modbus | No |… (vendor_submittal.md §2)

**Benchmark label:**
- Required value: supported
- Submitted value: not supported
- Expected finding: The protocol matrix shows Modbus unsupported; both Modbus and BACnet are required.
- Severity: medium
- Expected commissioning test: Protocol interoperability review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P020-L04
**Pair ID:** pair_020
**System:** bms
**Label type:** clean_negative
**Difficulty:** direct_value
**Component:** point count
**Parameter:** points

**Owner requirement (excerpt):**
> 28 — …oller shall support **both Modbus and BACnet**. - Minimum **28** hardware points. - Supply shall be **24 V dc**.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> 28 — …-AAC**. - Transport: **BACnet MS/TP**. - Hardware points: **28**. - Supply: **24 V dc**. ## 2. Protocol support matrix |… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 28
- Submitted value: 28
- Expected finding: No deviation — 28 points as required.
- Severity: none
- Expected commissioning test: documentation / acceptance review
- Schedule impact category: commissioning_delay_risk
- Source basis: synthetic negative

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P021-L01
**Pair ID:** pair_021
**System:** fire_suppression
**Label type:** positive_deviation
**Difficulty:** domain_recall
**Component:** agent GWP
**Parameter:** agent_gwp

**Owner requirement (excerpt):**
> GWP shall be <= 750 (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Agent: FM-200 (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 750
- Submitted value: FM-200 (GWP 3220)
- Expected finding: FM-200 (HFC-227ea) GWP (~3220) far exceeds the 750 limit.
- Severity: high
- Expected commissioning test: Agent / F-Gas compliance review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P022-L01
**Pair ID:** pair_022
**System:** ats_sts
**Label type:** positive_deviation
**Difficulty:** unit_conversion
**Component:** transfer time
**Parameter:** transfer_time

**Owner requirement (excerpt):**
> <= 100 ms — …design intent.* ## 1. Transfer - Transfer time shall be **<= 100 ms**. - Withstand/close-on rating shall be **>= 65 kA**. - Swi… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Transfer time: 4 s (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 100 ms
- Submitted value: 4 s
- Expected finding: Transfer time 4 s (4000 ms) far exceeds the 100 ms requirement.
- Severity: high
- Expected commissioning test: Transfer-time acceptance test
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P023-L02
**Pair ID:** pair_023
**System:** cooling_tower
**Label type:** positive_deviation
**Difficulty:** table_or_layout
**Component:** approach temperature
**Parameter:** approach_c

**Owner requirement (excerpt):**
> <= 3 C — …be at least **5000 kW**. - Approach temperature shall be **<= 3 C**. - Drift shall be **<= 0.001%**. - Fans shall be **EC var… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Approach temperature: 5 C (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 3 C
- Submitted value: 5 C
- Expected finding: Approach temperature 5 C exceeds the 3 C requirement.
- Severity: medium
- Expected commissioning test: Approach-temperature test
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P026-L01
**Pair ID:** pair_026
**System:** generator
**Label type:** adversarial_instruction
**Difficulty:** adversarial_noise
**Component:** start time
**Parameter:** start_time_sec

**Owner requirement (excerpt):**
> <= 10 s — …* ## 1. Start & rating - Start/accept-load time shall be **<= 10 s**. - Fuel shall be **diesel**. - Rated power shall be **200… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Start time: 30 s (vendor_submittal.md §2)

**Benchmark label:**
- Required value: 10 s
- Submitted value: 30 s
- Expected finding: Despite the note to ignore mismatches, the 30 s start time exceeds the 10 s requirement.
- Severity: high
- Expected commissioning test: Start/load-acceptance test
- Schedule impact category: commissioning_delay_risk
- Source basis: adversarial (team-authored)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P029-L01
**Pair ID:** pair_029
**System:** refrigerant
**Label type:** positive_deviation
**Difficulty:** domain_recall
**Component:** refrigerant GWP
**Parameter:** refrigerant_gwp

**Owner requirement (excerpt):**
> GWP shall be <= 750 (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Refrigerant: R-407C (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 750
- Submitted value: R-407C (GWP 1774)
- Expected finding: R-407C GWP (~1774) exceeds the 750 limit (value not stated).
- Severity: high
- Expected commissioning test: Refrigerant compliance review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P036-L01
**Pair ID:** pair_036
**System:** metering_power_quality
**Label type:** positive_deviation
**Difficulty:** adversarial_noise
**Component:** input THD (current)
**Parameter:** input_thd_percent

**Owner requirement (excerpt):**
> <= 5 percent — …owner's design intent.* ## 1. Input - Input THD shall be **<= 5 percent**. - Displacement power factor shall be **>= 0.99**.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Current measured Input THD: 8 percent — …## 1. Data - Legacy note (2019): Input THD **3 percent**. - Current measured Input THD: **8 percent**. - Displacement power factor: **0.99**.… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 5 percent
- Submitted value: 8 percent
- Expected finding: The current measured THD (8%) governs over the legacy 3% note and exceeds the 5% limit.
- Severity: medium
- Expected commissioning test: Power-quality acceptance test
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P039-L01
**Pair ID:** pair_039
**System:** ups
**Label type:** ocr_extraction_case
**Difficulty:** scanned_or_image
**Component:** battery autonomy
**Parameter:** runtime_minutes

**Owner requirement (excerpt):**
> >= 10 minutes — …intent.* ## 1. Requirements - Battery autonomy shall be **>= 10 minutes**. - Online efficiency shall be **>= 96 percent**.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):** *(vendor submittal is provided as an image: `pair_context/`)*
> Battery runtime: 8 minutes (vendor_submittal.png image)

**Benchmark label:**
- Required value: 10 minutes
- Submitted value: 8 minutes
- Expected finding: In the scanned table, battery runtime (8 min) is below the 10-min requirement.
- Severity: high
- Expected commissioning test: UPS autonomy discharge test
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P040-L01
**Pair ID:** pair_040
**System:** pdu_rpp
**Label type:** ocr_extraction_case
**Difficulty:** scanned_or_image
**Component:** branch B1 load
**Parameter:** branch_load_a

**Owner requirement (excerpt):**
> not exceed rating — …ements - Branch circuits are **32 A**; connected load shall not exceed rating. - Form factor shall be **Zero-U 3-phase**.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):** *(vendor submittal is provided as an image: `pair_context/`)*
> Branch B1 ... Load 40A (vendor_submittal.png image)

**Benchmark label:**
- Required value: 32 A
- Submitted value: 40 A
- Expected finding: In the scanned schedule, branch B1 load (40 A) exceeds its 32 A rating.
- Severity: high
- Expected commissioning test: Branch-circuit load verification
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P041-L01
**Pair ID:** pair_041
**System:** switchgear
**Label type:** ocr_extraction_case
**Difficulty:** scanned_or_image
**Component:** short-circuit withstand
**Parameter:** icw_ka

**Owner requirement (excerpt):**
> >= 65 kA / 1 s — ….* ## 1. Requirements - Short-circuit withstand shall be **>= 65 kA / 1 s**. - Internal separation shall be **Form 4b**.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):** *(vendor submittal is provided as an image: `pair_context/`)*
> Icw: 50 kA / 1 s (vendor_submittal.png image)

**Benchmark label:**
- Required value: 65 kA
- Submitted value: 50 kA
- Expected finding: In the scanned nameplate, Icw is 50 kA, below the 65 kA requirement.
- Severity: high
- Expected commissioning test: Switchgear type-test review
- Schedule impact category: commissioning_delay_risk
- Source basis: team-authored (owner design basis)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P044-L01
**Pair ID:** pair_044
**System:** generator
**Label type:** positive_deviation
**Difficulty:** categorical_reasoning
**Component:** emissions tier
**Parameter:** epa_tier

**Owner requirement (excerpt):**
> EPA Tier 4 — …s design intent.* ## 1. Emissions - Emissions shall meet **EPA Tier 4** for new stationary CI engines. - Rated voltage shall be *… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> EPA Tier 2 — …60 Subpart IIII.* ## 1. Data - Emissions certification: **EPA Tier 2**. - Rated voltage: **415 V**.… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: EPA Tier 4
- Submitted value: EPA Tier 2
- Expected finding: EPA Tier 2 does not meet the Tier 4 requirement (40 CFR 60 Subpart IIII).
- Severity: high
- Expected commissioning test: Emissions compliance review
- Schedule impact category: commissioning_delay_risk
- Source basis: primary-source-derived (public product value)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P044-L02
**Pair ID:** pair_044
**System:** generator
**Label type:** clean_negative
**Difficulty:** direct_value
**Component:** rated voltage
**Parameter:** voltage_v

**Owner requirement (excerpt):**
> 415 V — …* for new stationary CI engines. - Rated voltage shall be **415 V**.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> 415 V — …Emissions certification: **EPA Tier 2**. - Rated voltage: **415 V**.… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 415 V
- Submitted value: 415 V
- Expected finding: No deviation — 415 V as required.
- Severity: none
- Expected commissioning test: documentation / acceptance review
- Schedule impact category: commissioning_delay_risk
- Source basis: synthetic negative

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P045-L01
**Pair ID:** pair_045
**System:** refrigerant
**Label type:** positive_deviation
**Difficulty:** domain_recall
**Component:** refrigerant GWP
**Parameter:** refrigerant_gwp

**Owner requirement (excerpt):**
> GWP shall be <= 750 (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> Refrigerant: R-410A (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 750
- Submitted value: R-410A (GWP 2088)
- Expected finding: R-410A GWP (2088, IPCC AR4) exceeds the 750 limit.
- Severity: high
- Expected commissioning test: Refrigerant / F-Gas compliance review
- Schedule impact category: commissioning_delay_risk
- Source basis: primary-source-derived (public product value)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P045-L02
**Pair ID:** pair_045
**System:** refrigerant
**Label type:** clean_negative
**Difficulty:** categorical_reasoning
**Component:** leak detection
**Parameter:** leak_detection

**Owner requirement (excerpt):**
> provided — …** (EU F-Gas alignment). - A leak-detection system shall be provided.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> provided — …## 1. Data - Refrigerant: **R-410A**. - Leak-detection: **provided**.… (vendor_submittal.md §1)

**Benchmark label:**
- Required value: provided
- Submitted value: provided
- Expected finding: No deviation — leak detection provided.
- Severity: none
- Expected commissioning test: documentation / acceptance review
- Schedule impact category: commissioning_delay_risk
- Source basis: synthetic negative

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P051-L01
**Pair ID:** pair_051
**System:** crac_crah
**Label type:** ambiguous_contested
**Difficulty:** categorical_reasoning
**Component:** supply-air setpoint
**Parameter:** supply_air_temp_c

**Owner requirement (excerpt):**
> should not exceed 27 C (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> setpoint: 30 C (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 27 C recommended
- Submitted value: 30 C
- Expected finding: Contested: 30 C is above the ASHRAE A1 recommended 27 C but within the allowable band; a CxA could rule either way.
- Severity: info
- Expected commissioning test: Thermal set-point review (judgment call)
- Schedule impact category: commissioning_delay_risk
- Source basis: primary-source-derived (public product value)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:

---

**Label ID:** P052-L01
**Pair ID:** pair_052
**System:** pdu_rpp
**Label type:** positive_deviation
**Difficulty:** derived_arithmetic
**Component:** branch B1 total load
**Parameter:** branch_load_a

**Owner requirement (excerpt):**
> not exceed its rating — …capacity - Each **32 A** branch total connected load shall not exceed its rating. - Form factor shall be **Zero-U 3-phase**.… (owner_requirement.md §1)

**Vendor/submittal (excerpt):**
> C13-1 16 A; C13-2 14 A; C13-3 12 A (vendor_submittal.md §1)

**Benchmark label:**
- Required value: 32 A
- Submitted value: 42 A
- Expected finding: Summed B1 outlet load (16+14+12 = 42 A) exceeds the 32 A branch rating.
- Severity: high
- Expected commissioning test: Branch-circuit load verification
- Schedule impact category: commissioning_delay_risk
- Source basis: primary-source-derived (team-authored from public values)

**Reviewer questions:**
1. Is this label valid? accept / modify / reject / contested / needs_more_evidence
2. Is the evidence enough?
3. Is the required value clear?
4. Is the submitted value clear?
5. Is the expected finding too broad or too narrow?
6. Is this actually a clean negative or a positive deviation?
7. Any missing related issue in the same pair?
8. Notes:
