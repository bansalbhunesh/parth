# Pair context — pair_018

- **System type:** chiller
- **Source basis:** team-authored (owner design basis)
- **Vendor submittal modality:** text

## Owner requirement (design basis — team-authored, not a public standard)

```
# Owner Design Basis Requirement — Water-cooled chiller

*Team-authored owner-requirement fixture (design basis). Not a vendor document. Requirement values are the owner's design intent.*

## 1. Capacity & redundancy
- Cooling capacity shall be at least **1000 kW** per chiller.
- Chiller plant shall be **N+1** redundant.
- Refrigerant GWP shall be **<= 750**.
- Supply voltage shall be **415 V**.
- Chilled-water flow shall be **>= 40 L/s**.
- A factory performance test report shall be provided.
```

## Vendor/submittal (team-authored fixture — NOT a real vendor datasheet)

```
# Vendor Submittal — Centrifugal chiller

*Team-authored submittal fixture.*

## 1. Data
- Rated cooling capacity: **850 kW**.
- Plant configuration: **N** (no standby).
- Refrigerant: **R-134a**.
- Supply voltage: **415 V**.
- Chilled-water flow: **45 L/s**.
```

## Labels from this pair included for review

- `P018-L01` — positive_deviation / direct_value — capacity_kw
- `P018-L02` — positive_deviation / categorical_reasoning — redundancy
- `P018-L03` — positive_deviation / domain_recall — refrigerant_gwp
- `P018-L04` — omission / omission_detection — test_report
- `P018-L05` — clean_negative / direct_value — voltage_v

## Known limitation

- Single-author frozen label, pending two-person review. Fixture is team-authored.
