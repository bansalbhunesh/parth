# Pair context — pair_036

- **System type:** metering_power_quality
- **Source basis:** team-authored (owner design basis)
- **Vendor submittal modality:** text

## Owner requirement (design basis — team-authored, not a public standard)

```
# Owner Design Basis Requirement — Power quality (conflicting values)

*Team-authored owner-requirement fixture (design basis). Not a vendor document. Requirement values are the owner's design intent.*

## 1. Input
- Input THD shall be **<= 5 percent**.
- Displacement power factor shall be **>= 0.99**.
```

## Vendor/submittal (team-authored fixture — NOT a real vendor datasheet)

```
# Vendor Submittal — UPS submittal (conflicting)

*Team-authored adversarial fixture (duplicate conflicting values).*

## 1. Data
- Legacy note (2019): Input THD **3 percent**.
- Current measured Input THD: **8 percent**.
- Displacement power factor: **0.99**.
```

## Labels from this pair included for review

- `P036-L01` — positive_deviation / adversarial_noise — input_thd_percent

## Known limitation

- Single-author frozen label, pending two-person review. Fixture is team-authored.
