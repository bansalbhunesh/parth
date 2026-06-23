# Pramaan — Execution Brief

## Status: Competition-Ready (v2)

All components implemented, tested, and polished:

- [x] Corpus generation (10 systems, 33 requirements, 7 seeded deviations)
- [x] LLM reconciliation brain with confidence scoring
- [x] Extraction agent with accuracy scoring
- [x] Commissioning twin with L1–L5 timeline + LLM fallback
- [x] RFI copilot with TF-IDF retrieval + prior-RFI matching
- [x] Evidence pack (JSON + printable HTML) + /metrics endpoint
- [x] Baseline eval: P/R/F1 = 1.000, Cx prediction = 1.000
- [x] Backend graceful fallback (all 11 endpoints return 200 without API key)
- [x] 14-section frontend dashboard with scroll animations
- [x] Hero intro, architecture diagram, ROI calculator, before/after comparison
- [x] Standards KB, eval dashboard, scale story, academic references
- [x] Standards scraper v2 (3-tier: Firecrawl → Crawl4ai → Playwright)

## To Run with LLM Key

```bash
export GEMINI_API_KEY=your_key_here
python3 eval/run_eval.py --detector llm
```

## Demo Script (60 seconds)

1. **Open** → Hero intro frames the problem. Sentinel fires: UPS-02 battery 7 min vs 10 min.
2. **Lead time** → 27 weeks early. Point to timeline strip.
3. **149 weeks** → Giant animated counter. Total savings across all 7 deviations.
4. **Before/After** → Toggle: manual review (10–15 weeks) vs Pramaan (< 5 minutes).
5. **Pipeline** → 5 agents animate in sequence. Architecture diagram shows full stack.
6. **System health** → 10 systems grid. 4 critical, 3 major.
7. **Cx Twin** → IST-07, IST-09, IST-11 pulsing red. These tests WILL fail.
8. **ROI** → Slide project value. ₹1,788L rework avoided on ₹800 Cr project.
9. **Copilot** → "Has UPS battery runtime come up before?" → RFI-014 cited.
10. **Eval** → P/R/F1 = 1.000. Zero false positives. Reproducible harness.
11. **Export** → One click → HTML evidence pack with full audit trail.

## Guardrails

- Never hardcode deviation answers. The reasoning must be real; the eval proves it.
- Never reproduce copyrighted standard text — paraphrased summaries only.
- Keep agents at 5 and narratable. Legible beats clever.
- The lead-time number is the story. If a change buries it, revert.
- No secrets in the repo. `.env` and API keys stay in `.gitignore`.
