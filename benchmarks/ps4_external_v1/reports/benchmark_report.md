# PS4 External Benchmark — Report (v1.0.0)

_Generated 2026-07-03T15:06:51+00:00 · run
`scripts/benchmark_report.py` to refresh. Every metric carries an evidence label._

## Composition
| item | value | evidence |
|---|---|---|
| Source documents | 32 | `team_authored` |
| Pairs | 16 | `team_authored` |
| Labels | 16 | `team_authored` |
| Positive-type labels | 12 | `team_authored` |
| Clean negatives | 3 | `team_authored` |
| Contested labels | 1 | `team_authored` |
| Systems covered | 8 (battery, cabling, crac_crah, generator, metering_power_quality, refrigerant, switchgear, ups) | — |
| Provenance SHA-256 completeness | 1.0 | `measured` |
| Primary-source docs | 0 | `measured` |
| Team-authored docs | 32 | `measured` |

**Difficulty mix (positive labels):** {'adversarial_noise': 1, 'categorical_reasoning': 2, 'derived_arithmetic': 2, 'direct_value': 3, 'domain_recall': 1, 'omission_detection': 2, 'unit_conversion': 1}

**Source-origin mix:** {'adversarial_team_authored': 1, 'owner_design_basis_team_authored': 16, 'synthetic_negative': 3, 'team_authored_from_public_values': 12}

## Results
### Rule-engine baseline  
`deterministic_offline`

- Primary recall (semantic, not-run counted as miss): **0.4167** (5/12)
- Primary recall (exact): 0.4167
- Secondary recall (semantic, not-run excluded): 0.4167 (over 12 positives)
- False positives: **0** · clean-negative false-alert rate: **0.0**
- Not-run pairs: 0  · error rate: 0.0
- Latency p50/p95 (ms): 0.0 / 6.0

| difficulty | caught | recall |
|---|---|---|
| adversarial_noise | 1/1 | 1.0 |
| categorical_reasoning | 0/2 | 0.0 |
| derived_arithmetic | 0/2 | 0.0 |
| direct_value | 3/3 | 1.0 |
| domain_recall | 0/1 | 0.0 |
| omission_detection | 1/2 | 0.5 |
| unit_conversion | 0/1 | 0.0 |

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
- **Can:** "On an independent, frozen, provenance-tracked benchmark of 16 pairs,
  the rule engine catches 5/12 positive
  checks with 0 false positives and a
  0.0 clean-negative false-alert rate."
- **Cannot (yet):** any headline external-accuracy number — the seed is team-authored and
  single-author labeled; primary-source acquisition + adjudication are pending.

See [`BENCHMARK_PROTOCOL.md`](../BENCHMARK_PROTOCOL.md) for the acquisition backlog to 40–50 pairs.
