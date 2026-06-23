# Scraped: UPTIME-TIER4

Source: WebSearch — Uptime Institute Tier IV certification requirements

## Uptime Institute Tier Classification — Detailed Comparison (paraphrased)

### Tier Comparison Table

| Attribute | Tier I | Tier II | Tier III | Tier IV |
|-----------|--------|---------|----------|---------|
| Availability | 99.671% | 99.749% | 99.982% | 99.995% |
| Annual downtime | 28.8 hr | 22 hr | 1.6 hr | 26.3 min |
| Power redundancy | N (single path) | N+1 components | N+1, dual path (one active) | 2N, dual path (both active) |
| Cooling redundancy | N | N+1 | N+1, concurrently maintainable | 2(N+1) or N+2, fault tolerant |
| Distribution paths | Single | Single | Active + standby | Simultaneously active |
| Concurrent maintainability | No | No | Yes | Yes |
| Fault tolerance | No | No | No | Yes |
| Compartmentalisation | No | No | Partial | Full |

### Tier IV Specific Requirements
- Fully redundant 2N distribution from utility entrance to rack PDU
- Two independent utility feeds or equivalent on-site generation
- Each power path carries full critical load independently
- Automatic transfer with zero IT load impact on any single failure
- Battery autonomy minimum 10 minutes at full rated load
- Physical isolation between redundant cooling and power paths
- All IT equipment must be dual-corded (A+B feed)
- Single worst-case failure must not impact IT operations

### Certification Types
- Tier Certification of Design Documents (TCDD) — paper review
- Tier Certification of Constructed Facility (TCCF) — physical inspection
- Tier Certification of Operational Sustainability (TCOS) — operational audit

### Note on Availability Figures
Uptime Institute removed specific availability predictions from the Tier Standard in 2009. The figures above are historical/industry consensus values still widely referenced but not part of the current formal standard.
