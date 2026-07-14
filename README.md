<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/PRA-MAAN-00d4ff?style=for-the-badge&labelColor=0a0d11&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzAwZDRmZiI+PHBhdGggZD0iTTEyIDJMMyA3djEwbDkgNSA5LTVWN2wtOS01eiIvPjwvc3ZnPg==">
    <img alt="Pramaan" src="https://img.shields.io/badge/PRA-MAAN-00d4ff?style=for-the-badge&labelColor=0a0d11">
  </picture>
</p>

<h3 align="center">Pramaan: Spec-to-Site Deviation Sentinel</h3>

<p align="center">
  <strong>EPC Deviation Intelligence for Hyperscale Data Centres</strong><br>
  <em>ET AI Hackathon 2026 &middot; Problem Statement 4</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/reproducible_tests-647-5b8cff?style=flat-square&labelColor=111820" alt="647 tests">
  <img src="https://img.shields.io/badge/benchmark_recall-0.862-ffb020?style=flat-square&labelColor=1a1508" alt="Benchmark recall 0.862">
  <img src="https://img.shields.io/badge/clean--negative_false_alerts-0-35c98b?style=flat-square&labelColor=0d1a14" alt="0 false alerts on 64 controls">
  <img src="https://img.shields.io/badge/license-MIT-5b8cff?style=flat-square&labelColor=111820" alt="MIT License">
  <img src="https://img.shields.io/badge/docker-compose-2496ED?style=flat-square&labelColor=111820&logo=docker&logoColor=white" alt="Docker">
</p>

<p align="center">
  <a href="https://parth-tan.vercel.app/judge"><img src="https://img.shields.io/badge/★_JUDGE_MODE-90--second_proof-ffb020?style=for-the-badge&labelColor=1a1508" alt="Judge Mode"></a>
  <a href="https://parth-tan.vercel.app"><img src="https://img.shields.io/badge/▶_LIVE_DEMO-parth--tan.vercel.app-00d4ff?style=for-the-badge&labelColor=0a0d11" alt="Live Demo"></a>
  <a href="https://parth-1-ma30.onrender.com/health"><img src="https://img.shields.io/badge/API-parth--1--ma30.onrender.com-35c98b?style=for-the-badge&labelColor=0d1a14" alt="API"></a>
</p>

<p align="center">
  <sub>
    Submission documents:
    <a href="docs/BUSINESS.md">Business case</a> ·
    <a href="docs/VALIDATION.md">Validation dossier</a> ·
    <a href="docs/JUDGE_BRIEF.md">Judge brief</a> ·
    <a href="docs/PRODUCTION_BLUEPRINT.md">Production blueprint</a> ·
    <a href="docs/ARCHITECTURE.md">Architecture one-pager</a> ·
    <a href="docs/DECK.md">Pitch deck outline</a>
  </sub>
</p>

---

> [!NOTE]
> ### Why this counts as PS4 (Spec-to-Site Deviation Sentinel)
> Problem Statement 4 demands a solution for catching discrepancies between design documents (owner project requirements) and vendor submittals to avoid late-stage commissioning delays. Pramaan solves this directly by cross-referencing unstructured spec PDFs, scanned datasheets, and images against design bases and 7 governing standards (Uptime, NFPA, ASHRAE, etc.). It extracts silent omissions and value deviations, maps them to the Level 1-5 commissioning tests they will fail, and calculates the remediation lead-time window—stopping delayed components before any equipment is ordered.

> [!IMPORTANT]
> ### Why these numbers are honest
> We do not claim 100% recall, zero-latency real-time API guarantees, or field-hardened production readiness. The aggregate "1,024 lead-time-weeks" and the 12-project portfolio are synthetic breadth benchmarks built by construction to verify generalisation. The actual engine is measured against fifteen team-authored real-datasheet evaluation pairs (Vertiv, STULZ, Cummins, ABB, Tate, Schneider, etc.) targeting 27 hard deviation claims: 4 are checked deterministically offline (yielding 0 false positives), and 23 require live-model evaluation (F1 1.000 limit). If the live API is rate-limited or suspended, the system gracefully degrades to a deterministic local rule floor.

---

## The Pitch: Catching Deviations Before the Bolt Turns

In hyperscale data centre builds, subtle deviations between design specifications, vendor datasheets, and standards hide in thousands of pages of unstructured documentation. Today, they are caught during commissioning—**33 weeks too late**, causing millions in schedule rework and delays.

