# Project Meghdoot — Design Basis: Uninterruptible Power Supply & Battery
_System: UPS · Uptime Tier IV · 40 MW_
_Client: Meghdoot Digital Infrastructure Pvt. Ltd._
_EPC: Patel-Larsen JV_

## Overview

The UPS system shall provide uninterrupted, conditioned power to the critical IT load during any single-point utility or generator failure event, inclusive of concurrent maintenance windows. Battery strings shall be sized for full-load ride-through per the Tier IV design basis, accounting for end-of-life capacity degradation at year 10 and an ambient temperature envelope of 20-35 deg C.

## Requirements

- **UPS-02** — battery runtime min: shall be **10 min** (ref: UPTIME-TIER4; clause DB-4.3)
- **UPS-02** — redundancy: shall be **2N topology** (ref: UPTIME-TIER4; clause DB-4.1)
- **UPS-02** — rated power kw: shall be **1200 kW** (ref: DESIGN-BASIS; clause DB-4.2)
- **UPS-02** — efficiency pct: shall be **96 %** (ref: DESIGN-BASIS; clause DB-4.5)
