#!/usr/bin/env python3
"""benchmark_manifest_check.py — validate manifest, labels, and freeze integrity.

Exit 1 on any error. Pure stdlib (CI-safe). Also asserts the benchmark uses none
of the seeded data/corpus/ground_truth.json labels.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402


def _ground_truth_ids() -> set[str]:
    gt = L.ROOT / "data" / "corpus" / "ground_truth.json"
    if not gt.exists():
        return set()
    data = json.loads(gt.read_text(encoding="utf-8"))
    return {d.get("id") for d in data.get("seeded_deviations", []) if d.get("id")}


def main() -> int:
    rows = L.load_manifest()
    labels = L.load_labels()
    errors: list[str] = []
    if not rows:
        errors.append("manifest.csv is empty or missing")
    if not labels:
        errors.append("labels/labels.jsonl is empty or missing")

    errors += L.validate_manifest(rows)
    errors += L.validate_labels(labels)

    # independence guard: no overlap with the seeded corpus ids
    seeded = _ground_truth_ids()
    bench_ids = {lb.get("label_id") for lb in labels}
    overlap = seeded & bench_ids
    if overlap:
        errors.append(f"benchmark reuses seeded ground_truth ids: {sorted(overlap)}")

    # freeze integrity
    freeze_path = L.BENCH / "labels" / "labels_freeze.json"
    if not freeze_path.exists():
        errors.append("labels/labels_freeze.json missing")
    else:
        fz = json.loads(freeze_path.read_text(encoding="utf-8"))
        cur = L.labels_freeze_hash(labels)
        if fz.get("labels_freeze_sha256") != cur:
            errors.append("label freeze hash mismatch — labels edited since freeze; "
                          "bump benchmark_version and regenerate")
        if fz.get("label_count") != len(labels):
            errors.append(f"freeze label_count {fz.get('label_count')} != actual {len(labels)}")

    print(f"manifest rows: {len(rows)} | labels: {len(labels)} | seeded-id overlap: {len(overlap)}")
    if errors:
        print(f"FAIL — {len(errors)} error(s):")
        for e in errors:
            print("  -", e)
        return 1
    print("OK — manifest + labels + freeze valid; independent of seeded corpus")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
