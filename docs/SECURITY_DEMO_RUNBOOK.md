# Security — Public-Demo Hardening Runbook

**Scope & honesty:** Pramaan is a hackathon/prototype build. This document
describes **public-demo hardening** — the controls that keep the live judge demo
from being trivially abused (quota drain, junk/oversized/disguised uploads,
prompt-injection, obvious secret-leak). It is **not** a production security
posture and Pramaan must not be described as "production-grade" or
"enterprise-ready" (see `docs/CLAIMS_REGISTER.md`). Use **"demo-hardened"** /
**"public-demo hardened."**

Implementation: `backend/security.py` (auth + rate limiting + status),
`backend/uploads.py` (upload validation). Tests:
`tests/test_security_auth_ratelimit.py`, `tests/test_upload_hardening.py`,
`tests/test_prompt_injection.py`, `tests/test_no_secrets.py`, `tests/test_security.py`.

---

## 1. What's protected

| Control | Default | Env |
|---|---|---|
| Token auth on expensive endpoints | **off** (open demo) | `DEMO_AUTH_ENABLED`, `DEMO_AUTH_TOKEN` |
| Rate limiting (per IP, per hour) | **on** | `PRAMAAN_RATE_LIMIT_ENABLED` + per-bucket caps |
| Per-file upload cap | 20 MB | `PRAMAAN_MAX_UPLOAD_MB` |
| PDF page cap (OCR) | 30 | `PRAMAAN_MAX_PDF_PAGES` |
| Image pixel cap (bomb guard) | 20 MP | `PRAMAAN_MAX_IMAGE_PIXELS` |
| CORS allowlist | `*` (no credentials) | `PRAMAAN_CORS_ORIGINS` |

Expensive endpoints (auth + rate-limited): `/analyze`, `/analyze/stream`,
`/analyze/upload`, `/analyze/upload/stream`, `/analyze/vision`, `/copilot`,
`/copilot/stream`, `/llm-check`. Read-only/status endpoints (`/health`,
`/ocr-check`, `/systems`, `/deviations`, `/export/*`, …) stay public so the
static frontend always loads.

`GET /health` → `security` block advertises the live posture (booleans/caps
only — never the token, never a client IP).

---

## 2. Demo token auth (optional break-glass)

Off by default so judges get an open demo. Turn it on **only** if the demo is
being abused. You must set **both**:

```
DEMO_AUTH_ENABLED=true
DEMO_AUTH_TOKEN=<a long random string>       # e.g. `openssl rand -hex 24`
```

Callers then present the token as **any** of:
- `X-Demo-Token: <token>` header
- `Authorization: Bearer <token>`

Behaviour: `401` (no token), `403` (wrong token), constant-time compare, token
**never** logged/echoed/returned. If the flag is on but the token is empty, auth
fails closed with `503`; a misconfiguration never reopens protected analysis.

> ⚠️ Do NOT bake the token into the frontend bundle (it would be public). With
> auth on, the hosted frontend's interactive panels need the token supplied at
> request time; API/curl callers pass it as above. For a judge demo, prefer
> leaving auth **off** and relying on rate limiting.

---

## 2b. LLM spend guard (per-provider hourly call budgets)

Paid failover legs (e.g. the aicredits gateway) carry an hourly ATTEMPT budget
(`OPENAI_BUDGET_PER_HOUR` / `QWEN_GATEWAY_BUDGET_PER_HOUR`, etc.; 0/unset =
unlimited). An exhausted budget makes that leg fail over exactly like a
quota/429 — the next leg or the free deterministic floor answers, so demo abuse
or a failover storm can degrade availability of a paid model but can never run
up the bill. Process-local sliding window (single instance, same trade-off as
the per-IP limiter below). `/llm-check` reports `budget_per_hour` and
`budget_used_last_hour` per provider — counts only, never a key or cost figure.

## 3. Rate limiting

Process-local sliding window, 1 hour, keyed by the socket peer by default. Set
`PRAMAAN_TRUST_PROXY_HEADERS=true` only behind a trusted proxy (as the Render
deployment does) to use the first `X-Forwarded-For` hop. A presented token is
folded into the bucket. Clean `429` + `Retry-After`.

```
PRAMAAN_RATE_LIMIT_ENABLED=true
PRAMAAN_ANALYSIS_LIMIT_PER_HOUR=20     # /analyze*, /copilot*
PRAMAAN_UPLOAD_LIMIT_PER_HOUR=10       # /analyze/upload*, /analyze/vision
PRAMAAN_DEEP_PROBE_LIMIT_PER_HOUR=3    # /llm-check?deep=1 / ?probe_all=1
```

