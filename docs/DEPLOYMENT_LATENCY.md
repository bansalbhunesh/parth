# Deployment Latency — Cold vs. Warm, by Endpoint

Answers the honest gap the external audit flagged: `scripts/verify_live.py`'s
10-check bundle took ~119s end-to-end, which conflates "one endpoint is slow"
with "the free-tier backend was cold" — this measures each endpoint
separately so the actual judge-facing risk is visible.

Measured with `scripts/measure_deployment_latency.py` against the live
deployment (`https://parth-1-ma30.onrender.com` backend on Render's free tier,
`https://parth-tan.vercel.app` frontend on Vercel) on **2026-07-11**. Raw
output: `docs/latency_final.json`.

## Cold start (backend genuinely idle beforehand)

| Endpoint | Cold latency |
|---|---|
| `GET /health` | **23.5s** |
| `POST /analyze` (first call) | **15.7s** |

These are real, not estimated: the prior 20-req/hour `/analyze` rate limit
and Render's own idle window were both allowed to lapse (~40 min of no
traffic) before this run, and the cold `/health` call landing at 23.5s —
two orders of magnitude above the ~250ms warm baseline below — is itself the
evidence the instance had actually spun down rather than merely being the
first request of a warm instance.

**What this means for a judge:** if a judge is the first visitor in >15
minutes, the *first* page action that touches the backend (loading `/judge`
is fine — that's a Vercel-served static/ISR route with no cold-start
penalty; the first `/analyze` call is what pays it) can sit for **~20-25
seconds** before anything happens. That is a real attention-window risk on a
demo day with gaps between judges, and is now measured rather than
guessed at.

## Warm (backend already responding to traffic)

| Endpoint | n | p50 | p95 | min | max |
|---|---|---|---|---|---|
| `GET /health` | 10 | 247ms | 371ms | 205ms | 371ms |
| `GET /judge` (page HTML) | 10 | 165ms | 207ms | 126ms | 207ms |
| `POST /analyze` (distinct payload, real LLM call) | 3 | 6.5s | 6.7s | 4.9s | 6.7s |
| `POST /analyze/stream` (time-to-first-token) | 3 | 1.8s | 12.5s | 1.6s | 12.5s |

**Honest caveats on the last two rows, stated plainly rather than dressed
up:**
- **n=3, not a tight interval.** The `/analyze` and `/analyze/stream`
  endpoints are rate-limited to 20 requests/hour per client (by design, to
  protect the shared upstream LLM provider quota — see
  `backend/security.py`), and this script had already spent part of that
  budget on the cold-start sample plus earlier throwaway runs in the same
  hour. A 3-sample p95 is really just "the max," not a real tail estimate;
  treat these as directional, not a committed SLA.
- **These warm samples were taken immediately after the cold-start call**,
  not after a separate steady-state warm-up period, so some of the ~5-7s
  seen here may still include connection/provider-pool warm-up rather than
  pure steady-state latency. The benchmark's own cited **p50 ~2.5s**
  (`docs/ARCHITECTURE.md` evidence section, from the frozen
  `ps4_external_v1` eval harness) was measured in a different, more
  controlled context and should not be read as contradicting this — they're
  answering different questions (offline eval throughput vs. one live
  judge-facing request over the public internet, including LLM failover
  possibly landing on a slower configured leg).
- **The `/analyze/stream` max (12.5s) is a likely failover event**, not a
  representative number: the demo's provider chain
  (`gemini,groq,qwen,claude`, per `docs/pramaan-llm-failover` state) retries
  a slower leg on a timeout/quota miss from a faster one, and one sample out
  of three landing well above the other two is consistent with that, not
  with a broken endpoint (all 3 samples returned `ok=True`).

## What this closes, and what it doesn't

**Closes:** the audit's ask was "record cold and warm p50/p95 ... prevent
free-tier cold start from consuming a judge's attention window" — cold vs.
warm is now measured and disclosed (~23s cold vs. sub-second-to-single-digit
seconds warm) rather than left as an untested 119-second bundle number.

**Does not close:** this does not add a keep-warm mechanism (e.g., a
scheduled ping to prevent the free-tier instance from idling out before a
demo). That is a legitimate follow-up if the actual demo/judging slot is
known in advance, but is out of scope for a measurement task — see
`docs/EXTERNAL_AUDIT_ET_AI_HACKATHON_2026-07-10.md` for where that would be
tracked if picked up.

Reproduce: `python scripts/measure_deployment_latency.py --json-out
docs/latency_final.json` (pass `--skip-cold` to only measure warm latency
without waiting for an idle backend).
