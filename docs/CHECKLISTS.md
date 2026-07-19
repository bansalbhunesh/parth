# Pramaan — Submission Checklist (ET AI Hackathon 2.0, Phase 2)

> **Pre-flight the day you submit?** Use the **Final Submission Checklist**
> section below in this same file — every judge-facing URL, artifact path, and
> truth-gate in one place. This section tracks the deliverables; that section
> verifies them.
>
> One row per deliverable: what the form wants → the exact artifact → status.
> Fill the **Unstop form field names + the deadline** from the dashboard (they
> are not public); everything else is ready or has a named owner.

## Hard deadline

- [x] **Phase 2 submission deadline (live Unstop record):** `2026-07-22, 23:59:21 IST` (re-confirmed 2026-07-19 against the live public Unstop record; still re-confirm on the dashboard before submitting — organizers may adjust)
- [ ] Submit by **21 July evening** (leave a full night of slack for cold starts, upload retries, form surprises).
- [ ] Freeze window: **no risky changes after 19 July** — final 3 days (20–22 July) are verify/rehearse/record only.

## Deliverables

| # | Deliverable (per rules) | Artifact | Status |
|---|---|---|---|
| 1 | **Public GitHub repository** | `https://github.com/bansalbhunesh/parth` | ✅ public since 2026-07-03; CI badge verified "passing" logged-out. NOTE: the repo home renders `main`'s README — keep `main` fast-forwarded to the submission tip |
| 2 | **Pitch video** (2:50) | YouTube unlisted link → also placed in the README "Judges: start here" block, `UNSTOP_SUBMISSION.md`, the Final Submission Checklist section below, and `docs/detailed_submission.html`. NOTE: the paste commit trips `scripts/check_protected_scope.py` (video-token lines) — update that script's freeze in the SAME commit (self-edits are exempt) so CI stays green | ⬜ **BLOCKER** — record per `docs/VIDEO_RUNBOOK.md` (script: `PITCH.md`) |
| 3 | **Architecture document** | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) (+ `docs/pipeline-diagram.svg`) | ✅ |
| 4 | **Impact model** (quantified business benefit) | [`docs/BUSINESS.md`](BUSINESS.md) — every figure cited | ✅ |
| 5 | Pitch deck (if the form takes a file) | [`docs/Pramaan_Deck.pdf`](Pramaan_Deck.pdf) — 12 pages, regenerate with `python scripts/export_deck.py` after any deck edit | ✅ |
| 6 | Live demo URL | `https://parth-tan.vercel.app/judge` (front) · `https://parth-1-ma30.onrender.com/health` (API) | ✅ live & verified 2026-07-16 against deployed `main` (`6adc9ad`): `verify_live.py` passed 10/10 in 142 s · `/health` ready · all three PS4 layers live · deep probe 5 findings/13.9 s · `/analyze` and `/analyze/stream` both `mode: llm` with 5 findings · frontend `/` and `/judge` 200. `/ocr-check` remains the hosted Docker/Tesseract readiness gate. Re-verify after the final submission commit and again on submission day with `make verify-live` |
| 7 | Team details | 1–4 members, one team per person — from the Unstop registration | ⬜ confirm roster matches registration |

## Pre-submission gates (run in this order, same day)

1. `main` fast-forwarded to the branch tip (Render + Vercel deploy from `main`).
2. Fresh `GEMINI_API_KEY` set in Render → Manual Deploy → latest commit.
3. `make verify-live` → **`GREEN -- demo away.`** (checks deployed commit, PS4
   layers, deep LLM probe, real GXT5 pair through both analyze paths, frontend).
