# PS4 External Validation Benchmark — v1

An **independent** benchmark for Pramaan's document-comparison / deviation-detection
ability, deliberately separate from the seeded synthetic corpus
(`data/corpus/ground_truth.json`) and from the demo fixtures. Nothing here is
called a "real datasheet": pairs are **team-authored fixtures**, honestly labeled,
with values cited from public product/standard figures where used.

> **Status:** framework complete; seeded with **16 pairs / 32 source docs / 16 labels**
> across 8 systems. Target is 40–50 pairs, 60–80 sources, 120–180 labels — see the
> acquisition backlog in [`BENCHMARK_PROTOCOL.md`](BENCHMARK_PROTOCOL.md).

## What can / cannot be claimed
- **Can:** "An independent, frozen, provenance-tracked benchmark of N pairs; the
  rule engine catches X of the deterministic checks with 0 false alerts; the
  live model recovers Y more, reported per-run with not-run counted as misses."
- **Cannot (yet):** any headline external-accuracy number, because the seed is
  team-authored (not downloaded primary sources) and single-author labeled. A
  two-reviewer adjudication and primary-source acquisition are backlog items.

## Layout
```
manifest.csv            one row per source doc (provenance + sha256)
manifest.schema.json    contract for manifest rows
labels.schema.json      contract for labels
run_config.yaml         scoring policy + run defaults
sources/                raw + normalized primary sources (backlog) + hashes.json
pairs/pair_NNN/         owner_requirement.md, vendor_submittal.md, label.json, notes.md
labels/                 labels.jsonl (frozen) + negatives/contested/adjudicated + freeze
runs/                   one dir per benchmark run (predictions, per-pair, summary)
reports/                aggregated report.md, benchmark_card.json, CSVs
```

## Commands
```powershell
python scripts/benchmark_manifest_check.py          # validate manifest + labels + freeze
python scripts/benchmark_hash_sources.py            # (re)hash docs -> sources/hashes.json, cross-check
python scripts/benchmark_ps4_external.py --mode rule                     # rule-engine baseline (no key)
python scripts/benchmark_ps4_external.py --mode llm --provider gemini --repeat 3   # live model (needs key)
python scripts/benchmark_report.py                  # aggregate latest runs -> reports/
```

If no provider key/quota is available, `--mode llm` records each pair as
`not_run` (never fabricated predictions); `not_run` counts as a miss in the
**primary** recall and is excluded from the clearly-labeled **secondary** recall.

## Authoring
Seed pairs were authored via `scripts/benchmark_seed_pairs.py` (the reviewable
source). The written files are the canonical frozen benchmark. Re-running the
generator after a model run must bump `benchmark_version` (the freeze file records
the label hash so drift is detectable).
