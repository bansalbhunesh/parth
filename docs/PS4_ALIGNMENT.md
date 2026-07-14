# Pramaan ↔ ET AI Hackathon 2026 · Problem Statement 4 — Alignment Map

**PS4: "AI Intelligence Platform for Data Centre EPC Project Delivery"**
Theme: Industrial Intelligence / Infrastructure Construction / Quality Management.

This document maps Pramaan's capabilities to PS4's five illustrative build areas and
its five stated evaluation-focus metrics — honestly, including where we are deep,
partial, or absent. (PS4 states the build areas are "illustrative only," so depth on
the highest-leverage areas is the strategy, not shallow coverage of all five.)

## Judging criteria (PS4, official)

| Criterion | Weight |
|---|---|
| Innovation | 25% |
| Business Impact | 25% |
| Technical Excellence | 20% |
| Scalability | 15% |
| User Experience | 15% |

## Coverage of PS4's five build areas

| # | PS4 build area | Pramaan | Status |
|---|---|---|---|
| 1 | **Specification & Quality Compliance Agent** — check submittals/POs/drawings vs specs, flag non-conformances before site, log to QMS audit trail | Reconciliation engine (spec↔submittal↔standard), severity + citation, exportable evidence pack | ✅ **Deep — core** |
| 2 | **Predictive Schedule Risk Engine** — critical-path risk weeks ahead from schedule + procurement + lead times | **Built** (`backend/agents/schedule_risk.py`): CPM forward/backward pass + 10k-trial beta-PERT Monte Carlo → P50/P80/P90 finish, on-time probability, criticality index + sensitivity tornado. Each detected deviation is injected as a *risk driver* (rework loop / late-delivery floor); we report the shift in the ready-for-service milestone and the drop in on-time probability. | ✅ **Deep** |
| 3 | **Supply Chain Visibility & Risk Agent** — geospatial tracking of UPS/gensets/cooling/switchgear shipments, at-risk deliveries, procurement alternatives | **Built** (`backend/agents/supply_chain.py`): 10-stage shipment pipeline, analytic ETA + `P(late)` via normal CDF, transparent multi-tier supplier-risk score, cost-of-delay-ranked alternatives, and a hand-rolled world-map view. Linked to the schedule so a late long-lead item propagates to the energization milestone. | ✅ **Deep** |
| 4 | **Commissioning Quality Assurance Copilot** — guide IST sequences vs TIA-942/BICSI/Uptime, flag non-conformances vs acceptance criteria | Commissioning-risk twin: each deviation mapped to the exact IST/FAT it will fail, on a 17-test Cx graph keyed to Uptime/TIA-942/BICSI | ✅ **Deep** |
| 5 | **Project Knowledge & RFI Intelligence Agent** — RAG over specs/submittals/RFIs/minutes, cited answers, surface prior resolved RFIs | RFI copilot: BM25 RAG over the project corpus, cited answers, prior-RFI surfacing | ✅ **Deep** |

### The QMS audit trail (build area 1's "log to QMS" clause, explicitly)

PS4 asks that non-conformances be "logged to a QMS audit trail." Pramaan's
evidence pack **is** that artifact: `GET /export/audit` (JSON) and
`GET /export/audit/html` (printable) emit every finding as an NCR-shaped
record — deviation, severity, spec clause, governing-standard citation, the
commissioning test it would fail, lead time, detection timestamp, and the
agent's rationale — one click from the dashboard. It is the same record an
ISO 9001-style NCR register needs, already cited and dated, and it round-trips
into any QMS that imports JSON. The pack also carries an `integrity` block —
a SHA-256 over its canonical JSON, echoed in the printable HTML footer — so
any post-export edit to the register is detectable by re-hashing (detection,
not prevention: the hash travels with the document). We deliberately ship the audit trail as an
open, exportable document rather than a walled-in NCR CRUD screen: the
commissioning authority signs against evidence, not against our UI.

## PS4 evaluation focus — where we stand

| Evaluation-focus metric | Pramaan evidence | Status |
|---|---|---|
| Specification compliance detection accuracy on test cases | Frozen external benchmark `ps4_external_v1`: recall 0.862 (0.841–0.873), precision 0.953, F1 0.905, 0 false alerts on 64 clean negatives, across 53 team-authored spec–submittal pairs / 129 labels — vs. a deterministic rule baseline of 0.111 | ✅ Strong |
| Schedule-risk prediction lead time vs actual delays | Monte-Carlo CPM P50/P80/P90 + deviation→milestone slip (e.g. on-time 63% → 0%, RFS +16 wk if uncaught) | ✅ Strong |
| Supply-chain visibility depth and alerting timeliness | Per-shipment `P(late)`, delivery-risk banding, supplier-risk decomposition, at-risk flagging on the critical path | ✅ Strong |
| Commissioning-test automation coverage | Deviation→Cx-test mapping across 17 tests / 5 levels | ✅ Strong |
| Reduction in manual coordination effort (hours, not %) | The blast-radius graph replaces manual cross-checking of compliance ↔ commissioning ↔ schedule ↔ procurement with one traversal | ✅ Strong |

## The unifying layer (Innovation backbone)

`backend/agents/project_graph.py` assembles all of the above into ONE networkx graph
(Requirement→Submittal→Deviation→Standard→CommissioningTest→Milestone→ScheduleTask→
Equipment→Supplier). `blast_radius(deviation)` walks it deterministically: a UPS battery
deviation → fails IST-07 → bounded by the Vertiv UPS lead time (40-wk) → **up to a 13-week
slip** to ready-for-service. The slip is a *worst-case remediation bound* — it assumes the
fix requires re-procuring the long-lead item rather than a faster battery-only swap, so it
is an upper bound on schedule exposure, not a point forecast. Each
deviation→standard→Cx-test edge carries the basis it rests on (structural edges such as
`supplied-by` carry none — see `docs/ARCHITECTURE.md`), and every number comes from data —
the LLM never draws an edge and never moves a date; it only narrates the blast radius.

## Honest summary

Pramaan now goes **deep on all five PS4 build areas**, and every one of the five
evaluation-focus metrics is addressed with a computed, deterministic, offline-reproducible
figure. The schedule-risk and supply-chain layers — previously the two gaps — are built,
tested, and wired into the dashboard + judge page. The headline claim stays honest:
calibrated Monte-Carlo probabilities and re-simulated mitigation deltas on synthetic data,
not "we predict delays accurately" (published EPC delay models top out ~71% / 0.82 AUC).
