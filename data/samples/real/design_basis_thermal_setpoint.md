# Design Basis — Cooling Supply-Air Setpoint
_Project Helios DC-2 · Precision cooling · Rev A_
_Document DB-HELIOS-THERMAL · Issued for Tender_

This section governs the rack-inlet / supply-air temperature delivered by the
precision cooling units in the critical IT hall.

## 1. Thermal envelope

- **Supply-air temperature.** The cooling system shall maintain the rack-inlet
  air within the **ASHRAE TC 9.9 (2021, 5th ed.) Class A1 _recommended_
  envelope: 18 °C to 27 °C**. The design intent is continuous operation inside
  the *recommended* band, not merely the allowable band.
- **Humidity.** Per ASHRAE A1 recommended (−9 °C DP to 15 °C DP and 60% RH).
- **Redundancy.** N+1 at the hall level.

> Note for reviewers: ASHRAE A1 also defines an **allowable** range of 15–32 °C.
> Operating above 27 °C (but ≤ 32 °C) is *within allowable* and is an accepted
> efficiency strategy at many operators — so a supply setpoint between 27 °C and
> 32 °C is a genuine engineering **judgment call**, not a clear-cut
> non-conformance. This pair is deliberately ambiguous (see PROVENANCE.md).
