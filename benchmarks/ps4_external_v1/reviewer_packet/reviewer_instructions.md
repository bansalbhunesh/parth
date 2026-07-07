# Reviewer Instructions — ps4_external_v1 label validation

Thank you for reviewing. **You are checking the benchmark's ground-truth labels —
not any software's output.** For each selected label you decide whether the label
is correct, too broad, wrong, ambiguous, or missing evidence, using only the
material provided in this packet.

## What you are given per label
- the **owner requirement** excerpt (a team-authored design-basis fixture),
- the **vendor/submittal** excerpt (a team-authored fixture; some are shown as a
  rendered image), and
- the **benchmark label**: required value, submitted value, expected finding,
  severity, expected commissioning test, schedule-impact category, source basis,
  and the evidence spans the label points to.

## Your task — answer these for each label
1. **Is the label valid?** (does the claimed deviation / clean-negative actually hold?)
2. **Is the evidence sufficient?** (do the excerpts support the label?)
3. **Is the required value clear?**
4. **Is the submitted value clear?**
5. **Is the severity reasonable?**
6. **Is the difficulty category reasonable?**
7. **Is the commissioning-test mapping reasonable?**
8. **Should the label be accepted, modified, rejected, or marked contested?**
9. **Is there any missing label in the same pair?** (a deviation the benchmark
   did not capture)
10. **Any notes?**

## Do not use outside assumptions
Judge each label **only** from the excerpts provided. Do **not** apply values from
memory or external standards **unless** the pair's context file includes an
explicit public-source / provenance note — in that case you may use that cited
public value to check the derivation.

## Verdict options (column `reviewer_verdict`)
- `accept` — label is correct and well-evidenced.
- `accept_with_minor_edit` — correct, but a small wording/value tidy would help.
- `modify` — the label needs a substantive change (say what in `suggested_correction`).
- `reject` — the label is wrong or unsupported.
- `contested` — genuinely arguable either way.
- `needs_more_evidence` — cannot decide from what is provided.

## Confidence options (column `reviewer_confidence`)
- `high` / `medium` / `low`

## How to record
The easiest way is `reviewer_form.html` — open it in any browser, answer each
label, and click **Download my CSV** (your answers autosave locally as you go;
nothing leaves your machine until you send the file back yourself).

Alternatively, fill one row per label in `reviewer_form.csv` (or
`reviewer_form.jsonl`). The `label_review_packet.md` file shows the same labels
in a readable layout if you prefer to read there and record in the form. Leave
a field blank only if a question does not apply, and use `reviewer_notes` for
anything else.
