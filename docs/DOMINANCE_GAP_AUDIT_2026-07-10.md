# Pramaan Dominance Gap Audit

Date: 2026-07-10
Branch audited: `main`
Commit audited: `9ac3c3d`
Repository: `bansalbhunesh/parth`

## Executive Verdict

Pramaan is far stronger than a normal hackathon repo on engineering depth,
truth-gating, live demo readiness, benchmark discipline, and domain specificity.
It already looks like a serious technical product, not a toy.

Brutal truth: the gap between Pramaan and a winner is no longer "more code". The
winning gap is trust conversion:

1. A complete submission artifact set, especially the video.
2. Real independent reviewer/adjudication evidence.
3. Proof that the practitioner quotes and validation claims are real, permissioned,
   and auditable.
4. A cleaner production-readiness story: persistent queues/storage, observability,
   shared rate limiting, and end-to-end browser/a11y audits in CI.
5. Less overwhelming judge surface. The repo is impressive, but also dense enough
   that a tired judge can miss the killer story.

Current winner-readiness score: **82/100 if video is ignored; 74/100 with the
mandatory video blocker included.**

Ceiling after P0/P1 fixes: **91-94/100**.

## Evidence Collected

Commands run during this audit:

| Check | Result |
|---|---|
| `git status --short --branch` | clean, `main...origin/main` |
| GitHub public page | public repo visible, 247 commits, README surface visible |
| `python -m ruff check .` | passed |
| `python -m pytest tests -q --tb=short` | 605 passed |
| `python -m pytest tests --collect-only -q` | 605 tests collected |
| `npm run typecheck` | passed |
| `npm test` | 6 Vitest tests passed |
| `npm run build` | Next.js production build passed |
| `npm audit --audit-level=moderate` | 0 vulnerabilities |
| `python scripts/benchmark_hash_sources.py` | 218 docs hashed, manifest hashes match |
| `python scripts/benchmark_manifest_check.py` | manifest + labels + freeze valid |
| `python scripts/benchmark_label_audit.py` | 123/129 consistent, 6 human-review candidates |
| `python scripts/check_real_source_links.py --no-write --timeout 8` | 13 ok, 6 manual_check, 0 hard unreachable |
| `python scripts/verify_live.py` | 10/10 live checks passed in 140s |
| `python scripts/check_submission_ready.py` | failed only on video placeholders |

Repo size snapshot:

| Area | Files | Lines |
|---|---:|---:|
| backend | 22 | 5,172 |
| frontend | 64 | 41,510 |
| tests | 33 | 4,786 |
| docs | 45 | 39,843 |
| benchmarks | 390 | 13,610 |
| data | 389 | 29,034 |
| eval | 14 | 1,584 |
| scripts | 21 | 3,889 |

## Overall Scores

| Dimension | Score | Verdict |
|---|---:|---|
| Core engineering | 9/10 | Excellent for hackathon, credible beyond it |
| Backend/API | 8.5/10 | Strong, demo-hardened, honest fallbacks; not production infra |
| Frontend/Judge UX | 8/10 | Distinctive, dense, strong proof pages; needs e2e a11y/perf audits |
| Benchmark/evaluation | 7.5/10 | Strong and honest, but still single-author and team-authored |
| Evidence/provenance | 7/10 | Much improved; still lacks external adjudication and stored-source depth |
| Security | 7/10 | Demo-hardened well; not production-grade, by design |
| Deployment/live demo | 8.5/10 | Live verified green; free-tier/cold/quota risk remains |
| Documentation | 8/10 | Very strong truth governance, but too much volume and some stale phrasing |
| Product/market validation | 5.5/10 | Problem story is strong; customer/proof gap is the biggest winner separator |
| Submission completeness | 4/10 until video | Mandatory video blocker remains |

## Frontend Technical Audit Score

