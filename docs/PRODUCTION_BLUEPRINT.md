# Pramaan Production Blueprint

This is the target architecture for taking the hackathon prototype into a
serious hosted service. It is not a claim that every item below is already live.

## Current public shape

- Frontend: Next.js on Vercel.
- Backend: FastAPI on Render.
- Evidence: repository-tracked fixtures, benchmark runs, labels, and docs.
- Demo hardening: optional token auth, upload validation, in-memory rate limits,
  prompt-injection-resistant prompts, status endpoints without secret leakage.
- Verification: GitHub Actions, Python tests, frontend type/build checks, Docker
  smoke test, benchmark manifest/hash validation.

## Target service topology

| Layer | Target | Why it matters |
|---|---|---|
| Frontend | Vercel app with `/judge`, `/evidence`, authenticated project workspace | Keeps the judge path fast while supporting real users later |
| API | FastAPI service behind managed TLS | Existing API shape remains stable |
| Queue | Redis/Valkey queue or managed job queue | OCR, LLM calls, and benchmark jobs should not block request threads |
| Worker | Separate worker service sharing the API image | Long document jobs, retries, and scheduled re-checks |
| Database | Postgres with pgvector | Projects, documents, findings, reviewer state, embeddings, audit history |
| Object store | S3-compatible bucket | Uploaded PDFs/images/source artifacts stored by SHA-256 |
| Cache/rate limit | Redis/Valkey | Shared rate limits, result cache, provider-budget counters |
| Observability | Structured logs, traces, uptime checks, error alerts | Proves failures are visible and diagnosable |
| Secrets | Managed env/secrets per environment | No keys in repo; provider order and budgets configured per deployment |

## Request flow

```text
Browser upload
  -> API validates MIME/magic bytes/size
  -> object store writes raw artifact by SHA-256
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

## Next build order

P0: finish pitch video, reviewer-2/adjudication, and stored source artifacts.

P1: add Postgres + object storage + worker queue + shared rate limit.

P2: add authenticated workspaces, reviewer assignment, source archive UI,
observability dashboards, and scheduled delta re-checks.
