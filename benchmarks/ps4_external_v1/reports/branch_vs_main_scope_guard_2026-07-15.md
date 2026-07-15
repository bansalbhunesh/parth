# Main vs branch — clean three-pass comparison

Generated `2026-07-15T16:54:49+00:00` from frozen `ps4_external_v1` evidence.

| Metric | Main published series | Branch `branch-e2e-541dae8-scope-guard` | Δ branch − main |
|---|---:|---:|---:|
| Semantic recall | 0.8624 | 0.7619 | -0.1005 |
| Precision | 0.9534 | 0.9173 | -0.0361 |
| F1 | 0.9055 | 0.8324 | -0.0731 |
| Exact recall | 0.6984 | 0.6137 | -0.0847 |
| Clean-negative FAR | 0.0000 | 0.0104 | +0.0104 |
| False positives | 2.6667 | 4.3333 | +1.6666 |
| Latency p50 (ms) | 2481.3333 | 2160.3333 | -321.0000 |
| Latency p95 (ms) | 8490.5667 | 6040.6667 | -2449.9000 |
| Not-run pairs | 0.3333 | 0.0000 | -0.3333 |

**Verdict:** `main_stronger`

**Branch vision completeness:** `True`

**Branch revision:** `541dae88ef77acd291c605ea9cc176eefd1f1959`

Main runs: `2026-07-04_openai_google-gemini-3.1-flash-lite_run1`, `2026-07-04_openai_google-gemini-3.1-flash-lite_run2`, `2026-07-04_openai_google-gemini-3.1-flash-lite_run3`

Branch runs: `2026-07-15_openai_google-gemini-3.1-flash-lite_branch-e2e-541dae8-scope-guard_run1`, `2026-07-15_openai_google-gemini-3.1-flash-lite_branch-e2e-541dae8-scope-guard_run2`, `2026-07-15_openai_google-gemini-3.1-flash-lite_branch-e2e-541dae8-scope-guard_run3`

## Limitations

- Three passes estimate run-to-run variation but do not establish field accuracy.
- The benchmark sources and labels remain team-authored and single-author frozen.
