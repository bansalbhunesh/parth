# Real-World Eval — 6 Sourced Datasheet Pairs

The numbers that matter most: **a recall/precision result on real third-party
equipment, not the synthetic benchmark.** Each pair was analysed live by
`gemini-2.5-flash` over the raw documents; results below are from those runs
(individually, this session). Sources for every value: [`../data/samples/real/PROVENANCE.md`](../data/samples/real/PROVENANCE.md).

## Result

| Pair | System | Expected | LLM recovered | Mode | Time |
|------|--------|----------|---------------|------|------|
| 1 | UPS + Generator | 5 | **5** (battery 10→7, eff 96→95.9, THD omission, EPA Tier4→2, fuel **38.83h** derived) | llm | 17 s |
| 2 | Cooling (CRAC) | 3 | **3** (N+2→N+1, **R-410A GWP 2088**, 200→180 kW) | llm | 22 s |
| 3 | LV Switchgear | 3 | **3** (Icw 65→50 kA, Form 4b→3b, IEC 61641 omission) | llm | 18 s |
| 4 | Fire suppression | 1 | **1** (**FM-200 GWP 3220**) | llm | — |
| 5 | Chiller | 1 | **1** (**R-134a GWP 1430**) | llm | — |
| 6 | Battery | 2 | **2** (life 10→3–5 yr, monitoring omission) | llm | — |
| | **TOTAL** | **15** | **15** | | |

- **Recall = 15/15 = 1.000** on real, sourced datasheets.
- **0 false positives** — every true negative was correctly cleared: IP54 (≥IP42),
  415 V (=415 V), 10-second start (NFPA 110 met), EC fans (compliant), 24 °C
  supply (≤27 °C). The model did **not** over-flag compliant or exceeding values.
- **Genuine reasoning, not matching:** it derived `4000 ÷ 103 = 38.83 h`, and
  recalled three refrigerant/agent GWPs (2088, 1430, 3220) the datasheets never
  stated.

## Baseline (LLM off) — "no silent zeros"

With the LLM disabled, the rule-based fallback still recovered **2/15** from the
real prose (battery 10→7, efficiency 96→95.9 on the power pair) — the rest require
reasoning (arithmetic, GWP recall, Form/Icw judgement). So the demo never returns
zero, and the gap (2 → 15) is exactly the value the reasoning layer adds.

## Reproduce

```bash
export GEMINI_API_KEY=<a key with quota>   # free tier = 20 req/day per model
export PRAMAAN_LLM=gemini GEMINI_MODEL=gemini-2.5-flash
python - <<'PY'
import pathlib; from backend.analyze import run_analysis
d=pathlib.Path("data/samples/real")
for sf,su in [("design_basis_helios.md","submittal_gxt5_qsk60.md"),
              ("design_basis_cooling.md","submittal_stulz_cyberair.md"),
              ("design_basis_switchgear.md","submittal_abb_mns.md"),
              ("design_basis_fire.md","submittal_fm200.md"),
              ("design_basis_chiller.md","submittal_chiller_r134a.md"),
              ("design_basis_battery.md","submittal_vrla.md")]:
    r=run_analysis((d/sf).read_text(encoding="utf-8"),(d/su).read_text(encoding="utf-8"),"X")
    print(sf, r.mode, len(r.deviations))
PY
```

> Caveat: free-tier `gemini-2.5-flash` allows **20 requests/day per project**; a
> single-batch re-run of all six needs a key with remaining quota (or a paid tier).
> The per-pair results above were each captured under `mode:"llm"`.
