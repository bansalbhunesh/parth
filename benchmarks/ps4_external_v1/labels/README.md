# labels/

- `labels.jsonl` — the canonical **frozen** label set (one JSON object per line).
- `negatives.jsonl` — the `clean_negative` subset (generated).
- `contested.jsonl` — the `ambiguous_contested` subset (generated; excluded from
  primary metrics unless configured).
- `adjudicated.jsonl` — populated by the two-reviewer adjudication step (backlog;
  empty in the v1 single-author seed).
- `labels_freeze.json` — `benchmark_version`, `frozen_on`, counts, and
  `labels_freeze_sha256` (order-independent hash of every label).

Editing labels after a run is a **version event**: bump `benchmark_version` in
`scripts/benchmark_seed_pairs.py` and regenerate, so the freeze hash changes and
prior runs are clearly against an older label set. The scorer never reads
`data/corpus/ground_truth.json` or any seeded demo label.
