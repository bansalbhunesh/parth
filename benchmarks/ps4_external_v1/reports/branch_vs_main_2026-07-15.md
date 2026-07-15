# Main vs branch — clean three-pass comparison

Generated `2026-07-15T16:35:53+00:00` from frozen `ps4_external_v1` evidence.

| Metric | Main published series | Branch `branch-e2e-9d8ac01` | Δ branch − main |
|---|---:|---:|---:|
| Semantic recall | 0.8624 | 0.9101 | +0.0477 |
| Precision | 0.9534 | 0.8006 | -0.1528 |
| F1 | 0.9055 | 0.8517 | -0.0538 |
| Exact recall | 0.6984 | 0.7619 | +0.0635 |
| Clean-negative FAR | 0.0000 | 0.0417 | +0.0417 |
| False positives | 2.6667 | 14.3333 | +11.6666 |
| Latency p50 (ms) | 2481.3333 | 1994.3333 | -487.0000 |
| Latency p95 (ms) | 8490.5667 | 4092.3333 | -4398.2334 |
| Not-run pairs | 0.3333 | 0.0000 | -0.3333 |

**Verdict:** `mixed`

**Branch vision completeness:** `True`

**Branch revision:** `9d8ac01c71159183bb555a3e7d4105e005ac9219`

Main runs: `2026-07-04_openai_google-gemini-3.1-flash-lite_run1`, `2026-07-04_openai_google-gemini-3.1-flash-lite_run2`, `2026-07-04_openai_google-gemini-3.1-flash-lite_run3`

Branch runs: `2026-07-15_openai_google-gemini-3.1-flash-lite_branch-e2e-9d8ac01_run1`, `2026-07-15_openai_google-gemini-3.1-flash-lite_branch-e2e-9d8ac01_run2`, `2026-07-15_openai_google-gemini-3.1-flash-lite_branch-e2e-9d8ac01_run3`

## Limitations

- Three passes estimate run-to-run variation but do not establish field accuracy.
- The benchmark sources and labels remain team-authored and single-author frozen.