| Dimension | Score / 4 | Key Finding |
|---|---:|---|
| Accessibility | 3 | Many labels/ARIA/reduced-motion hooks exist; focus coverage is uneven |
| Performance | 3 | Build passes; dashboard is large and visually dense; no Lighthouse budget |
| Theming | 3 | Strong brand tokens, but many hard-coded colors and inline styles remain |
| Responsive design | 3 | Breakpoints exist; dense tables and war-room panels need device testing |
| Anti-patterns | 3 | Much better than generic AI UI; some glow/gradient/card-density remains |
| Total | **15/20** | Good. Not weak, but not yet "undeniably polished on every device." |

## P0 - Blocking / Winner-Critical

### P0.1 - Pitch video is still missing

Location:
- `README.md:65`
- `docs/UNSTOP_SUBMISSION.md:19`
- `docs/UNSTOP_SUBMISSION.md:64`
- `docs/SUBMISSION_CHECKLIST.md:22`
- `docs/FINAL_SUBMISSION_CHECKLIST.md:41`
- `docs/detailed_submission.html:155`

Impact:
- This is the only hard submission blocker detected by
  `python scripts/check_submission_ready.py`.
- A winning repo with a missing mandatory artifact can lose before technical
  judging begins.

Fix:
- Record the 3-minute video using `docs/VIDEO_RUNBOOK.md` and `PITCH.md`.
- Upload unlisted.
- Verify logged-out access.
- Paste the same URL into all listed surfaces.
- Rerun `python scripts/check_submission_ready.py`.

### P0.2 - Practitioner quotes are not repo-verifiable

Location:
- `docs/VALIDATION.md:55-113`
- `README.md:68`
- `docs/OUTREACH.md:108-122`

Impact:
- The validation section contains named practitioner quotes and says contact
  records are held off-repo.
- If every quote is real, permissioned, and traceable, this is a strength.
- If even one is drafted, invented, unpermissioned, or not auditable, it becomes
  the most damaging risk in the whole project. It would destroy trust faster
  than any code bug.

Fix:
- Create a private evidence pack: email/LinkedIn screenshot, consent line,
  approved quote text, title/company preference, date, and whether name may be
  public.
- If consent cannot be proven, remove the named quote immediately or replace it
  with "outreach pending".
- Add a public note saying "permission records held off-repo; available to judges
  on request" only if that is literally true.

### P0.3 - Reviewer-2 and adjudication are not complete

Location:
- `benchmarks/ps4_external_v1/labels/REVIEW_STATUS.md`
- `benchmarks/ps4_external_v1/reviewer_packet/`
- `docs/CLAIMS_REGISTER.md:36`

Impact:
- The benchmark is honest, but it is still single-author frozen.
- Winners usually have one external validation artifact that is boring and hard
  to argue with. This is the missing artifact.
- The automated audit still flags 6 labels for human review.

Fix:
- Get at least one qualified external reviewer to fill the reviewer CSV.
- Import it with `scripts/import_reviewer2_feedback.py`.
- Resolve the 6 automated-audit candidates first.
- Publish agreement/disagreement counts, not just a success headline.

## P1 - Major Gaps Separating Pramaan From a Winner

### P1.1 - No real customer/field validation

Location:
- `docs/CLAIMS_REGISTER.md:38`
- `docs/BUSINESS.md:111`
- `docs/TECHNICAL_OVERVIEW.md:109`

Impact:
- The benchmark proves technical capability on a controlled evaluation.
- It does not yet prove that a customer would trust this on live submittals or
  that it changes a real workflow.
- Judges comparing against a product with a pilot, LOI, or real customer
  document may score that competitor higher on adoption.

Fix:
- Run a 30-minute practitioner screen-share using the reviewer packet or Judge
  Mode.
- Capture a signed/permissioned short feedback note.
- Best artifact: one real anonymized submittal pair from a practitioner, with
  their verdict on whether Pramaan's findings are useful.

