# Reproducing the ps4_external_v1 benchmark

One command, safe by default (spends **no** API quota):

```powershell
python scripts/run_benchmark_suite.py
```

This runs the manifest check, the hash/source check, the deterministic rule
baseline, and report generation. The live LLM benchmark runs **only** with
`--llm`.

## Reproduce the rule baseline (no key needed)

```powershell
python scripts/run_benchmark_suite.py --rule-only
# or directly:
python scripts/benchmark_ps4_external.py --mode rule
```

Deterministic and offline. Expected: semantic recall **0.111 (7/63)**, **0 false
positives**, clean-negative false-alert rate **0.000**, with the image pairs
recorded `not_run` (the rule path is text-only).

## Reproduce the LLM benchmark (needs a configured key)

The featured result is `google/gemini-3.1-flash-lite` via an OpenAI-compatible
gateway. Set the provider env, then:

```powershell
# OpenAI-compatible gateway (featured configuration)
$env:OPENAI_API_KEY="..."; $env:OPENAI_BASE_URL="https://<gateway>/v1"
$env:OPENAI_MODEL="google/gemini-3.1-flash-lite"; $env:OPENAI_VISION_MODEL="google/gemini-3.1-flash-lite"
$env:OPENAI_MAX_TOKENS="10000"; $env:PRAMAAN_LLM_TIMEOUT="150"; $env:PRAMAAN_LLM="openai"
python scripts/run_benchmark_suite.py --llm --provider openai --model google/gemini-3.1-flash-lite --repeat 3

# native Gemini
$env:GEMINI_API_KEY="..."
python scripts/run_benchmark_suite.py --llm --provider gemini --repeat 1
```

`--repeat 3` produces three passes; the report aggregates them into the featured
mean + band. **No key configured?** Every pair is recorded `not_run` and counts
as a miss — nothing is fabricated.

## Outputs generated

- `benchmarks/ps4_external_v1/runs/<date>_<provider>_<model>_run<k>/` — per run:
  `predictions.jsonl`, `per_pair_results.csv`, `per_label_results.csv`,
  `errors.jsonl`, `run_config.yaml`, `summary.json`.
- `benchmarks/ps4_external_v1/reports/` — `benchmark_report.md`,
  `benchmark_card.json`, `benchmark_results.csv`, `per_pair_results.csv`,
  and (via `scripts/benchmark_error_analysis.py`) `error_analysis.md`,
  `false_positives.csv`, `false_negatives.csv`.

## How `not_run` / timeouts are counted

`not_run` covers: no provider key, a fall-back to the rule engine, an
unparseable response, a timeout past `PRAMAAN_LLM_TIMEOUT` (default 60 s), or a
provider error after bounded retries. **Every `not_run` counts as a miss in the
PRIMARY recall metric** (`count_not_run_as_miss: true` in each run's config).
Nothing is ever fabricated. The secondary recall (reported separately) excludes
not-run pairs for a "when it answered" view.

## Verify the source hashes

```powershell
python scripts/benchmark_hash_sources.py     # recomputes sha256 of every doc, cross-checks the manifest
python scripts/benchmark_manifest_check.py   # validates manifest + labels + freeze, asserts 0 overlap with the seeded corpus
```

`benchmark_hash_sources.py` writes `sources/hashes.json` and fails if any file's
hash disagrees with the manifest. The label freeze hash is order-independent and
recorded in `labels/labels_freeze.json`.

## Regenerate `benchmark_card.json`

```powershell
python scripts/benchmark_report.py
```

Reads every run's `summary.json`, aggregates the featured model
(`gemini-3.1-flash-lite`) into mean + band, renders `gemini-2.5-flash` as a
comparison/ablation, and writes `benchmark_report.md` + `benchmark_card.json`
with evidence labels and the visible limitations block.
