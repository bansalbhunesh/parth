export const EXAMPLE_SPEC = `# Design Basis: UPS System
- **UPS-02** — battery runtime min: shall be **10 min** (ref: UPTIME-TIER4; clause DB-4.3)
- **UPS-02** — redundancy: shall be **2N topology** (ref: UPTIME-TIER4; clause DB-4.1)
- **UPS-02** — efficiency pct: shall be **96 %** (ref: DESIGN-BASIS; clause DB-4.5)`;

export const EXAMPLE_SUBMITTAL = `# Vendor Submittal: UPS System
- **UPS-02** — battery runtime min: **7 min** (vendor datasheet)
- **UPS-02** — redundancy: **2N topology** (vendor datasheet)
- **UPS-02** — efficiency pct: **93 %** (vendor datasheet)`;

// A realistic design basis + vendor datasheet written in natural prose + tables
// (nothing like the structured corpus). Proves the reasoning generalises to a
// document a vendor would actually send. Buried deviations: redundancy (2N
// required vs N+1 offered) and battery autonomy (10 min EoL required vs 8 min
// BoL offered). Compliant rows (efficiency, THD, noise) must NOT be flagged.
export const REAL_SPEC = `SECTION 26 33 53 — STATIC UPS · Project Helios (Tier IV) · Issued for Construction

2. PERFORMANCE REQUIREMENTS
The Contractor shall provide a double-conversion UPS meeting these minimums.
A proposal differing from these values is non-conforming unless a formal
deviation is approved in writing.

  2.1 System configuration ......... Distributed redundant, 2N across two paths
  2.2 Module rated power ........... 1000 kW per module, minimum
  2.3 Battery autonomy at full load  Not less than 10 minutes, at END OF LIFE,
                                     minimum design temperature, one string out
  2.4 Efficiency at 100% load ...... >= 96.0%
  2.5 Input THDi at full load ...... <= 3%
  2.6 Acoustic noise at 1 m ........ <= 72 dB(A)

3. REDUNDANCY
Any single module, static switch or path must be removable for maintenance
without dropping the critical load. A 2N topology is mandatory; N+1 does not
satisfy this requirement. Runtime quoted at beginning of life only shall not
be accepted as evidence of compliance.`;

export const REAL_SUBMITTAL = `TECHNICAL SUBMITTAL — PowerGuard ePX-1000 UPS
Submitted by Apex Critical Power · Submittal APX-EL-0241 · For Approval

The ePX-1000 is a field-proven transformer-free double-conversion system trusted
by leading hyperscale operators.

1. System Overview
Modular UPS units arranged in an N+1 redundant configuration on each power bus,
delivering excellent availability while optimising capital cost for the client.

2. Guaranteed Technical Particulars
  2.1 Topology ......................... Double conversion (VFI-SS-111)
  2.2 Module rated active power ........ 1000 kW
  2.3 System redundancy (per bus) ...... N+1
  2.4 Battery autonomy at full load .... 8 minutes (VRLA, beginning of life @ 25C)
  2.5 Online efficiency at 100% load ... 96.5%
  2.6 Input current THD ................ < 3%
  2.7 Audible noise at 1 m ............. 71 dB(A)

4. Compliance Statement
Apex Critical Power confirms the ePX-1000 meets or exceeds all applicable
performance requirements and is offered as fully compliant with the project
specification.`;

// Clean-negative demo: a submittal that MEETS or EXCEEDS every requirement in
// REAL_SPEC (2N, 1000 kW, 10 min EoL autonomy, >=96% eff, THD <=3%, <=72 dB).
// The correct answer is ZERO deviations — it demonstrates the low false-alert
// behaviour the benchmark measures (0 false alerts on 64 clean-negative controls),
// not just the ability to find faults.
export const CLEAN_SUBMITTAL = `TECHNICAL SUBMITTAL — TruePower DCX-1000 UPS
Submitted by Meridian Power Systems · Submittal MPS-EL-0117 · For Approval

1. System Overview
Modular double-conversion UPS arranged in a full 2N configuration across two
independent power paths. Any single module, static switch or path can be removed
for maintenance without dropping the critical load.

2. Guaranteed Technical Particulars
  2.1 Topology ......................... Double conversion (VFI-SS-111)
  2.2 Module rated active power ........ 1000 kW
  2.3 System redundancy ................ 2N (two independent paths)
  2.4 Battery autonomy at full load .... 11 minutes at END OF LIFE, minimum
                                         design temperature, one string out
  2.5 Online efficiency at 100% load ... 96.4%
  2.6 Input current THD ................ 2.7%
  2.7 Audible noise at 1 m ............. 70 dB(A)

3. Compliance Statement
Meridian confirms the DCX-1000 meets or exceeds every performance requirement in
Section 26 33 53, including the 2N topology and end-of-life autonomy provisions.`;