### P1.2 - Source/provenance is traceable, but still not independently archived

Location:
- `docs/REAL_SOURCE_LINK_CHECK.md`
- `data/samples/real/PROVENANCE.md`
- `benchmarks/ps4_external_v1/sources/README.md`

Impact:
- Current status is honest and better than before: 13 OK links, 6 manual browser
  checks, 0 hard unreachable.
- But link-based provenance is weaker than archived, hash-addressed, license-safe
  extracts.
- Vendor websites change; judges may not manually check blocked pages.

Fix:
- For every public source that permits it, store a normalized excerpt with URL,
  retrieval date, hash, license basis, and exact derived field.
- For pages that block bots, add a manual reviewer screenshot hash or local
  citation note where license permits.
- Keep proprietary standards citation-only.

### P1.3 - CLOSED: `DocumentDiff` XSS debt removed

Location:
- `frontend/components/DocumentDiff.tsx`
- `frontend/__tests__/components.test.tsx`

Status:
- Replaced HTML string replacement with tokenized React spans.
- Text now escapes by construction through React rendering.
- Added a regression test with hostile document text to prove it renders as
  text, not markup, while preserving highlight styling.

### P1.4 - CI is good, but not winner-grade DevSecOps yet

Location:
- `.github/workflows/ci.yml`

Impact:
- CI runs ruff, backend tests with coverage, evals, frontend typecheck/build,
  and Docker build/OCR smoke.
- Missing gates: `npm audit`, source link verifier, submission placeholder guard,
  CodeQL, Dependabot, frontend component tests, and possibly Playwright smoke.
- Local audit found these pass, but CI should prove them on every PR.

Fix:
- Add CI steps for:
  - `npm audit --audit-level=moderate`
  - `npm test`
  - `python scripts/check_submission_ready.py` gated only for release branches
  - `python scripts/check_real_source_links.py --no-write`
  - CodeQL or equivalent static scan
  - Dependabot config
  - Playwright smoke for `/`, `/judge`, `/evidence`, `/war-room`

### P1.5 - Production architecture is intentionally prototype-level

Location:
- `backend/jobs.py`
- `backend/security.py`
- `docs/SCALABILITY_PROOF.md`
- `docs/SECURITY_DEMO_RUNBOOK.md`

Impact:
- The repo is honest: in-memory cache/jobs, process-local rate limiting, optional
  demo token, no persistent DB/queue.
- For a hackathon, this is acceptable.
- For "dominant overall product", a judge can say: this is demo-hardened, not
  ready for production use.

Fix:
- Add a production blueprint:
  - Redis/Upstash for rate limits and job state.
  - Postgres for analysis runs, reviewer records, projects, and audit trails.
  - Object storage for uploaded docs with retention policy.
  - Background worker for long LLM/OCR jobs.
  - Structured logs plus Sentry/OpenTelemetry.

### P1.6 - Frontend has proof power, but too much weight lives in one CSS/app surface

Location:
- `frontend/app/globals.css` is about 2,400 lines.
- `frontend` total is about 41,510 lines.
- Multiple components use hard-coded colors or inline styles.

Impact:
- It works and has a strong identity.
- But the implementation is harder to maintain and harder to theme than it needs
  to be.
- A design/system reviewer may see "impressive demo" rather than "product design
  system".

Fix:
- Extract semantic tokens and shared panel/table/button primitives.
- Move one-off inline styles into component classes.
- Add visual regression checks for `/judge`, `/evidence`, and `/war-room`.
- Keep the dashboard dense, but make Judge Mode the primary first impression.

### P1.7 - The repo is extremely strong but too dense for a tired judge

Location:
- `README.md` is about 61 KB.
- `docs/` is about 39,843 lines.

Impact:
- The density proves work, but can bury the winning narrative.
- Judges do not reward every document equally. They reward the 90-second path
  that makes the product impossible to forget.

