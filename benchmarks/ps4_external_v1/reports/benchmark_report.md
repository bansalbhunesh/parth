# PS4 External Benchmark — Report (v1.2.0)

_Generated 2026-07-09T06:29:27+00:00 · run
`scripts/benchmark_report.py` to refresh. Every metric carries an evidence label._

> **Positioning (judge-safe):** Pramaan reports the repeatable 3-pass
> `gemini-3.1-flash-lite` result as the **primary benchmark** because it is
> stable, fast, precise, and demo-suitable. `gemini-2.5-flash` achieved higher
> peak recall in comparison runs but was less reliable for full repeat
> evaluation.

## Primary featured result
**Model:** `google/gemini-3.1-flash-lite` · **3-pass completed run** · `live_model`

| metric | value |
|---|---|
| mean semantic recall | **0.862** |
| recall band | 0.841–0.873 |
| mean semantic precision | **0.953** |
| mean semantic F1 | **0.905** |
| mean exact recall | 0.698 |
| clean-negative false-alert rate | **0.000** |
| p50 latency | ~2.5 s |
| not_run | 0 on 2/3 passes; 1 transient in pass 3 |
| positive labels (denominator) | 63 |

## Model comparison (ablation — not headlined)
**Model:** `google/gemini-2.5-flash` (ablation / comparison — *not* the primary result)

- Peak semantic recall: **0.952** · precision 0.938
- Higher peak recall (~0.95) but slower and did not complete a clean repeat-3 run; reported as an ablation / model comparison, NOT the primary validated result.

## Rule-engine baseline
`deterministic_offline` — semantic recall 0.1111 (7/63), false positives 0, clean-negative false-alert rate 0.0.

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

**Review status:** single_author_frozen_pending_review (no two-person adjudication claimed).

**Difficulty mix (positive labels):** {'adversarial_noise': 6, 'categorical_reasoning': 17, 'derived_arithmetic': 4, 'direct_value': 6, 'domain_recall': 6, 'omission_detection': 8, 'scanned_or_image': 6, 'table_or_layout': 8, 'unit_conversion': 2}

## Limitations (kept visible)
- Mostly team-authored benchmark fixtures (not downloaded primary sources).
- 10 primary-source-derived documents (5 with a verified public URL).
- Single-author frozen labels.
- Reviewer-2 (two-person human) adjudication pending.
- Source files are not stored in this benchmark yet; source links/derivations are tracked.

## Non-claims
- NOT a real-world-accuracy, field-validation, or real-datasheet-accuracy claim.
- Seed is team-authored and single-author labeled; primary-source acquisition and two-person reviewer adjudication are pending.

See [`BENCHMARK_PROTOCOL.md`](../BENCHMARK_PROTOCOL.md) for the acquisition backlog
and [`labels/REVIEW_STATUS.md`](../labels/REVIEW_STATUS.md) for the review state.
