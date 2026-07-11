# Unstop Submission Text — paste-ready

> Copy-paste blocks for the Phase-2 submission form. Fill the ONE mandatory
> blocker (the video link) after recording. Everything else is final and
> consistent with the claims register. Keep the judge journey at the very top
> — judges decide in the first 30 seconds whether to engage.

---

## The 30-second judge journey (put this FIRST in the form)

```
PRAMAAN — EPC Deviation Intelligence (PS4)

See it work (90 seconds):  https://parth-tan.vercel.app/judge
  → click "Load deviation demo ★", hit Analyze, watch it reason live.
Every number + its limitation:  https://parth-tan.vercel.app/evidence
Full source, benchmark, 635 tests, CI:  https://github.com/bansalbhunesh/parth
Pitch video (3 min):  <VIDEO_LINK_HERE>
```

## Project description (main body)

```
Pramaan reads a vendor submittal against the owner's design basis and the
governing standards (Uptime, NFPA, ASHRAE, IEC, IS 1893…) and flags every
deviation THE DAY the document lands — then tells you exactly which
commissioning test that deviation will fail and how many weeks of lead time
remain to fix it. That converts a design-review miss into a scheduled,
preventable commissioning failure, at the one moment the fix is a one-line RFI
instead of a seven-figure schedule slip.

Measured, not asserted: on our frozen, provenance-tracked benchmark
(ps4_external_v1 v1.2 — 53 spec–submittal pairs, 129 frozen labels, 17 system
types, 64 clean-negative controls) the featured configuration
(gemini-3.1-flash-lite, 3-pass) reports mean recall 0.862, precision 0.953,
F1 0.905, and 0 false alerts on the clean negatives, versus a deterministic
rule baseline of 0.111 on the same labels. Fixtures are team-authored (10
derived from public primary sources); labels are single-author frozen with
two-person adjudication pending — a benchmark result, not a field-validation
claim. The full error analysis, limitations, and a no-API-key reproduction
harness are public in the repo.

Architecture: one compliance reasoning graph (LangGraph, a single LLM
reasoning core with bounded retrieval + self-critique cycles) surrounded by
deterministic services — commissioning-test mapping, Monte-Carlo schedule
risk, supply-chain risk, and a blast-radius project graph — plus a reliability
layer: multi-provider failover with per-provider spend guards, a deterministic
rule floor (no silent zeros), OCR for scanned submittals, and honest
provenance chips on every result. 635 automated tests, full CI, live on
Vercel + Render.

Why it generalises: any specification → vendor submittal → acceptance-test
domain (pharma GMP qualification, aerospace AS9100, medical-device V&V) is the
same problem. Data-centre EPC is the highest-stakes instance we proved it on.
```

## Deliverable links (form fields)

| Field | Value |
|---|---|
| GitHub repo | https://github.com/bansalbhunesh/parth |
| Live demo | https://parth-tan.vercel.app/judge |
| Pitch video | `<VIDEO_LINK_HERE>` (YouTube Unlisted — check it opens logged-out) |
| Architecture document | https://github.com/bansalbhunesh/parth/blob/main/docs/ARCHITECTURE.md |
| Impact model | https://github.com/bansalbhunesh/parth/blob/main/docs/BUSINESS.md |
| Detailed submission (PDF) | https://github.com/bansalbhunesh/parth/blob/main/docs/Pramaan_Detailed_Submission.pdf |
| Pitch deck (PDF) | https://github.com/bansalbhunesh/parth/blob/main/docs/Pramaan_Deck.pdf |

## Pre-submit gate

Run `docs/FINAL_SUBMISSION_CHECKLIST.md` end-to-end first — every truth-gate
must be green, `make verify-live` must say `GREEN -- demo away.`, `make
verify-submission` must pass, and the video link must open in an incognito
window.

## The one line to never contradict (also in the video)

> Pramaan is not claiming field-validated ROI yet. It is a benchmarked
> prototype that proves a reliable first-pass deviation detection workflow
> across EPC document pairs.