Fix:
- Add a one-page `docs/JUDGE_BRIEF.md`:
  - what to click
  - what claim is proven
  - what is not claimed
  - why this beats generic AI submittal review
  - current blockers
- Make README link to it before the long technical detail.

### P1.8 - Python dependency reproducibility is weaker than frontend reproducibility

Location:
- `backend/requirements.txt`
- `pyproject.toml`

Impact:
- Frontend has `package-lock.json`.
- Python dependencies are range-pinned, not lock-pinned.
- CI and local may drift as packages release.

Fix:
- Add a generated lock or constraints file for judged/release builds.
- Keep flexible ranges in `pyproject.toml`, but use constraints in Docker/CI.

## P2 - Important But Not Blocking

### P2.1 - Pytest warnings are noisy

Evidence:
- Full suite passed, but emitted 54,410 warnings locally, mostly dependency
  deprecations under Python 3.14.

Impact:
- Not a product failure.
- But warning floods hide real warnings and make reports look less clean.

Fix:
- Pin/test against Python 3.11 for CI parity.
- Add warning filters for known third-party deprecations.
- Track a separate "warnings must not increase" gate.

### P2.2 - CLOSED: older "stored PDFs pending" framing normalized

Updated locations:
- `docs/CLAIMS_REGISTER.md:37`
- `docs/ARCHITECTURE.md:121-123`
- `docs/detailed_submission.html:99`
- `docs/detailed_submission.html:140`
- `docs/detailed_submission.html:169`
- `scripts/benchmark_report.py`
- `benchmarks/ps4_external_v1/reports/benchmark_card.json`
- `benchmarks/ps4_external_v1/reports/benchmark_report.md`

Status:
- Replaced the weaker phrasing with: "source files are not stored in this
  benchmark yet; source links/derivations are tracked."
- Kept source-file archiving as a trust-building backlog item, not a hidden
  current claim.

### P2.3 - CORS/auth posture is correct for demo, weak for production

Location:
- `backend/main.py:49-63`
- `backend/security.py`
- `render.yaml:78-94`

Impact:
- Wildcard CORS and auth-off-by-default make the public demo frictionless.
- For production, this would be unacceptable.

Fix:
- Keep demo defaults.
- Add a production environment profile with locked CORS, auth required, shared
  rate limiter, and audit logging.

### P2.4 - Live demo is green, but free-tier/quota/cold-start risk remains

Evidence:
- `python scripts/verify_live.py`: 10/10 passed in 140s.
- Deep LLM probe took about 15.5s; real-pair analyze took about 16s.

Impact:
- Good enough for demo when pre-warmed.
- Still fragile under judge traffic or quota exhaustion.

Fix:
- Warm the app before judging.
- Add a visible "last verified" badge sourced from live verifier output.
- Consider a paid/always-on instance for final judging hours.

### P2.5 - No Lighthouse/axe/Playwright report in CI

Impact:
- Frontend build/typecheck proves correctness, not UX quality.
- A mobile overlap, focus trap, or contrast issue could slip through.

Fix:
- Add Playwright smoke:
  - desktop and mobile screenshots
  - no console errors
  - analyze demo flow starts
  - `/evidence` loads with live/fallback state
- Add axe scan for `/judge` and `/evidence`.

### P2.6 - Frontend a11y is decent, but focus semantics are uneven

Location examples:
- `frontend/app/globals.css:368`, `503`, `1265` use `outline: none`.
- `frontend/components/DeviationRegister.tsx` uses sortable `th` elements with
  `tabIndex`.
- `frontend/components/AnalyzePanel.tsx` uses a custom dropzone with role button.

Impact:
- Much of the UI is labelled, but keyboard behavior should be tested directly.

Fix:
- Add focus-visible styles for every interactive class that removes outline.
- Convert sortable headers to real buttons inside `th`.
- Add keyboard tests for dropzone and table sorting.

