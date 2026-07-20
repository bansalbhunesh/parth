<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/badges/wordmark-dark.svg">
    <img alt="Pramaan" src="docs/badges/wordmark-light.svg">
  </picture>
</p>

<h1 align="center">Pramaan</h1>
<h3 align="center">EPC Deviation Intelligence for Hyperscale Data Centre Builds</h3>

<p align="center">
  <strong>Pramaan detects vendor-submittal deviations when documents arrive, cites the requirement, and maps each supported finding to the commissioning test at risk.</strong><br>
  <em>ET AI Hackathon 2026 &middot; Problem Statement 4 (Data Centre EPC)</em>
</p>

<p align="center">
  <a href="https://github.com/bansalbhunesh/parth/actions/workflows/ci.yml"><img src="https://github.com/bansalbhunesh/parth/actions/workflows/ci.yml/badge.svg" alt="Pramaan CI status"></a>
  <img src="docs/badges/benchmark-recall.svg" alt="Benchmark recall 0.862">
  <img src="docs/badges/false-alerts.svg" alt="0 false alerts on 64 controls">
  <img src="docs/badges/tests-1141.svg" alt="1,141 automated checks">
  <img src="docs/badges/license-mit.svg" alt="MIT License">
</p>

## 🎬 Product Pitch

https://github.com/bansalbhunesh/parth/releases/download/v1.0.0-video/pitch.mp4

<p align="center">
  <sub>▶ <a href="https://youtu.be/A6l1nf87rIQ"><strong>Watch on YouTube ↗</strong></a> (3:16 Unlisted) &middot; Live product, frozen benchmark, and published limits</sub>
</p>

---

### ⚡ Quick Start for Judges (90 seconds)

