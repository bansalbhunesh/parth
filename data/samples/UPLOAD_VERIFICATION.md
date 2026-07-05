# Live Upload Verification — Real PDF, Before vs After

Captured against the deployed API (`https://parth-1-ma30.onrender.com`), not a
local run. Proves the real-document PDF upload now catches deviations where it
previously returned zero.

## Before (deterministic-only, pre-resilience)

Judge Mode → Upload PDFs → `design_basis_edge.pdf` + Vertiv UPS datasheet:

> **0 deviations found — submittal meets all identified requirements.** (`ms · deterministic mode`)

The template-only fallback couldn't parse a real vendor datasheet, so an LLM
outage produced a silent zero.

## After (commit `e1dc922`)

Same `design_basis_edge.pdf` spec vs the Vertiv UPS submittal, three paths:

| Path | Mode | Result |
|------|------|--------|
| `POST /analyze/upload/stream` (demo panel) | **llm** | **4 deviations**, 12 live token events |
| `POST /analyze/upload` (sync, 60 s cap) | **llm** | **4 deviations**, 35.8 s |
| `POST /analyze/upload` during a real 429 outage | rule-based | **3 deviations** — never zero |

**LLM-recovered deviations (real reasoning over extracted PDF text):**

| Component / Parameter | Required → Provided | Severity |
|---|---|---|
| UPS / battery_autonomy_min | 10 → **8** min | Critical |
| UPS / output_power_factor | ≥ 0.9 → **Not stated** | Major |
| UPS / acoustic_noise_dba | 55 → **71** dBA | Major |
| UPS / network_management | SNMP card w/ remote shutdown → **Not stated** | Major |

It catches value mismatches *and* omissions ("Not stated"), not just template
diffs.

## Why this matters
- **No silent zeros.** When the model is rate-limited (free-tier reality), the
  rule-based fallback still returns Cx-mapped deviations.
- **`PRAMAAN_LLM_TIMEOUT`** bounds the wait (60 s for the demo so sync returns the
  full LLM result; the streaming panel is uncapped).
- Verify live anytime: `GET /llm-check` for model status, then upload a datasheet.

## Reproduce
```bash
API=https://parth-1-ma30.onrender.com
curl -s -X POST $API/analyze/upload \
  -F "spec_file=@data/samples/design_basis_edge.pdf;type=application/pdf" \
  -F "submittal_file=@data/samples/vendor_submittal_ups.md;type=text/markdown" \
  -F "system_id=UPS"
```
