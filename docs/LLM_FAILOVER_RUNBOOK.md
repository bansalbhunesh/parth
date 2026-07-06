# LLM Provider Failover — Runbook

**What this is:** a self-healing LLM provider chain that keeps the live demo
answering when Gemini quota/429s, rate-limits, times out, or fails. It is a
**reliability / availability** feature, **not** an accuracy feature — every
provider is scored, guarded, and grounded identically, and the final floor is
the deterministic rule engine, which computes deviations from the actual
documents (never seeded or fake findings).

Implementation: `backend/llm.py`. Tests: `tests/test_failover.py` (pre-Phase-4
contract) + `tests/test_failover_phase4.py` (Ollama leg, canonical env names,
order override, separate-quota guard, no-secret-leak).

---

## The chain

```
gemini  →  Groq  →  Qwen / OpenAI-compatible gateway  →  Claude  →  local Ollama  →  deterministic rule engine
(primary) (insurance)        (separate quota)           (failover)   (offline)        (always-present floor)
```

> **Hosted-demo note (updated 2026-07-06):** the gateway leg is **funded via
> aicredits.in** and pinned to `google/gemini-3.1-flash-lite` — the exact
> benchmark-featured model — so the canonical order
> `PRAMAAN_LLM_PROVIDER_ORDER=gemini,qwen,groq,claude` is restored: the first
> failover lands on the featured configuration. The paid leg carries a **spend
> guard** (`OPENAI_BUDGET_PER_HOUR`, default 30 on the hosted demo): an
> exhausted hourly budget counts as a leg failure and the chain walks on to
> Groq / the free rule floor, so abuse or a failover storm can never run up the
> bill. The Claude leg stays **unconfigured** (no key set). The live service's
> env is **dashboard-managed** — set values in the Render dashboard (render.yaml
> is documentation for fresh deploys), then Manual Deploy. Do not describe any
> leg as live unless `/llm-check?probe_all=1` shows it `ok:true` that day
> (budget state appears there too: `budget_per_hour` / `budget_used_last_hour`).

- **Only configured providers are attempted.** A leg with no key (or, for
  Ollama, `LOCAL_LLM_ENABLED` unset) is filtered out. So a **Gemini-only**
  deployment behaves exactly as before: a one-element chain, one attempt, the
  same `LLMError` on failure.
