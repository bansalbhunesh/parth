# Pair context — pair_020

- **System type:** bms
- **Source basis:** team-authored (owner design basis)
- **Vendor submittal modality:** text

## Owner requirement (design basis — team-authored, not a public standard)

```
# Owner Design Basis Requirement — BMS supervisory controller

*Team-authored owner-requirement fixture (design basis). Not a vendor document. Requirement values are the owner's design intent.*

## 1. Profile & protocols
- Controller shall be BACnet profile **B-BC**.
- Native transport shall be **BACnet/IP**.
- Controller shall support **both Modbus and BACnet**.
- Minimum **28** hardware points.
- Supply shall be **24 V dc**.
```

## Vendor/submittal (team-authored fixture — NOT a real vendor datasheet)

```
# Vendor Submittal — BMS controller

*Team-authored submittal fixture.*

## 1. Profile
- BTL profile: **B-AAC**.
- Transport: **BACnet MS/TP**.
- Hardware points: **28**.
- Supply: **24 V dc**.

## 2. Protocol support matrix

| Protocol | Supported |
|---|---|
| BACnet | Yes |
| Modbus | No |
```

## Labels from this pair included for review

- `P020-L03` — positive_deviation / table_or_layout — modbus_support
- `P020-L04` — clean_negative / direct_value — points

## Known limitation

- Single-author frozen label, pending two-person review. Fixture is team-authored.
