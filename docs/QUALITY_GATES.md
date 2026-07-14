# Evidence-backed quality gates

Passing a gate means the named artifact or command exists and passes. It does not mean the software has no possible defects.

## Enforced in CI

- Python production and CI dependencies are resolved for CPython 3.11/Linux in hash-checked lock files. Regenerate them only with the exact `uv pip compile` commands recorded in their headers and review the diff.
- Python warnings fail tests; Ruff and strict mypy cover the new platform boundary.
- Backend files are at most 500 lines, cyclomatic complexity is at most 10, and backend imports are acyclic.
- The reviewed OpenAPI snapshot and protected scope must not drift.
- Frontend TypeScript is strict; active-component coverage thresholds are 95% statements/lines and 90% branches/functions.
- Playwright runs critical journeys on Chromium, Firefox, WebKit, Pixel, and iPhone profiles, including Axe, forced colors, reduced motion, reflow, focus, names, and headings.
- Dependency, source, secret, container, and CodeQL scans run with pinned actions and least-privilege workflow permissions.
- Backend and frontend containers are digest-pinned, non-root, health-checked, and scanned for high/critical findings.
- A CycloneDX SBOM is generated on every CI run.

The backend floor is currently ratcheted independently at 88% line and 78% branch coverage, not the final 95%/90% exit threshold. The threshold must only increase with tests that assert behavior, not exclusions or generated lines.

## Implemented but environment-dependent

- Supabase migrations define tenant tables, database membership authorization, RLS, private storage, durable queues, retention fields, and worker-private objects.
- Production adapters cover asymmetric JWT verification, Redis fail modes, signed storage URLs, visibility-timeout queue reads, dead-letter handling, and worker idempotency boundaries.
- OTLP trace export activates when `OTEL_EXPORTER_OTLP_ENDPOINT` is configured.
- Local Docker and Supabase reset rehearsals depend on a running Docker engine.

## External gates still required before a 10/10 claim

- Independent WCAG 2.2 AA keyboard and screen-reader review.
- External penetration test with no open critical/high issue.
- Staging restore rehearsal proving RPO/RTO, deletion across database/storage, load/soak, worker termination, and alerts.
- Three representative pilots covering at least 30 cases, with measured task success and citation correctness.

Results belong in dated, immutable evidence artifacts. Until those reviews exist, the product must be described as production-oriented, not independently production-certified.