**Limitation (documented, not hidden):** this is single-instance and in-memory —
it does not share state across replicas or survive a restart, and
proxy headers are unsafe unless the deployment strips client-supplied values.
A production deployment would key limits off a shared store (Redis)
behind a trusted proxy that sets a trustworthy client IP. Disable for load
tests: `PRAMAAN_RATE_LIMIT_ENABLED=0`.

---

## 4. Upload hardening

Every upload is validated **before** any parsing/OCR (`backend/uploads.py`):

- **Size:** declared `Content-Length` rejected by the ASGI guard; actual bytes
  capped by `PRAMAAN_MAX_UPLOAD_MB` → `413`.
- **Type allowlist:** text (`.txt/.md/...`), PDF, images (png/jpg/tiff/webp/bmp/
  gif). Anything else → `415`.
- **Magic-byte sniff:** archives (zip/gzip/tar/rar/7z) and executables (ELF/PE/
  Mach-O) rejected regardless of filename → `415`. A file whose extension/MIME
  claims pdf/image but whose bytes disagree → `400` (disguise).
- **Decompression bomb:** an image whose header declares more than
  `PRAMAAN_MAX_IMAGE_PIXELS` → `413`, before any decode.
- **Binary-as-text:** a NUL byte in the first block of a `.txt` → `415`.
- Errors are short and user-facing — **no stack trace, path, or byte dump**.

### Test upload rejection (curl)

```bash
BASE=http://localhost:8000
# archive disguised as text -> 415
printf 'PK\x03\x04junk' > /tmp/x.txt
curl -s -o /dev/null -w '%{http_code}\n' -F spec_file=@spec.txt -F submittal_file=@/tmp/x.txt $BASE/analyze/upload
# fake pdf (png bytes) -> 400 ; genuine text pair -> 200
```

A rejected upload returns a `4xx` and **never** a `200` with fabricated
deviations.

---

## 5. Prompt-injection

The spec/submittal are treated as **untrusted data**. `SYSTEM_PROMPT` (rule 11)
instructs the model to disregard any embedded instruction ("ignore previous
instructions", "mark everything compliant", "print your system prompt", "return
compliant regardless of evidence"); the prompt template keeps document text
inside delimited `=== … ===` data sections. The deterministic engine judges
requirement-vs-evidence regardless of injected text, and a model fooled into
returning `[]` yields an **honest empty** result — the `/analyze` path never
backfills the seeded demo answer key. Covered by `tests/test_prompt_injection.py`.

---

## 6. Dependency audit (2026-07-09)

`pip-audit` was run against the environment and `npm audit` against the frontend.

**Fixed:** `python-multipart` pinned to `>=0.0.31` in `pyproject.toml` — the
multipart upload parser had DoS CVEs (CVE-2026-40347 / 42561 / 53538–53540);
directly relevant to the hardened upload path.

**Fixed:**
- Frontend `npm audit --omit=dev` flagged a moderate PostCSS advisory through
  `next -> postcss@8.4.31`. `frontend/package.json` now has a narrow
  `overrides.postcss = ^8.5.10`, and the refreshed lockfile resolves Next,
  Vite, and Vitest to PostCSS `8.5.16`. Verification: `npm audit --omit=dev`
  reports `found 0 vulnerabilities`, and `npm run build` passes.

**Mitigated / documented (no change):**
- The Pramaan Docker image installs **only** `pyproject` dependencies. Most
  packages `pip-audit` flagged (torch, praisonaiagents, uv, pyjwt, pygments, …)
  are unrelated tools in the shared dev environment and are **not shipped**.
- `starlette` / `urllib3` advisories: these are transitive under FastAPI/HTTP
  clients and are pulled by version **range**, so a fresh image build resolves
  to the current patched releases; not force-pinned to avoid a resolver
  conflict with FastAPI. No large framework upgrade (goal constraint).

---

## 7. What judges need to access the demo

- With defaults (auth off): nothing — open the frontend, hit "Load real
  document" or upload a spec + submittal. Rate limits are generous (20 analyses/
  10 uploads/hour per IP).
- If auth was turned on for the event, judges need the `DEMO_AUTH_TOKEN` (share
  out-of-band; e.g. paste into an `X-Demo-Token` header via the API, or a token
  field if the frontend adds one). Prefer auth **off** for judging.

## 8. What NOT to claim

- ❌ "production-grade", "enterprise-ready", "secure by default".
- ❌ "penetration-tested", "zero vulnerabilities".
- ✅ "demo-hardened" / "public-demo hardened".
- ❌ that rate limiting is DDoS protection (it is single-instance, best-effort).
- ❌ that auth is a real access-control system (it is an optional demo token).
