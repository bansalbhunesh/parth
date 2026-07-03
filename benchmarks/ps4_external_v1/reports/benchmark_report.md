# PS4 External Benchmark — Report (v1.1.0)

_Generated 2026-07-03T16:12:54+00:00 · run
`scripts/benchmark_report.py` to refresh. Every metric carries an evidence label._

## Composition
| item | value | evidence |
|---|---|---|
| Source documents | 86 | `team_authored` |
| Pairs | 43 | `team_authored` |
| Labels | 110 | `team_authored` |
| Positive-type labels | 52 | `team_authored` |
| Clean negatives | 57 | `team_authored` |
| Contested labels | 1 | `team_authored` |
| Systems covered | 17 (ats_sts, battery, bms, cabling, chiller, cooling_tower, crac_crah, fire_suppression, generator, metering_power_quality, networking, pdu_rpp, rack_aisle, refrigerant, switchgear, transformer, ups) | — |
| Provenance SHA-256 completeness | 1.0 | `measured` |
| Primary-source docs | 0 | `measured` |
| Team-authored docs | 86 | `measured` |

**Difficulty mix (positive labels):** {'adversarial_noise': 6, 'categorical_reasoning': 13, 'derived_arithmetic': 2, 'direct_value': 6, 'domain_recall': 4, 'omission_detection': 6, 'scanned_or_image': 6, 'table_or_layout': 7, 'unit_conversion': 2}

**Source-origin mix:** {'adversarial_team_authored': 7, 'owner_design_basis_team_authored': 43, 'synthetic_negative': 7, 'team_authored_from_public_values': 29}

## Results
### Rule-engine baseline  
`deterministic_offline`

- Primary recall (semantic, not-run counted as miss): **0.1346** (7/52)
- Primary recall (exact): 0.1346
- Secondary recall (semantic, not-run excluded): 0.1522 (over 46 positives)
- False positives: **0** · clean-negative false-alert rate: **0.0**
- Not-run pairs: 5 ['pair_039', 'pair_040', 'pair_041', 'pair_042', 'pair_043'] · error rate: 0.1163
- Latency p50/p95 (ms): 0.0 / 1.0

| difficulty | caught | recall |
|---|---|---|
| adversarial_noise | 3/6 | 0.5 |
| categorical_reasoning | 0/13 | 0.0 |
| derived_arithmetic | 0/2 | 0.0 |
| direct_value | 3/6 | 0.5 |
| domain_recall | 0/4 | 0.0 |
| omission_detection | 1/6 | 0.1667 |
| scanned_or_image | 0/6 | 0.0 |
| table_or_layout | 0/7 | 0.0 |
| unit_conversion | 0/2 | 0.0 |

### LLM-enhanced

_No llm-enhanced run recorded yet._


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
- **Can:** "On an independent, frozen, provenance-tracked benchmark of 43 pairs,
  the rule engine catches 7/52 positive
  checks with 0 false positives and a
  0.0 clean-negative false-alert rate."
- **Cannot (yet):** any headline external-accuracy number — the seed is team-authored and
  single-author labeled; primary-source acquisition + adjudication are pending.

See [`BENCHMARK_PROTOCOL.md`](../BENCHMARK_PROTOCOL.md) for the acquisition backlog to 40–50 pairs.
