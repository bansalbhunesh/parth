# Prompt-Naive Eval Tier — Pairs Built From Documents That Never Touched the Prompt

Two pairs. Both genuinely new: neither the specific parameters, products, nor
numeric thresholds here appear anywhere in `../PROVENANCE.md`, the frozen
`benchmarks/ps4_external_v1` corpus, or the reconcile prompt (checked —
`backend/agents/reconciliation.py` contains exactly one embedded example,
"spec says '10 min' and submittal says '7 min'", a generic format
illustration, not a domain-specific answer key; neither pair below uses that
pattern).

**Both sides of both pairs are grounded in verifiable real-world facts** —
the spec side quotes or directly derives from the stored primary-source
regulatory text in `../primary_sources/`, not paraphrase; the submittal side
cites a real, currently-marketed product with a checkable public reference,
following the same citation discipline as `../PROVENANCE.md`.

## Results — live-verified against the deployed backend, not simulated

Both pairs were run against `https://parth-1-ma30.onrender.com/analyze` on
2026-07-11 (not the local offline rule engine — see the honesty note below on
why). Raw responses, including `request_id` and `input_hash` for anyone who
wants to reproduce the call:

| Pair | Result | Mode | Latency | request_id |
|---|---|---|---|---|
| Fire pump driver | **0 deviations (compliant)** | `llm` (gemini-2.5-flash, not rule-floor) | 9,961 ms | `9864aa03f6b44b06b89516b215e1ea46` |
| Auxiliary cooling | **0 deviations (compliant)** | `llm` | 1,504 ms | `a05fcfe058614d438530844a28648012` |

Reproduce either call:
```bash
curl -sS -X POST https://parth-1-ma30.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d "$(python -c "import json; print(json.dumps({'spec_text': open('data/samples/real/held_out/design_basis_firepump.md', encoding='utf-8').read(), 'submittal_text': open('data/samples/real/held_out/submittal_firepump_clarke_ju4h.md', encoding='utf-8').read(), 'system_id': 'MERIDIAN'}))")"
```
(swap the two file paths for the auxiliary-cooling pair)

## Pair 1 — Fire pump diesel driver (compliant)

`design_basis_firepump.md` quotes 40 CFR 60 Subpart IIII Table 4 verbatim
(2011+ row, 56≤kW<75 class: NMHC+NOx ≤ 4.7 g/kW-hr, CO ≤ 5.0, PM ≤ 0.40).
`submittal_firepump_clarke_ju4h.md` cites a real Clarke Fire Protection
Products engine (JU4H-UFADJ2, John Deere 4045HF280-series base, 99 BHP/74 kW,
EPA Family CJDXL04.5141, Certificate CJDXL04.5141-027, 2012 model year) from
Clarke's own published Tier 3 Certified Engines summary. A 2012-model-year
certification against this power class implies compliance with the 2011+
Table 4 row — the model correctly found no deviation.

**What is not claimed:** the exact measured g/kW-hr test result for this
engine family was not located (Clarke's public summary lists certificate
identifiers, not raw numbers); compliance is inferred from what an EPA
certificate legally attests to, not from an independently reproduced test
value. The local deterministic rule engine (`_resilient_fallback`) was also
run and found 0 findings — but it has no rule for NMHC+NOx/CO/PM parameters
at all (its rule table covers UPS runtime, GWP, floor load, busway Icw, and
similar fixed parameter types), so that 0 is "no matching rule," not a
second independent confirmation. Only the live LLM run above is a genuine
verification.

## Pair 2 — Auxiliary/IT-closet cooling (compliant)

`design_basis_auxcooling.md` requires refrigerant GWP ≤ 750, matching the
threshold already established in `../design_basis_cooling.md`.
`submittal_auxcooling_daikin_vrv_r32.md` cites a real Daikin VRV S-series
R-32 unit (RXTA outdoor unit), confirmed R-32-exclusive from Daikin's own
product page. HFC-32's GWP is 677 per the stored primary-source table
(`../primary_sources/40_CFR_98_Table_A-1_GWP.md`) — under the 750 threshold.
The model correctly found no deviation.

## Honest limitation of this tier as it stands

**Both pairs are compliant (true negatives). Neither demonstrates the
pipeline catching a deviation on a document it has never seen.** That is a real gap, not a
rounding error: this tier currently proves "doesn't false-positive on two
real, primary-source-and-vendor-cited compliant configurations," which is
useful but is a narrower claim than "catches real deviations on documents
it has never seen." Constructing a genuine deviation pair here would need
either a real product that's actually non-compliant with a real regulatory
threshold (harder to find publicly — vendors don't advertise
non-compliance) or a defensible project-specific stricter requirement, in
the same spirit as `../design_basis_helios.md`'s Tier 4 choice — neither
was built in this pass rather than force one that wouldn't hold up.
