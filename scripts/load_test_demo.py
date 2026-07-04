#!/usr/bin/env python
"""
Prototype load / concurrency probe for the Pramaan demo.

Measures, under a chosen concurrency: requests attempted, success/error rate,
rate-limit (429) behavior, p50/p95 latency, and the LLM-vs-fallback-vs-cached
mix (read from the response's `mode`/`cached` fields when present).

SAFE BY DEFAULT — it does NOT hammer the LLM: it fires the SAME payload, so
after a one-request warm-up every hit is an input-hash cache hit (see
backend/jobs.py). At most one real analysis is computed regardless of --requests.
Use --vary to force distinct (uncached) inputs — that DOES spend quota per
request against a live key, so it prints a warning.

Examples:
  python scripts/load_test_demo.py --local --requests 20 --concurrency 5
  python scripts/load_test_demo.py --base-url http://localhost:8000 --requests 20 --concurrency 5
  python scripts/load_test_demo.py --base-url https://host --method GET --endpoint /health --requests 50
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_SPEC = "**UPS-02** - battery runtime: shall be **10 min** at full load."
_SUB = "**UPS-02** - battery runtime: **7 min**."


def _percentile(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    k = min(len(s) - 1, max(0, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]


def _make_client(args):
    if args.local:
        # Keep the in-process demo posture predictable for a local probe.
        os.environ.setdefault("DEMO_AUTH_ENABLED", "false")
        from fastapi.testclient import TestClient

        from backend.main import app
        return TestClient(app)
    try:
        import httpx
    except ImportError:
        sys.exit("httpx is required for --base-url mode (pip install httpx)")
    return httpx.Client(base_url=args.base_url, timeout=args.timeout)


def _payload(args, i):
    sub = _SUB if not args.vary else f"{_SUB} (variant {i})"
    return {"spec_text": _SPEC, "submittal_text": sub, "system_id": "UPS"}


def _one(client, args, headers, i):
    t0 = time.perf_counter()
    try:
        if args.method == "GET":
            r = client.get(args.endpoint, headers=headers)
        else:
            r = client.post(args.endpoint, json=_payload(args, i), headers=headers)
        dt = (time.perf_counter() - t0) * 1000.0
        body = {}
        try:
            body = r.json()
        except Exception:
            pass
        return dt, r.status_code, body
    except Exception as exc:  # network / timeout / connection
        dt = (time.perf_counter() - t0) * 1000.0
        return dt, None, {"_error": str(exc)[:80]}


def main():
    ap = argparse.ArgumentParser(description="Pramaan demo load probe")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--local", action="store_true",
                     help="run in-process via TestClient (no network; safe default)")
    src.add_argument("--base-url", help="target a running server, e.g. http://localhost:8000")
    ap.add_argument("--requests", type=int, default=20)
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--endpoint", default="/analyze")
    ap.add_argument("--method", choices=["GET", "POST"], default="POST")
    ap.add_argument("--token", help="demo auth token (sent as X-Demo-Token) if auth is on")
    ap.add_argument("--vary", action="store_true",
                    help="force distinct inputs (defeats caching; SPENDS QUOTA on a live key)")
    ap.add_argument("--no-warmup", action="store_true")
    ap.add_argument("--timeout", type=float, default=30.0)
    args = ap.parse_args()
    if not args.local and not args.base_url:
        args.local = True  # safe default

    client = _make_client(args)
    headers = {"X-Demo-Token": args.token} if args.token else {}
    mode = "local (in-process)" if args.local else args.base_url

    if args.vary and args.method == "POST":
        print("WARNING: --vary defeats the cache; every request computes fresh "
              "and will spend LLM quota against a live key.\n")

    if not args.no_warmup and args.method == "POST":
        _one(client, args, headers, -1)  # warm the input-hash cache

    print(f"Load probe: target={mode} endpoint={args.method} {args.endpoint} "
          f"requests={args.requests} concurrency={args.concurrency} "
          f"vary={args.vary}\n")

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        results = list(ex.map(lambda i: _one(client, args, headers, i),
                              range(args.requests)))
    wall = time.perf_counter() - t0

    lat = [dt for dt, _, _ in results]
    ok = [r for r in results if r[1] and 200 <= r[1] < 300]
    accepted = [r for r in results if r[1] in (200, 202)]
    limited = [r for r in results if r[1] == 429]
    errors = [r for r in results if r[1] is None or (r[1] >= 400 and r[1] != 429)]
    cached = sum(1 for _, _, b in results if isinstance(b, dict) and b.get("cached") is True)
    modes = {}
    for _, _, b in results:
        if isinstance(b, dict) and b.get("mode"):
            modes[b["mode"]] = modes.get(b["mode"], 0) + 1

    n = len(results) or 1
    print("===== RESULTS =====")
    print(f"  concurrency        : {args.concurrency}")
    print(f"  requests attempted : {len(results)}")
    print(f"  success (2xx)      : {len(ok)}  ({100.0*len(ok)/n:.1f}%)")
    print(f"  accepted (200/202) : {len(accepted)}")
    print(f"  rate-limited (429) : {len(limited)}")
    print(f"  errors             : {len(errors)}  ({100.0*len(errors)/n:.1f}%)")
    print(f"  throughput         : {len(results)/wall:.1f} req/s over {wall:.2f}s")
    print(f"  latency p50 / p95  : {_percentile(lat,50):.0f} / {_percentile(lat,95):.0f} ms")
    print(f"  latency min / max  : {min(lat):.0f} / {max(lat):.0f} ms")
    print(f"  cache hits         : {cached}  (idempotent reuse; safe by design)")
    if modes:
        print(f"  analysis modes     : {modes}")
    if errors:
        sample = next((b for _, _, b in errors if isinstance(b, dict)), {})
        detail = sample.get("_error") or sample.get("detail") or ""
        if detail:
            print(f"  sample error       : {str(detail)[:80]}")
    print("\nNote: this is a single-instance, in-memory probe - not a distributed "
          "load test. See docs/SCALABILITY_PROOF.md for method + limitations.")


if __name__ == "__main__":
    main()
