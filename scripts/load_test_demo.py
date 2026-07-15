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
import asyncio
import json
import os
import platform
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
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


def _make_local_client():
    # Keep the in-process demo posture predictable for a local probe.
    os.environ.setdefault("DEMO_AUTH_ENABLED", "false")
    from fastapi.testclient import TestClient

    from backend.main import app

    return TestClient(app)


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


async def _one_async(client, args, headers, i):
    t0 = time.perf_counter()
    try:
        if args.method == "GET":
            response = await client.get(args.endpoint, headers=headers)
        else:
            response = await client.post(args.endpoint, json=_payload(args, i), headers=headers)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        try:
            body = response.json()
        except Exception:
            body = {}
        return elapsed_ms, response.status_code, body
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return elapsed_ms, None, {"_error": str(exc)[:80]}


def _run_local(args, headers):
    client = _make_local_client()
    if not args.no_warmup and args.method == "POST":
        _one(client, args, headers, -1)

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = list(executor.map(lambda i: _one(client, args, headers, i), range(args.requests)))
    return results, time.perf_counter() - started


async def _run_remote(args, headers):
    try:
        import httpx
    except ImportError:
        sys.exit("httpx is required for --base-url mode (pip install httpx)")

    limits = httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=args.concurrency,
    )
    async with httpx.AsyncClient(base_url=args.base_url, timeout=args.timeout, limits=limits) as client:
        if not args.no_warmup and args.method == "POST":
            await _one_async(client, args, headers, -1)

        semaphore = asyncio.Semaphore(args.concurrency)

        async def bounded(index):
            async with semaphore:
                return await _one_async(client, args, headers, index)

        started = time.perf_counter()
        results = await asyncio.gather(*(bounded(index) for index in range(args.requests)))
        return results, time.perf_counter() - started


def _summarize(results, wall, args):
    latencies = [elapsed_ms for elapsed_ms, _, _ in results]
    successes = [result for result in results if result[1] and 200 <= result[1] < 300]
    accepted = [result for result in results if result[1] in (200, 202)]
    limited = [result for result in results if result[1] == 429]
    errors = [result for result in results if result[1] is None or (not 200 <= result[1] < 300 and result[1] != 429)]
    cached = sum(1 for _, _, body in results if isinstance(body, dict) and body.get("cached") is True)
    modes = {}
    for _, _, body in results:
        if isinstance(body, dict) and body.get("mode"):
            modes[body["mode"]] = modes.get(body["mode"], 0) + 1

    count = len(results)
    sample_error = ""
    if errors:
        body = next((body for _, _, body in errors if isinstance(body, dict)), {})
        sample_error = str(body.get("_error") or body.get("detail") or "")[:80]
    return {
        "concurrency": args.concurrency,
        "requests_attempted": count,
        "success_2xx": len(successes),
        "success_rate_percent": round(100.0 * len(successes) / count, 3),
        "accepted_200_202": len(accepted),
        "rate_limited_429": len(limited),
        "errors": len(errors),
        "error_rate_percent": round(100.0 * len(errors) / count, 3),
        "throughput_rps": round(count / wall, 3),
        "wall_seconds": round(wall, 3),
        "latency_ms": {
            "p50": round(_percentile(latencies, 50), 3),
            "p95": round(_percentile(latencies, 95), 3),
            "min": round(min(latencies), 3),
            "max": round(max(latencies), 3),
        },
        "cache_hits": cached,
        "analysis_modes": modes,
        "sample_error": sample_error,
    }


