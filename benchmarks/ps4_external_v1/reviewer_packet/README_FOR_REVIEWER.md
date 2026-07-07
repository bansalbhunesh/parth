# Benchmark v1.2 — Reviewer Validation Packet

This packet asks one thing: **help us check whether the benchmark's ground-truth
labels are correct.** It is a self-contained set of 44 labels drawn from the
`ps4_external_v1` EPC deviation benchmark, with the owner-requirement and
vendor/submittal excerpts and the evidence each label relies on.

> **Please fill `reviewer_form.csv`. If you are unsure, mark `contested` or
> `needs_more_evidence`. Do not force accept/reject. Your honest disagreement is
> useful.**

> **Do not judge the product, UI, model quality, or business idea. Only judge
> whether the benchmark labels and evidence are correct.**

## What this is (and is not)
- The documents are **team-authored fixtures** modeled on public reference values
  — they are **not** real vendor datasheets or real submittals.
- Ten pairs derive a value from a **public primary source**; those carry a
  provenance URL in their `pair_context/` file so you can check the derivation.
- Labels are **single-author frozen and pending independent review** — that is
  exactly why we are asking you.
- There are **no model predictions and no accuracy scores** anywhere in this
  packet, on purpose. This review is about the ground truth, not any system.

## What's in the packet
| file / folder | purpose |
|---|---|
| `reviewer_instructions.md` | how to review each label (read this first) |
| `reviewer_form.html` | **easiest way to review** — open in any browser, answer, download your CSV |
| `selected_labels.csv` | the 44 labels and why each was chosen |
| `label_review_packet.md` | readable per-label review sheets |
| `reviewer_form.csv` / `.jsonl` | where you record verdicts if you prefer a spreadsheet (one row per label) |
| `pair_context/` | per-pair owner + vendor excerpts and any provenance note |
| `source_excerpts/` | per-label evidence spans and source category |

## How to do the review

**Easiest path:** open `reviewer_form.html` in any browser (double-click — no
install, no internet needed). It shows every label with its evidence and pair
context, saves your answers in the browser as you go, and gives you a
**Download my CSV** button at the end. Send back that one file.

**Spreadsheet path**, if you prefer:
1. Read `reviewer_instructions.md`.
2. For each label, read its sheet in `label_review_packet.md` (and the matching
   `pair_context/<pair>_context.md` for fuller context).
3. Record your verdict, confidence, and notes in `reviewer_form.csv`.
4. Send back the filled `reviewer_form.csv` (or `.jsonl`).

If several people are reviewing, each person works **independently** (no
discussing verdicts before returning the form) and sends back their own file.

## After you return the form
We import it with `python scripts/import_reviewer2_feedback.py` — it becomes the
second-reviewer record (`labels/reviewer_2.jsonl`) and produces an agreement
summary. Your original file is never overwritten.

## Known limitations (so nothing is hidden)
- Team-authored fixtures, not real datasheets.
- Single-author frozen labels (this review is the second opinion).
- A subset of labels was auto-flagged by a consistency check as worth a closer
  look; those are included here and marked in `selected_labels.csv`.
- Stored primary-source PDFs and full two-person adjudication are still pending.
