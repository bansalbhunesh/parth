# Pramaan Judge Brief

Use this page when you have two minutes and want the fastest honest read of the
project.

## 90-second path

1. Open Judge Mode: <https://parth-tan.vercel.app/judge>
2. Click `Load deviation demo *`.
3. Click `Analyze`.
4. Check that each finding includes the mismatched value, cited basis, predicted
   commissioning test, severity, and lead-time impact.
5. Open Evidence: <https://parth-tan.vercel.app/evidence>

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
