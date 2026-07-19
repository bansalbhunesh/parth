#!/usr/bin/env python3
"""verify_live.py — one-command pre-demo gate for the deployed stack.

Answers the only question that matters before a judge sees Pramaan:
*will the live demo actually fire, end to end, right now?*

Checks (in order):
  1. Backend /health is up and reports the expected deployed commit
  2. /llm-check?deep=1 — a reconcile-sized LLM call succeeds (the tiny probe
     can pass while demo-sized calls 429; this is the honest check)
  3. PS4 layers are live: /projects/meghdoot/{schedule,supply-chain,graph}
  4. POST /analyze on the real Vertiv GXT5 + Cummins QSK60 pair returns
     analysis_mode=llm with the expected findings (not the rule fallback)
  5. POST /analyze/stream streams and ends in an llm-mode result
  6. Frontend / and /judge respond 200

Exit 0 = green-light the demo. Exit 1 = do NOT demo; the failures are listed.

Usage:
  python scripts/verify_live.py                       # production defaults
  python scripts/verify_live.py --api http://localhost:8000 --skip-commit
  make verify-live
"""

import argparse
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
REAL_SPEC = ROOT / "data" / "samples" / "real" / "design_basis_helios.md"
REAL_SUB = ROOT / "data" / "samples" / "real" / "submittal_gxt5_qsk60.md"

# Render free tier cold-starts in 30-50s; first hit gets a generous timeout.
COLD_START_TIMEOUT = 90
# The deep probe + live analyze are bounded server-side by PRAMAAN_LLM_TIMEOUT
# (default 60s); give the network round-trip headroom past that.
LLM_TIMEOUT = 150

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    mark = "PASS" if ok else "FAIL"
    line = f"  [{mark}] {label}"
    if detail:
        line += f" — {detail}"
    print(line, flush=True)
    results.append((ok, label))
    return ok


def get_json(url: str, timeout: int):
    req = urllib.request.Request(url, headers={"User-Agent": "pramaan-verify"})
    # B310 accepted risk: url is built from --api, which defaults to the
    # fixed, hardcoded production endpoint (see argparse default below); this
    # is a maintainer-run pre-demo gate, not code reachable from untrusted input.
    with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
        return r.status, json.loads(r.read())


def post_json(url: str, body: dict, timeout: int, stream: bool = False):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json", "User-Agent": "pramaan-verify",
        **({"Accept": "text/event-stream"} if stream else {}),
    })
    # B310 accepted risk: url is built from --api, which defaults to the
    # fixed, hardcoded production endpoint (see argparse default below); this
    # is a maintainer-run pre-demo gate, not code reachable from untrusted input.
    with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
        if stream:
            return r.status, r.read().decode("utf-8", "ignore")
        return r.status, json.loads(r.read())


def head_status(url: str, timeout: int) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": "pramaan-verify"})
    # B310 accepted risk: url is built from --app, which defaults to the
    # fixed, hardcoded production frontend URL (see argparse default below);
    # this is a maintainer-run pre-demo gate, not reachable from untrusted input.
    with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
        return r.status


