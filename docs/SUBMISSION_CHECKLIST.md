# Pramaan — Submission Checklist (ET AI Hackathon 2.0, Phase 2)

> One row per deliverable: what the form wants → the exact artifact → status.
> Fill the **Unstop form field names + the deadline** from the dashboard (they
> are not public); everything else is ready or has a named owner.

## Hard deadline

- [x] **Phase 2 submission deadline confirmed on Unstop:** `2026-07-27` (exact hour TBC on the dashboard — treat as morning IST until confirmed)
- [ ] Submit by **26 July evening** (leave a full night of slack for cold starts, upload retries, form surprises).
- [ ] Freeze window: **no risky changes after 24 July** — final 3 days are verify/rehearse/record only.

## Deliverables

| # | Deliverable (per rules) | Artifact | Status |
|---|---|---|---|
| 1 | **Public GitHub repository** | `https://github.com/bansalbhunesh/parth` | ✅ public since 2026-07-03; CI badge verified "passing" logged-out. NOTE: the repo home renders `main`'s README — keep `main` fast-forwarded to the submission tip |
| 2 | **Pitch video** (3 min) | YouTube unlisted link → also placed in README "Judges: start here" §3 | ⬜ record per `docs/VIDEO_RUNBOOK.md` (script: `PITCH.md`) |
| 3 | **Architecture document** | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) (+ `docs/pipeline-diagram.svg`) | ✅ |
| 4 | **Impact model** (quantified business benefit) | [`docs/BUSINESS.md`](BUSINESS.md) — every figure cited | ✅ |
| 5 | Pitch deck (if the form takes a file) | [`docs/Pramaan_Deck.pdf`](Pramaan_Deck.pdf) — 15 pages, regenerate with `python scripts/export_deck.py` after any deck edit | ✅ |
| 6 | Live demo URL | `https://parth-tan.vercel.app/judge` (front) · `https://parth-3puc.onrender.com/health` (API) | ⬜ blocked on Render: paste the fresh `GEMINI_API_KEY` + Manual Deploy latest `main`. Key verified locally 2026-07-03: deep probe 5 findings/23s · GXT5 pair 5 findings/16s (llm) · scanned-PDF OCR 3 findings/18.5s (llm) — OCR stays in the demo |
| 7 | Team details | 1–4 members, one team per person — from the Unstop registration | ⬜ confirm roster matches registration |

## Pre-submission gates (run in this order, same day)

1. `main` fast-forwarded to the branch tip (Render + Vercel deploy from `main`).
2. Fresh `GEMINI_API_KEY` set in Render → Manual Deploy → latest commit.
3. `make verify-live` → **`GREEN -- demo away.`** (checks deployed commit, PS4
   layers, deep LLM probe, real GXT5 pair through both analyze paths, frontend).
4. `make verify` on a **fresh clone** (proves the judge's-laptop story).
5. Repo public → open the README logged-out: CI badge green, screenshots load,
   Judge-Mode link works, video link present (not the placeholder).
6. Submit the form; screenshot the confirmation page.

## Warm-up before ANY judged demo

- Hit the live app once (~40 s Render cold start), run one warm-up Analyze,
  then `make verify-live` again. Pre-flight ritual: `PITCH.md` §Pre-flight.

## Do NOT touch after the final gate

`eval/` + committed results · `data/samples/real/` + `PROVENANCE.md` ·
`data/corpus/` (git add -f trap) · `gemini-2.5-flash` pin · git history.