- **What triggers a failover:** quota / `429` / rate-limit / timeout / any
  provider exception. `429`/quota is **not** retried on the same provider (the
  daily cap won't clear in seconds) — it fails straight over. Transient
  server-side blips (`503` / `overloaded` / `internal`) get a couple of bounded
  retries on the *same* provider first (free-tier models 503 under load).
- **When everything fails:** `complete()` raises `LLMError`; the callers
  (`backend/analyze.py`) catch it and return the deterministic rule-engine
  result with `mode="deterministic"`. The response is always produced — never an
  exception to the user, never a seeded label.
- **Streaming** only fails over *before the first token*. Once a provider has
  emitted output we do not switch mid-stream (that would duplicate text to the
  judge); a rare mid-stream drop surfaces to the caller, which degrades to the
  rule engine.

Override the order with `PRAMAAN_LLM_PROVIDER_ORDER` (comma-separated; unknown
names dropped; `qwen`/`gateway` are accepted aliases for the gateway leg). The
`PRAMAAN_LLM` primary is always floated to the front of the resolved order.

---

## Environment variables

Canonical name first; the older alias in parentheses still works (so a live
deployment wired with the old names keeps running unchanged).

| Leg | Key | Model / endpoint | Notes |
|-----|-----|------------------|-------|
| gemini | `GEMINI_API_KEY` | `GEMINI_MODEL` (`gemini-2.5-flash`) | primary; AI Studio free tier |
| qwen gateway | `QWEN_GATEWAY_API_KEY` (`OPENAI_API_KEY`) | `QWEN_GATEWAY_BASE_URL` (`OPENAI_BASE_URL`), `QWEN_GATEWAY_MODEL` (`OPENAI_MODEL`), `QWEN_GATEWAY_JSON_MODE`, `QWEN_GATEWAY_MAX_TOKENS` | **must be a separate provider/quota** — see below |
| groq | `GROQ_API_KEY` | `GROQ_MODEL` (`llama-3.3-70b-versatile`), `GROQ_BASE_URL` | free tier, its own quota |
| claude | `CLAUDE_API_KEY` (`ANTHROPIC_API_KEY`) | `CLAUDE_MODEL` (`claude-opus-4-8`) | |
| ollama | *(keyless)* `LOCAL_LLM_ENABLED=1` | `OLLAMA_BASE_URL` (`http://localhost:11434`), `OLLAMA_MODEL` (`llama3.1`) | local daemon; needs no network/quota |
| — | `PRAMAAN_LLM` | primary provider id | `gemini` \| `qwen` \| `claude` \| `ollama` |
| — | `PRAMAAN_LLM_TIMEOUT` | seconds (`60`) | sync `/analyze` wait before the rule floor |
| — | `PRAMAAN_LLM_PROVIDER_ORDER` | e.g. `gemini,qwen,groq,claude,ollama` | overrides the whole order |

### The Qwen gateway must be a genuinely separate quota

Do **not** point `QWEN_GATEWAY_BASE_URL` at Google's OpenAI-compatible endpoint
(`generativelanguage.googleapis.com/...`) and call it a backup — that would just
re-spend Gemini's quota, so the "failover" would 429 at the same moment Gemini
does. Use an independent provider (e.g. OpenRouter: `https://openrouter.ai/api/v1`).
`/llm-check` reports `providers.openai.separate_quota=false` if it detects a
Google endpoint, so a misconfiguration is visible, not silent.

### Local Ollama (offline last leg)

```bash
# one-time
ollama pull llama3.1
# then run the backend with:
export LOCAL_LLM_ENABLED=1
export OLLAMA_MODEL=llama3.1        # or any pulled model
# OLLAMA_BASE_URL defaults to http://localhost:11434
```

Ollama is **not** used on the hosted Render demo (no local daemon there); it is
for local / offline resilience. On Render it stays filtered out.

---

## `/llm-check`

- **`GET /llm-check`** — a *tiny* one-token probe + the full report: the resolved
  `order`, the configured `chain` actually tried, each provider's non-secret
  config (`configured`, `model`, `separate_quota`, …), `last_successful_provider`,
  `last_failover` (redacted reason + timestamp), `on_rule_engine_floor`, and
  `deterministic_fallback_available`. Never returns a key or secret-bearing URL.
- **`GET /llm-check?deep=1`** — the *expensive* probe: the exact reconcile-sized
  prompt the demo sends, bounded by `PRAMAAN_LLM_TIMEOUT`. Use this to pre-flight
  before a demo (a tiny probe can pass while demo-sized calls 429 on
  token-weighted quotas). Costs real tokens — run sparingly.
- **`GET /llm-check?probe_all=1`** — one tiny call per configured provider, to see
  which legs are individually healthy. Also costs tokens.

`GET /health` carries the same `llm` summary (`provider`, `chain`, `ready`) plus
`analysis_mode` (`llm` vs `rule-based-fallback`).

---

## Pre-demo checklist

```bash
curl -s https://<backend>/health | jq '.llm, .analysis_mode'
curl -s https://<backend>/llm-check | jq '.failover.chain, .failover.providers'
# Pre-flight the real path (spends a little quota):
curl -s "https://<backend>/llm-check?deep=1" | jq '.ok, .findings, .elapsed_ms, .error'
```

Green when `failover.chain` lists your configured providers, each intended leg
shows `configured:true`, the gateway shows `separate_quota:true`, and `deep=1`
returns `ok:true`. If `on_rule_engine_floor:true`, no LLM key is set and the demo
runs on the deterministic engine (still answers, low recall by design).

---

## Verification (local)

```bash
python -m pytest tests/test_failover.py tests/test_failover_phase4.py tests/test_resilience.py -q
python -m ruff check backend/llm.py tests/test_failover_phase4.py
```

## Guarantees these tests pin

1. Gemini success → no fallback called.
2. Gemini quota/429 → Qwen gateway; Qwen fail → Groq → Claude → Ollama.
3. Every LLM leg failing → `LLMError` → callers land on the deterministic engine
   (`mode="deterministic"`), never an exception, never a seeded label.
4. Single configured provider → unchanged one-element behaviour.
5. Canonical (`QWEN_GATEWAY_*` / `CLAUDE_*`) **and** legacy (`OPENAI_*` /
   `ANTHROPIC_*`) env names both configure their leg.
6. `PRAMAAN_LLM_PROVIDER_ORDER` reorders the chain; `qwen` alias resolves.
7. A Google gateway endpoint is flagged `separate_quota:false`.
8. No API key (any alias) leaks into logs, the failover record, or the report.
9. `/llm-check` surfaces the order + `deterministic_fallback_available` with no
   secret in the payload.

**Reminder:** none of this is an accuracy claim. See `docs/CLAIMS_REGISTER.md`
row 22 — failover is reliability/availability only.
