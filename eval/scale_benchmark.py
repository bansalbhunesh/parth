"""Scale benchmark — measures the deterministic detection layer's throughput on a
large synthetic portfolio, and projects enterprise scale. The LLM layer scales
horizontally (per-system, parallelisable + cached); this benchmarks the
non-LLM extraction/comparison path that runs on every document.

Run:  python eval/scale_benchmark.py [--systems 1000]
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from backend.analyze import _resilient_fallback  # noqa: E402

DATA = pathlib.Path(__file__).parent.parent / "data"


def _load_corpus_pairs():
    pairs = []
    specs = DATA / "corpus" / "specs"
    subs = DATA / "corpus" / "submittals"
    if specs.exists():
        for s in sorted(specs.glob("*.md")):
            sub = subs / s.name
            if sub.exists():
                pairs.append((s.read_text(encoding="utf-8"),
                              sub.read_text(encoding="utf-8")))
    # add the real-world pairs for realistic free-form prose
    real = DATA / "samples" / "real"
    for spec, sub in [("design_basis_helios.md", "submittal_gxt5_qsk60.md"),
                      ("design_basis_cooling.md", "submittal_stulz_cyberair.md"),
                      ("design_basis_switchgear.md", "submittal_abb_mns.md")]:
        sp, su = real / spec, real / sub
        if sp.exists() and su.exists():
            pairs.append((sp.read_text(encoding="utf-8"),
                          su.read_text(encoding="utf-8")))
    return pairs or [("**X** — y: shall be **1 a**", "**X** — y: **2 a**")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", type=int, default=1000)
    args = ap.parse_args()

    base = _load_corpus_pairs()
    n = args.systems
    devs = 0
    t0 = time.time()
    for i in range(n):
        spec, sub = base[i % len(base)]
        devs += len(_resilient_fallback(spec, sub, f"SYS-{i}"))
    elapsed = time.time() - t0

    rate = n / elapsed
    # An enterprise project ≈ 500 systems; a portfolio ≈ 100 projects.
    proj_500 = 500 / rate
    portfolio = 50_000 / rate
    print(f"\n{'='*62}")
    print(f"  PRAMAAN SCALE BENCHMARK - deterministic detection layer")
    print(f"{'='*62}")
    print(f"  systems processed     : {n:,}")
    print(f"  deviations found      : {devs:,}")
    print(f"  wall time             : {elapsed:.2f} s")
    print(f"  throughput            : {rate:,.0f} systems/sec")
    print(f"{'~'*62}")
    print(f"  projected 500-system project : {proj_500:.2f} s")
    print(f"  projected 100-project (50k sys) portfolio : {portfolio:.1f} s")
    print(f"{'~'*62}")
    print(f"  LLM layer: per-system, parallelisable + response-cached;")
    print(f"  delta ingest re-checks only changed submittals.")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    main()
