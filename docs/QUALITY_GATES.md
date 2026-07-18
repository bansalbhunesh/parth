# Evidence-backed quality gates

Passing a gate means the named artifact or command exists and passes. It does not mean the software has no possible defects.

## Enforced in CI

- Python production and CI dependencies are resolved for CPython 3.11/Linux in hash-checked lock files. Regenerate them only with the exact `uv pip compile` commands recorded in their headers and review the diff.
- Python warnings fail tests; Ruff and strict mypy cover the new platform boundary.
- Backend files are at most 500 lines, cyclomatic complexity is at most 10, and backend imports are acyclic.
- The reviewed OpenAPI snapshot and protected scope must not drift.
- Frontend TypeScript is strict; active-component coverage thresholds are 95% statements/lines and 90% branches/functions.
- Every discovered page must keep its initial JavaScript at or below 200 KiB gzip, measured from the standalone production bundle.
- Playwright runs critical journeys on Chromium, Firefox, WebKit, Pixel, and iPhone profiles, including Axe, forced colors, reduced motion, reflow, focus, names, and headings.
- Playwright builds and serves the standalone production bundle with bounded workers; development HMR behavior is outside the release gate.
- Supabase CI rebuilds every migration from an empty database, runs pgTAP structural and behavioral RLS tests, lints the public/private schemas, and fails on security or performance advisor warnings.
- Dependency, source, secret, container, and CodeQL scans run with pinned actions and least-privilege workflow permissions.
- Backend and frontend containers are digest-pinned, non-root, health-checked, and scanned for high/critical findings.
- A CycloneDX SBOM is generated on every CI run.
- The scheduled or explicitly `mutation-ready` PR run fails below an 85% mutation score and rejects incomplete runs. Detected mutants are reported as explicit test/type-check kills and bounded timeouts separately; survivors, untested, suspicious, crashed, or incomplete mutants never count as detected.

Backend coverage is ratcheted at the final 95% line and 90% branch threshold. Security, job state/idempotency, citation provenance, Redis cache, durable worker, and webhook delivery modules must each retain 100% line and branch coverage. Every other backend module must additionally clear an 80% line / 65% branch per-file floor so no single file can silently rot behind the whole-tree average; `backend/agents/ocr_util.py` is the one documented exemption, because its coverage depends on the tesseract binary, which is present only in the container image. The threshold only increases through tests that assert behavior, never exclusions or generated lines.

## Latest verified working-tree evidence (2026-07-18)

- Backend: 898 tests; 97.17% line and 93.09% branch coverage; every critical module is 100% line and branch covered, and every non-exempt module clears the 80% line / 65% branch per-file floor. A CI claim gate (`scripts/check_claim_counts.py`) now fails the build when any published test count drifts from the collected suite.
- Frontend: 72 tests; 98.78% line and 91.31% branch coverage; strict TypeScript, design-system audit, dependency audit, and production build pass. Every discovered page is within the enforced 200 KiB initial-JavaScript budget (181.25-189.54 KiB gzip in the latest local build).
- Browser: 160/160 production-mode journeys pass (latest green CI on `main`) across Chromium, Firefox, WebKit, Pixel, and iPhone projects, including exact visible-label matching, route-wide console/error/rejection guards, no-JavaScript navigation, and deferred-layout anchor behavior.
- Database: empty reset succeeds; 36/36 pgTAP assertions pass; schema lint and both database advisors report no issues.
- Security/evidence: both locked Python dependency audits are clean, Bandit reports no medium/high issue, and the frozen benchmark manifest/hash/calibration/evaluation checks pass.
- Mutation: two consecutive completed remote gates each scored 1,315 mutants and passed well above the enforced 85% minimum: 97.26% (768 explicit kills, 511 bounded timeouts, 36 survivors) and 96.73% (767 explicit kills, 505 bounded timeouts, 43 survivors). Exact-head status remains a required PR check.

## Implemented but deployment-dependent

- Supabase migrations define tenant tables, database membership authorization, RLS, private storage, durable queues, retention fields, and worker-private objects.
- Production adapters cover asymmetric JWT verification, Redis fail modes, signed storage URLs, visibility-timeout queue reads, dead-letter handling, and worker idempotency boundaries.
- OTLP trace export activates when `OTEL_EXPORTER_OTLP_ENDPOINT` is configured.
- Managed Supabase, Redis, worker, and OTLP behavior still requires a configured staging or production environment even though the local migration and adapter contracts pass.

## External gates still required before a 10/10 claim

- The mobile performance lab target is now met on Linux. A `ubuntu-latest` Lighthouse job (`.github/workflows/perf.yml`, `@lhci/cli`, five mobile runs, median-of-five) against the standalone bundle scored a **median 97** (runs 75/97/97/97/99), median LCP 2.535 s, median TBT 74 ms — versus the earlier memory-constrained Windows median of 79 (TBT 654 ms), which was CPU starvation, not a bundle-budget problem. The single 75 is a cold-start outlier; four of five runs scored ≥ 97. This is a lab measurement recorded as evidence, not yet a per-push blocking gate. Production **INP p75** (real-user field data via a Speed-Insights-style collector) remains the one outstanding mobile-performance artifact.
- Independent WCAG 2.2 AA keyboard and screen-reader review.
- External penetration test with no open critical/high issue.
- Staging restore rehearsal proving RPO/RTO, deletion across database/storage, load/soak, worker termination, and alerts.
- Three representative pilots covering at least 30 cases, with measured task success and citation correctness.

Results belong in dated, immutable evidence artifacts. Until those reviews exist, the product must be described as production-oriented, not independently production-certified.
