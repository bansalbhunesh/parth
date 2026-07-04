# Pair context — pair_019

- **System type:** pdu_rpp
- **Source basis:** team-authored (owner design basis)
- **Vendor submittal modality:** text

## Owner requirement (design basis — team-authored, not a public standard)

```
# Owner Design Basis Requirement — Rack PDU

*Team-authored owner-requirement fixture (design basis). Not a vendor document. Requirement values are the owner's design intent.*

## 1. Metering & capacity
- PDU shall provide **per-outlet** energy metering.
- Outlets shall be **individually switched**.
- Each branch load shall not exceed its **32 A** rating.
- Form factor shall be **Zero-U 3-phase 415 V**.
- Environmental sensor ports shall be provided.
```

## Vendor/submittal (team-authored fixture — NOT a real vendor datasheet)

```
# Vendor Submittal — Rack PDU (monitored series)

*Team-authored submittal fixture.*

## 1. Metering
- Metering: **inlet-level only**.
- Outlets: **unswitched**.
- Form factor: **Zero-U 3-phase 415 V**.
- Environmental sensor ports: **provided**.

## 2. Branch load schedule

| Branch | Rating | Connected load |
|---|---|---|
| B1 | 32 A | 40 A |
| B2 | 32 A | 22 A |
| B3 | 32 A | 18 A |
```

## Labels from this pair included for review

- `P019-L03` — positive_deviation / table_or_layout — branch_load_a
- `P019-L04` — clean_negative / categorical_reasoning — form_factor

## Known limitation

- Single-author frozen label, pending two-person review. Fixture is team-authored.
