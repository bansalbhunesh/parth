# Dev corpus v1 — coverage-matrix development fixtures (NOT a benchmark)

**Purpose.** The frozen `ps4_external_v1` error analysis and the 2026-07-15
coverage-matrix experiment ended with a binding instruction: *"Any next
omission experiment should be developed on a separate development corpus and
frozen before returning to this benchmark. Do not tune further to named frozen
pairs."* This directory is that separate corpus. Future omission-prompt
candidates may be iterated **here and only here**; the frozen benchmark is
reserved for one declared shot per frozen candidate.

**What it is.** 14 team/AI-authored spec–submittal pairs over equipment
systems deliberately **absent from the frozen benchmark's 17 systems**
(lightning protection, earthing grid, fuel polishing, water leak detection,
hydrogen detection, EPO, load bank, condenser-water treatment, SCR/DEF
emissions, acoustic attenuation, fire-rated transits). Labels follow the
frozen schema and are scored with the frozen benchmark's exact one-to-one
semantic matcher (`scripts/benchmark_lib.py`) via
`scripts/dev_corpus_eval.py`.

**Composition (25 frozen labels):**

| Class | Pairs | Why it exists |
|---|---|---|
| Omission positives | 5 | The failure mode the coverage matrix targets (spec constrains a parameter; submittal silent) |
| Clean negatives — restatement traps | 6 | The failure mode that blocked v1.7's promotion: compliant values restated in different units, summary tables, compliance-by-reference clauses, or exceeding phrasing |
| Value-deviation positives | 3 | Regression check that ordinary detection (direct, adversarial, derived) is not lost |

**Rules.**

1. Never copy, paraphrase, or derive content from named frozen
   `ps4_external_v1` pairs. This corpus exists so tuning never touches them.
2. Results here are development signals only — they are never quoted as
   benchmark numbers, never enter README/claims surfaces, and never substitute
   for a frozen-benchmark run.
3. When a candidate is promoted to a frozen one-shot attempt, record this
   corpus's final dev results in the experiment report alongside the frozen
   run so the tuning trail is auditable.
4. `runs/` outputs are provenance artifacts (config, per-pair results,
   prompt version, provider, git revision). Keep candidate outputs on their
   experiment branch; do not automatically add them to production `main`.

**Freeze.** Corpus version `1.0.0` was frozen on 2026-07-16. Its immutable
counts and hashes are recorded in `labels_freeze.json`. Candidate-specific
results and promotion decisions belong on their experiment branch.

**Provenance.** Fixtures are team/AI-authored for development, values chosen
from public engineering ranges; they are not vendor documents and carry no
claim of field realism beyond plausibility.