**Pramaan** runs a single compliance reasoning graph wrapping a generative reasoning core in deterministic, inspectable QMS validation gates. It catches compliance mismatches the day the submittal lands:
- **Catches Silent Omissions:** Flagging when a required design clause (like safety clearances or seismic ratings) is completely absent from a vendor submittal.
- **Performs Derived Calculations:** Tracing implicit math (e.g., verifying that a proposed 4,000-gal fuel tank meets a 48-hour runtime requirement based on a 103 GPH consumption rate).
- **Graceful Degradation:** A deterministic rule-based floor catches the most critical deviations even when LLM APIs are rate-limited or offline.

---

## ⚡ Deployed Verification Status (`make verify-live`)

Pramaan runs an automated health-and-deployment validation script to verify that the deployed backend is live, API credentials are functional, and all frontend components load cleanly:

```
Pramaan live verification • API https://parth-1-ma30.onrender.com • APP https://parth-tan.vercel.app
  [PASS] backend /health ok • commit 90b404a / llm ready=True
  [PASS] PS4 layer /schedule live
  [PASS] PS4 layer /supply-chain live
  [PASS] PS4 layer /graph live
  [PASS] PS4 layer /register live
  [PASS] PS4 layer /remediation live
  [PASS] frontend landing page loads ok • title 'Pramaan'
  [PASS] frontend judge page loads ok • title 'Pramaan'
  [PASS] /evidence status 200 ok
  [PASS] /evidence table is populated
```

---

## Competitive Moat & Core Features

Other tools stop at the basic text-mismatch level. Pramaan integrates the compliance check with the actual site lifecycle:
1. **Commissioning Risk Twin:** Automatically maps each detected deviation to the exact commissioning test it will fail (e.g., IST-07 or FPT-04) and estimates the lead time available to correct the issue.
2. **What-if Remediation Slider:** An interactive slider that shows how schedule slippage and cost impact curve upward in real time based on the week a deviation is triaged.
3. **Downstream Webhooks & RFI Drafts:** Fires Slack notifications, Email layouts, and JSON payloads with pre-drafted RFI copy the instant a Critical or Major deviation is found.
4. **Client-Side Zero-Deploy Offline Mode:** Allows judges to toggle "Local Engine" on the pasting panel to run compliance rules instantly in the browser, avoiding API cold starts.

---

## Quick Start (Offline Checks)

You can run the entire verification suite, deterministic eval harnesses, and frontend type checks offline without any API keys:

```bash
# 1. Install dependencies & generate datasets
make setup
make corpus

# 2. Run the full test suite (647 tests, no API key needed)
make test

# 3. Run deterministic evals (no-key offline harnesses)
python eval/real_pairs_offline.py   # Runs the 15 real-datasheet check
python eval/text_eval.py            # Recovers seeded deviations from raw text
python eval/multi_project_eval.py   # Synthetic breadth portfolio check

# 4. Launch localhost
make run                            # Backend API (localhost:8000)
make run-frontend                   # Frontend Next.js app (localhost:3000)
```

---

## Reproducibility & Frozen Benchmark

To cut through AI hype, we evaluate Pramaan against a frozen, independent benchmark: **`ps4_external_v1` (v1.2)**. 

- **Recall:** 0.862
- **Precision:** 0.953
- **F1 Score:** 0.905
- **False Alarm Rate (FAR):** 0.000 on 64 clean-negative controls
- **Evaluation Details:** Ground-truth and proof lists are live at `/evidence`. Stratified confidence intervals and calibration metrics are tracked in [`calibration_report.md`](benchmarks/ps4_external_v1/reports/calibration_report.md).

---

## Git Commit History (`git log --oneline -n 25`)

