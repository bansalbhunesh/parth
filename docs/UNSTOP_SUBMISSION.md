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
Full source, benchmark, 901 tests, CI:  https://github.com/bansalbhunesh/parth
Pitch video (2:50):  <VIDEO_LINK_HERE>
```

## Project description (main body)

```
Pramaan is the proof engine for construction documents. It reads a vendor
submittal against the owner's design basis and the governing standards
(Uptime, NFPA, ASHRAE, IEC, IS 1893…) and flags every deviation THE DAY the
document lands — then tells you exactly which
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
provenance chips on every result. 901 automated tests, full CI, live on
Vercel + Render.

The finding is the start of a workflow, not the end of a report: one click
persists it as a case, assigns a named owner, drafts and issues the RFI,
re-analyzes the vendor's revised submittal, and closes only when the same
deviation no longer appears — with an audit register (JSON + printable HTML,
SHA-256 integrity hash) exported straight from the dashboard. Scanned and
image-only submittals are read via Tesseract OCR with an explicit
"verify critical values" caveat, and a documented Gemini-vision path reads
stamped datasheet images directly. The demo stays honest under failure:
every result carries a provenance chip (live model, cache replay, or
deterministic rule floor), and each failover leg has its own time budget so
a slow provider degrades gracefully instead of silently.

All five PS4 build areas are implemented deeply, not sketched: the
specification-compliance agent (the reasoning core above), a schedule-risk
engine (critical-path analysis plus 10,000-trial Monte-Carlo giving
P50/P80/P90 finish dates and the on-time-probability drop each uncaught
deviation causes), a supply-chain layer (per-shipment lateness probability
and cost-of-delay-ranked alternatives), a commissioning QA copilot (each
deviation mapped to the exact test it will fail on a 17-test graph keyed to
Uptime/TIA-942/BICSI), and an RFI intelligence service (cited answers over
the project corpus with prior-RFI surfacing). A deterministic project graph
ties them together, so one deviation's blast radius — the failed test, the
long-lead procurement exposure, the milestone slip — is a single traversal
computed from data; the LLM narrates it but never draws an edge or moves a
date.

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

Run the Final Submission Checklist section of `docs/CHECKLISTS.md` end-to-end first — every truth-gate
must be green, `make verify-live` must say `GREEN -- demo away.`, `make
verify-submission` must pass, and the video link must open in an incognito
window.

## The one line to never contradict (also in the video)

> Pramaan is not claiming field-validated ROI yet. It is a benchmarked
> prototype that proves a reliable first-pass deviation detection workflow
> across EPC document pairs.
