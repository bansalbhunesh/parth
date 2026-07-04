#!/usr/bin/env python3
"""run_benchmark_suite.py — one-command reproducibility for the ps4_external_v1
benchmark.

DEFAULT BEHAVIOUR SPENDS NO API QUOTA. With no flags (or --rule-only / --skip-llm)
it runs, in order:

  1. manifest check          (scripts/benchmark_manifest_check.py)
  2. hash / source check     (scripts/benchmark_hash_sources.py)
  3. rule baseline           (benchmark_ps4_external.py --mode rule)
  4. report generation       (scripts/benchmark_report.py)

The live LLM benchmark runs ONLY when you pass --llm (and it will spend provider
quota if a key is configured). Examples:

  python scripts/run_benchmark_suite.py                       # safe, no API
  python scripts/run_benchmark_suite.py --rule-only           # safe, explicit
  python scripts/run_benchmark_suite.py --skip-llm            # safe, alias
  python scripts/run_benchmark_suite.py --llm --provider gemini --repeat 1
  python scripts/run_benchmark_suite.py --llm --provider openai \
      --model google/gemini-3.1-flash-lite --repeat 3
"""
import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable

SAFE_STEPS = [
    ("manifest check", ["scripts/benchmark_manifest_check.py"]),
    ("hash / source check", ["scripts/benchmark_hash_sources.py"]),
    ("rule baseline (no key)", ["scripts/benchmark_ps4_external.py", "--mode", "rule"]),
    ("report generation", ["scripts/benchmark_report.py"]),
]


def run_step(name: str, args: list[str]) -> bool:
    print(f"\n=== {name} ===", flush=True)
    resolved = [str(ROOT / a) if a.endswith(".py") else a for a in args]
    rc = subprocess.run([PY, *resolved], cwd=ROOT).returncode
    print(f"--- {name}: {'OK' if rc == 0 else f'FAILED (exit {rc})'}", flush=True)
    return rc == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--llm", action="store_true",
                    help="also run the live LLM benchmark (SPENDS API quota if a key is set)")
    ap.add_argument("--rule-only", action="store_true", help="safe steps only (explicit default)")
    ap.add_argument("--skip-llm", action="store_true", help="safe steps only (alias of default)")
    ap.add_argument("--provider", default="gemini", help="LLM provider for --llm")
    ap.add_argument("--model", default=None, help="model id for --llm")
    ap.add_argument("--repeat", type=int, default=1, help="passes for --llm")
    args = ap.parse_args()

    results = [(name, run_step(name, a)) for name, a in SAFE_STEPS]

    do_llm = args.llm and not (args.rule_only or args.skip_llm)
    if do_llm:
        print("\n[!] --llm requested: this WILL spend provider quota if a key is configured. "
              "With no key, every pair is recorded not_run (a miss) and nothing is fabricated.")
        llm = ["scripts/benchmark_ps4_external.py", "--mode", "llm",
               "--provider", args.provider, "--repeat", str(args.repeat)]
        if args.model:
            llm += ["--model", args.model]
        results.append(("LLM benchmark", run_step("LLM benchmark", llm)))
        results.append(("report (post-LLM)", run_step("report (post-LLM)",
                                                       ["scripts/benchmark_report.py"])))
    else:
        print("\n[i] LLM benchmark skipped — safe default, no API quota spent. Pass --llm to enable.")

    print("\n===== SUITE SUMMARY =====")
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
