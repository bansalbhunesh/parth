# pairs/

One directory per document pair:

- `owner_requirement.md` — the owner design-basis requirement (team-authored fixture).
- `vendor_submittal.md` — the vendor submittal (team-authored; values cited from
  public figures where noted).
- `label.json` — the frozen label(s) for this pair (per-pair view of `labels/labels.jsonl`).
- `notes.md` — why the pair exists and the expected reasoning.

Pairs are authored via `scripts/benchmark_seed_pairs.py`. The analysis input is
`owner_requirement.md` (spec) vs `vendor_submittal.md` (submittal).
