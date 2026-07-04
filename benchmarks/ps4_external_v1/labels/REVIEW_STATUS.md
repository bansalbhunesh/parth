# Review status — ps4_external_v1

**Current: `single_author_frozen_pending_review`.**

- Labels were authored and frozen by a **single author** (`reviewer_1.jsonl`
  holds the author verdicts).
- `reviewer_2.jsonl` is **empty** — no independent second reviewer has run yet.
- `adjudicated.jsonl` is **empty** — no two-reviewer adjudication has occurred.

**Therefore the benchmark and its report do NOT claim independent two-reviewer
adjudication.** That is a Phase-1C+ backlog item (see `ADJUDICATION_PROTOCOL.md`).

Coverage: 100% of labels have a `reviewer_1` verdict; 0% have a second-reviewer
verdict; 0 adjudicated. When a second reviewer runs, follow
`ADJUDICATION_PROTOCOL.md`, populate `reviewer_2.jsonl` + `adjudicated.jsonl`, set
each label's `review_status` to `reviewed_two_person`/`adjudicated`, and bump
`benchmark_version`.

## Automated consistency audit (NOT a second human reviewer)

`scripts/benchmark_label_audit.py` runs an independent, deterministic second-pass
check of every label against its own pair documents (is the required_value
grounded in the owner doc? the submitted_value in the vendor doc? does a positive
deviation actually differ?). Results: `labels/automated_audit.jsonl`.

This is **machine QA, not human adjudication** — it flags candidates for a human
to review, it does not confirm correctness and does not substitute for the
pending two-person review. Latest run: **123/129 consistent, 6 flagged**
(labels whose submitted_value carries an added annotation or phrasing not
literally present in the document). A human reviewer should adjudicate the
flagged six as part of the reviewer-2 pass.
