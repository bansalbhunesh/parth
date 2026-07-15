# Performance evidence

This directory contains dated, non-overwriting summaries of performance runs.
Each artifact records the source revision, profile, tool/runtime metadata,
individual samples, medians, source-report hashes, and limitations.

Local lab artifacts are directional diagnostics, not production Core Web
Vitals or release proof. The release gate requires repeatable Linux/production
Lighthouse results and field INP p75 evidence.

## 2026-07-15 exact-revision Windows diagnostic

Source revision: `6815984`. Profile: Lighthouse 13.4.0 default mobile simulated
throttling against the production standalone homepage. The compact artifact is
[`2026-07-15_6815984_local-mobile-lighthouse.json`](2026-07-15_6815984_local-mobile-lighthouse.json).

| Run | Performance | Accessibility | Best practices | SEO | LCP | TBT | CLS | Host benchmark |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 79 | 100 | 100 | 100 | 2,677 ms | 654 ms | 0 | 1,022.0 |
| 2 | 78 | 100 | 100 | 100 | 2,715 ms | 676 ms | 0 | 996.5 |
| 3 | 82 | 100 | 100 | 100 | 2,671 ms | 566 ms | 0 | 1,237.5 |
| Median | 79 | 100 | 100 | 100 | 2,677 ms | 654 ms | 0 | 1,022.0 |

The host benchmark was materially lower than an earlier non-exact working-tree
sample, so this evidence does not support a 95+ performance claim. Lighthouse
wrote and parsed every JSON report before the Windows Chrome launcher emitted
its known temporary-profile cleanup error.
