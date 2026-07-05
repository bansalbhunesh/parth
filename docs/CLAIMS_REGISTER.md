# Pramaan — Claims Register

Single source of truth for what may and may not be claimed about Pramaan and the
**ps4_external_v1 (v1.2)** benchmark, across README, benchmark report, deck
source, detailed submission PDF source, and any future video/demo script.

**Rule:** if a claim is not in this register, do not make it. Every quantitative
claim must appear with its nearby limitation. Numbers are from
`benchmarks/ps4_external_v1/reports/benchmark_card.json` (regenerate with
`python scripts/benchmark_report.py`). Provenance governance (source origin,
derived-vs-stored, standards-citation-only) is indexed in
[`SOURCE_PROVENANCE.md`](SOURCE_PROVENANCE.md).

Evidence types: `measured` (deterministic count/hash), `benchmarked` (from the
3-pass featured run), `deterministic_offline` (rule engine), `team_authored`
(fixture provenance), `pending` (not yet done). Status: verified / benchmarked /
scenario / pending / do-not-use.

## Claims table

| # | Claim | Exact number / wording | Evidence source | Evidence type | Allowed wording | Banned wording | Venues | Nearby limitation (must appear) | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Benchmark size — pairs | **53 pairs** | manifest + labels (card.composition) | measured | "53 spec–submittal pairs" | "53 real datasheets", "53 vendor documents" | README, deck, video, demo, report | team-authored fixtures | verified |
| 2 | Frozen labels | **129 frozen labels** | `labels_freeze.json` | measured | "129 frozen, provenance-tracked labels" | "129 human-adjudicated labels" | all | single-author frozen; reviewer-2 pending | verified |
| 3 | Systems covered | **17 system types** | labels | measured | "17 datacenter system types (UPS, chiller, switchgear, …)" | "all datacenter systems" | all | — | verified |
| 4 | Clean negatives | **64 clean negatives** | labels | measured | "64 clean-negative (compliant) controls" | — | all | — | verified |
| 5 | Repeated evaluation | **3-pass run** | featured lite runs | benchmarked | "3-pass repeated evaluation" | "extensively benchmarked", "battle-tested" | all | one model, one gateway | benchmarked |
| 6 | Recall | **mean semantic recall 0.862 (0.841–0.873)** | card.primary_result | benchmarked | "0.862 mean recall across 3 passes on the ps4_external_v1 benchmark" | "86% real-world accuracy", "detects 86% of field deviations", "100% recall" | report, deck, video, demo | team-authored benchmark; not field-validated | benchmarked |
| 7 | Precision | **mean semantic precision 0.953** | card.primary_result | benchmarked | "0.953 mean precision on the benchmark" | "95% real-world precision" | report, deck, video, demo | benchmark only; 8 scorer/label FPs remain | benchmarked |
| 8 | F1 | **mean semantic F1 0.905** | card.primary_result | benchmarked | "0.905 mean F1 on the benchmark" | "0.905 real-world F1" | report, deck, video, demo | benchmark only | benchmarked |
| 9 | Clean-negative false-alert rate | **FAR 0.000** | card.primary_result | benchmarked | "0 false alerts on 64 clean-negative controls in this benchmark" | "zero false positives overall", "never false-alarms" | report, deck, video, demo | clean-negative controls only; 8 scorer/label FPs exist on positive pairs | benchmarked |
| 10 | Latency | **p50 ~2.5 s** | lite summary.json | measured | "~2.5 s median latency per pair (gemini-3.1-flash-lite via gateway)" | "real-time", "instant" | report, deck, demo | gateway/model dependent | benchmarked |
| 11 | Rule baseline | **recall 0.111 (7/63), 0 FP** | rule summary.json | deterministic_offline | "deterministic offline rule baseline: 7/63 recall, 0 false positives" | "the rule engine is production-accurate" | report, deck | low recall by design (a floor) | benchmarked |
| 12 | Primary-source-derived docs | **10 (5 verified URLs)** | manifest | measured | "10 documents derived from public primary sources; 5 cite a verified public URL" | "10 stored primary-source PDFs", "10 real datasheets" | all | derived ≠ stored primary file | verified |
| 13 | Fixture nature | **team-authored fixtures** | manifest source_origin | team_authored | "team-authored fixtures modeled on public reference values" | "real vendor datasheets", "real unseen submittals" | all | this IS the limitation | verified |
| 14 | Reviewer status | **reviewer-2 pending** | `REVIEW_STATUS.md` | pending | "single-author frozen; automated consistency audit run (123/129 consistent, 6 flagged); two-person adjudication pending" | "two-reviewer adjudicated", "independently reviewed" | all | second human review not yet done | pending |
| 15 | Stored primary sources | **stored primary PDFs pending** | BENCHMARK_PROTOCOL backlog | pending | "stored primary-source PDFs are a backlog item" | "stored primary-source benchmark", "sourced from real datasheets" | all | only citations/derivations exist today | pending |
| 16 | Field validation | **none** | — | pending | "not yet validated in the field" | "field-validated", "real-world accuracy", "proven in production" | all (as a disclaimer) | — | do-not-use |
| 17 | Production maturity | **none** | — | pending | "prototype / hackathon build" | "production-grade", "enterprise-ready" | all | — | do-not-use |
| 18 | Datasheet realism | **none** | — | team_authored | "fixtures, not real datasheets" | "real-datasheet accuracy", "tested on real unseen datasheets" | all | — | do-not-use |
| 19 | Customer ROI | **none** | — | pending | (say nothing) | "customer ROI", "saves customers $X", "N% cost reduction" | none | — | do-not-use |
| 20 | OCR (scanned PDF + image) | **text-first + Tesseract fallback** | `eval/OCR_SCANNED_PDF.md`, `tests/test_ocr.py`, `backend/agents/ocr_util.py` | measured | "reads scanned / image-only PDFs and uploaded images via Tesseract OCR where the tesseract binary is installed; text-first with an OCR fallback, best-effort" | "OCR works everywhere", "reads any scanned PDF", "pixel-perfect OCR", "lossless OCR", "100% OCR accuracy" | README, report, demo, docs | needs the tesseract system binary (shipped in the `Dockerfile.backend` image / Render Docker build); English-only, best-effort (not lossless — e.g. GXT5→GXTS); `GET /ocr-check` reports whether OCR is live in a given deployment | verified |
| 21 | Vision (image via LLM) | **Gemini reads values from the picture** | `data/samples/real/VISION_RESULT.md`, `backend/analyze.py` | measured | "given a datasheet image, Gemini vision reads the values from the picture (a separate path from Tesseract OCR)" | "vision works on any image", "always reads images", "vision-grade accuracy" | README, docs, demo | Gemini-only (no text-model failover); degrades to `mode=vision-unavailable` on any error; demonstrated on one sample, not headlined as a benchmark number | scenario |
| 22 | LLM provider failover | **self-healing chain → deterministic floor** | `backend/llm.py`, `tests/test_failover.py`, `tests/test_failover_phase4.py`, `docs/LLM_FAILOVER_RUNBOOK.md` | measured | "on quota/429/rate-limit/timeout the demo fails over gemini → Qwen gateway → Groq → Claude → local Ollama → deterministic rule engine; only configured providers are tried; `/llm-check` shows the live chain and last failover" | "failover improves accuracy", "more accurate with failover", "never goes down", "100% uptime", "self-healing accuracy" | README, docs, demo, video | **reliability/availability only, NOT accuracy** — every leg is scored the same; the rule floor is deliberately low-recall (see #11) and computes from the real documents, never seeded labels; the Qwen gateway must be a genuinely separate quota (not Google's endpoint) | verified |
| 23 | Public-demo security hardening | **auth (opt-in) + rate limits + upload validation** | `backend/security.py`, `backend/uploads.py`, `tests/test_security*.py`, `tests/test_upload_hardening.py`, `tests/test_prompt_injection.py`, `tests/test_no_secrets.py`, `docs/SECURITY_DEMO_RUNBOOK.md` | measured | "demo-hardened: optional token auth, per-IP rate limiting, MIME/magic-byte upload validation (rejects archives/executables/disguised/oversized/bomb images), prompt-injection-resistant prompts, and no secret leakage in status endpoints" | "production-grade", "enterprise-ready", "secure by default", "penetration-tested", "zero vulnerabilities", "DDoS protection", "hardened against all attacks" | README, docs, demo, video | **demo hardening, not production security** — rate limiting is single-instance/in-memory (no shared store), auth is an optional demo token (not access control), and the dependency audit fixed the in-scope upload-parser CVE while documenting dev-only/unshipped advisories | verified |

## Architecture claims

Governs how the runtime may be described (README, deck, docs, diagrams, video).
Verify against `backend/orchestrator.py` + `backend/main.py`.

| # | Claim | Allowed wording | Banned wording | Runtime truth |
|---|---|---|---|---|
| A1 | Overall shape | "one compliance reasoning graph + connected deterministic intelligence services + reliability layer" | "five AI agents", "5 autonomous agents", "multi-agent AI system" (as the headline), "fully autonomous" | LangGraph graph with conditional routing + 2 bounded cycles; one LLM node |
| A2 | LLM footprint | "a single LLM reasoning core (`reconcile`); other nodes are deterministic-first" | "every step is AI", "agentic at every stage" | `node_reconcile` is the only node that reasons with an LLM; ingest/load_standards/validate/retrieve/critique are deterministic; `cx_predict` is rule/graph-first with an LLM **fallback** only for unmapped classes; the copilot uses an LLM only to phrase a retrieved answer |
| A3 | The two cycles | "two bounded cycles — a retrieval tool-call and a self-critique/reflexion loop" | "unbounded agent loop", "recursive self-improvement" | `PRAMAAN_MAX_RETRIEVALS` / `PRAMAAN_MAX_REVISIONS` bound both; graph always terminates |
| A4 | Deterministic services | "deterministic commissioning/schedule/supply-chain/graph services" | "AI-computed schedule", "the AI predicts the slip" | CPM + Monte Carlo + rule tables; commissioning mapping falls back to an LLM only for unmapped classes; LLM otherwise only narrates, with a labelled `mode` |
| A5 | Graph edges | "each deviation→standard→Cx-test edge carries the basis it rests on" | "all graph edges standards-cited", "every edge is standards-cited" | Some edges (e.g. `supplied-by`) are structural and carry no `basis` |
| A6 | Provider failover | "provider failover for availability; `/llm-check` shows the live chain" | "failover improves accuracy", "self-healing accuracy", "never goes down" | Reliability only; every leg scored the same (see #22) |
| A7 | OCR availability | "OCR runtime availability exposed through `/ocr-check`" | "OCR always available", "reads any scanned PDF" | Needs the tesseract binary; `/ocr-check` is authoritative (see #20) |
| A8 | Maturity | "benchmark-backed prototype / hackathon build" | "production-grade", "enterprise-ready" (see #17) | Prototype; demo hardening, not production security |

## Do NOT say (banned phrases — grep-enforced)

These must never appear in README, benchmark report, deck source, detailed PDF
source, or video script:

- "real-world accuracy"
- "real unseen datasheets"
- "field-validated" / "field validated"
- "production-grade"
- "100% recall"
- "zero false positives overall"
- "customer ROI"
- "fully independent benchmark"
- "two-reviewer adjudicated"
- "stored primary-source benchmark"
- "OCR works everywhere"
- "reads any scanned PDF"
- "pixel-perfect OCR" / "lossless OCR"
- "100% OCR accuracy"
- "failover improves accuracy" / "more accurate with failover"
- "never goes down" / "100% uptime"
- "secure by default" / "penetration-tested" / "zero vulnerabilities"
- "DDoS protection" / "hardened against all attacks"
- "five AI agents" / "5 autonomous agents" / "fully autonomous"
- "all graph edges standards-cited" / "every edge is standards-cited"

## Safe framing (paste-ready)

> "On the independent, frozen, provenance-tracked **ps4_external_v1** benchmark
> (53 team-authored spec–submittal pairs, 129 single-author-frozen labels, 17
> systems, 64 clean negatives), Pramaan's featured configuration
> (`gemini-3.1-flash-lite`, 3-pass) reports **mean semantic recall 0.862
> (0.841–0.873), precision 0.953, F1 0.905, and 0 false alerts on the 64 clean
> negatives**, vs a deterministic rule baseline of 0.111. Fixtures are
> team-authored (10 derived from public primary sources, 5 with verified URLs);
> labels are single-author frozen with two-person adjudication and stored
> primary-source PDFs still pending. This is a benchmark result, **not** a
> real-world-accuracy or field-validation claim."
