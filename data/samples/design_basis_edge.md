# DESIGN BASIS — EDGE DATA CENTRE / NETWORK EQUIPMENT ROOM
## UPS for Critical Network Load · Single-Phase · Issued for Tender (Rev B)

### 1. SCOPE

This design basis governs the uninterruptible power supply serving the critical
network and edge-compute load of a Tier-equivalent **edge data centre / network
equipment room** (single-phase, ≤ 6 kW critical load). The UPS shall protect
routers, switches, and edge-compute nodes through utility disturbances and short
outages until the standby generator assumes load or an orderly shutdown completes.

Where a vendor proposal differs from any requirement below, the proposal shall be
recorded as a deviation and is non-conforming unless approved in writing by the
Engineer. Efficiency, runtime, and power-factor claims shall be substantiated by
the manufacturer's published datasheet.

### 2. PERFORMANCE REQUIREMENTS

| Ref | Parameter | Requirement |
|-----|-----------|-------------|
| 2.1 | Topology | **Online double-conversion (VFI-SS-111).** Line-interactive and standby topologies are not acceptable. |
| 2.2 | Rated capacity | ≥ **6 kVA / 6 kW** continuous at the stated reference conditions |
| 2.3 | Output power factor | **≥ 0.9** (unity preferred) |
| 2.4 | Operating efficiency at 100% load | **≥ 96.0% in online (double-conversion) mode.** Efficiency achieved only in ECO/eco-mode shall NOT be accepted as evidence of compliance. |
| 2.5 | Battery autonomy at full rated load | **≥ 10 minutes** with internal/standard batteries, at end of design life |
| 2.6 | Input current THD | ≤ 5% |
| 2.7 | Availability / redundancy | **N+1** (parallel-capable, so one module can be serviced without dropping the network load) |
| 2.8 | Acoustic noise at 1 m | ≤ 55 dB(A) |
| 2.9 | Network management | SNMP-capable management card with remote shutdown |

### 3. NOTES TO TENDERER

- A single, non-parallel unit does **not** satisfy clause 2.7.
- Quote efficiency in **online mode**, not ECO mode (clause 2.4). Many compact
  UPS reach their headline efficiency only in ECO/line-interactive mode, which is
  not the operating mode required here.
- State battery autonomy at **full rated load**; runtimes quoted at 50% load or
  beginning-of-life only will be treated as non-conforming evidence.
