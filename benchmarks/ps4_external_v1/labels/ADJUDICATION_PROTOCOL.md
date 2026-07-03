# Adjudication protocol — ps4_external_v1

1. Two reviewers label independently → `reviewer_1.jsonl`, `reviewer_2.jsonl`.
2. Agreements (`accept`/`accept`) are copied to `adjudicated.jsonl` with
   `review_status: reviewed_two_person`.
3. Disagreements are discussed; the resolved verdict goes to `adjudicated.jsonl`
   with `review_status: adjudicated` and a note recording the disagreement.
4. Genuinely irreducible disagreements become `ambiguous_contested` labels in
   `contested.jsonl` and are excluded from primary metrics.
5. Any label change bumps `benchmark_version` (the freeze hash changes), so runs
   scored against the old labels remain clearly attributable.

**Current status:** single-author frozen (`reviewer_1.jsonl` populated,
`reviewer_2.jsonl` empty). The two-reviewer pass is a Phase-1C backlog item; until
it runs, no two-reviewer adjudication is claimed.
