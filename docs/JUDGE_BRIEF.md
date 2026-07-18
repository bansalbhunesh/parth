# Pramaan Judge Brief

Use this page when you have two minutes and want the fastest honest read of the
project.

## 90-second path

1. Open Judge Mode: <https://parth-tan.vercel.app/judge>
2. Click `Load deviation demo *`.
3. Click `Analyze`.
4. Check that each finding includes the mismatched value, cited basis, predicted
   commissioning test, severity, and lead-time impact.
5. Read the **Systemic risk** panel above the findings — this is the 90-second
   money shot. On the demo pair it shows the project compound-risk band
   (**Critical · 100%**), the converged failure cluster, and a **Fix this
   first** action. The story to tell: two findings are not two tickets — the
   2N→N+1 topology gap and the 10→8-minute autonomy shortfall converge on the
   *same UPS commissioning gate at Week 36*, and fixing either one alone leaves
   that gate failing; the panel ranks the converged cluster, not line items.
   (When findings span multiple systems, the panel also names the schedule
   cliff — the soonest week where two or more of them fail together.)
6. Note each finding's **Evidence: <band>** chip — a deterministic strength read
   (numeric exactness, rule/graph grounding, citation), not a probability of
   correctness.
7. Open Evidence: <https://parth-tan.vercel.app/evidence>

## What to verify locally

```bash
git clone https://github.com/bansalbhunesh/parth.git
cd parth
make verify
```

For the stricter pre-judge gate, run:

```bash
make demo-gate
```

`make demo-gate` runs Python lint/tests, benchmark manifest/hash checks,
frontend component tests, TypeScript, dependency audit, frontend build, and live
deployment health. The pitch video is handled separately because its public link
is intentionally the remaining submission blocker.

## What is strongest

- The core product does not stop at "values differ"; it maps each deviation to
  the commissioning test it will fail and the lead time at risk.
- Beyond per-finding detection, a deterministic decision loop computes the
  systemic compound risk, the schedule cliff, and a risk-ranked remediation plan
  — offline and reproducible, each unit-tested at 100% line and branch. Fixing one
  of a converged set is correctly surfaced as low-leverage.
- The benchmark reports both positive labels and clean-negative controls, with
  reviewer status and fixture provenance labelled near the numbers.
- The demo degrades honestly: provider failover is described as availability,
  OCR availability is exposed by `/ocr-check`, and the deterministic fallback is
  not sold as an accuracy boost.
- Claims are governed by `docs/CLAIMS_REGISTER.md` and tested by
  `tests/test_claims_register.py`.

## Honest limits

- Pitch video link is still the submission blocker.
- Benchmark labels are single-author frozen; reviewer-2 human adjudication is
  still pending.
- Fixtures are team-authored. Some are derived from public primary-source values
  and some have verified public URLs, but source files are not stored in this
  benchmark yet.
- The public app is a hackathon prototype with demo hardening. Multi-tenant auth,
  shared rate limiting, durable job queues, stored source artifacts, and full
  operations monitoring are production-path work, not current claims.

## One-line defense

Pramaan turns a submittal mismatch into a commissioning-risk finding: exact value,
evidence basis, failed Cx test, and weeks of schedule exposure, with the evidence
trail and limitations visible instead of buried.