4. `make verify` on a **fresh clone** (proves the judge's-laptop story).
5. Repo public → open the README logged-out: CI badge green, screenshots load,
   Judge-Mode link works, video link present (not the placeholder), and
   `python scripts/check_submission_ready.py` passes.
6. Submit the form; screenshot the confirmation page.

## Warm-up before ANY judged demo

- Hit the live app once (~40 s Render cold start), run one warm-up Analyze,
  then `make verify-live` again. Pre-flight ritual: `PITCH.md` §Pre-flight.

## Do NOT touch after the final gate

`eval/` + committed results · `data/samples/real/` + `PROVENANCE.md` ·
`data/corpus/` (git add -f trap) · `gemini-2.5-flash` pin · git history.
# Pramaan — Final Submission Checklist (Phase 11)

> The single pre-flight page for the ET AI Hackathon 2026 · PS4 submission. It
> collects every judge-facing URL, artifact path, and truth-gate in one place.
> This is the **verification** companion to the deliverable-tracking
> Submission Checklist section above and the shoot script
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
| Unstop form text | [`UNSTOP_SUBMISSION.md`](UNSTOP_SUBMISSION.md) | paste-ready after the video URL is inserted |
| Pitch video | ⬜ **BLOCKER** — YouTube (Unlisted) → paste into the README "Judges: start here" block, Submission Checklist row 2 above, Unstop, and detailed submission source | record per `VIDEO_RUNBOOK.md` |

## 3. Repo / deploy state (fill on submission day)

- Latest commit on submission tip: `__________` (`git log -1 --format='%h %s'`)
- Branch merged to `main` and fast-forwarded (Render + Vercel deploy from `main`): ⬜
- Render backend Manual-Deployed with fresh `GEMINI_API_KEY`: ⬜
- `make verify-live` → **`GREEN -- demo away.`**: ⬜

### Judging-day environment (set in the Render dashboard, revert after)

- ⬜ **Finale window (recorded)** — the live competition record shows Phase 3
  as a **10–15 minute live session with demo + Q&A**, in a recorded window
  overlapping 22–23 July (per the live Unstop record, 2026-07-19); apply every
  toggle in this section before that session, not only for async judging.
- ⬜ **Raise the per-IP rate limits** — a venue's shared Wi-Fi NAT puts every
  judge behind ONE public IP, so the defaults (20 analyses / 3 deep probes
  per hour) become a *shared* budget. Set `PRAMAAN_ANALYSIS_LIMIT_PER_HOUR=120`
  and `PRAMAAN_DEEP_PROBE_LIMIT_PER_HOUR=12` before the session; restore the
  defaults afterwards.
- ⬜ **Gateway balance** — the featured-model leg spends real credit
  (aicredits.in); check the balance covers the session, or the leg 402s and
  the chain silently serves the Groq model instead
  (`/llm-check?probe_all=1` must show all three legs `ok: true`).
- ⬜ **Morning-of probe** — Gemini free-tier quota resets daily and has
  failed probes before (2026-07-14); run `make verify-live` the morning of,
  not just the night before.
- ⬜ **Keep-warm active** — `.github/workflows/keepwarm.yml` pings `/health`
  every 10 minutes (guard lapses after 2026-07-24) so the first judge click
  never hits a Render cold start; delete the workflow after judging.

## 4. Truth gates (all must pass — commands are copy-paste)

Run from repo root.

- [ ] **Tests** — `python -m pytest tests/ -q` → 901 passed.
- [ ] **Lint** — `python -m ruff check .` → clean.
- [ ] **Mandatory placeholders** — `python scripts/check_submission_ready.py` → green only after the pitch-video URL is public and logged-out accessible.
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
# Deployment Checklist

One-page pre-flight for deploying the Pramaan demo (backend on Render/Docker,
frontend on Vercel). Companion docs: `docs/SECURITY_DEMO_RUNBOOK.md`,
`docs/LLM_FAILOVER_RUNBOOK.md`, and the OCR Deployment Checklist section below.

> Pramaan is a prototype / hackathon build, **demo-hardened** — not production-grade.
> Keep claims accordingly (`docs/CLAIMS_REGISTER.md`).

## 1. Backend (Render — Docker runtime)

Build from `Dockerfile.backend` (installs the `tesseract` binary so OCR works).
`render.yaml` carries the non-secret env; set secrets in the dashboard.

**Secrets (dashboard, `sync:false`):** `GEMINI_API_KEY`, and optionally the
failover legs `OPENAI_API_KEY`(Qwen gateway)/`GROQ_API_KEY`. `DEMO_AUTH_TOKEN`
only if enabling auth.

**Security env (already in `render.yaml`):**
```
PRAMAAN_RATE_LIMIT_ENABLED=true
PRAMAAN_ANALYSIS_LIMIT_PER_HOUR=20
PRAMAAN_UPLOAD_LIMIT_PER_HOUR=10
PRAMAAN_DEEP_PROBE_LIMIT_PER_HOUR=3
PRAMAAN_MAX_UPLOAD_MB=20
DEMO_AUTH_ENABLED=false        # flip to true (+DEMO_AUTH_TOKEN) only if abused
```

**LLM env:** `PRAMAAN_LLM=gemini`, `GEMINI_MODEL=gemini-2.5-flash`,
`PRAMAAN_LLM_TIMEOUT=60`, `PRAMAAN_LLM_PROVIDER_ORDER=gemini,qwen,groq`
(the gateway leg is funded via aicredits.in and pinned to the
benchmark-featured `gemini-3.1-flash-lite`; Claude stays out of the order
until a key exists — see `LLM_FAILOVER_RUNBOOK.md`).

## 2. Frontend (Vercel)

- `NEXT_PUBLIC_API=https://<backend-host>` (inlined at build — redeploy after a
  change). No secrets in the frontend bundle (never the demo token).

## 3. Pre-deploy verification (local)

```powershell
python -m pytest tests -q --tb=short
python -m ruff check .
python scripts/benchmark_manifest_check.py
python scripts/benchmark_hash_sources.py
docker build -f Dockerfile.backend -t pramaan-verify .
```

## 4. Post-deploy verification (live)

```bash
BASE=https://<backend-host>
curl -s $BASE/health        | jq '.commit, .security, .ocr_available, .llm.chain'
curl -s $BASE/ocr-check     | jq '.status'          # expect "ready"
curl -s $BASE/llm-check     | jq '.ok, .failover.chain'
```

Green when: `commit` = the deployed SHA; `security.rate_limit_enabled=true`;
`ocr-check.status="ready"`; `llm-check.ok=true` (or `on_rule_engine_floor` if no
key). Upload rejection spot-check per the security runbook §4.

## 5. Security posture toggles

| Situation | Action |
|---|---|
| Demo being abused (quota drain) | already rate-limited; tighten `*_LIMIT_PER_HOUR` |
| Need to lock the demo | `DEMO_AUTH_ENABLED=true` + `DEMO_AUTH_TOKEN=<random>`; share token with judges out-of-band |
| Load testing | `PRAMAAN_RATE_LIMIT_ENABLED=0` temporarily |
| Restrict browsers | `PRAMAAN_CORS_ORIGINS=https://<frontend-host>` |

## 6. Rollback

- **Backend:** Render → Deploys → **Rollback** to the previous image, or
  `git revert <sha>` + push (redeploys). All Phase-5 controls are env-gated:
  setting `PRAMAAN_RATE_LIMIT_ENABLED=0` and `DEMO_AUTH_ENABLED=false` reverts
  to fully-open behaviour without a code change. Upload validation cannot be
  env-disabled — to bypass it, roll back the image.
- **Frontend:** Vercel → Deployments → promote the previous build.
- No database/state to migrate; rollback is image/deploy-level only.
# OCR Deployment Checklist

Pramaan reads scanned / image-only PDFs **and** directly-uploaded images
(`.png/.jpg/.tiff/.webp`) via **Tesseract OCR**, text-first with an OCR fallback.
OCR is best-effort (not lossless) and needs the `tesseract` **system binary**.
This checklist makes OCR demo-safe: it either works and is proven, or it is
honestly reported as unavailable — never a silent zero and never a false claim.

## The one rule

> A deployment may only imply OCR works if `GET /ocr-check` returns
> `"status": "ready"`. That endpoint live-probes the tesseract binary, so it is
> the single source of truth — the UI badge and docs defer to it.

## Where OCR runs

| Target | OCR binary? | How |
|---|---|---|
| Local dev (`make run`) | only if `tesseract` is on PATH | install Tesseract locally, or set `TESSERACT_CMD` |
| Docker (`Dockerfile.backend`) | ✅ yes | `apt-get install tesseract-ocr` in the image |
| docker-compose (`make docker`) | ✅ yes | backend service builds `Dockerfile.backend` |
| Render (`render.yaml`) | ✅ yes | `runtime: docker` → builds `Dockerfile.backend` |
| Plain Python buildpack | ❌ no | buildpack can't `apt-get` → graceful "OCR unavailable" |

There is **one** OCR-capable backend image (`Dockerfile.backend`); Render,
compose, and CI all use it, so they can't drift apart.

## Verify locally

```bash
make verify-ocr          # in-process: probes + image/scanned-PDF recovery + disable path
# or, prove the shipping image:
make verify-ocr-docker   # builds Dockerfile.backend, asserts /ocr-check == ready
```

`make verify-ocr` **skips cleanly** (exit 0) when no binary is installed — pass
`python scripts/verify_ocr.py --require-tesseract` to make its absence a failure
(CI/Docker use this expectation via the docker-build smoke test).

## Deploy to Render (enables OCR in production)

1. Merge the branch so `render.yaml` (Docker runtime → `Dockerfile.backend`) is on `main`.
2. Render → the `pramaan-backend` service → **Manual Deploy → latest commit**.
   (First Docker build is slower than the buildpack — it apt-installs Tesseract.)
3. Confirm the live backend:
   ```bash
   curl -s https://<your-backend>.onrender.com/ocr-check
   # expect: {"status":"ready","ocr_available":true,"tesseract_version":"5.x.x",...}
   curl -s https://<your-backend>.onrender.com/health   # ok:true, ocr_available:true
   ```
4. In Judge Mode, the upload panel shows **"OCR ready — scanned PDFs & images
   supported (Tesseract 5.x)"**. Upload a scanned PDF; the result carries an
   amber **"Read via OCR — verify critical values"** caveat.

## Config (env)

| Var | Default | Meaning |
|---|---|---|
| `PRAMAAN_OCR_ENABLED` (alias `PRAMAAN_OCR`) | `1` | `0` disables OCR everywhere |
| `PRAMAAN_OCR_DPI` | `300` | scanned-PDF rasterization DPI |
| `PRAMAAN_MAX_PDF_PAGES` | `30` | cap on pages OCR'd per PDF |
| `PRAMAAN_MAX_IMAGE_PIXELS` | `20000000` | reject larger images (bomb guard) |
| `TESSERACT_CMD` | — | path to the binary if not on PATH |
| `TESSDATA_PREFIX` | — | language-data dir |

## If OCR becomes risky near a deadline — disable honestly

Prefer honest disabling over half-working OCR. Any of these makes the product
truthful with OCR off, with **no false claims** (the UI badge, `/ocr-check`, and
docs all report "unavailable"):

- Set `PRAMAAN_OCR_ENABLED=0` (badge shows "OCR disabled", uploads of scanned
  PDFs/images return the honest 400 message), **or**
- Revert `render.yaml` to the Python buildpack (badge shows "OCR unavailable").

Either way, text-based PDFs and pasted text keep working, and nothing in the UI
or docs claims OCR that the runtime can't deliver.

## What OCR does NOT claim

- Not lossless (e.g. `GXT5` can read as `GXTS`) — hence the verify-values warning.
- English-only, best-effort; no per-page scanned detection (whole-document
  20-char heuristic). See [`../eval/OCR_SCANNED_PDF.md`](../eval/OCR_SCANNED_PDF.md)
  and claims-register rows 20–21 in [`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md).
- Image OCR here (Tesseract → text) is distinct from `/analyze/vision` (an LLM
  reads the picture) — different paths, different contracts.
