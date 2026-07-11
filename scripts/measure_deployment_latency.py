#!/usr/bin/env python3
"""measure_deployment_latency.py — cold vs. warm p50/p95 latency by endpoint
against the deployed stack (P1-5 from the external audit).

Why this exists: `scripts/verify_live.py`'s own 10-check run took ~102s, and
the honest audit gap was "we don't know how much of that is one slow endpoint
vs. a genuinely cold Render free-tier instance" — this measures each
endpoint separately instead of only a pass/fail bundle.

Quota-conscious by design, same posture as load_test_demo.py:
- /health is free (no rate limit, no LLM call) — sampled generously.
- /analyze and /analyze/stream are rate-limited per-client (backend/security.py
  buckets by IP+token, so this script's own traffic never competes with a
  judge's browser for THAT budget) but DO spend from the shared upstream LLM
  provider quota / spend guard — kept to a small, explicitly-disclosed n
  (default 3) rather than hammered for a tighter interval.
- Judge-page HTML load is a Vercel ISR route (10-minute revalidate per
  frontend/app/judge/page.tsx) — "cold" isn't the same phenomenon there as a
  Render free-tier backend spin-up, so this script does not claim a frontend
  cold-start number; only the backend gets one.

Cold-start requires the Render instance to have actually gone idle first
(typically ~15 min of no traffic on the free tier) — this script cannot force
that; run it right after a genuine idle period for a real cold sample, or
pass --skip-cold to only record warm numbers.
"""

import argparse
import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_API = "https://parth-1-ma30.onrender.com"
DEFAULT_APP = "https://parth-tan.vercel.app"

# A random run tag is baked into every payload so distinct-payload samples
# can never accidentally cache-hit a previous (or killed/retried) run's
# input_hash — the analyze endpoint caches by exact text content, and a
# prior 3-minute run of this script was killed mid-flight after already
# sending the fixed n=1..5 payloads, silently turning the next run's
# "fresh" samples into cache-hit reads (233ms vs. the ~1.7s an uncached
# call actually takes) until this was caught and fixed.
_RUN_TAG = os.urandom(4).hex()
_SPEC_TMPL = "**UPS-{tag}-{n:02d}** - battery runtime: shall be **10 min** at full load."
_SUB_TMPL = "**UPS-{tag}-{n:02d}** - battery runtime: **7 min**."


def _payload(n):
    return {
        "spec_text": _SPEC_TMPL.format(tag=_RUN_TAG, n=n),
        "submittal_text": _SUB_TMPL.format(tag=_RUN_TAG, n=n),
        "system_id": "UPS",
    }


def _percentile(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    k = min(len(s) - 1, max(0, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]


def _timed_get(url, timeout):
    t0 = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": "pramaan-latency-probe"})
    try:
        # B310 accepted risk: url is built from --api/--app, which default to
        # the fixed, hardcoded production endpoints (see argparse defaults
        # below); this is a maintainer-run measurement script, not code
        # reachable from untrusted input.
        with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
            r.read()
            ok = 200 <= r.status < 300
    except Exception:
        ok = False
    return (time.monotonic() - t0) * 1000, ok


def _timed_post_json(url, body, timeout):
    t0 = time.monotonic()
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "pramaan-latency-probe"},
    )
    try:
        # B310 accepted risk: url is built from --api, which defaults to the
        # fixed, hardcoded production endpoint (see argparse default below);
        # this is a maintainer-run measurement script, not code reachable
        # from untrusted input.
        with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
            r.read()
            ok = 200 <= r.status < 300
    except Exception:
        ok = False
    return (time.monotonic() - t0) * 1000, ok


def _time_to_first_sse_token(url, body, timeout):
    """Time from request-sent to the first `event: token` line — the number
    that actually matters for perceived latency on a streaming UI, distinct
    from total-request time (which is dominated by how long the full
    analysis takes, not how long a judge stares at a blank panel)."""
    t0 = time.monotonic()
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "pramaan-latency-probe",
                 "Accept": "text/event-stream"},
    )
    try:
        # B310 accepted risk: url is built from --api, which defaults to the
        # fixed, hardcoded production endpoint (see argparse default below);
        # this is a maintainer-run measurement script, not code reachable
        # from untrusted input.
        with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
            saw_event_line = False
            for raw_line in r:
                line = raw_line.decode("utf-8", "replace").strip()
                if line.startswith("event: token") or line.startswith("event:token"):
                    return (time.monotonic() - t0) * 1000, True
                if line.startswith("event:"):
                    saw_event_line = True
            # Stream ended without a token event (e.g. 0-deviation result
            # streams straight to `done`) — report time to the first SSE
            # event of any kind instead of failing the sample outright.
            return (time.monotonic() - t0) * 1000, saw_event_line
    except Exception:
        return (time.monotonic() - t0) * 1000, False


