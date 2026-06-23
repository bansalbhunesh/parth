# Uptime Institute Tier IV — Detailed Technical Reference

**Standard:** Uptime Institute Tier Classification System (Tier IV — Fault Tolerant)
**Version:** Current (Tier Standard continuously maintained by Uptime Institute)
**Scope:** Defines the highest level of data centre infrastructure resilience, covering power, cooling, and physical site topology for mission-critical facilities.

---

## 1. Availability and Downtime

| Metric | Value |
|--------|-------|
| Expected availability | 99.995% |
| Maximum annual downtime | ~26.3 minutes per year |

**Note:** Uptime Institute removed specific availability predictions from the Tier Standard in 2009. The figures above (99.995% / 26.3 min) are historical industry-consensus values that remain widely referenced in engineering practice but are not part of the current formal standard text.

---

## 2. Tier Comparison Summary

| Attribute | Tier I | Tier II | Tier III | Tier IV |
|-----------|--------|---------|----------|---------|
| Availability (historical) | 99.671% | 99.749% | 99.982% | 99.995% |
| Annual downtime (historical) | 28.8 hr | 22 hr | 1.6 hr | 26.3 min |
| Power redundancy | N (single path) | N+1 components | N+1, dual path (one active) | 2N or 2(N+1), dual path (both active) |
| Cooling redundancy | N | N+1 | N+1, concurrently maintainable | 2N or 2(N+1), fault tolerant |
| Distribution paths | Single | Single | Active + standby | Simultaneously active |
| Concurrent maintainability | No | No | Yes | Yes |
| Fault tolerance | No | No | No | Yes |
| Compartmentalisation | No | No | Partial | Full physical isolation |

---

## 3. Tier IV Key Definitions

### 3.1 Concurrent Maintainability
Any planned maintenance activity on any single capacity component or distribution path can be performed while the data centre continues to operate at full IT load without any interruption to IT services. No manual switchover or operator intervention is required.

### 3.2 Fault Tolerance
An unplanned failure of any single component or any single distribution path does not interrupt IT operations. The facility automatically continues at full load on the remaining systems. This goes beyond concurrent maintainability by also covering unplanned events — not just scheduled work.

---

## 4. Power Infrastructure Requirements

| Requirement | Tier IV Specification |
|-------------|----------------------|
| Redundancy model | 2N or 2(N+1) — fully redundant |
| Distribution paths | Two independent, simultaneously active paths from utility entrance to rack PDU |
| Utility feeds | Two independent utility feeds, or equivalent on-site generation |
| Path independence | Each power path must carry the full critical load independently |
| Transfer mechanism | Automatic transfer with zero IT load impact on any single failure; no manual switching |
| UPS systems | Redundant UPS systems on each path |
| Battery autonomy | Minimum 10-12 minutes at full rated load per UPS string |
| Generators | N+1 generator sets per power path; 96-hour fuel storage capacity recommended |
| Generator start | Automatic start and load acceptance within 10-12 seconds of utility loss |
| IT equipment | All IT equipment must be dual-corded (A+B feed) to be compatible with fault-tolerant topology |

---

## 5. Cooling Infrastructure Requirements

| Requirement | Tier IV Specification |
|-------------|----------------------|
| Redundancy model | 2N or 2(N+1) for all cooling components |
| Continuous cooling | No brief thermal exposure even during component failure |
| Chiller plants | Dual independent chiller plants, each sized for full load |
| Cooling distribution | Multiple independent cooling distribution loops |
| CRAH/CRAC units | Redundant units with automatic failover |
| Piping | Independent piping systems for each cooling path |
| Physical isolation | Redundant cooling paths must be physically separated to prevent single-event compromise |

---

## 6. Physical Isolation and Compartmentalisation

- Redundant capacity components and distribution paths must be housed in independent, physically isolated spaces.
- A fire, flood, or mechanical failure in one path's physical space must not compromise the other path.
- Electrical and mechanical rooms for Path A and Path B must be in separate fire-rated compartments.
- Continuous fault-detection and monitoring systems are required across all paths.

---

## 7. Certification Types

| Certification | Description |
|---------------|-------------|
| TCDD (Tier Certification of Design Documents) | Paper review of design documents against Tier criteria |
| TCCF (Tier Certification of Constructed Facility) | Physical inspection of the as-built facility |
| TCOS (Tier Certification of Operational Sustainability) | Operational audit of management, maintenance, and operating practices |

---

## 8. Relevance to Data Centre EPC Projects

- Tier IV is the benchmark for mission-critical facilities (government, financial, healthcare, hyperscale cloud).
- The 2N requirement doubles capital cost compared to Tier III (N+1), making detailed cost-benefit analysis essential during EPC planning.
- Physical compartmentalisation requirements drive building layout, fire-rated wall placement, and MEP routing from the earliest architectural stages.
- Dual-cord IT equipment compatibility must be specified at procurement stage.
- 96-hour fuel autonomy and dual utility feeds require site selection consideration (fuel delivery access, utility diversity).
- Commissioning must validate fault-tolerance through live failure simulation testing.

---

## Sources

- [INGENIOUS.BUILD — Data Center Tiers Explained (2026 Guide)](https://www.ingenious.build/blog-posts/data-center-tiers-explained)
- [Flexential — Data Center Tiers: Behind the Numbers](https://www.flexential.com/resources/blog/data-center-tiers-behind-numbers)
- [CoreSite — Breaking Down Data Center Tier Classifications](https://www.coresite.com/blog/breaking-down-data-center-tiers-classifications)
- [Colocation America — Data Center Standards (Tiers I-IV)](https://www.colocationamerica.com/data-center/tier-standards-overview)
- [Uptime Institute — Tier Classification System](https://uptimeinstitute.com/tiers)
- [NEXTDC — Understanding Data Centre Tiers](https://www.nextdc.com/blog/understanding-data-centre-tiers)
- [RED Engineering — Data Centre Tiers Explained](https://www.red-eng.com/insights/knowledge-base/data-centre-tiers-explained)
- [Construct and Commission — Data Center Uptime Tiers Explained](https://constructandcommission.com/data-center-uptime-tiers-explained/)
- [datacenterss.com — Uptime Institute Tier Certifications 2026](https://datacenterss.com/uptime-institute-tier-certifications-what-data-centers-need-to-know/)
- [MassiveGRID — Tier III vs Tier IV Data Centers](https://massivegrid.com/blog/tier-iii-vs-tier-iv-data-center-hosting/)
