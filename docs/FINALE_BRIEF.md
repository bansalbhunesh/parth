# Finale brief — official-record intelligence (2026-07-19)

Dated preparation notes for Phase 3, built from the **official live Unstop
competition record** (public API) and the dated field census. Facts below are
quoted from the record as inspected on 2026-07-19; the organisers reserve the
right to modify rules, guidelines, or timelines, so re-check the dashboard on
submission day.

Reproduce the record snapshot:

```bash
curl -s -H "User-Agent: Mozilla/5.0" -H "Accept: application/json" \
  "https://unstop.com/api/public/competition/1675680" > unstop_record.json
```

## 1. Confirmed timeline (live record, 2026-07-19)

| Phase | Recorded window (IST) | Notes |
|---|---|---|
| Phase 2: Build Sprint — Prototype Submission | 2026-06-22 12:11 → **2026-07-22 23:59:21** | Matches the deadline in `CHECKLISTS.md` exactly |
| Phase 3: Finale | 2026-07-22 07:34 → 2026-07-23 07:35 | Recorded window overlaps submission close — treat the dates as provisional, the **format** as authoritative |

Finale format, quoted from the round description: *"Top teams present their
solutions to a panel of industry experts in a **10–15 minute session, followed
by a live demo and Q&A with the jury.** Teams will be evaluated on innovation,
business impact, execution quality, and scalability."*

Practical consequence: the 2:50 pitch recording covers async judging, but the
finale slot is 10–15 minutes **live**. The 12-slide deck + Judge Mode
walkthrough + the `COMPETITIVE.md` §4 pushback answers are the 10–15-minute
material; rehearse the live Analyze once during warm-up, per the pre-flight
ritual in `PITCH.md`.

## 2. Official judging criteria (quoted from the live record)

The record lists **six** axes — note the first one, which the weight table we
planned against did not name explicitly:

1. **Relevance to Problem Statement** — "how effectively the solution addresses the chosen problem"
2. **Innovation & Creativity** — originality and problem-solving approach
3. **Technical Implementation** — "quality of architecture, code, and use of AI"
4. **Business Viability** — practicality and real-world applicability
5. **Presentation & Clarity** — "effectiveness of demo, pitch, and communication"
6. **Impact & Scalability** — potential for meaningful impact at scale

Mapping to existing Pramaan surfaces (nothing new to build — say it out loud):

| Axis | Where Pramaan answers it |
|---|---|
| Relevance | Deck opens on **Problem Statement 4**; every layer (deviation → Cx test → schedule → supplier) is data-centre-EPC-native, not a generic RAG shell |
| Innovation | The commissioning-risk join + `blast_radius()` + what-if remediation — the layer the commercial tools and the visible field do not expose |
| Technical | CI on a public repo, the test suite behind the README badges, the LLM failover chain with per-leg time budgets, live deploys with honest health/`llm-check` surfaces |
| Business | `BUSINESS.md` worked ledger (in-app ₹ scenario, cited lease benchmarks, disclosed negative-low case) |
| Presentation | Judge Mode 4-step journey, the annotated document-pair hero, the deck, the recorded pitch |
| Impact & Scalability | Multi-project aggregate on /evidence, 25+ standards across 11 countries, the data-flywheel section of `COMPETITIVE.md` (stated as architecture, not accumulated data) |

## 3. Rules compliance map (quoted rule → our evidence)

| Rule (live record) | Pramaan's position |
|---|---|
| "All submission links (GitHub, demo, docs) are public and accessible" | Repo public with logged-out CI badge check; frontend + API live; the Final Submission Checklist re-verifies logged-out on submission day |
| "All ideas, code, documents, and assets must be original and created during the hackathon" | Repository **created 2026-06-22 — the day Phase 2 opened**; the entire commit history sits inside the build-sprint window and is publicly auditable |
| "Licensed tools/datasets may be used only with valid authorization" | Corpus provenance documented in `data/samples/real/PROVENANCE.md`; external figures cited to their public datasheets |
| "All submissions must be made via the Unstop platform within the given timelines" | `UNSTOP_SUBMISSION.md` paste-ready; plan submits 21 July evening with a night of slack |
| Team rules (1–4 members, one team per person) | Confirm roster against the registration (Submission Checklist row 7) |

## 4. Jury pool (edition-1 finale — treat as likely pool, not a roster)

The 2.0 finale panel is not published. The **first-edition** finale jury
(April 2026, press coverage) was: Ankit Aggarwal (Unstop), Gaurav Baid
(Avataar AI), Murali Swaminathan (Freshworks), Deepit Purkayastha (Inshorts).
The same coverage stated the bar plainly: judges assess whether prototypes are
*"solid, usable, and ready"* to *"stand up outside the competition."*

If a similar panel returns, the profile mix rewards exactly what is already
built: a SaaS-engineering judge looks for operational honesty (health checks,
failover, rate limits), a consumer-product judge rewards the 90-second guided
story over a feature index, and an applied-AI founder probes what is real vs.
demo-ware — which is what the evidence dashboard and claims register exist for.

## 5. Field state at freeze (dated census, 2026-07-19)

From the reproducible public-repo census (`scripts/audit_et_hackathon_field.py`,
408 unique candidates on 2026-07-19; heuristic repository evidence, **not** a
judge ranking): the classified PS4 field is 17 repositories; none of the other
16 shows an evaluation artifact or a committed demo recording in its visible
tree, and the strongest rival's linked live demo returned 404 at inspection
time.
Detailed, named observations live in `docs/COMPETITIVE_SCAN_2026-07-15.md` and
the anonymized product view in `COMPETITIVE.md` §1.

## 6. Judging-day ops (already in `CHECKLISTS.md` — now with a date attached)

The finale's recorded window means these apply **from the morning of 22 July**:

- Keep-warm workflow is active through 2026-07-24 (covers the recorded window).
- Raise per-IP rate limits before the live session (venue NAT = shared budget).
- `make verify-live` the morning of — free-tier quota resets daily.
- Check the funded gateway-leg balance so the failover chain stays three-deep.
- One warm-up Analyze before the slot; then don't hammer the free tier.
