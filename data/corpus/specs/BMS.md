# Project Meghdoot — Design Basis: Building Management & EPMS
_System: BMS · Uptime Tier IV · 40 MW_
_Client: Meghdoot Digital Infrastructure Pvt. Ltd._
_EPC: Patel-Larsen JV_

## Overview

The BMS/EPMS shall provide complete visibility of all critical infrastructure systems with a comprehensive alarm point list. The critical alarm set SHALL include, at minimum: power failure, generator status, UPS alarms, temperature exceedance, humidity exceedance, leak detection, fire panel interface, and security breach. Omission of any critical alarm point is a non-conformance.

## Requirements

- **BMS** — critical alarm points: shall be **complete set** (ref: DESIGN-BASIS; clause DB-9.5)
- **BMS** — monitoring redundancy: shall be **dual topology** (ref: UPTIME-TIER4; clause DB-9.1)
- **BMS** — protocol: shall be **BACnet_IP standard** (ref: DESIGN-BASIS; clause DB-9.3)
