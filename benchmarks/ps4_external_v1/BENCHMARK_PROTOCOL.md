# Benchmark Protocol — ps4_external_v1

## Why this benchmark exists
The synthetic 12-project portfolio scores 1.000 **by construction** (it grades
against deviations it seeded itself), so it proves plumbing/breadth, not external
accuracy. This benchmark is the honest counterweight: an independent set of
document pairs with **frozen labels authored before model runs**, one-to-one
scoring, clean negatives, adversarial cases, and full provenance — designed so a
skeptical judge can reproduce and trust the numbers.

## Source selection
- Prefer **primary, legally reusable** public vendor/government documents. Record
  URL, owner, retrieval date, version, SHA-256, and license/usage basis in
  `manifest.csv`. Store the immutable file under `sources/raw/` and a normalized
  text extract under `sources/normalized/`.
- Where a primary file cannot be legally stored, use a **team-authored fixture**
  whose values are *cited from* public figures, and label its origin honestly
  (`team_authored_from_public_values`). Never call it a "real datasheet".
- **Never** copy proprietary standard text (Uptime, TIA, BICSI, NFPA, ...). Name
  the standard and paraphrase; cite it, don't reproduce it.
- Documents with unclear license go in origin `unknown_do_not_use_for_claims` and
  must not feed a headline metric.

## How labels are frozen
1. Author owner requirement + vendor submittal + label(s) per pair.
2. Labels carry `status: frozen` and required/submitted evidence spans.
3. `labels/labels_freeze.json` records `benchmark_version`, `frozen_on`, counts,
   and `labels_freeze_sha256` (an order-independent hash of every label).
4. A benchmark run records the label hash it scored against. If labels change,
   the hash changes and the report flags a version mismatch. **Editing labels
   after a run requires bumping `benchmark_version`.**

## Contested labels
`ambiguous_contested` labels (e.g. a supply-air setpoint within *allowable* but
above *recommended*) are **excluded from primary metrics** unless
`include_contested_in_primary: true`. They are always reported separately so the
benchmark is never a suspicious 1.000.

## Clean negatives
`clean_negative` labels assert a value is compliant and must **not** be flagged.
A predicted finding touching a negative-control parameter is a **false alert**;
the report gives the clean-negative false-alert rate.

## Model runs
- `--mode rule` calls the deterministic rule detector only (no LLM, no key).
- `--mode llm` calls the live analysis path; a pair whose analysis fell back to
  the rule engine or errored is recorded `not_run` for the LLM metric — never
  fabricated. `--repeat N` runs each pair N times to expose variance.
- Each run writes `run_config.yaml`, `predictions.jsonl`, `per_pair_results.csv`,
  `summary.json`, `errors.jsonl` under `runs/<date>_<provider>_<model>_runK/`.

## How not-run / timeouts are counted
- **Primary recall** counts `not_run`/timeout pairs' positive labels as **misses**.
- **Secondary recall** excludes `not_run` pairs and is clearly labeled as such.
- Timeout/error rate and latency p50/p95 are reported alongside.

## Scoring
- One-to-one (greedy bipartite) matching: one finding → at most one label, one
  label → at most one finding. FP = unmatched findings (never negative).
- Both **exact** (numeric/value-anchored) and **semantic** (parameter + value
  overlap) match scores are reported.
- Per-difficulty and per-system breakdowns are produced.

## Reproduce
```
python scripts/benchmark_manifest_check.py
python scripts/benchmark_hash_sources.py
python scripts/benchmark_ps4_external.py --mode rule
python scripts/benchmark_report.py
```

## Limitations and non-claims (v1 seed)
- Seed pairs are **team-authored**, not downloaded primary sources → **no external
  accuracy claim** yet.
- Labels are **single-author frozen**; two-reviewer adjudication is a backlog step.
- OCR/vision and several systems (transformer, chiller, pdu, bms, fire, ...) are
  **backlog**, not yet covered.
- The rule-engine baseline only fires on the numeric/omission parameters it knows;
  low rule recall on reasoning cases is expected and honest.

## Acquisition backlog (to reach 40–50 pairs / 60–80 sources / 120–180 labels)
Primary-source targets (search queries; record URL + retrieval date + SHA-256 when obtained):
- "Vertiv Liebert GXT5 UPS data sheet SL-70719 pdf" (UPS runtime/efficiency)
- "Cummins QSK60-G6 standby data sheet pdf" (generator emissions/fuel)
- "ABB MNS low voltage switchgear system guide pdf" (Icw / Form)
- "Schneider Canalis KTA busway catalogue Icw pdf" (busway withstand)
- "Tate ConCore 1250 access floor data sheet pdf" (concentrated load)
- "Raritan PX3 rack PDU data sheet DPC-RAR-PX3 pdf" (metering/switching)
- "Xtralis VESDA VLC LaserCOMPACT product guide pdf" (ASD coverage)
- "Distech ECB-600 BACnet controller datasheet pdf" (BMS profile)
- "STULZ CyberAir 3 DX CRAH data sheet pdf" (cooling capacity/redundancy)
- "US EPA 40 CFR 60 stationary CI engine tier table" (government, emissions)
- "NFPA 855 energy storage code summary (non-proprietary)" (li-ion fire area)
- "IEC 61439-2 / 61641 scope summary (non-proprietary)" (switchgear)
Systems still needed: transformer, chiller, pdu_rpp, bms, fire_suppression,
ats_sts, cooling_tower, rack_aisle, networking. Difficulties still needed:
`table_or_layout`, `scanned_or_image` (OCR/vision assets).
