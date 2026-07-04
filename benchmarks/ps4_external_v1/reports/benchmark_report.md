# PS4 External Benchmark — Report (v1.2.0)

_Generated 2026-07-03T22:03:55+00:00 · run
`scripts/benchmark_report.py` to refresh. Every metric carries an evidence label._

## Composition
| item | value | evidence |
|---|---|---|
| Source documents | 106 | `team_authored` |
| Pairs | 53 | `team_authored` |
| Labels | 129 | `team_authored` |
| Positive-type labels | 63 | `team_authored` |
| Clean negatives | 64 | `team_authored` |
| Contested labels | 2 | `team_authored` |
| Systems covered | 17 (ats_sts, battery, bms, cabling, chiller, cooling_tower, crac_crah, fire_suppression, generator, metering_power_quality, networking, pdu_rpp, rack_aisle, refrigerant, switchgear, transformer, ups) | — |
| Provenance SHA-256 completeness | 1.0 | `measured` |
| Primary-source files (stored) | 0 | `measured` |
| Primary-source-derived docs (cited public refs) | 10 | `measured` |
| Docs with verified public URL | 5 | `measured` |
| Team-authored docs | 106 | `measured` |

**Review status:** single_author_frozen_pending_review (no two-reviewer adjudication claimed).

**Difficulty mix (positive labels):** {'adversarial_noise': 6, 'categorical_reasoning': 17, 'derived_arithmetic': 4, 'direct_value': 6, 'domain_recall': 6, 'omission_detection': 8, 'scanned_or_image': 6, 'table_or_layout': 8, 'unit_conversion': 2}

**Source-origin mix:** {'adversarial_team_authored': 7, 'owner_design_basis_team_authored': 53, 'synthetic_negative': 7, 'team_authored_from_public_values': 39}

## Results
### Rule-engine baseline  
`deterministic_offline`

- Primary recall (semantic, not-run counted as miss): **0.1111** (7/63)
- Primary recall (exact): 0.1111
- Secondary recall (semantic, not-run excluded): 0.1228 (over 57 positives)
- False positives: **0** · clean-negative false-alert rate: **0.0**
- Not-run pairs: 5 ['pair_039', 'pair_040', 'pair_041', 'pair_042', 'pair_043'] · error rate: 0.0943
- Latency p50/p95 (ms): 0.0 / 1.0

| difficulty | caught | recall |
|---|---|---|
| adversarial_noise | 3/6 | 0.5 |
| categorical_reasoning | 0/17 | 0.0 |
| derived_arithmetic | 0/4 | 0.0 |
| direct_value | 3/6 | 0.5 |
| domain_recall | 0/6 | 0.0 |
| omission_detection | 1/8 | 0.125 |
| scanned_or_image | 0/6 | 0.0 |
| table_or_layout | 0/8 | 0.0 |
| unit_conversion | 0/2 | 0.0 |

### LLM-enhanced  
`live_model`

- Primary recall (semantic, not-run counted as miss): **0.8095** (51/63)
- Primary recall (exact): 0.6349
- Secondary recall (semantic, not-run excluded): 0.8947 (over 57 positives)
- False positives: **31** · clean-negative false-alert rate: **0.0625**
- Not-run pairs: 6 ['pair_033', 'pair_039', 'pair_040', 'pair_041', 'pair_042', 'pair_043'] · error rate: 0.0943
- Latency p50/p95 (ms): 15432.0 / 39778.0

| difficulty | caught | recall |
|---|---|---|
| adversarial_noise | 6/6 | 1.0 |
| categorical_reasoning | 17/17 | 1.0 |
| derived_arithmetic | 4/4 | 1.0 |
| direct_value | 6/6 | 1.0 |
| domain_recall | 5/6 | 0.8333 |
| omission_detection | 6/8 | 0.75 |
| scanned_or_image | 0/6 | 0.0 |
| table_or_layout | 7/8 | 0.875 |
| unit_conversion | 0/2 | 0.0 |


## Cost
`not_yet_measured` — the analysis path does not currently surface provider token
usage; cost estimation is a backlog item.

## Limitations / non-claims
- Seed pairs are **team-authored** (not downloaded primary sources) → **no
  external-accuracy claim** yet.
- Labels are **single-author frozen**; two-reviewer adjudication is backlog.
- Rule-engine recall is low on reasoning cases **by design** — those need the LLM.
- OCR/vision (`scanned_or_image`, `table_or_layout`) and several systems are backlog.

## What can / cannot be claimed
- **Can:** "On an independent, frozen, provenance-tracked benchmark of 53 pairs,
  the rule engine catches 7/63 positive
  checks with 0 false positives and a
  0.0 clean-negative false-alert rate."
- **Cannot (yet):** any headline external-accuracy number — the seed is team-authored and
  single-author labeled; primary-source acquisition + adjudication are pending.

See [`BENCHMARK_PROTOCOL.md`](../BENCHMARK_PROTOCOL.md) for the acquisition backlog to 40–50 pairs.
