# Deployment Checklist

One-page pre-flight for deploying the Pramaan demo (backend on Render/Docker,
frontend on Vercel). Companion docs: `docs/SECURITY_DEMO_RUNBOOK.md`,
`docs/LLM_FAILOVER_RUNBOOK.md`, `docs/OCR_DEPLOYMENT_CHECKLIST.md`.

> Pramaan is a prototype / hackathon build, **demo-hardened** — not
> production-grade. Keep claims accordingly (`docs/CLAIMS_REGISTER.md`).

## 1. Backend (Render — Docker runtime)

Build from `Dockerfile.backend` (installs the `tesseract` binary so OCR works).
`render.yaml` carries the non-secret env; set secrets in the dashboard.

**Secrets (dashboard, `sync:false`):** `GEMINI_API_KEY`, and optionally the
failover legs `OPENAI_API_KEY`(Qwen gateway)/`GROQ_API_KEY`. `DEMO_AUTH_TOKEN`
only if enabling auth.

**Security env (already in `render.yaml`):**
```
PRAMAAN_RATE_LIMIT_ENABLED=true
PRAMAAN_ANALYSIS_LIMIT_PER_HOUR=20
PRAMAAN_UPLOAD_LIMIT_PER_HOUR=10
PRAMAAN_DEEP_PROBE_LIMIT_PER_HOUR=3
PRAMAAN_MAX_UPLOAD_MB=20
DEMO_AUTH_ENABLED=false        # flip to true (+DEMO_AUTH_TOKEN) only if abused
```

**LLM env:** `PRAMAAN_LLM=gemini`, `GEMINI_MODEL=gemini-2.5-flash`,
`PRAMAAN_LLM_TIMEOUT=60`, `PRAMAAN_LLM_PROVIDER_ORDER=gemini,groq,qwen,claude`
(Groq second while the Qwen/OpenRouter leg is unfunded and 402s — see
`LLM_FAILOVER_RUNBOOK.md`).

## 2. Frontend (Vercel)

- `NEXT_PUBLIC_API=https://<backend-host>` (inlined at build — redeploy after a
  change). No secrets in the frontend bundle (never the demo token).

## 3. Pre-deploy verification (local)

```powershell
python -m pytest tests -q --tb=short
python -m ruff check .
python scripts/benchmark_manifest_check.py
python scripts/benchmark_hash_sources.py
docker build -f Dockerfile.backend -t pramaan-verify .
```

## 4. Post-deploy verification (live)

```bash
BASE=https://<backend-host>
curl -s $BASE/health        | jq '.commit, .security, .ocr_available, .llm.chain'
curl -s $BASE/ocr-check     | jq '.status'          # expect "ready"
curl -s $BASE/llm-check     | jq '.ok, .failover.chain'
```

Green when: `commit` = the deployed SHA; `security.rate_limit_enabled=true`;
`ocr-check.status="ready"`; `llm-check.ok=true` (or `on_rule_engine_floor` if no
key). Upload rejection spot-check per the security runbook §4.

## 5. Security posture toggles

| Situation | Action |
|---|---|
| Demo being abused (quota drain) | already rate-limited; tighten `*_LIMIT_PER_HOUR` |
| Need to lock the demo | `DEMO_AUTH_ENABLED=true` + `DEMO_AUTH_TOKEN=<random>`; share token with judges out-of-band |
| Load testing | `PRAMAAN_RATE_LIMIT_ENABLED=0` temporarily |
| Restrict browsers | `PRAMAAN_CORS_ORIGINS=https://<frontend-host>` |

## 6. Rollback

- **Backend:** Render → Deploys → **Rollback** to the previous image, or
  `git revert <sha>` + push (redeploys). All Phase-5 controls are env-gated:
  setting `PRAMAAN_RATE_LIMIT_ENABLED=0` and `DEMO_AUTH_ENABLED=false` reverts
  to fully-open behaviour without a code change. Upload validation cannot be
  env-disabled — to bypass it, roll back the image.
- **Frontend:** Vercel → Deployments → promote the previous build.
- No database/state to migrate; rollback is image/deploy-level only.