1. 🚀 **[Open Judge Mode](https://parth-tan.vercel.app/judge)** → Click **Load deviation demo ★** → **Analyze** (watch real-time streaming reasoning and systemic risk panel).
2. 📊 **[Evidence Dashboard](https://parth-tan.vercel.app/evidence)** → Review frozen benchmark recall (0.862), zero false-alert rate (0/64), and published limitations.
3. 🔍 **[Judge Brief](docs/JUDGE_BRIEF.md)** → Guided technical walkthrough and verification steps.

---

## 1. The Problem: Buried Deviations Become Expensive at Commissioning

In hyperscale data centre builds, subtle deviations between design specifications, vendor datasheets, and governing standards hide within thousands of pages of unstructured documentation. In the demonstration project, vendor submittals arrive at **Week 11**, but manual cross-checking misses discrepancies until commissioning at **Weeks 30–44**—costing millions in schedule rework and delays.

| What went wrong | Spec requirement | Vendor proposal | Consequence & Impact | Fix Lead |
|---|---|---|---|---|
| **UPS battery runtime** | 10 min (End of Life) | 8 min (Beginning of Life) | Tier IV fault tolerance broken; **IST-07 at risk** | 27 weeks |
| **Generator fuel autonomy** | 24 h | 12 h | Cannot sustain design-duration outage; **IST-02 at risk** | 30 weeks |
| **Cooling redundancy** | N+2 | N+1 | No concurrent maintenance tolerance; **FPT-04 at risk** | 28 weeks |
| **Switchgear fault rating** | 50 kA | 40 kA | Below prospective fault level; **IST-01 at risk** | 19 weeks |

* **Today:** Discrepancies surface during commissioning at **Weeks 30–44**, causing late-stage rework.
* **With Pramaan:** Deviation review moves to submittal day (**Week 11**), catching gaps before equipment is ordered.
* *Note: ₹54 crore represents illustrative modelled exposure for the demonstration case based on published assumptions—not field-validated savings.*

---

## 2. The Solution: Detect → Consequence → Act → Verify

Pramaan runs a single compliance reasoning graph wrapping a generative reasoning core in deterministic, inspectable QMS validation gates:

<p align="center">
  <img src="docs/demo.gif" alt="Pramaan judge mode: load a vendor document, click Analyze, watch AI stream reasoning and return cited deviations" width="900">
  <br>
  <sub><strong>The 4-Step Resolution Loop:</strong> 1. <strong>Detect</strong> (cited mismatch) → 2. <strong>Consequence</strong> (IST test mapped) → 3. <strong>Act</strong> (RFI issued to owner) → 4. <strong>Verify</strong> (Revision C re-analyzed & closed).</sub>
</p>

### Platform Showcase

| Step 1 & 2: Detect & Consequence | Step 3 & 4: Act & Verify |
|---|---|
| <img src="docs/screenshots/judge_systemic_risk.png" alt="Judge Mode after Analyze: live LLM reasoning, cited finding, and systemic-risk panel" width="480"> | <img src="docs/screenshots/war_room_brief.png" alt="Intervention brief: priority finding, decision ledger, and one-click resolution workflow" width="480"> |
| [Judge Mode](https://parth-tan.vercel.app/judge) — live model reasoning, systemic compound risk, and a **Fix this first** action, each with its provenance chip. | [Intervention brief](https://parth-tan.vercel.app/war-room) — decision ledger, priority finding, blast radius, and one-click RFI resolution workflow. |

---

## 3. Benchmark Proof & Limitations

> [!IMPORTANT]
> ### Benchmark Results (`ps4_external_v1` v1.2)
> Evaluated on a frozen, zero-data-leak benchmark containing **53 spec–submittal pairs and 129 labels across 17 systems**:
>
> | Metric | Pramaan (3-run featured) | Rule Baseline |
> |---|---|---|
> | **Semantic Recall** | **0.862** | 0.111 |
> | **Precision** | **0.953** | 1.000 |
> | **F1 Score** | **0.905** | 0.200 |
> | **False Alert Rate** | **0 / 64** (clean-negative controls) | 0 / 64 |

> [!NOTE]
> ### Transparent Limitations & Governance
> * **Omission Recall:** Supports silent-omission detection, currently the weakest measured class and an explicit improvement priority.
> * **Verified Cache Replay:** Identical inputs may return a verified cache replay, clearly labelled with input identity and provenance.
> * **Evaluation Scope:** Benchmark fixtures are reviewer-adjudicated; evaluation was conducted on a frozen set after configuration freeze.

---

## 4. Moats & Differentiators

* **Beyond Keyword Matching:** Connects document evidence to commissioning consequences, schedule impact, and verified closure.
* **Commissioning Risk Twin:** Maps each supported deviation to the Level 1–5 commissioning test (e.g., IST-07, FPT-04) most directly at risk.
* **What-if Remediation Simulator:** Interactive catch-week slider updates project cost and schedule curves in real-time.
* **Client-Side Zero-Deploy Engine:** Instant compliance checks executed locally in-browser (~1ms).

---

## 5. Technical Architecture

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/pipeline-diagram-dark.svg">
    <img src="docs/pipeline-diagram.svg" alt="Pramaan architecture diagram: Ingest, Validate gate, generative reasoning core, Cx predictor, and RFI workflow" width="100%">
  </picture>
</p>

* **Deterministic Validation Gates:** Generative reasoning is bounded by schema validation, audit logging, and rule floors.
* **Security Controls:** Environment-managed secrets, parameterised database access, dependency scanning, secret scanning, and non-root container execution.

---

## 6. Capability Matrix

| Capability | Status | Notes |
|---|---|---|
| **Spec-to-Submittal Deviation Detection** | ✅ **Live** | Full pipeline active on 17 data centre sub-systems |
| **Commissioning Test Risk Mapping** | ✅ **Live** | Maps findings to Level 1–5 commissioning tests |
| **Interactive Judge Mode & Resolution Loop** | ✅ **Live** | Case credentials in browser, RFI drafting & closure |
| **Client-Side Local Engine** | ✅ **Live** | Instant browser-only local compliance check |
| **JSON Webhook Payload Dispatch** | ✅ **Live / Verified** | Webhook delivery on deviation detection |
| **Slack Alert Delivery** | 🟡 **Prototype** | Webhook payload structure verified |
| **Email Inbox Submittal Ingestion** | 🔵 **Roadmap** | Direct email submittal ingest |

---

## 7. Quick Start

### 30-Second Verification (No API key needed)

```bash
git clone https://github.com/bansalbhunesh/parth.git
cd parth
make verify
```

### Local Development

```bash
make setup
make run
make run-frontend
```

> **Live Deployment Verification:** [View live verification evidence](docs/evidence/live/)

---

## 8. Automated Test Suite

Pramaan is governed by **1,141 automated checks**:
* **901** backend tests (`python -m pytest`)
* **80** frontend component tests (`vitest`)
* **160** browser/device journey tests (`playwright`)

---

## 9. Team

**Team Pramaan**
* **Bhunesh Bansal** — Product, AI Architecture & Full-Stack Engineering
* Built for **ET AI Hackathon 2026** · Problem Statement 4 (Data Centre EPC)

---

<details>
<summary><strong>📁 Click to expand Submission Package & Technical Evidence</strong></summary>

| Document / Asset | File Path |
|---|---|
| Pitch deck — 12-page PDF | [`docs/Pramaan_Deck.pdf`](docs/Pramaan_Deck.pdf) |
| Detailed submission — PDF | [`docs/Pramaan_Detailed_Submission.pdf`](docs/Pramaan_Detailed_Submission.pdf) |
| Deck source — HTML | [`presentation.html`](presentation.html) |
| Detailed submission source — HTML | [`docs/detailed_submission.html`](docs/detailed_submission.html) |
| Architecture one-pager | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Business case & impact model | [`docs/BUSINESS.md`](docs/BUSINESS.md) |
| Judge brief — guided walkthrough | [`docs/JUDGE_BRIEF.md`](docs/JUDGE_BRIEF.md) |
| Pitch script | [`PITCH.md`](PITCH.md) |
| Validation dossier | [`docs/VALIDATION.md`](docs/VALIDATION.md) |
| Claims register — wording governance | [`docs/CLAIMS_REGISTER.md`](docs/CLAIMS_REGISTER.md) |
| Frozen benchmark — data & reports | [`benchmarks/ps4_external_v1/`](benchmarks/ps4_external_v1/) |
| Executive summary | [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md) |
| Production blueprint | [`docs/PRODUCTION_BLUEPRINT.md`](docs/PRODUCTION_BLUEPRINT.md) |

</details>

---

## License

Distributed under the [MIT License](LICENSE).
