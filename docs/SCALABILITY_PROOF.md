# Scalability & Reliability — Prototype Proof

**Honest scope:** Pramaan is a **demo / prototype-hardened** build. This document
describes a *prototype-level* scalability proof — enough to show the shape scales
and to keep the live demo reliable under a burst — **not** a production system.
Everything here is **single-instance and in-memory**; a restart or a second
replica loses this state.

Implemented in `backend/jobs.py` (+ `/analyze`, `/jobs/*` in `backend/main.py`),
probed by `scripts/load_test_demo.py`. Tests: `tests/test_jobs_cache.py`.

---

## 1. What was added

### Idempotency / input-hash caching
Every analysis is keyed by
```
input_hash = sha256(owner_doc + vendor_doc + system_id + pipeline_signature)
pipeline_signature = "<primary_provider>:<model>:<PROMPT_VERSION>"
```
- An identical spec+submittal (same model/prompt version) is **computed once**
  and reused; the response carries `cached: true`. A model or prompt change flips
  the signature and invalidates old entries.
- **Single-flight:** concurrent identical requests coalesce behind a per-hash
  lock, so a burst of duplicates triggers **one** compute, not N. (Test:
  `test_single_flight_computes_once`.)
- The hash is **one-way** and reversible to nothing; **no secrets and no raw
  uploaded bytes are cached** — only the computed deviations + metadata (hashes,
  timings, mode). Cache is bounded (LRU, `PRAMAAN_CACHE_MAX=256`) with a TTL
  (`PRAMAAN_CACHE_TTL_S=3600`).

Every `/analyze` response now includes `request_id`, `input_hash`, and `cached`
for traceability.

### Async-style job flow
```
POST /jobs/analyze      -> 202 { job_id, request_id, input_hash, status:"queued", poll, result }
GET  /jobs/{job_id}     -> status metadata (queued|running|done|error, timings, latency_ms, cached)
GET  /jobs/{job_id}/result -> 200 done + deviations | 202 running | 404 unknown/expired
```
A bounded in-memory job store (`PRAMAAN_JOB_MAX=256`) + a small worker pool
(`PRAMAAN_JOB_WORKERS=2`) run analyses off the request thread and reuse the
cache. Same auth + analysis rate limit as `/analyze`; job-status GETs require
auth (when enabled) but are not rate-limited (polling). Unguessable 128-bit ids.

`GET /health` → `scalability` block exposes non-secret counters
(`cache_entries`, `cache_max`, `jobs_tracked`, `job_workers`, `pipeline_signature`).

---

## 2. Load-test method

`scripts/load_test_demo.py` fires N requests at a chosen concurrency and reports
attempted / success / error / 429 counts, p50 & p95 latency, throughput, cache
hits, and the analysis-mode mix (llm / deterministic / cached).

**Safe by default:** it sends the *same* payload, so after a one-request warm-up
every hit is a cache hit — **at most one real analysis is computed** regardless
of `--requests`, and no LLM quota is burned. `--vary` forces distinct
(uncached) inputs and prints a quota warning.

```powershell
# in-process, no network (default, safe):
python scripts/load_test_demo.py --local --requests 20 --concurrency 5
# against a running server:
python scripts/load_test_demo.py --base-url http://localhost:8000 --requests 20 --concurrency 5
# pure throughput (no analysis): --method GET --endpoint /health
```

### Measured (local, in-process, deterministic engine)

`--local --requests 20 --concurrency 5` (rate limiting off):
```
success (2xx)      : 20  (100.0%)
errors             : 0
rate-limited (429) : 0
latency p50 / p95  : 16 / 21 ms
throughput         : ~300 req/s
cache hits         : 20   (all served from cache after warm-up)
analysis modes     : { deterministic: 20 }
```

Rate-limit behavior — `--requests 25 --concurrency 5`,
`PRAMAAN_ANALYSIS_LIMIT_PER_HOUR=10`:
```
success (2xx)      : 9
rate-limited (429) : 16     (clean 429 + Retry-After; warm-up consumed 1 slot)
errors             : 0
```

**What this shows:** the pipeline stays correct and fast under concurrency,
caching/single-flight makes repeated work free (and quota-safe), and the limiter
sheds excess load cleanly rather than failing. **What it does NOT show:**
multi-node throughput, sustained real-LLM load, or behavior under memory
pressure — those need the production pieces below.

### Limitations of the probe
- In-process `--local` mode shares the interpreter with the app (not a true
  network/multi-process load test); `--base-url` adds real HTTP but is still
  single-client.
- Latency reflects the deterministic engine unless a live LLM key is present.
- Numbers are indicative on a laptop, not a benchmarked SLA.

---

## 3. Honest limitations (current state)

- **Not distributed.** The rate limiter, cache, and job store are all
  **in-process** — no shared state across replicas, no persistence across
  restart. On a multi-instance deploy each replica limits/caches independently.
- **No tenant isolation.** There is no per-tenant auth, quota, or data
  separation — the optional demo token is a single shared secret, not
  access control.
- **Rate limiting is best-effort.** Keyed by `X-Forwarded-For` (client-settable);
  it slows abuse, it is not DDoS protection.
- **Jobs are ephemeral.** Job/cache entries are bounded and lost on restart;
  there is no durable result store.

## 4. What production would need

| Concern | Prototype (now) | Production |
|---|---|---|
| Rate limiting | in-process sliding window | **Redis** (or gateway) shared counter behind a trusted proxy |
| Result cache / idempotency | in-memory LRU+TTL | Redis / durable KV, keyed by the same input hash |
| Job queue | in-process thread pool | **worker queue** (Celery/RQ/Cloud Tasks) + brokers, retries, backpressure |
| Result store | in-memory dict | **persistent DB** (Postgres/object store) with TTL/GC |
| Multi-tenant | none | **tenant auth**, per-tenant quotas + data isolation |
| Observability | logs + `/health` | **tracing** (OpenTelemetry), metrics, structured request-id propagation |
| Horizontal scale | single instance | stateless app + externalized state (all of the above) |

The input-hash contract and the submit→poll→result shape are deliberately the
same ones a production queue would use, so the migration is "swap the in-memory
store for Redis/DB + a real worker," not a rewrite.
