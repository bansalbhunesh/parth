# SECTION 26 33 53 — STATIC UNINTERRUPTIBLE POWER SUPPLY
## Project Helios Data Centre — Issued for Construction (Rev C)

### 1. GENERAL

This section governs the supply, installation, testing and commissioning of the
static UPS system serving the critical IT load of the Helios facility, a
concurrently-maintainable, fault-tolerant data centre classified to Uptime
Institute Tier IV. The UPS subsystem shall comply with this design basis and
with IEC 62040 and NFPA 70 as applicable.

### 2. PERFORMANCE REQUIREMENTS

The Contractor shall provide a double-conversion (VFI-SS-111) UPS system meeting
the following minimum performance criteria. Where a vendor proposal differs from
these values, the proposal shall be treated as non-conforming unless a formal
deviation is approved in writing by the Engineer.

| Ref | Parameter | Requirement |
|-----|-----------|-------------|
| 2.1 | System configuration | Distributed redundant, **2N** across two independent power paths |
| 2.2 | Module rated power | 1000 kW per module, minimum |
| 2.3 | Battery autonomy at full load | **Not less than 10 minutes** to the design fault-clearing point |
| 2.4 | Double-conversion efficiency at 100% load | **≥ 96.0%** |
| 2.5 | Input THDi at full load | ≤ 3% |
| 2.6 | Acoustic noise at 1 m | ≤ 72 dB(A) |

### 3. REDUNDANCY AND FAULT TOLERANCE

The UPS system shall be arranged so that any single module, static switch, or
distribution path may be removed from service for maintenance without dropping
the critical load — consistent with the Tier IV concurrent-maintainability and
fault-tolerance objectives. A 2N topology is mandatory; N+1 arrangements do not
satisfy this requirement.

### 4. BATTERY

The battery shall be sized for the autonomy specified in clause 2.3 at end of
design life (10 years), at the minimum design temperature, with one string out
of service. Runtime quoted at beginning of life only shall not be accepted as
evidence of compliance.
