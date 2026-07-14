# ADR-001: Managed production platform

Status: accepted for the production foundation; local/demo adapters remain supported.

## Decision

Use Supabase Postgres, Auth, private Storage, and Queues as authoritative production services. Use Redis only for shared rate limiting, short-lived cache, provider budgets, and idempotency leases. Keep SQLite and in-process jobs for deterministic local/demo operation.

Production authorization derives from verified bearer JWT subjects and database membership checks. Every exposed table uses RLS. Worker-only tables and functions stay in a private schema. Uploaded objects live in a private bucket under organization/case paths and are accessed through short-lived signed URLs after authorization.

Queue consumers use visibility timeouts, archive only after successful processing, dead-letter after a bounded attempt count, and make visible effects idempotent. Redis failure closes expensive write/analysis paths and may allow inexpensive reads with an alert.

## Compatibility

`/api/v1` is the managed contract. Legacy routes remain deprecated for one compatibility release. `/api/v1/demo/*` remains bounded, deterministic, and non-persistent. Local case-secret mode must not be enabled in production.

## Migration

Schema changes are reviewed migrations. Data cutover uses expand/contract changes, a staging reset, count/hash verification of the SQLite import, canary traffic, and a monitored acceptance window. A rollback never depends on destructive queue reads.
