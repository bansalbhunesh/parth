# Main vs branch — clean three-pass comparison

Generated `2026-07-16T12:21:02+00:00` from frozen `ps4_external_v1` evidence.

| Metric | Main published series | Branch `main-live3-cc6b118` | Δ branch − main |
|---|---:|---:|---:|
| Semantic recall | 0.8624 | 0.8942 | +0.0318 |
| Precision | 0.9534 | 0.8802 | -0.0732 |
| F1 | 0.9055 | 0.8871 | -0.0184 |
| Exact recall | 0.6984 | 0.7355 | +0.0371 |
| Clean-negative FAR | 0.0000 | 0.0000 | +0.0000 |
| False positives | 2.6667 | 7.6667 | +5.0000 |
| Latency p50 (ms) | 2481.3333 | 2198.0000 | -283.3333 |
| Latency p95 (ms) | 8490.5667 | 3518.0667 | -4972.5000 |
| Not-run pairs | 0.3333 | 0.0000 | -0.3333 |

**Verdict:** `mixed`

**Branch vision completeness:** `True`

**Branch revision:** `cc6b118d6738900f1683e8655d295440320f6b18`

Main runs: `2026-07-04_openai_google-gemini-3.1-flash-lite_run1`, `2026-07-04_openai_google-gemini-3.1-flash-lite_run2`, `2026-07-04_openai_google-gemini-3.1-flash-lite_run3`

Branch runs: `2026-07-16_openai_google-gemini-3.1-flash-lite_main-live3-cc6b118_run1`, `2026-07-16_openai_google-gemini-3.1-flash-lite_main-live3-cc6b118_run2`, `2026-07-16_openai_google-gemini-3.1-flash-lite_main-live3-cc6b118_run3`

## Limitations

- Three passes estimate run-to-run variation but do not establish field accuracy.
- The benchmark sources and labels remain team-authored and single-author frozen.
- The published main summaries predate exact code-revision and provider-used metadata, so this is same-model/dataset evidence rather than an isolated code-only A/B test.
- Main averaged 0.333 not-run pairs; branch ran every pair including vision, so recall also reflects evaluation completeness.
