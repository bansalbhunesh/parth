# PS4 External Validation Benchmark — v1

An **independent** benchmark for Pramaan's document-comparison / deviation-detection
ability, deliberately separate from the seeded synthetic corpus
(`data/corpus/ground_truth.json`) and from the demo fixtures. Nothing here is
called a "real datasheet": pairs are **team-authored fixtures**, honestly labeled,
with values cited from public product/standard figures where used.

> **Status (v1.2, frozen):** **53 pairs / 106 source docs / 129 labels** across 17
> systems (64 clean negatives, 2 contested). Labels are **single-author frozen**;
> a two-reviewer human adjudication is still **pending** — an automated consistency
> audit has run (machine QA, not human; 123/129 consistent, 6 flagged), see
> [`labels/REVIEW_STATUS.md`](labels/REVIEW_STATUS.md). Featured live run:
> `gemini-3.1-flash-lite` via the gateway (3-pass); the public demo's default
> primary is `gemini-2.5-flash` — both are live-model results, see
> [`reports/benchmark_card.json`](reports/benchmark_card.json).

## What can / cannot be claimed
- **Can:** the frozen v1.2 benchmark result — mean semantic recall 0.862
  (0.841–0.873), precision 0.953, F1 0.905, 0 false alerts on the 64 clean
  negatives, vs a deterministic rule baseline of 0.111 — reported **as a benchmark
  result**, per-run, with not-run pairs counted as misses.
- **Cannot:** any field-accuracy claim. The pairs are team-authored fixtures (not
  downloaded primary sources) and labels are single-author frozen with two-person
  adjudication pending — this is a benchmark number, not a field-validation result.

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
