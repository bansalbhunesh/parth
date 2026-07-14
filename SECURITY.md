# Security policy

## Supported versions

Security fixes are applied to the `main` branch. Production deployments should use a reviewed commit from `main`, not an arbitrary development branch.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub private vulnerability reporting for this repository and include the affected route or component, reproduction steps, impact, and any suggested mitigation. Do not include real customer documents, credentials, access tokens, signed URLs, or webhook secrets.

We aim to acknowledge a report within three business days, confirm severity within seven business days, and provide a remediation target after validation. Timelines may change with exploitability and deployment risk.

## Security boundaries

- Public judge analysis is deterministic, size-bounded, rate-limited, and non-persistent.
- Production identity is designed for verified Supabase bearer JWTs; editable user metadata is never an authorization source.
- Production tables and private storage are scoped by organization membership and RLS.
- Redis is non-authoritative and is limited to cache, rate-limit, provider-budget, and idempotency coordination.
- Local case-secret mode and the in-process worker are demo-only facilities.
- Secrets belong in deployment environment variables or the platform secret store and must never be committed.

Automated scans help reduce risk but are not a substitute for the external penetration test required by the production exit gate.
