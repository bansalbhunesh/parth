# Design Basis — BMS Supervisory Network Controller
_Project Helios DC-2 · Building management system · Rev A_
_Document DB-HELIOS-BMSC · Issued for Tender_

This section governs the supervisory network controllers for the building
management system (one per plant zone). The governing case is **standalone
supervisory capability**: each controller must schedule, trend, alarm, and
route between field buses and the operator workstation over IP, and remain
autonomous if the head-end is lost. Requirements derive from the **BACnet
device profiles (ASHRAE 135 / BTL)**. A submittal providing less shall be
recorded as a non-conformance.

## 1. BACnet conformance

- **Device profile.** BTL-listed **B-BC (BACnet Building Controller)** —
  the field-programmable supervisory profile.
- **Transport.** Native **BACnet/IP** at the controller (not via an external
  router or gateway).

## 2. Supervisory functions (at the controller, head-end independent)

- **Scheduling** (BACnet Schedule/Calendar objects), **trending**
  (Trend Log objects), and **alarming** (intrinsic + algorithmic) resident
  in the controller.
- **Field-bus routing.** Integral routing BACnet/IP <-> MS/TP for downstream
  application controllers.
- **Programmability.** Fully field-programmable control logic.
