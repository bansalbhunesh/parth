# Scraped: TIA-942

Source: WebSearch — TIA-942-C 2024 cabling and rated levels

## ANSI/TIA-942-C (May 2024) — Data Center Cabling Standard (paraphrased)

### Rated Level Classification

| Level | Redundancy | Distribution | Uptime Target | Maintainability |
|-------|-----------|--------------|---------------|-----------------|
| Rated 1 | None (N) | Single pathway | 99.671% | Requires shutdown |
| Rated 2 | N+1 components | Single pathway | 99.741% | Component-level |
| Rated 3 | N+1, dual pathway | Active + standby | 99.982% | Concurrent |
| Rated 4 | 2N, dual pathway | Both active | 99.995% | Fault tolerant |

### Cabling Media Requirements
- **Copper**: Category 6A (ANSI/TIA-568.2-D) or higher for horizontal
- **Single-mode fibre**: OS2 per ANSI/TIA-568.3-D for backbone
- **Multimode fibre**: OM3 minimum, OM4 recommended for 40/100G short reach
- **Coaxial**: 75-ohm per Telcordia GR-139-CORE (legacy signaling only)
- Minimum 2 optical fibres per horizontal and backbone link (new in -C revision)

### Key Changes in TIA-942-C (2024)
- Cabinet width standardised to 800 mm (was 600/700/800 previously)
- Minimum fibre count increased to 2 per link
- Renamed "Tier" to "Rated" to avoid confusion with Uptime Institute terminology
- Enhanced guidance on high-density deployments and liquid cooling infrastructure
- Updated pathway fill ratios for high-density cable bundles
- Alignment with TIA-607-D grounding/bonding for data centers

### Pathway and Space
- Overhead cable tray fill: max 50% for maintenance access
- Under-floor pathway: minimum 450 mm clear depth for airflow + cabling
- Bend radius: minimum 10× cable OD for fibre, 4× for Cat6A
- Maximum bundle size: 48 cables per BICSI-002 best practice
