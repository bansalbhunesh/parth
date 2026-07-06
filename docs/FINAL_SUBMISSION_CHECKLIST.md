# Pramaan — Final Submission Checklist (Phase 11)

> The single pre-flight page for the ET AI Hackathon 2026 · PS4 submission. It
> collects every judge-facing URL, artifact path, and truth-gate in one place.
> This is the **verification** companion to the deliverable-tracking
> [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) and the shoot script
> [`VIDEO_RUNBOOK.md`](VIDEO_RUNBOOK.md). Governance of every claim lives in
> [`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md).

**Hard deadline:** `2026-07-22, 23:59 IST` (re-confirm on the Unstop dashboard before submitting).

---

## 1. Live URLs (open each, logged-out / incognito)

| Surface | URL | What it must show |
|---|---|---|
| GitHub repo (public) | https://github.com/bansalbhunesh/parth | README renders on `main`; CI badge "passing" while logged out |
| Judge Mode | https://parth-tan.vercel.app/judge | Load deviation demo ★ → Analyze streams; provenance chip visible |
| Evidence dashboard | https://parth-tan.vercel.app/evidence | Benchmark v1.2 card; reviewer-2 pending shown; graceful (not falsely green) if backend asleep |
| Backend health | https://parth-1-ma30.onrender.com/health | `"ready": true` when the key is wired |
| LLM status (deep) | https://parth-1-ma30.onrender.com/llm-check?deep=1 | true provider status; not a false-green tiny probe |
| OCR ground truth | https://parth-1-ma30.onrender.com/ocr-check | `"status":"ready"` (tesseract in the Docker image) |

> If `NEXT_PUBLIC_API` is unset on Vercel, the frontend falls back to bundled
> data (renders correctly, but is not live-served). For a live demo, set it to
> the Render URL and Manual-Deploy the backend with a fresh `GEMINI_API_KEY`.

## 2. Artifacts (attach / link on the form)

| Artifact | Path | Verify |
|---|---|---|
| Pitch deck (PDF) | [`docs/Pramaan_Deck.pdf`](Pramaan_Deck.pdf) | **12 pages**, ~1.0 MB, image-based (regenerate: `python scripts/export_deck.py`) |
| Detailed submission (PDF) | [`docs/Pramaan_Detailed_Submission.pdf`](Pramaan_Detailed_Submission.pdf) | **5 pages**, ~0.16 MB, **selectable text** (regenerate: `python scripts/export_detailed.py`) |
| Deck source | [`../presentation.html`](../presentation.html) | 12 truthful slides; every metric carries an evidence label |
| Detailed source | [`detailed_submission.html`](detailed_submission.html) | 10 sections; leads with benchmark v1.2 |
| Pitch script | [`../PITCH.md`](../PITCH.md) | 3–4 min; carries the safe line verbatim (§3) |
| Architecture | [`ARCHITECTURE.md`](ARCHITECTURE.md) + [`pipeline-diagram.svg`](pipeline-diagram.svg) | one reasoning graph; one LLM node; copilot = service |
| Impact model | [`BUSINESS.md`](BUSINESS.md) | figures labelled illustrative scenario |
| Pitch video | ⬜ **placeholder** — YouTube (Unlisted) → paste into README §3, `SUBMISSION_CHECKLIST.md` row 2, Unstop | record per `VIDEO_RUNBOOK.md` |

## 3. Repo / deploy state (fill on submission day)

- Latest commit on submission tip: `__________` (`git log -1 --format='%h %s'`)
- Branch merged to `main` and fast-forwarded (Render + Vercel deploy from `main`): ⬜
- Render backend Manual-Deployed with fresh `GEMINI_API_KEY`: ⬜
- `make verify-live` → **`GREEN -- demo away.`**: ⬜

## 4. Truth gates (all must pass — commands are copy-paste)

Run from repo root.

- [ ] **Tests** — `python -m pytest tests/ -q` → 605 passed (count varies slightly by Python version).
- [ ] **Lint** — `ruff check .` → clean.
- [ ] **Benchmark integrity untouched** — `git status --porcelain benchmarks/` → empty (labels/scores/reviewer files pristine).
- [ ] **Frontend** — `cd frontend && npx tsc --noEmit && npm run build` → clean.
- [ ] **Banned wording (automated)** — `python -m pytest tests/test_claims_register.py -q` → green. The gate scans README, PITCH, COMPETITIVE, deck + detailed sources, all docs, frontend text, benchmark + sample docs for every `CLAIMS_REGISTER.md` banned phrase (affirmative use fails; same-sentence disclaimers pass).
- [ ] **No secrets** — no real API keys committed; `.env` gitignored; grep for `GEMINI_API_KEY=`/`sk-`/`AIza` returns only placeholders.
- [ ] **PDF sanity** — both PDFs open, page counts as above, each < 50 MB; detailed PDF text-extracts (searchable).
- [ ] **Number consistency** — benchmark reads **53 pairs · 129 labels · 17 systems · 64 clean negatives · recall 0.862 · precision 0.953 · F1 0.905 · FAR 0.000 · rule baseline 0.111 · p50 ~2.5 s** across /evidence, README, deck, pitch, detailed PDF, architecture docs.
- [ ] **Reviewer-2 honesty** — every benchmark surface says reviewer-2 **pending** and calls the automated cross-check **machine QA, not human**.
- [ ] **OCR** — `/ocr-check` ready on the hosted backend (tesseract in the Docker image).
- [ ] **Failover** — `/llm-check?deep=1` reports the true provider; failover is framed as **availability, not accuracy**.
- [ ] **Rule floor** — with no model, endpoints still return 200 and the UI labels a rule-floor result **inconclusive / low-recall**, never a clean bill of health.

## 5. The one line to never contradict

> **Pramaan is not claiming field-validated ROI yet. It is a benchmarked
> prototype that proves a reliable first-pass deviation detection workflow across
> EPC document pairs.**

Everything on the form and in the video must be consistent with this. Evidence before confidence.