def _summarize(label, samples_ms, oks):
    # Percentiles are computed over successful requests only — a 429/5xx
    # response usually comes back FASTER than a real analysis (no LLM call
    # happens), so blending its latency into "warm p50" would understate
    # real latency rather than reflect it. Failures are still counted and
    # surfaced, just not averaged in as if they were successful analyses.
    n = len(samples_ms)
    n_ok = sum(oks)
    ok_samples = [ms for ms, ok in zip(samples_ms, oks) if ok]
    if not ok_samples:
        print(f"{label:<28} n={n:<3} ok={n_ok}/{n}  (no successful samples — cannot compute latency)")
        return {"label": label, "n": n, "n_ok": n_ok, "p50_ms": None, "p95_ms": None, "min_ms": None, "max_ms": None}
    line = (f"{label:<28} n={n:<3} ok={n_ok}/{n}  "
            f"p50={_percentile(ok_samples, 50):7.0f}ms  "
            f"p95={_percentile(ok_samples, 95):7.0f}ms  "
            f"min={min(ok_samples):7.0f}ms  max={max(ok_samples):7.0f}ms"
            + ("" if n_ok == n else "  [percentiles exclude failed/rejected requests]"))
    print(line)
    return {"label": label, "n": n, "n_ok": n_ok,
            "p50_ms": round(_percentile(ok_samples, 50), 1),
            "p95_ms": round(_percentile(ok_samples, 95), 1),
            "min_ms": round(min(ok_samples), 1), "max_ms": round(max(ok_samples), 1)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--app", default=DEFAULT_APP)
    ap.add_argument("--warm-requests", type=int, default=10, help="samples for free endpoints (health, judge page)")
    ap.add_argument("--analysis-requests", type=int, default=3, help="samples for rate-limited/LLM-quota endpoints")
    ap.add_argument("--skip-cold", action="store_true", help="only measure warm latency")
    ap.add_argument("--json-out", default=None, help="write results as JSON to this path")
    args = ap.parse_args()

    report = {"api": args.api, "app": args.app, "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    if not args.skip_cold:
        print("=== COLD (first hit this run — only meaningful if the backend had genuinely idled) ===")
        cold_health_ms, cold_health_ok = _timed_get(f"{args.api}/health", timeout=90)
        print(f"{'health (cold)':<28} {cold_health_ms:7.0f}ms  ok={cold_health_ok}")
        cold_analyze_ms, cold_analyze_ok = _timed_post_json(
            f"{args.api}/analyze", _payload(0), timeout=90,
        )
        print(f"{'analyze (cold, 1st call)':<28} {cold_analyze_ms:7.0f}ms  ok={cold_analyze_ok}")
        report["cold"] = {
            "health_ms": round(cold_health_ms, 1), "health_ok": cold_health_ok,
            "analyze_first_call_ms": round(cold_analyze_ms, 1), "analyze_first_call_ok": cold_analyze_ok,
        }
        print()

    print(f"=== WARM (backend already responding; n={args.warm_requests} for free endpoints, "
          f"n={args.analysis_requests} for LLM-quota endpoints) ===")

    health_samples, health_oks = [], []
    for _ in range(args.warm_requests):
        ms, ok = _timed_get(f"{args.api}/health", timeout=30)
        health_samples.append(ms)
        health_oks.append(ok)
    report["health"] = _summarize("health", health_samples, health_oks)

    judge_samples, judge_oks = [], []
    for _ in range(args.warm_requests):
        ms, ok = _timed_get(f"{args.app}/judge", timeout=30)
        judge_samples.append(ms)
        judge_oks.append(ok)
    report["judge_page_load"] = _summarize("judge-page HTML load", judge_samples, judge_oks)

    analyze_samples, analyze_oks = [], []
    for i in range(args.analysis_requests):
        ms, ok = _timed_post_json(
            f"{args.api}/analyze", _payload(i + 1), timeout=90,
        )
        analyze_samples.append(ms)
        analyze_oks.append(ok)
        time.sleep(1)  # be a polite, distinguishable client — not a burst
    report["analyze"] = _summarize("analyze (distinct payload)", analyze_samples, analyze_oks)

    stream_samples, stream_oks = [], []
    for i in range(args.analysis_requests):
        ms, ok = _time_to_first_sse_token(
            f"{args.api}/analyze/stream", _payload(i + 101), timeout=90,
        )
        stream_samples.append(ms)
        stream_oks.append(ok)
        time.sleep(1)
    report["stream_first_token"] = _summarize("stream time-to-first-token", stream_samples, stream_oks)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nWrote {args.json_out}")

    return report


if __name__ == "__main__":
    main()
