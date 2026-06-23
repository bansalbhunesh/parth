# Scraped: BICSI-002

Source: WebSearch — BICSI 002-2024 commissioning levels

## ANSI/BICSI 002-2024 — Commissioning Levels L1–L5 (paraphrased)

### Commissioning Level Framework (Tag System)

| Level | Tag | Name | Scope | Location |
|-------|-----|------|-------|----------|
| L1 | Red Tag | Factory Acceptance Testing (FAT) | Component verification at manufacturer facility | Factory |
| L2 | Yellow Tag | Site Delivery & Pre-Installation | Delivery inspection, spec compliance, installation readiness | Site |
| L3 | Green Tag | Pre-Commissioning & Initial Startup | Individual component functional checks, initial power-up | Site |
| L4 | Blue Tag | Functional Performance Testing | Comprehensive performance evaluation per design criteria | Site |
| L5 | White Tag | Integrated Systems Testing (IST) | Full facility event simulation, interoperability, 72-hr sustained ops | Site |

### Level Details

**L1 — Factory Acceptance (Red Tag)**
Conducted at manufacturer's facility before shipping. Verifies equipment meets purchase order specifications, dimensional accuracy, electrical characteristics, and factory test reports. Witnessed by owner's representative.

**L2 — Site Acceptance (Yellow Tag)**
Performed upon delivery. Verifies no shipping damage, completeness of accessories and documentation, correct model/serial numbers, compliance with approved submittals. Equipment placed in designated location.

**L3 — Startup Testing (Green Tag)**
Individual equipment powered up for first time on-site. Checks protective relay settings, control sequences, alarm setpoints, rotation direction, basic functionality. Each system tested in isolation.

**L4 — Performance Testing (Blue Tag)**
System-level validation under design load conditions. Includes failover testing (generator start, UPS transfer), thermal performance under load, and verification of N+1 or 2N redundancy operation. May run 24-48 hours.

**L5 — Integrated Systems Testing (White Tag)**
Full-facility event simulation. Tests coordinated response to utility outage, cooling failure, fire alarm, and cascading scenarios. Runs 72+ hours continuous operation. All systems operating simultaneously. Final acceptance gate before beneficial occupancy.

### Key BICSI-002 Design Best Practices
- Maximum 48 cables per bundle in pathways
- Minimum 900 mm raised floor height for Tier III/IV (airflow + cabling)
- Structured cabling topology: MDA → HDA → ZDA per TIA-942
- Hot/cold aisle containment recommended for PUE < 1.4
