# Hackathon Winning Engineering Playbook

This is the repository's durable memory for future builds. It records the
repeatable engineering and presentation patterns applied to Pramaan; it is a
working standard, not a claim that Devpost uses a hidden numeric rubric.

## The winning shape

A strong hackathon project compresses one consequential story into a reliable
judge path:

`input → visible intelligence → concrete consequence → human action → verified outcome`

The product should make that loop obvious within 90 seconds. Architecture,
benchmarks, and breadth support the loop; they do not replace it.

| Layer | Standard for future projects | Failure to avoid |
|---|---|---|
| Problem | One costly user decision, stated in domain language | A platform with no urgent decision |
| Frontend | A guided primary route with realistic inputs and visible state | A dashboard tour requiring narration |
| Backend | One canonical execution path shared by demo, API, and tests | A special demo endpoint with different truth |
| AI | Explicit model/rule/cache/unavailable provenance | Calling every output “live AI” |
| Workflow | Persist the actual output, assign ownership, and close the loop | Showing analysis and a separate hard-coded workflow |
| Evidence | Frozen benchmark, baselines, error classes, and reproducible gates | One accuracy percentage without a denominator |
| Reliability | Timeouts, cancellation, cache identity, fallback, and cleanup | Spending quota on repeated judge clicks |
| Presentation | Stakes in 12 seconds, product proof by 55 seconds, close under 3 minutes | Feature inventory before the live proof |
| README | Judge links and honesty boundary above the fold | Installation instructions before the value |
| Video | Cursor-led evidence, legible UI, rehearsed recovery path | Unlabelled cached/fallback footage |

## Frontend contract

1. Maintain a single visual thesis. Reuse typography, spacing, color, and control
   behavior; polish hierarchy before adding decoration.
2. Put the primary action and its required inputs in one viewport on common
   laptop and mobile widths.
3. Preserve user input on failures and cancellation.
4. Expose progress, errors, provenance, and completion through accessible text,
   not color alone.
5. Give every custom interaction keyboard behavior, a visible focus state, a
   usable accessible name, and at least a 44-pixel touch target where practical.
6. Make demo data controlled and realistic, then label it as controlled. Never
   imply that team-authored fixtures are customer data.
7. Display the consequence beside the finding: affected gate, decision window,
   owner, next action, and verification state.
8. Store only the minimum resumable browser state. Provide a visible restart and
   cleanup path for judge-created records.

## Backend contract

1. Route UI, synchronous API, and streaming API through the same domain service.
2. Hash normalized inputs together with system, prompt version, and model
   configuration. Cache only non-secret results and expose whether a result was
   reused.
3. Use single-flight behavior so simultaneous identical requests do not duplicate
   expensive model work.
4. Return request IDs and input hashes for traceability without leaking secrets.
5. Put timeouts and bounded retries around external providers. Cancellation must
   stop client reads and should stop server work where the runtime permits it.
6. Keep deterministic validation and workflow state transitions inspectable.
   Provider failover improves availability, not benchmark equivalence.
7. Make state-changing judge flows explicit: finding persisted, owner accepted,
   RFI issued, response verified, audit read back, demo record deletable.
8. Keep health responses product-correct and non-secret. Separate product name,
   sample project, commit, provider readiness, OCR, authentication, and rate limits.

## AI and evidence contract

- Label the original reasoning mode and the delivery mode separately. A cached
  model result remains model-originated evidence, but the current request is a
  **verified cache replay**, not a fresh inference.
- Treat a deterministic fallback as a low-recall availability floor. A zero from
  that floor is inconclusive unless the benchmark supports a stronger claim.
- Freeze datasets and labels before headline evaluation. Publish pair count,
  label count, clean-negative count, run count, baseline, and known weak classes.
- Keep benchmark claims attached to the exact model/configuration measured.
- Publish limitations in the product and pitch. Independent review, field ROI,
  primary-source retention, security review, and load evidence remain external
  milestones until actually completed.

## Demo and video flow

Target 2:50, with no scene depending on a cold start:

1. **0:00–0:12 — stakes:** identify the expensive late decision.
2. **0:12–0:25 — promise:** state the input-to-outcome transformation.
3. **0:25–0:55 — proof:** run one controlled document pair and point to cited gaps.
4. **0:55–1:25 — consequence:** persist that finding, assign an owner, issue the
   action, re-check the revision, and show audit-backed closure.
5. **1:25–1:50 — evidence:** show the frozen benchmark and baseline.
6. **1:50–2:15 — engineering:** show the minimum architecture that explains trust.
7. **2:15–2:38 — boundaries:** name the two largest known weaknesses.
8. **2:38–2:50 — close:** repeat the user outcome, not the feature list.

Warm the deployment, but narrate a cache replay as a replay. Record the critical
flow twice. If the provider falls back, either explain the fallback or restart;
never splice footage from another build.

## Definition of ready

A project is judge-ready only when all applicable checks are green:

- unit and integration tests for the primary domain path;
- one real browser test spanning UI → API → persisted state → response;
- mobile reflow, keyboard navigation, automated accessibility, and console checks;
- type checking, production build, dependency audit, and bundle budget;
- cache miss and cache hit behavior tested;
- cancellation, error, resume, and cleanup behavior tested;
- README, pitch, and video runbook describe the same product truth;
- video URL, team/roster, submission form, and external reviewer evidence completed
  by humans rather than represented by placeholders.

## Reuse rule

For the next project, copy the principles—not Pramaan's screens or domain nouns.
Start by writing the five-stage judge story, the evidence contract, and the two
known limitations. Build the thinnest real vertical slice that proves all five
stages, then add breadth only when it strengthens that proof.