```
90b404a feat: Implement competitor-inspired features including Indian standards, downstream webhooks, what-if simulator slider, and client-side offline mode
9872311 feat(audit): implement P0/P1 fixes from ecosystem audit (case deletion, omission recall, ITP frontend, telemetry)
4fda5e6 feat(qms): SHA-256 integrity block on the audit evidence pack + test count 644->647
82aba27 fix(judge-surface): close the 2026-07-14 external-audit findings
15e19fb fix(deploy): ship the frozen benchmark reports so /metrics headline works live
29b6c1f docs(readme): collapse deep-reference sections to cut judge surface (P1.3)
6c674b3 chore(submission): harden repo hygiene, fix doc drift, foreground benchmark on /metrics
28e576e docs: polish pass - test count 635->644, document the two new endpoints
85379e6 feat: PDF Inspection & Test Plan export for the case workflow
17a37ad feat: per-stage latency + provider telemetry on /analyze response
f99e7b1 fix: stale benchmark claim in PS4_ALIGNMENT.md + close its CI coverage gap
64810cf fix: bandit B310 in measure_deployment_latency.py
48f1250 fix: ruff E501 line-length in measure_deployment_latency.py
0c8c1f0 docs: measure real cold vs warm deployment latency by endpoint
e055b60 docs: full consistency pass — this session's work was invisible everywhere
f6392dc feat(eval): stratified confidence intervals for the frozen benchmark (P2-4)
61de5b2 test(metrics): enforce headline benchmark numbers can't silently drift (P2-3)
3e39f69 feat(e2e): add Playwright coverage for upload, paste, evidence links, keyboard nav, mobile (P2-2)
ecc18b7 fix(cases): eliminate B608 f-string SQL, caught by our own new CI gate
bc9634e feat(cases): persisted, tenant-isolated submittal->RFI workflow (P1-3)
f520ebe feat(evidence): build and live-verify two prompt-naive eval pairs (P1-1)
f9976f5 feat(evidence): store two primary-source documents, not just cite them (P1-1)
269e4fa ci: gate on pip-audit and bandit, not just pytest/ruff (P2-1)
d15e857 fix(deps): eliminate Python 3.14 pytest-asyncio warning debt (P1-6)
ca4d030 fix(a11y,perf): close /judge Lighthouse gaps (P1-4) — Perf 53->92, A11y 92->100
a4f4d08 fix(business): replace deterministic ROI claims with an expected-value model
7e7580b audit: add reproducible competitor-discovery script + judge-page Lighthouse baseline
d6f4741 fix(security): bump Pillow floor to 12.2 (closes 7 open advisories)
aad58ef fix: close audit gaps from competitor scan
8aa50aa docs: add dominance gap audit
9ac3c3d docs: harden provenance and reviewer handoff
6fc0411 experiment: bind war room to live graph actions
603dd7e experiment: add commissioning war room
4d2fc67 audit: harden submission polish and verification
aa76d8e docs(competitive): make field-data honesty an explicit strength within section 6
fc9247a fix(truth): retire stale failover order + last hardcoded lead-time claim
3105a8e feat(benchmark): browser-based reviewer form for multi-person label review
6dea18e fix(claims-ui): retire last 'Total savings' claim in register footer
c7a1e10 fix(claims-ui): live-computed lead-time window replaces hardcoded 'Total savings'
c27a514 fix(design): eliminate AI-slop tells + a11y contrast/focus/touch fixes
6dfbbde docs(design): project design context for design-skill work (.impeccable.md)
7b2ae53 fix(mobile): contain residual horizontal spill on small phones
aa88a47 fix(mobile+deps): supply-chain table scroll container + multipart CVE floor
aebf48d feat(frontend): branded Open Graph / Twitter cards + GitHub repo presentation
a3841eb docs(submission): paste-ready Unstop text + practitioner quote on Judge Mode
daa8adf config(failover): drop claude from the recommended provider order
46abe6d feat(llm): per-provider hourly spend guard + aicredits gateway leg (benchmark-featured model)
d76a323 docs(validation): publish the five practitioner problem-validation quotes
23a8f6a fix(llm): fail over on empty/unparseable JSON responses, not just call errors
```

---

## Technical Architecture & Guardrails

Pramaan uses a single LLM reasoning core wrapped in deterministic pipelines:

```
[Design Spec / Submittal PDF] ──> Ingestion (pdfplumber) ──> Raw text
                                                                │
[Deterministic Local KB]   <─── Retrieval / Standards ◄─── Reconcile (LLM Core)
                                                                │
                                                            Outputs ──> Cx Test Predictor
                                                                    ──> Downstream Webhooks
                                                                    ──> Remediation Curves
```

- **Guardrail:** Never hardcode deviation answers. The reasoning must occur dynamically over raw documents.
- **Guardrail:** Never reproduce copyrighted standard text. We maintain paraphrased summaries only.
- **Failover Chain:** Core LLM requests dynamically fail over on quota/rate-limits: **native Gemini 2.5 → Qwen-gateway → Groq Llama-3.3 → deterministic fallback**.

---

<p align="center">
  <strong>Pramaan Compliance Engine</strong><br>
  <em>EPC Deviation Intelligence &middot; ET AI Hackathon 2026 &middot; Problem Statement 4</em><br>
  <sub>647 tests passed &middot; CI Green &middot; Verified Live</sub>
</p>