### P2.7 - Manual source checks are honest but still friction

Location:
- `docs/REAL_SOURCE_LINK_CHECK.md`

Impact:
- 6 manual browser checks are acceptable, but a judge may not follow them.

Fix:
- For each manual check, add a short "what to verify" note and fallback source
  if the page blocks automation.

### P2.8 - README still has a few high-energy claims that need careful guarding

Location examples:
- `README.md:116`
- `README.md:722`
- `COMPETITIVE.md`

Impact:
- The claims register catches the worst banned phrases.
- But phrases like "one-line moat" and broad generalization claims can feel like
  pitch heat unless immediately paired with limitations.

Fix:
- Keep the ambition, but attach "proved on this benchmark/prototype" language
  near broad generalization claims.

## Positive Findings

- The live stack is genuinely up: backend, frontend, Judge Mode, LLM deep probe,
  stream analysis, schedule/supply/graph layers all passed.
- The test suite is broad for a hackathon: 605 backend tests plus frontend tests.
- Security posture is much better than typical demos: upload magic-byte checks,
  archive/executable rejection, size limits, no-secret tests, prompt-injection
  tests, rate limiting, auth option.
- The claims register is a serious trust asset. Most projects do not have an
  automated banned-claims gate.
- Benchmark card is honest: recall, precision, F1, false-alert rate, not-run
  pairs, reviewer status, and limitations are visible.
- Source provenance is no longer hand-wavy: link verifier and manual-check labels
  exist.
- The product has a real domain wedge: not just "find mismatch", but "map the
  mismatch to commissioning test and schedule risk".
- Frontend has a distinctive instrument-panel identity aligned with the project
  design context.

## What Separates Pramaan From Winners

If another finalist has weaker code but a cleaner story, they can still beat
Pramaan if they have:

1. A finished 3-minute video.
2. One real external reviewer/adjudicator.
3. One real practitioner/customer artifact with verifiable consent.
4. A simpler judge path.
5. A production-readiness roadmap that sounds immediately executable.

Pramaan beats most projects on technical depth. It loses only if the judges
cannot quickly trust the evidence or cannot quickly understand why this is more
than a polished demo.

## Recommended Fix Order

### First 24 hours

1. Finish video and clear `check_submission_ready.py`.
2. Verify practitioner quote consent records; remove anything not provable.
3. Get reviewer-2 CSV from one qualified reviewer.
4. DONE: Fix `DocumentDiff.tsx` to avoid `dangerouslySetInnerHTML`.
5. DONE: Add `docs/JUDGE_BRIEF.md`.

### Next 48 hours

1. Import reviewer-2 feedback and publish agreement stats.
2. PARTIAL: Add CI gates for `npm test`, `npm audit`, benchmark manifest/hash
   checks; source URL verifier and release-only submission guard remain separate.
3. Add Playwright smoke screenshots for `/judge`, `/evidence`, `/war-room`.
4. DONE: Normalize remaining "stored PDFs pending" wording.
5. DONE: Add production blueprint: Redis, Postgres, object storage, worker, observability.

### After submission / if continuing as a company

1. Run a real customer pilot on anonymized documents.
2. Store audit trail per analysis run.
3. Move cache/jobs/rate limits to shared infrastructure.
4. Add user auth/orgs/projects.
5. Add reviewer/adjudication workflow inside the app.
6. Build a real dataset flywheel: accepted/rejected findings become training and
   evaluation evidence.

## Final Brutal Score

| Scenario | Score |
|---|---:|
| Current repo including missing video | **74/100** |
| Current repo if video is ignored | **82/100** |
| After video + consent proof + reviewer-2 | **89/100** |
| After P1 production/CI/frontend polish | **92-94/100** |

Bottom line: the product is already technically formidable. The remaining gap is
trust, evidence, and packaging. The winners will not necessarily have more code;
they will have fewer reasons for a judge to hesitate.
