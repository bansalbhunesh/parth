# Design Basis — Intelligent Rack PDU (Critical IT Racks)
_Project Helios DC-2 · Rack power distribution · Rev A_
_Document DB-HELIOS-PDU · Issued for Tender_

This section governs the intelligent rack power distribution units (rPDUs) for
the critical IT racks. The governing cases are **billing-grade energy metering
at the outlet level** (per-tenant chargeback and stranded-capacity recovery)
and **remote outlet control** (per-device remote reboot without dispatching to
the hall). Metering accuracy requirements derive from **ISO/IEC 62053-21
(Class 1)**. A submittal providing less shall be recorded as a non-conformance.

## 1. Metering

- **Metering scope.** Energy metering at **inlet, branch/breaker, AND every
  individual outlet** (per-outlet kWh, V, A, kW, kVA, PF).
- **Metering accuracy.** Billing-grade **+/- 1%** energy metering per
  **ISO/IEC 62053-21 Class 1**.

## 2. Outlet control

- **Outlet switching.** Individually **switched (relay-controlled) outlets**
  for remote power-cycle of hung devices, with per-outlet on/off/reboot via
  the network interface.

## 3. Environment / mechanical

- **Operating temperature.** Continuous operation at >= **45 C** intake
  (hot-aisle containment service).
- **Form factor.** Zero-U vertical, 3-phase 400 V input.
- **Environmental sensors.** Support for plug-in temperature/humidity sensors.
