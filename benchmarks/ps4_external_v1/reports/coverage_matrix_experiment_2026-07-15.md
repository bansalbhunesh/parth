# Coverage-matrix prompt experiment — 2026-07-15

Status: **measured and rejected for promotion**. The production/default prompt
remains the published baseline.

## Question

Can an explicit requirement-coverage pass improve silent-omission recall without
regressing precision or the clean-negative false-alert rate?

The frozen `ps4_external_v1` labels, scoring policy, manifest, and source hashes
were not changed. Runs used the paid OpenAI-compatible AICredits gateway with
`google/gemini-3.1-flash-lite`. The API key is not stored in any artifact.

## Preflight iterations

- **v1.3–v1.4:** rejected before a full run. The model returned checklist rows
  without the required deviation fields.
- **v1.5:** exposed a JSON extraction defect: a valid object containing nested
  arrays was reduced to its first array. The extractor now preserves the actual
  top-level JSON container. A full v1.5 attempt was not saved because the new
  provenance writer passed a binary diff to a text hash helper; the writer was
  fixed before any result was accepted.
- **v1.6:** returned the stable deviation-array schema, but applied requirements
  from unrelated equipment packages. Its saved full pass is retained as negative
  evidence.
- **v1.7:** added a general equipment-scope gate before the internal checklist.
  A clean-negative smoke and an omission smoke passed before the full run.

No preflight result was promoted or substituted for a frozen-benchmark run.

## Comparable 2026-07-15 runs

All three runs below used one pass, the same model and provider, 48 text pairs,
the same five unavailable Gemini-only vision pairs, and `count_not_run_as_miss`.
The v1.7 candidate and contemporaneous baseline share the same tracked-diff hash,
`3add29687f16dc260503e0f84227971ec66f72a39890949bafcd1eba836efadb`.

| Metric | Contemporaneous baseline | Coverage v1.6 | Coverage v1.7 |
|---|---:|---:|---:|
| Semantic recall | 0.8095 (51/63) | 0.7937 (50/63) | 0.8095 (51/63) |
| Text-only secondary recall | 0.8947 (51/57) | 0.8772 (50/57) | 0.8947 (51/57) |
| Precision | 0.8361 | 0.5376 | 0.8500 |
| F1 | 0.8226 | 0.6410 | 0.8293 |
| Exact recall | 0.6667 | 0.6508 | 0.6667 |
| Omission recall | 0.875 (7/8) | 0.750 (6/8) | **1.000 (8/8)** |
| False positives | 10 | 43 | 9 |
| Clean-negative false alerts | 1/64 | 4/64 | 2/64 |
| Clean-negative FAR | **0.0156** | 0.0625 | **0.0312** |
| Not-run pairs | 5 | 5 | 5 |
| Latency p50 / p95 | 2125 / 4185 ms | 3291 / 7346 ms | 2144 / 3323 ms |

Artifacts:

- [`baseline run1`](../runs/2026-07-15_openai_google-gemini-3.1-flash-lite_run1/summary.json)
- [`coverage-matrix-v1.6 run1`](../runs/2026-07-15_openai_google-gemini-3.1-flash-lite_coverage-matrix-v1.6_run1/summary.json)
- [`coverage-matrix-v1.7 run1`](../runs/2026-07-15_openai_google-gemini-3.1-flash-lite_coverage-matrix-v1.7_run1/summary.json)

Each directory contains the run configuration, predictions, per-pair and
per-label results, errors, input/output hashes, actual provider per pair, exact
Git revision, dirty-worktree flag, and tracked-diff hash.

## Decision

v1.7 recovered the final omission label and reduced total false positives by one,
but it did **not** improve overall recall and doubled clean-negative FAR from
0.0156 to 0.0312 in the same-day comparison. That violates the pre-declared
promotion gate. It therefore remains opt-in and off by default. No headline
benchmark number changes.

The older published three-pass baseline remains the public primary result
(recall 0.862, precision 0.953, F1 0.905, clean-negative FAR 0.000). It included
vision availability and is not directly substituted by these one-pass,
no-vision experiments.

## Spend and limitations

- Five image pairs (`pair_039`–`pair_043`, six positive labels) were honestly
  recorded `not_run` because the AICredits text gateway is not the benchmark's
  Gemini vision path.
- The saved v1.6 pass used approximately ₹15.58. v1.7 used approximately ₹9.96;
  the contemporaneous baseline used approximately ₹9.33. Preflight and the
  unsaved rejected attempt also consumed credit.
- Remaining wallet balance after the final check: approximately **₹36.61**.
- Only one pass per experimental prompt was run. A three-pass claim is not made.

Any next omission experiment should be developed on a separate development
corpus and frozen before returning to this benchmark. Do not tune further to
named frozen pairs.
