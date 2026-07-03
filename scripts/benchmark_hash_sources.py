#!/usr/bin/env python3
"""benchmark_hash_sources.py — hash every tracked benchmark document and
cross-check the manifest sha256 column. Writes sources/hashes.json. Exit 1 on
any mismatch. Pure stdlib (CI-safe).
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402


def main() -> int:
    hashes: dict[str, str] = {}
    for base in ("pairs", "sources/normalized"):
        d = L.BENCH / base
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.name != ".gitkeep":
                hashes[p.relative_to(L.BENCH).as_posix()] = L.sha256_file(p)

    out = L.BENCH / "sources" / "hashes.json"
    out.write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")

    rows = L.load_manifest()
    mism = []
    for r in rows:
        fn = (r.get("file_name") or "").strip()
        if fn in hashes and hashes[fn] != (r.get("sha256") or "").strip():
            mism.append(fn)

    print(f"hashed {len(hashes)} docs -> {out.relative_to(L.ROOT).as_posix()}")
    if mism:
        print(f"FAIL — {len(mism)} manifest sha256 mismatch(es):")
        for m in mism:
            print("  -", m)
        return 1
    print("OK — manifest hashes match disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