def _write_evidence(output_path, mode, args, summary):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime": {"python": platform.python_version(), "platform": platform.platform()},
        "profile": {
            "label": args.profile_label,
            "revision": args.revision,
            "target": mode,
            "method": args.method,
            "endpoint": args.endpoint,
            "requests": args.requests,
            "concurrency": args.concurrency,
            "timeout_seconds": args.timeout,
            "varied_inputs": args.vary,
            "warmup": not args.no_warmup and args.method == "POST",
        },
        "results": summary,
        "limitations": [
            "A single-client-host probe does not prove multi-replica or managed-service capacity.",
            "Cached deterministic analysis does not represent live-provider latency or cost.",
        ],
    }
    with path.open("x", encoding="utf-8") as handle:
        json.dump(artifact, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    ap = argparse.ArgumentParser(description="Pramaan demo load probe")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--local", action="store_true", help="run in-process via TestClient (no network; safe default)")
    src.add_argument("--base-url", help="target a running server, e.g. http://localhost:8000")
    ap.add_argument("--requests", type=int, default=20)
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--endpoint", default="/analyze")
    ap.add_argument("--method", choices=["GET", "POST"], default="POST")
    ap.add_argument("--token", help="demo auth token (sent as X-Demo-Token) if auth is on")
    ap.add_argument(
        "--vary", action="store_true", help="force distinct inputs (defeats caching; SPENDS QUOTA on a live key)"
    )
    ap.add_argument("--no-warmup", action="store_true")
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument(
        "--json-output",
        help="write a new JSON evidence artifact; refuses to overwrite an existing file",
    )
    ap.add_argument("--revision", help="source revision recorded in JSON evidence")
    ap.add_argument("--profile-label", help="named deployment/topology profile recorded in JSON evidence")
    args = ap.parse_args()
    if not args.local and not args.base_url:
        args.local = True  # safe default
    if args.requests <= 0:
        ap.error("--requests must be positive")
    if args.concurrency <= 0:
        ap.error("--concurrency must be positive")
    if args.json_output and (not args.revision or not args.profile_label):
        ap.error("--json-output requires --revision and --profile-label")

    headers = {"X-Demo-Token": args.token} if args.token else {}
    mode = "local (in-process)" if args.local else args.base_url

    if args.vary and args.method == "POST":
        print(
            "WARNING: --vary defeats the cache; every request computes fresh "
            "and will spend LLM quota against a live key.\n"
        )

    print(
        f"Load probe: target={mode} endpoint={args.method} {args.endpoint} "
        f"requests={args.requests} concurrency={args.concurrency} "
        f"vary={args.vary}\n"
    )

    if args.local:
        results, wall = _run_local(args, headers)
    else:
        results, wall = asyncio.run(_run_remote(args, headers))

    summary = _summarize(results, wall, args)
    print("===== RESULTS =====")
    print(f"  concurrency        : {summary['concurrency']}")
    print(f"  requests attempted : {summary['requests_attempted']}")
    print(f"  success (2xx)      : {summary['success_2xx']}  ({summary['success_rate_percent']:.1f}%)")
    print(f"  accepted (200/202) : {summary['accepted_200_202']}")
    print(f"  rate-limited (429) : {summary['rate_limited_429']}")
    print(f"  errors             : {summary['errors']}  ({summary['error_rate_percent']:.1f}%)")
    print(f"  throughput         : {summary['throughput_rps']:.1f} req/s over {summary['wall_seconds']:.2f}s")
    latency = summary["latency_ms"]
    print(f"  latency p50 / p95  : {latency['p50']:.0f} / {latency['p95']:.0f} ms")
    print(f"  latency min / max  : {latency['min']:.0f} / {latency['max']:.0f} ms")
    print(f"  cache hits         : {summary['cache_hits']}  (idempotent reuse; safe by design)")
    if summary["analysis_modes"]:
        print(f"  analysis modes     : {summary['analysis_modes']}")
    if summary["sample_error"]:
        print(f"  sample error       : {summary['sample_error']}")
    if args.json_output:
        _write_evidence(args.json_output, mode, args, summary)
        print(f"  evidence artifact  : {args.json_output}")
    print(
        "\nNote: this is a single-client-host probe, not evidence of multi-replica or "
        "managed-service capacity. See docs/SCALABILITY_PROOF.md for limitations."
    )


if __name__ == "__main__":
    main()
