# Competitor Response Actions - 2026-07-10

This note converts public competitor-repo observations into Pramaan fixes. It is
not a benchmark of their products and it does not claim private knowledge.

## Public repos checked

- Prahari: <https://github.com/sanskar9999/prahari>
- PlantIQ: <https://github.com/Agent-A345/PlantIQ>
- Exyons / Kisan: <https://github.com/Exyons/ET-GenAI-Hackathon>
- DKDVE / OCE: <https://github.com/DKDVE/et-hackathon>

## What they do that judges notice

| Competitor lesson | What it means for Pramaan |
|---|---|
| Prahari has an instant public demo path and an emotional public-safety frame | Keep Judge Mode as the first path and explain the commissioning-risk story in one page |
| PlantIQ foregrounds deployment/run instructions and domain breadth | Keep the domain depth, but make the run path and target service topology easier to inspect |
| Exyons shows Docker/deployment thinking across frontend/backend concerns | Document the worker, storage, queue, and deployment blueprint instead of leaving it implicit |
| DKDVE/OCE signals engineering discipline with CI, compose, PRD/TDD style docs | Strengthen CI and add a single pre-judge gate that catches regressions before a reviewer does |

## Fixes made from this scan

- Added `docs/JUDGE_BRIEF.md` as the shortest judge path.
- Added `docs/PRODUCTION_BLUEPRINT.md` for the target backend/frontend/service
  topology without overstating current maturity.
- Added `make demo-gate` for local pre-judge verification.
- Added GitHub Actions gates for benchmark manifest/hash checks.
- Added GitHub Actions gates for frontend component tests and `npm audit`.
- Removed `dangerouslySetInnerHTML` from the document diff highlighter.
- Added a regression test proving hostile document text is escaped while still
  highlighted.

## Remaining gaps after these fixes

- Video link is still the public-submission blocker.
- Reviewer-2 human adjudication is still pending.
- Stored primary-source artifacts are still a backlog item; current provenance is
  link/derivation based.
- No customer or paid pilot validation is claimed.
- Production-path infrastructure is documented but not fully provisioned in the
  public demo.
- Full browser accessibility/performance automation is not yet in CI.
