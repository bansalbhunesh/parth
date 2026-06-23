# Scraped: IS-1893

Source: WebSearch — IS 1893:2016 seismic zone factors and importance factors

## IS 1893 (Part 1):2016 — Seismic Design Criteria (paraphrased)

### Seismic Zone Classification

| Zone | Risk Level | Zone Factor (Z) | Peak Ground Acceleration |
|------|-----------|-----------------|-------------------------|
| II | Low | 0.10 | 0.10g |
| III | Moderate | 0.16 | 0.16g |
| IV | Severe | 0.24 | 0.24g |
| V | Very Severe | 0.36 | 0.36g |

### Notable Zone Assignments
- **Zone V**: Northeast India, parts of J&K, Himachal, Uttarakhand, Kutch (Gujarat)
- **Zone IV**: Delhi-NCR, parts of Maharashtra (incl. parts of Mumbai metro region)
- **Zone III**: Most of western & central India, Navi Mumbai corridor
- **Zone II**: Most of peninsular India, parts of Rajasthan

### Importance Factor (I)

| Category | I Factor | Examples |
|----------|----------|---------|
| Critical / Post-disaster | 1.5 | Hospitals, fire stations, lifeline structures, data centers housing essential services |
| Important / Business continuity | 1.2 | Commercial buildings, industrial structures |
| General | 1.0 | Residential, standard occupancy |

### Design Horizontal Seismic Coefficient
Ah = (Z × I × Sa/g) / (2 × R)

Where:
- Z = Zone factor
- I = Importance factor
- Sa/g = Spectral acceleration coefficient (depends on natural period and soil type)
- R = Response reduction factor (depends on structural system)

### Application to Data Centers
- Hyperscale data centers in Zone III (e.g., Navi Mumbai): Z=0.16, I=1.5
- Seismic base isolation recommended for Tier IV facilities in Zone IV/V
- Equipment anchorage per manufacturer + IS 1893 acceleration values
- Raised floor systems must be seismically braced (diagonal bracing at perimeter and every 3m grid)
- Battery racks require seismic restraint per Zone factor × I factor product
