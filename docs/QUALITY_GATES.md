# Evidence-backed quality gates

Passing a gate means the named artifact or command exists and passes. It does not mean the software has no possible defects.

## Enforced in CI

- Python production and CI dependencies are resolved for CPython 3.11/Linux in hash-checked lock files. Regenerate them only with the exact `uv pip compile` commands recorded in their headers and review the diff.
- Python warnings fail tests; Ruff and strict mypy cover the new platform boundary.
- Backend files are at most 500 lines, cyclomatic complexity is at most 10, and backend imports are acyclic.
- The reviewed OpenAPI snapshot and protected scope must not drift.
- Frontend TypeScript is strict; active-component coverage thresholds are 95% statements/lines and 90% branches/functions.
- Playwright runs critical journeys on Chromium, Firefox, WebKit, Pixel, and iPhone profiles, including Axe, forced colors, reduced motion, reflow, focus, names, and headings.
- Playwright builds and serves the standalone production bundle with bounded workers; development HMR behavior is outside the release gate.
- Supabase CI rebuilds every migration from an empty database, runs pgTAP structural and behavioral RLS tests, lints the public/private schemas, and fails on security or performance advisor warnings.
- Dependency, source, secret, container, and CodeQL scans run with pinned actions and least-privilege workflow permissions.
- Backend and frontend containers are digest-pinned, non-root, health-checked, and scanned for high/critical findings.
- A CycloneDX SBOM is generated on every CI run.
- The scheduled or explicitly `mutation-ready` PR run fails below an 85% mutation score and rejects incomplete runs. Detected mutants are reported as explicit test/type-check kills and bounded timeouts separately; survivors, untested, suspicious, crashed, or incomplete mutants never count as detected.

Backend coverage is ratcheted at the final 95% line and 90% branch threshold. Security, job state/idempotency, citation provenance, Redis cache, durable worker, and webhook delivery modules must each retain 100% line and branch coverage. The threshold only increases through tests that assert behavior, never exclusions or generated lines.

## Latest verified working-tree evidence (2026-07-15)

- Backend: 832 tests; 96.43% line and 91.87% branch coverage; every critical module is 100% line and branch covered.
- Frontend: 43 component tests; 99.25% line and 91.72% branch coverage; strict TypeScript, design-system audit, dependency audit, and production build pass.
- Browser: 130/130 production-mode journeys pass across Chromium, Firefox, WebKit, Pixel, and iPhone projects.
- Database: empty reset succeeds; 36/36 pgTAP assertions pass; schema lint and both database advisors report no issues.
- Security/evidence: both locked Python dependency audits are clean, Bandit reports no medium/high issue, and the frozen benchmark manifest/hash/calibration/evaluation checks pass.
- Mutation: the latest complete raw metadata contains 1,315 mutants and scores 88.82% detected (665 explicit kills, 503 bounded timeouts, 147 survivors). The workflow/reporting compatibility fix requires a fresh remote run after this branch is pushed.

## Implemented but deployment-dependent

- Supabase migrations define tenant tables, database membership authorization, RLS, private storage, durable queues, retention fields, and worker-private objects.
- Production adapters cover asymmetric JWT verification, Redis fail modes, signed storage URLs, visibility-timeout queue reads, dead-letter handling, and worker idempotency boundaries.
- OTLP trace export activates when `OTEL_EXPORTER_OTLP_ENDPOINT` is configured.
- Managed Supabase, Redis, worker, and OTLP behavior still requires a configured staging or production environment even though the local migration and adapter contracts pass.

## External gates still required before a 10/10 claim

- Independent WCAG 2.2 AA keyboard and screen-reader review.
- External penetration test with no open critical/high issue.
- Staging restore rehearsal proving RPO/RTO, deletion across database/storage, load/soak, worker termination, and alerts.
- Three representative pilots covering at least 30 cases, with measured task success and citation correctness.

Results belong in dated, immutable evidence artifacts. Until those reviews exist, the product must be described as production-oriented, not independently production-certified.
