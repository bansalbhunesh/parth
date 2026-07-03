# Reviewer instructions — ps4_external_v1

Each reviewer independently records a verdict per label in `reviewer_N.jsonl`
(one JSON object per line):

```json
{"label_id": "P018-L01", "reviewer": "author|reviewer2", "verdict": "accept|reject|revise", "notes": "..."}
```

Review each label against **both** documents in its pair:

1. **Evidence exists** — the `evidence_required` quote is in `owner_requirement.md`
   and the `evidence_submitted` quote is in the submittal (or the image, for
   `modality: image`).
2. **Direction is correct** — a positive label is a genuine non-conformance; a
   `clean_negative` is genuinely compliant and must NOT be flagged.
3. **Difficulty/severity** are reasonable.
4. **Contested** labels are marked `ambiguous_contested` and excluded from primary
   metrics.

Current state: labels are `single_author_frozen_pending_review` — authored and
frozen by one person (`reviewer_1.jsonl`). `reviewer_2.jsonl` is empty pending an
independent second reviewer. Do **not** claim two-reviewer adjudication until
`reviewer_2.jsonl` is populated and `adjudicated.jsonl` is produced per the
adjudication protocol.
