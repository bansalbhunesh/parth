# Pramaan — Execution Brief

## Status: Competition-Ready (v3)

All components implemented, tested, and polished:

- [x] Corpus generation (10 systems, 33 requirements, 14 seeded deviations per project)
- [x] Multi-project support (12 projects, 11 countries, 50 total deviations, 1,024 weeks saved)
- [x] LLM reconciliation brain with confidence scoring + citation faithfulness
- [x] Extraction agent with accuracy scoring
- [x] Commissioning twin with L1–L5 timeline + LLM fallback
- [x] RFI copilot with TF-IDF retrieval + prior-RFI matching
- [x] Evidence pack (JSON + printable HTML) + /metrics endpoint
- [x] Baseline eval: P/R/F1 = 1.000, Cx prediction = 1.000 (all 12 projects)
- [x] Backend graceful fallback (all 28 endpoints return 200 without API key)
- [x] 22-section frontend dashboard with scroll animations + 27 components
- [x] Hero intro, architecture diagram, ROI calculator, before/after comparison
- [x] Standards KB, eval dashboard, scale story, academic references
- [x] Standards scraper v2 (3-tier: Firecrawl → Crawl4ai → Playwright)
- [x] Docker Compose one-command setup with health checks
- [x] GitHub Actions CI (backend tests, frontend build, Docker smoke test)
- [x] 435 tests across API, agents, corpus, and multi-project eval

## Reproduce the Numbers

```bash
# Run 435 tests
python3 -m pytest tests/ -v

# Single project eval (14 devs, 267 weeks, F1=1.000)
python3 eval/run_eval.py

# Multi-project eval (50 devs, 1024 weeks, F1=1.000)
python3 eval/multi_project_eval.py

# Text-based eval (independent input path, NLP extraction)
python3 eval/text_eval.py

# Docker one-command
docker compose up --build
```

## To Run with LLM Key

```bash
export GEMINI_API_KEY=your_key_here
python3 eval/run_eval.py --detector llm
```

## Demo Script (60 seconds)

1. **Open** → Hero intro frames the problem. Sentinel fires: UPS-02 battery 7 min vs 10 min.
2. **Lead time** → 27 weeks early. Point to timeline strip.
3. **1,024 weeks** → Giant animated counter. Total savings across 12 projects, 11 countries.
4. **Before/After** → Toggle: manual review (10–15 weeks) vs Pramaan (< 5 minutes).
5. **Pipeline** → 5 agents animate in sequence. Architecture diagram shows full stack.
6. **System health** → 10 systems grid. 7 critical, 7 major deviations flagged.
7. **Cx Twin** → IST-07, IST-09, IST-11 pulsing red. These tests WILL fail.
8. **Multi-project** → 12 projects across 11 countries (synthetic breadth test — 1.000 by construction; the real proof is the sourced datasheet pairs).
9. **Copilot** → "Has UPS battery runtime come up before?" → RFI-014 cited.
10. **Eval** → real datasheets: 19 deviations (recall 1.000), 0 false positives, self-scored ~0.9 on one contested case (live-verified, gemini-2.5-flash). Reproducible no-key harness (`eval/real_pairs_offline.py`).
11. **Export** → One click → HTML evidence pack with full audit trail.

## Guardrails

- Never hardcode deviation answers. The reasoning must be real; the eval proves it.
- Never reproduce copyrighted standard text — paraphrased summaries only.
- Keep agents at 5 and narratable. Legible beats clever.
- The lead-time number is the story. If a change buries it, revert.
- No secrets in the repo. `.env` and API keys stay in `.gitignore`.
