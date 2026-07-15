# Scalability and reliability evidence

**Status:** repository-controlled foundation implemented; production capacity is
not yet certified.

Pramaan has two deliberately different runtime postures. The local/public-demo
path stays deterministic and low-operations. The managed production path has
reviewed interfaces, adapters, and database migrations, but it becomes evidence
only after those services are configured and exercised in staging.

## 1. Runtime boundaries

| Path | Current implementation | What is proven |
|---|---|---|
| Local/public demo | SQLite plus bounded in-process cache, rate limits, and jobs | Unit, integration, mutation, browser, and local HTTP probes |
| Managed production foundation | Supabase Postgres/Auth/private Storage/Queues, Redis limits/cache/leases, durable worker, signed webhooks, and optional OTLP export | Adapter contracts, migration reset, 36 pgTAP assertions, schema lint, and clean database advisors |
| Deployed production topology | At least two API replicas and an independently scalable worker | **Not yet proven**; requires configured staging, load/soak, failure injection, restore, and alert evidence |

The managed foundation does not silently turn the demo deployment into a
production system. `docs/PRODUCTION_BLUEPRINT.md` records the required cutover
and `docs/ADR-001-MANAGED-PLATFORM.md` records the authoritative-service
decision.

## 2. Local/demo reliability behavior

### Idempotency and input-hash caching

Each analysis is keyed by:

```text
input_hash = sha256(owner_doc + vendor_doc + system_id + pipeline_signature)
pipeline_signature = "<primary_provider>:<model>:<PROMPT_VERSION>"
```

- Identical work is reused and returns `cached: true`.
- Concurrent identical requests coalesce behind a per-hash lock.
- The cache stores results and bounded metadata, never raw uploaded bytes.
- Cache size and TTL are bounded by `PRAMAAN_CACHE_MAX` and
  `PRAMAAN_CACHE_TTL_S`.
- Model or prompt changes alter the pipeline signature and invalidate stale
  entries.

### Local job flow

```text
POST /jobs/analyze          -> 202 queued job
GET  /jobs/{job_id}         -> queued | running | done | error
GET  /jobs/{job_id}/result  -> result | 202 | 404
```

This compatibility path is intentionally in-process and restart-ephemeral. It
is not the production queue. The production worker uses visibility-timeout
reads, bounded retries, dead-letter handling, and archives only after successful
processing.

### Health semantics

- `GET /health/live` performs no dependency I/O and stays on the event loop.
- `GET /health/ready` checks the configured authoritative dependencies and
  returns 503 when configuration or a required dependency is unavailable.
- `GET /health` preserves the legacy diagnostic payload from cached,
  non-secret state.
- `/internal/metrics` is private and returns 404 without the configured bearer
  token.

## 3. Managed production foundation

Repository-controlled production pieces include:

- strict Supabase JWT verification and database-membership authorization;
- RLS on every exposed tenant table and private worker-only objects;
- private organization/case storage paths with short-lived signed URLs;
- Supabase Queue reads with visibility timeouts and non-destructive
  acknowledgement;
- Redis shared rate limits, short cache, provider budgets, and idempotency
  leases, never authoritative case/job storage;
- tenant-consistent foreign keys, retention enforcement, webhook delivery
  records, retry scheduling, and audit events;
- correlated request/job identifiers, structured logs, optional OTLP traces,
  and private operational metrics.

These pieces are covered by tests and migration checks. They are not a claim
that a managed environment has been provisioned, restored, soaked, or failed
over successfully.

## 4. Reproducible load probe

`scripts/load_test_demo.py` supports two modes:

- `--local`: in-process `TestClient` for a fast behavioral probe;
- `--base-url`: bounded asynchronous HTTP concurrency against a running server.

The safe default repeats one payload. After one warm-up, requests reuse the
input-hash cache and do not spend one provider call per request. `--vary`
defeats the cache and prints an explicit quota warning.

```powershell
# Fast local behavior check
python scripts/load_test_demo.py --local --requests 20 --concurrency 5

# Real HTTP health probe
python scripts/load_test_demo.py `
  --base-url http://127.0.0.1:8000 `
  --method GET --endpoint /health/live `
  --requests 1000 --concurrency 20

# Immutable evidence: revision and topology label are mandatory, and an
# existing artifact is never overwritten.
python scripts/load_test_demo.py `
  --base-url https://staging.example.test `
  --method GET --endpoint /health/live `
  --requests 1000 --concurrency 20 `
  --revision <git-sha> `
  --profile-label staging-two-api-replicas `
  --json-output docs/evidence/load/<dated-name>.json
```

Artifacts contain the target, revision, topology label, request profile,
runtime, success/error/rate-limit counts, throughput, p50/p95/min/max latency,
cache/mode mix, and explicit limitations. Tokens are never recorded.

## 5. Latest local HTTP evidence

The dated artifacts in `docs/evidence/load/` are bound to source revision
`ed152ca` and the `local-windows-two-uvicorn-workers` profile. With 20 concurrent
connections they recorded 100% success across 3,200 requests:

| Endpoint | Requests | p50 | p95 | Throughput |
|---|---:|---:|---:|---:|
| `/health/live` | 1,000 | 27 ms | 83 ms | 555.2 req/s |
| `/health/ready` | 1,000 | 37 ms | 111 ms | 412.2 req/s |
| `/health` | 1,000 | 36 ms | 128 ms | 305.0 req/s |
| `/analyze` repeated cached input | 200 | 49 ms | 138 ms | 322.1 req/s |

The liveness result clears the directional 100 ms p95 target in this local
profile. It does not award the production gate: the run used two local Uvicorn
workers, no managed dependencies, no live model provider, and no failure
injection or sustained soak.

## 6. What local probes can and cannot prove

A local probe can expose correctness, queueing, connection, and single-host
bottlenecks. It cannot certify:

- production network or managed-service latency;
- multi-replica coordination or Redis/Supabase failure behavior;
- live-provider cost, latency, or quota behavior when the cached deterministic
  profile is used;
- recovery after worker termination;
- RPO/RTO, backup restore, cross-store deletion, or alert delivery;
- two-hour stability under 100 active users and 20 concurrent analyses.

The production exit gate therefore remains a staged two-hour soak with at least
two API replicas and one worker, 100 active users, 20 concurrent analyses,
worker termination without lost or duplicated visible effects, and tested
database/storage/provider/alert failure paths. Results must be committed as
dated, non-overwriting evidence artifacts before a 10/10 reliability claim.
