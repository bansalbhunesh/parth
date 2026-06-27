# Design Basis — Critical Power & Standby Generation
_Project Helios DC-2 · Uptime Tier IV · US (EPA-regulated) site_
_Document DB-HELIOS-2 · Rev A · Issued for Tender_

This section governs the static UPS modules and the standby diesel generating
set serving the critical load. Where a vendor proposal differs from any
requirement below, it shall be recorded as a non-conformance and resolved
before equipment release. Requirements derive from the governing standards
cited; vendor economy modes and optional accessories are not credited toward a
requirement unless explicitly stated.

## 1. Static UPS (per module)

- **Battery autonomy.** The static UPS shall provide a minimum battery autonomy
  of **10 minutes at full rated load**, sufficient to ride through utility loss
  and confirm generator acceptance (Uptime Tier IV stored-energy practice).
- **Conversion efficiency.** Unit efficiency in continuous **online
  double-conversion** mode shall be at least **96 percent** at full load.
  Economy / ECO operating modes shall **not** be credited toward this
  requirement: they introduce transfer time and reduced power conditioning.
- **Input current distortion.** Input current total harmonic distortion (THD)
  shall not exceed **5 percent** at full load (IEEE 519).
- **Output power factor.** Rated output power factor shall be at least **0.9**.

## 2. Standby Diesel Generator

- **Start time.** The set shall start and accept the design block load within
  **10 seconds** of a utility-failure signal (NFPA 110, Type 10, Level 1).
- **Engine emissions.** The engine shall be certified to **EPA Tier 4** for new
  stationary compression-ignition engines at this site (EPA 40 CFR Part 60).
- **On-site fuel.** Usable on-site fuel shall provide at least **48 hours** of
  runtime at full load.
