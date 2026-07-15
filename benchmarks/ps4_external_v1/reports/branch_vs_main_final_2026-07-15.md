# Main vs branch — clean three-pass comparison

Generated `2026-07-15T17:31:17+00:00` from frozen `ps4_external_v1` evidence.

| Metric | Main published series | Branch `branch-e2e-69aaf94-alphanumeric` | Δ branch − main |
|---|---:|---:|---:|
| Semantic recall | 0.8624 | 0.9048 | +0.0424 |
| Precision | 0.9534 | 0.9145 | -0.0389 |
| F1 | 0.9055 | 0.9096 | +0.0041 |
| Exact recall | 0.6984 | 0.7619 | +0.0635 |
| Clean-negative FAR | 0.0000 | 0.0260 | +0.0260 |
| False positives | 2.6667 | 5.3333 | +2.6666 |
| Latency p50 (ms) | 2481.3333 | 2371.6667 | -109.6666 |
| Latency p95 (ms) | 8490.5667 | 4074.0667 | -4416.5000 |
| Not-run pairs | 0.3333 | 0.0000 | -0.3333 |

**Verdict:** `mixed`

**Branch vision completeness:** `True`

**Branch revision:** `69aaf94b17448bc1f0b72faa1e17ff50455f116c`

Main runs: `2026-07-04_openai_google-gemini-3.1-flash-lite_run1`, `2026-07-04_openai_google-gemini-3.1-flash-lite_run2`, `2026-07-04_openai_google-gemini-3.1-flash-lite_run3`

Branch runs: `2026-07-15_openai_google-gemini-3.1-flash-lite_branch-e2e-69aaf94-alphanumeric_run1`, `2026-07-15_openai_google-gemini-3.1-flash-lite_branch-e2e-69aaf94-alphanumeric_run2`, `2026-07-15_openai_google-gemini-3.1-flash-lite_branch-e2e-69aaf94-alphanumeric_run3`

## Limitations

- Three passes estimate run-to-run variation but do not establish field accuracy.
- The benchmark sources and labels remain team-authored and single-author frozen.
- The published main summaries predate exact code-revision and provider-used metadata, so this is same-model/dataset evidence rather than an isolated code-only A/B test.
- Main averaged 0.333 not-run pairs; branch ran every pair including vision, so recall also reflects evaluation completeness.