def expected_commit() -> str | None:
    """Short SHA of origin/main — what production *should* be running."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short=7", "origin/main"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=ROOT, timeout=10, check=True,
        )
        return out.stdout.strip()[:7]
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--api", default="https://parth-1-ma30.onrender.com")
    ap.add_argument("--app", default="https://parth-tan.vercel.app")
    ap.add_argument("--min-findings", type=int, default=3,
                    help="min LLM findings on the GXT5 pair to count the demo "
                         "path as working. The gate proves mode=llm (reasoning, "
                         "not the 2-finding rule fallback); the exact count "
                         "varies run-to-run on a free-tier key (the hard THD "
                         "omission is the swing case). 3 = comfortably above "
                         "the rule floor. Raise to 5 on a billing key.")
    ap.add_argument("--skip-commit", action="store_true",
                    help="don't compare the deployed commit to origin/main")
    ap.add_argument("--skip-llm", action="store_true",
                    help="only check availability, not the LLM path (rate-limit friendly)")
    ap.add_argument("--llm-spacing", type=float, default=20.0,
                    help="seconds between the gate's LLM calls so a free-tier "
                         "key isn't rate-limited into degraded responses "
                         "(mirrors real one-at-a-time demo usage; 0 on a "
                         "billing key)")
    args = ap.parse_args()
    api = args.api.rstrip("/")
    app = args.app.rstrip("/")

    print(f"Pramaan live verification — API {api} · APP {app}")
    t_start = time.time()

    # 1. Health + deployed commit (first hit absorbs the cold start)
    try:
        _, health = get_json(f"{api}/health", COLD_START_TIMEOUT)
    except Exception as exc:
        check(False, "backend /health reachable", str(exc)[:120])
        print("\nBackend unreachable -- nothing else can pass. Aborting early.")
        return summary(t_start)
    check(health.get("ok") is True, "backend /health ok",
          f"commit {health.get('commit')} / llm ready={health.get('llm', {}).get('ready')}")
    if not args.skip_commit:
        want = expected_commit()
        if want:
            got = str(health.get("commit", ""))[:7]
            check(got == want, "deployed commit == origin/main",
                  f"live {got} vs expected {want}" +
                  ("" if got == want else "  -> REDEPLOY on Render"))
        else:
            check(True, "commit check skipped (no git context)")

    # 2. PS4 layers live
    for layer in ("schedule", "supply-chain", "graph"):
        try:
            status, payload = get_json(f"{api}/projects/meghdoot/{layer}", 30)
            body_ok = status == 200 and isinstance(payload, dict) and payload
            unavailable = isinstance(payload, dict) and payload.get("available") is False
            check(body_ok and not unavailable, f"PS4 layer /{layer} live",
                  "available:false — data missing on deploy" if unavailable else "")
        except urllib.error.HTTPError as exc:
            check(False, f"PS4 layer /{layer} live",
                  f"HTTP {exc.code} — stale deploy? REDEPLOY from main tip")
        except Exception as exc:
            check(False, f"PS4 layer /{layer} live", str(exc)[:120])

    # 3. Deep LLM probe (reconcile-sized — the honest pre-flight)
    if args.skip_llm:
        check(True, "LLM checks skipped (--skip-llm)")
    else:
        try:
            _, deep = get_json(f"{api}/llm-check?deep=1", LLM_TIMEOUT)
            if deep.get("probe") != "deep":
                # An older deploy ignores the query param and answers with the
                # tiny probe — a green here would be exactly the false
                # confidence this script exists to kill.
                check(False, "deep LLM probe (/llm-check?deep=1)",
                      "deployed backend predates the deep probe -> REDEPLOY")
            else:
                check(deep.get("ok") is True, "deep LLM probe (/llm-check?deep=1)",
                      f"{deep.get('elapsed_ms', '?')}ms, {deep.get('findings', '?')} findings"
                      if deep.get("ok") else str(deep.get("error", deep))[:160])
        except Exception as exc:
            check(False, "deep LLM probe (/llm-check?deep=1)", str(exc)[:120])

        # 4. The actual demo call: real GXT5 pair through sync /analyze.
        # Space LLM calls apart: a free-tier key rate-limits a burst of
        # reconcile-sized calls and degrades later responses to 0-1 findings.
        # A real demo makes one call at a time, so the gate does too — pause
        # between the deep probe, sync, and stream calls. Set --llm-spacing 0
        # on a billing key to run them back-to-back.
        if REAL_SPEC.exists() and REAL_SUB.exists():
            body = {"spec_text": REAL_SPEC.read_text(encoding="utf-8"),
                    "submittal_text": REAL_SUB.read_text(encoding="utf-8")}
            if args.llm_spacing:
                time.sleep(args.llm_spacing)
            try:
                t0 = time.time()
                _, res = post_json(f"{api}/analyze", body, LLM_TIMEOUT)
                mode = res.get("analysis_mode") or res.get("mode")
                n = len(res.get("deviations", []))
                check(mode == "llm" and n >= args.min_findings,
                      "real-pair /analyze uses the LLM",
                      f"mode={mode}, {n} findings in {time.time()-t0:.0f}s "
                      f"(need mode=llm, >={args.min_findings})")
            except Exception as exc:
                check(False, "real-pair /analyze uses the LLM", str(exc)[:120])

            # 5. Streaming path — what the judge page actually calls
            if args.llm_spacing:
                time.sleep(args.llm_spacing)
            try:
                _, sse = post_json(f"{api}/analyze/stream", body, LLM_TIMEOUT,
                                   stream=True)
                final = {}
                for line in sse.splitlines():
                    if line.startswith("data: {"):
                        try:
                            parsed = json.loads(line[5:])
                            if "deviations" in parsed:
                                final = parsed
                        except json.JSONDecodeError:
                            pass
                mode = final.get("analysis_mode") or final.get("mode")
                n = len(final.get("deviations", []))
                check(mode == "llm" and n >= args.min_findings,
                      "real-pair /analyze/stream uses the LLM",
                      f"mode={mode}, {n} findings")
            except Exception as exc:
                check(False, "real-pair /analyze/stream uses the LLM", str(exc)[:120])
        else:
            check(False, "real demo pair files present",
                  f"missing {REAL_SPEC.name} / {REAL_SUB.name}")

    # 6. Frontend
    for path, label in (("", "frontend /"), ("/judge", "frontend /judge")):
        try:
            check(head_status(f"{app}{path}", 60) == 200, f"{label} responds 200")
        except Exception as exc:
            check(False, f"{label} responds 200", str(exc)[:120])

    return summary(t_start)


def summary(t_start: float) -> int:
    passed = sum(1 for ok, _ in results if ok)
    failed = [label for ok, label in results if not ok]
    print(f"\n{passed}/{len(results)} checks passed in {time.time()-t_start:.0f}s")
    if failed:
        print("DO NOT DEMO. Fix first:")
        for f in failed:
            print(f"  x {f}")
        return 1
    print("GREEN -- demo away.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
