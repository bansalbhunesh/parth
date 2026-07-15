# Pramaan Production Blueprint

This document separates the repository's implemented production foundation
from deployment evidence. The public demo still uses the bounded local/demo
path; the managed services below are not claimed as live until a staging or
production environment proves them.

## Current public shape

- Frontend: Next.js on Vercel.
- Backend: FastAPI on Render.
- Evidence: repository-tracked fixtures, benchmark runs, labels, and docs.
- Demo hardening: optional token auth, upload validation, in-memory rate limits,
  prompt-injection-resistant prompts, status endpoints without secret leakage.
- Verification: GitHub Actions, Python tests, frontend type/build checks, Docker
  smoke test, benchmark manifest/hash validation.
- Local/demo persistence: SQLite, case secrets, and an in-process job runner for
  deterministic use without managed infrastructure.

## Implemented production foundation

- Versioned `/api/v1` contracts with RFC 9457 problem details, request IDs,
  idempotency keys, cursor pagination, ETags/version checks, and compatibility
  routes for one deprecation window.
- Supabase Postgres/Auth/private Storage/Queues migrations with database
  membership authorization, RLS, private worker objects, tenant-consistent
  foreign keys, retention enforcement, and explicit deny-by-default grants.
- Repository, queue, cache, identity, storage, worker, and webhook adapters so
  managed services do not leak into domain logic.
- Redis-backed shared limits, cache, and idempotency leases with explicit
  fail-open/fail-closed behavior; Redis is never authoritative case/job storage.
- Correlated request/job IDs, structured logging, readiness checks, metrics,
  traces, retry/dead-letter behavior, and signed webhook delivery records.
- CI database reset, pgTAP RLS/tenant-isolation tests, schema lint, and security
  and performance advisors.

## Deployment topology

| Layer | Target | Why it matters |
|---|---|---|
| Frontend | Vercel app with `/judge`, `/evidence`, authenticated project workspace | Keeps the judge path fast while supporting real users later |
| API | FastAPI service behind managed TLS | Existing API shape remains stable |
| Queue | Supabase durable Queues | Visibility timeouts, retries, and dead letters without destructive pre-acknowledgement |
| Worker | Separate worker service sharing the API image | Long document jobs, retries, and scheduled re-checks |
| Database | Supabase Postgres with RLS | Organizations, cases, documents, findings, reviewer state, and audit history |
| Object store | Supabase private Storage | Authorized organization/case paths with short-lived signed URLs |
| Cache/rate limit | Redis | Shared limits, short cache, provider budgets, and idempotency leases only |
| Observability | Structured logs, traces, uptime checks, error alerts | Proves failures are visible and diagnosable |
| Secrets | Managed env/secrets per environment | No keys in repo; provider order and budgets configured per deployment |

## Request flow

```text
Browser upload
  -> API validates MIME/magic bytes/size
  -> private storage writes raw artifact by organization/case path and SHA-256
  -> database records document + project state
  -> queue schedules extraction/analyze job
  -> worker extracts text/OCR/images and calls reasoning graph
  -> findings, citations, Cx mapping, and audit trail are persisted
  -> frontend streams job status and renders results from durable state
```

## Release gates

Minimum gate before a public demo:

```bash
make demo-gate
python scripts/check_submission_ready.py
```

`check_submission_ready.py` is intentionally separate because it should fail
until the required pitch-video links are filled.

Additional gate before a paid pilot:

- Two-person benchmark adjudication completed or clearly scoped to a smaller
  pilot benchmark.
- Stored source artifacts hashed and linked from the benchmark manifest.
- Shared-store auth and rate limiting enabled.
- Background worker queue enabled for uploaded documents.
- Error monitoring wired to deployment alerts.
- Data-retention and deletion policy written.
- At least one practitioner screen-share review logged as product feedback, not
  as an accuracy claim.

## Failure-mode posture

| Failure | Expected behavior |
|---|---|
| LLM quota/rate limit | Fail over through configured providers, then deterministic fallback |
| OCR unavailable | `/ocr-check` reports unavailable; UI avoids implying OCR support |
| Worker crash | Job marked retryable/failed; uploaded artifact remains addressable by SHA |
| Source URL changes | Stored artifact hash remains stable once source files are archived |
| User uploads hostile file | Reject by type/size/magic-byte checks before parsing |
| Model returns malformed JSON | Retry boundedly; fall back or return labelled partial state |

## Next evidence order

P0: finish pitch video, reviewer-2/adjudication, and stored source artifacts.

P0: configure staging Supabase/Redis/OTLP secrets, apply migrations through the
reviewed release workflow, and prove authenticated organization isolation.

P1: deploy two API replicas plus an independently scalable worker; rehearse
queue retries, worker termination, dead letters, storage deletion, backup
restore, and alert delivery.

P2: complete the independent accessibility and security reviews, two-hour load
and soak profile, and three representative pilots/30 cases. Until those pass,
the implementation is production-oriented but not independently certified.
