# Data Handling — What Happens to an Uploaded Document

**Scope & honesty:** Pramaan is a hackathon/prototype build (see
`docs/CLAIMS_REGISTER.md` claim #17). This document describes, as accurately as
the code allows, what happens to a document a user uploads for analysis: what
is collected, which third parties see it, what persists and for how long, how
secrets are handled, and — bluntly — what this prototype does **not** protect
against. It is not a compliance document. It makes no certification claims
("GDPR compliant", "SOC2", etc.) because none have been sought or are true.

Everything below was verified by reading `backend/uploads.py`,
`backend/agents/ocr_util.py`, `backend/llm.py`, `backend/jobs.py`,
`backend/security.py`, `backend/main.py`, and `backend/analyze.py` on
2026-07-10, plus `render.yaml` for the hosted deployment's tracked config.
Anything not checkable from the code is marked **not verified**.

---

## 1. What data is collected

A user can submit document content two ways:

- **Pasted text** — `POST /analyze`, `/analyze/stream`: JSON body with
  `spec_text` / `submittal_text` (10–50,000 chars each) and a `system_id`.
- **File upload** — `POST /analyze/upload`, `/analyze/upload/stream`,
  `/analyze/vision`: a `spec_file` + `submittal_file` (or `submittal_image`
  for the vision path), multipart form data.

Accepted upload types (`backend/uploads.py`): text (`.txt/.md/.markdown/.text/
.csv/.log`), PDF, and raster images (`png/jpg/jpeg/tif/tiff/webp/bmp/gif`).
Anything else, anything disguised (extension says PDF, bytes don't), and any
archive/executable magic bytes are rejected before any parsing touches the
bytes. Per-file size cap: 20 MB (`PRAMAAN_MAX_UPLOAD_MB`).

There is also `POST /copilot` (a `query` string), but the copilot answers from
the repo-bundled demo corpus (`data/corpus/`, `data/projects/` —
team-authored fixtures shipped with the app), **not** from anything a user
uploads. It does not touch uploaded document content.

No account, project, or organization concept exists. There is no field for a
user's name, email, or company — the only identity signal captured anywhere is
a request's source IP (used only for rate-limit bucketing, see §6) and an
optional demo token.

---

## 2. Where it goes

### 2a. In-process handling

An uploaded file is read into memory with a capped `file.file.read(...)`
(`backend/main.py::_read_capped`) — application code never opens a file
handle to write uploaded bytes to disk. Extraction (`ocr_util.extract_document`)
runs entirely in memory: PDF text-layer extraction (pdfplumber / PyMuPDF), the
Tesseract OCR fallback for scanned PDFs/images, and plain-text decoding.

**One caveat the code itself flags** (`backend/main.py`, above
`BodySizeLimitMiddleware`): FastAPI/Starlette's `UploadFile` spools the *full*
multipart request body during ASGI parsing — this happens beneath the
application's control, before `_read_capped` or any app code runs. That
means an uploaded file's raw bytes can transiently touch an OS-level temp file
as part of request parsing, independent of anything the application does.
The exact spill threshold and cleanup timing of that framework-level buffering
were **not verified** in this audit — it is Starlette/Python `tempfile`
internals, not Pramaan code, and this doc does not claim otherwise.

### 2b. Third-party LLM providers — sent by name

Once extracted, the full plaintext of both documents (spec + submittal) is
embedded into a single prompt string (`backend/analyze.py`, via
`PROMPT_TEMPLATE.format(spec=..., submittal=..., standards=...)`) alongside
repo-bundled standards reference text. That prompt — i.e. the actual document
content — is sent over the network to whichever third-party LLM API answers
the request. The providers that can receive it, exactly as configured in
`backend/llm.py`:

| Provider | Vendor | Env key | Notes |
|---|---|---|---|
| `gemini` | Google (Gemini API) | `GEMINI_API_KEY` | default primary |
| `openai` (internal id; "Qwen gateway") | whatever OpenAI-compatible endpoint `QWEN_GATEWAY_BASE_URL`/`OPENAI_BASE_URL` points at | `QWEN_GATEWAY_API_KEY` / `OPENAI_API_KEY` | on the hosted demo per `render.yaml`, this is `https://aicredits.in/v1` proxying `google/gemini-3.1-flash-lite` — a third-party billing/routing intermediary sits between Pramaan and the underlying model |
| `groq` | Groq | `GROQ_API_KEY` | |
| `claude` | Anthropic | `CLAUDE_API_KEY` / `ANTHROPIC_API_KEY` | |
| `ollama` | none (local daemon) | *(keyless)*, gated by `LOCAL_LLM_ENABLED` | not used on the hosted Render demo — no local daemon there |

**What each of these providers does with the document content once it
receives it — their own retention, logging, or model-training practices — is
outside this codebase and was not verified here.** This document does not
and cannot certify third-party data handling; it only states that the
content is sent to them.

### 2c. Failover sends the SAME document content to multiple providers, in sequence

This is the part worth being explicit about: failover is not "pick one
provider." `complete_json()` / `complete()` / `complete_stream()`
(`backend/llm.py`) walk a **configured provider chain** — only providers with
an API key present are in it — and on a failure (quota/429, timeout,
unparseable output, transient 5xx) they retry the **identical prompt,
unmodified, containing the same document text**, against the next provider in
the chain. So on a bad day, one upload's content can be transmitted to
Gemini, then the gateway, then Groq, then Claude — one after another — before
the request either succeeds or falls through to the deterministic rule
engine (which computes locally and sends nothing anywhere). Only the
`/analyze/vision` image path is single-provider (Gemini only, or the gateway
if forced) — there is no cross-provider failover for image bytes.

The default code-level chain order (`_DEFAULT_ORDER` in `backend/llm.py`) is:

```
gemini → openai (Qwen/gateway) → groq → claude → ollama → deterministic rule engine
```

`render.yaml` (the repo-tracked config for a fresh deploy) sets
`PRAMAAN_LLM_PROVIDER_ORDER=gemini,qwen,groq` and explicitly excludes Claude
("no key exists" in that file's own comment). **The live hosted deployment's
actual order is dashboard-managed on Render and can differ from what's
committed in `render.yaml`** (the file says as much: "the live service's env
is dashboard-managed - edits here do NOT auto-apply"). This document does not
assert which providers are live on any given day — the only accurate,
checkable source for that is `GET /llm-check` on the running deployment,
which reports the resolved chain, each leg's `configured` state, and the last
failover event.

### 2d. The deterministic floor sends nothing anywhere

When every configured LLM leg fails (or none is configured), the rule-based
engine (`backend/analyze.py::_resilient_fallback`) computes deviations from
the actual document text using local regex/rule matching. No network call is
made and no document content leaves the process for that request.

---

## 3. Retention & deletion

**Raw uploaded document text is not stored anywhere beyond the request that
processes it.** There is no database in this codebase — confirmed by
searching `backend/` for `sqlite`, `postgres`, `redis`, and `.db`: the only
hits are code comments in `backend/jobs.py` and `backend/security.py`
explicitly contrasting today's in-memory approach with what "a production
deployment would" use (Redis, a persistent store) — neither exists today.

What **does** persist, in-process only (`backend/jobs.py`):

- **A result cache**, keyed by `sha256(spec_text + submittal_text + system_id +
  pipeline_signature)`. The hash is one-way and not reversible to the
  document text. The cache stores the **computed deviation findings** (which
  quote fragments of the source documents — component names, required vs.
  provided values, rationale strings) plus timing/mode metadata — **never the
  raw document text and never a secret** (stated as a design contract in the
  module docstring). Full LLM-backed results live up to `PRAMAAN_CACHE_TTL_S`
  (default 3600s / 1 hour); degraded/rule-floor results expire in
  `PRAMAAN_DEGRADED_CACHE_TTL_S` (default 120s). Bounded to
  `PRAMAAN_CACHE_MAX` entries (default 256), LRU-evicted.
- **Job records** (`/jobs/{id}` async flow): status metadata plus the same
  deviation-result view once done, bounded to `PRAMAAN_JOB_MAX` entries
  (default 256), LRU-evicted, no independent TTL beyond that eviction.

All of it is a plain Python dict in the worker process's memory. **A process
restart, redeploy, or a second replica loses all of it** — there is no
cross-instance sharing and nothing is flushed to disk on purpose. This is a
single-instance, in-memory prototype, not a persistence layer.

**Net answer:** raw uploaded document content does not persist beyond the
single request that analyzes it. Derived findings (short excerpts/paraphrases
of the documents, not the full text) persist in server memory for up to 1
hour or until the process restarts, whichever comes first.

---

## 4. Secrets handling

All provider keys (`GEMINI_API_KEY`, `QWEN_GATEWAY_API_KEY`/`OPENAI_API_KEY`,
`GROQ_API_KEY`, `CLAUDE_API_KEY`/`ANTHROPIC_API_KEY`) and the optional
`DEMO_AUTH_TOKEN` are read from environment variables only — never
hardcoded. `render.yaml` marks every one of them `sync: false` ("set this
secret in the Render dashboard"): **no key value is committed to this
repository.**

- **Not logged:** `backend/llm.py`'s `log.info` calls print `prompt_len`,
  the model name, and (for the gateway) the base URL — never the prompt
  content and never a key value.
- **Redacted on failure:** `_redact()` (`backend/llm.py`) strips every
  configured key's literal value out of any exception string before it is
  recorded in `FAILOVER_STATUS` or logged.
- **Status endpoints never leak them:** `GET /health`, `/ocr-check`,
  `/llm-check`, and `security_status()` report only booleans, counts, and
  model names. `tests/test_no_secrets.py` injects fake secret values and
  asserts they never appear in any of these responses — including the
  401/403 auth-failure bodies and the failover-error path.
- **Demo token:** compared with `secrets.compare_digest` (constant-time);
  never echoed in an error message. If `DEMO_AUTH_ENABLED=true` but no token
  is set, auth is treated as **inert** (fails open) rather than silently
  locking the demo — an availability choice, not a security one.

---

## 5. Explicit threat boundaries — what this prototype does NOT protect against

Stated as plainly as `docs/SECURITY_DEMO_RUNBOOK.md` states it, because
uploaded documents here are described as confidential EPC materials and that
deserves the same bluntness:

- **No authentication by default.** `DEMO_AUTH_ENABLED` defaults to `false`
  on the hosted deploy (`render.yaml`). Anyone with the URL can upload a
  document and run analysis. There are no user accounts.
- **Even with auth on, it is one shared token, not identity.** `DEMO_AUTH_TOKEN`
  is a single bearer/header/query-param secret checked the same way for every
  caller — not per-user credentials, not an access-control system. Anyone
  holding that one token can hit every token-protected endpoint.
- **No tenant isolation on the result cache.** `analyze_cached()`
  (`backend/jobs.py`) keys purely on a hash of the document content, with no
  per-user or per-session partitioning. If two different callers submit
  byte-identical spec+submittal text, the second caller is served the first
  caller's cached result. This is by design (it saves LLM quota), but it
  means the cache has no concept of "whose data is this."
- **No ownership check on job results.** `GET /jobs/{job_id}` and
  `/jobs/{job_id}/result` require only the (optional) demo token, not proof
  that the caller submitted that job. A job ID is an unguessable 128-bit
  UUID4, so brute-forcing one is impractical — but anyone who obtains a
  job ID by any other means (a shared link, a proxy log, browser history) can
  read that analysis's result, including the derived findings from someone
  else's document.
- **No encryption at rest for the in-memory cache.** There is no persistent
  "at rest" store for raw document text (see §3), so at-rest encryption is
  not applicable there — but the derived-findings cache sits in plain,
  unencrypted process memory for up to an hour.
- **Transport encryption is a deployment detail, not an application
  guarantee.** The application itself speaks plain HTTP; whether a given
  deployment sits behind TLS termination (Render's edge, for the hosted demo)
  is a hosting-platform property, **not verified** as part of this codebase
  audit.
- **Rate limiting is single-instance, in-memory, and IP-based
  (`backend/security.py`).** It does not survive a restart, does not share
  state across replicas, and keys off `X-Forwarded-For`, which a client can
  spoof. This slows abuse; it does not prove or protect identity, and it is
  not a substitute for network-layer protection.
- **CORS is wildcard (`*`) by default**, with `allow_credentials=False`. This
  is an intentionally open public-demo API surface, not a restricted one.
- **No audit trail of who uploaded what.** No per-request user identity is
  captured or logged anywhere — only an IP-derived rate-limit bucket that is
  never persisted beyond the current sliding window.
- **Third-party LLM providers see full plaintext document content**, as
  described in §2 — including, on a failover event, the same content sent to
  more than one provider in sequence. This project does not control, and has
  not audited, what those providers do with it afterward.

---

## 6. What NOT to claim about this document

Per `docs/CLAIMS_REGISTER.md` and enforced by `tests/test_claims_register.py`:

- ❌ "production-grade", "enterprise-ready", "secure by default" — this is a
  hackathon prototype (claim #17).
- ❌ "penetration-tested", "zero vulnerabilities", "hardened against all
  attacks" — none of that testing has been done.
- ❌ "GDPR compliant", "SOC2", or any other compliance certification — none
  has been sought, and nothing here should be read as one.
- ❌ "DDoS protection" — the rate limiter is a single-instance, best-effort
  sliding window, not a DDoS mitigation layer.
- ✅ "demo-hardened" / "public-demo hardened" (matches
  `docs/SECURITY_DEMO_RUNBOOK.md`'s framing) for the upload-validation and
  rate-limiting controls that do exist.
- ✅ "nothing persists beyond the request except an in-memory, TTL-bounded
  cache of derived findings, and that cache is lost on restart."

---

## 7. Verification

```bash
python -m pytest tests/test_claims_register.py -q
python -m pytest tests/test_no_secrets.py -q
python -m pytest tests/test_security_auth_ratelimit.py tests/test_upload_hardening.py -q
grep -rn "sqlite\|postgres\|redis\|\.db\b" backend/
```

The first two are the enforcement gates this document must not trip and the
secret-leak guard this document describes. The `grep` is the check backing
§3's "no database exists" claim — re-run it if `backend/` changes.
