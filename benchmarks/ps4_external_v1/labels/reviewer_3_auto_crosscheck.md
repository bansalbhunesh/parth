# Automated correctness cross-check — ps4_external_v1 (44-label subset)

**Type:** automated / machine-assisted correctness pass. **NOT a human review.**
**Performed by:** Claude (Anthropic) automated pass, on the 44-label reviewer subset.
**Date:** 2026-07-04
**Status of the benchmark:** single-author frozen; second **human** reviewer (reviewer-2) still **pending**.

> This document records an independent automated re-derivation of the 44 labels in the
> reviewer validation packet, checking each label against its own evidence excerpt. It
> raises confidence that the labels are *correct*. It does **not** constitute a second
> human review, is **not** two-person adjudication, and must not be cited as either.
> The `reviewer_2.jsonl` slot is intentionally left empty for a real human reviewer.

## Result

Concur with the ground truth on **44 / 44 labels** — no rejects, no mislabels.

## Arithmetic / unit-conversion checks (re-derived)

| Label | Claim | Re-derivation | OK |
|---|---|---|---|
| P005-L01 | 4000 m³/h < 2500 CFM | 4000 × 0.5886 = 2354 CFM < 2500 | ✓ |
| P006-L01 | 4000 gal ÷ 103 GPH = 38.8 h < 48 | 4000/103 = 38.83 h | ✓ (assumes 103 GPH = full-load burn) |
| P007-L01 | 24 × 26.5 kWh = 636 > 600 | 636 kWh | ✓ |
| P022-L01 | 4 s > 100 ms | 4 s = 4000 ms | ✓ |
| P052-L01 | 16+14+12 = 42 A > 32 | 42 A | ✓ |

## Domain-recall values (checked vs IPCC AR4 100-yr GWP)

| Label | Substance | Label GWP | Reference | OK |
|---|---|---|---|---|
| P008-L01 / P045-L01 | R-410A | 2088 | 2088 | ✓ |
| P018-L03 | R-134a | 1430 | 1430 | ✓ |
| P029-L01 | R-407C | 1774 | 1774 | ✓ |
| P021-L01 | FM-200 (HFC-227ea) | 3220 | 3220 | ✓ |
| P014-L01 | R-1234ze | <1 | <1 (≪ 750) | ✓ |

## OCR / scanned-image labels — images opened and read directly

| Label | Image (`vendor_submittal.png`) actually shows | Label | OK |
|---|---|---|---|
| P039-L01 | "Battery runtime: 8 minutes" | 8 min < 10 min req | ✓ |
| P040-L01 | "Branch B1 Rating 32A Load 40A" | B1 40 A > 32 A | ✓ |
| P041-L01 | "Icw: 50 kA / 1 s" | 50 kA < 65 kA req | ✓ |

## Clean negatives (10) and adversarial cases (2)

- Clean negatives P012, P013, P014, P017-L03, P017-L04, P018-L05, P019-L04, P020-L04,
  P044-L02, P045-L02 all show submitted == required — genuinely clean, no hidden deviation.
- Adversarial P016-L01 and P026-L01 correctly flag the real deviation despite the embedded
  "ignore mismatches / compliance" bait text.

## Notes for the human reviewer (nuance, not errors)

1. **P015-L01 and P051-L01 are the same scenario** (crac_crah supply-air 30 °C vs 27 °C
   recommended, both contested). Different pairs, but they test one identical judgment —
   real "contested" diversity is 1 scenario, not 2.
2. **P008-L01 and P045-L01 test the same fact** (R-410A GWP 2088 > 750), differing only in
   source basis. Distinct GWP facts covered ≈ 4, not 5.
3. **P020-L03** — original required/submitted phrasing ("supported" / "not supported") is
   weak; recommend "requires both Modbus and BACnet; matrix shows Modbus = No." (This was the
   only genuine content improvement in the quarantined change; re-apply it cleanly if desired.)
4. **P006-L01** — derivation valid only if 103 GPH is the full-load consumption; the excerpt
   is truncated. Human reviewer should confirm the burn-rate basis.
5. **P005-L01** — representation-sensitive: raw value (4000 m³/h) is numerically larger than
   the 2500 CFM threshold; the deviation only appears after conversion. Consider storing both
   raw and converted values.

## What still needs a human

- A real reviewer-2 (independent human) filling `reviewer_form.csv` in their own words, with
  the Y/N sub-fields (`evidence_sufficient`, `severity_ok`, `difficulty_ok`,
  `commissioning_mapping_ok`) actually marked, and a genuine sign-off.
- Only then should `run_config.yaml` version bump and the claims register (row 14) upgrade
  from "reviewer-2 pending."
