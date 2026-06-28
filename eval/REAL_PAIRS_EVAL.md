# Real-World Eval — 8 Sourced Datasheet Pairs

The number that matters most: **a recall result on real third-party equipment, not
the synthetic benchmark.** All eight pairs were analysed by `gemini-2.5-flash` over
the raw documents in a **single batch run (8/8 returned `mode:"llm"`)**. Sources for
every value: [`../data/samples/real/PROVENANCE.md`](../data/samples/real/PROVENANCE.md).

## Result — 17/17 recall, 0 false positives

| # | System | Real source | Deviation (LLM-recovered) |
|---|--------|-------------|---------------------------|
| 1 | UPS + Generator | Vertiv GXT5 + Cummins QSK60 | battery 10→7 min · eff 96→95.9% · THD omission · **EPA Tier 4→2** · fuel **48→38.83 h (derived)** |
| 2 | Cooling (CRAC) | STULZ CyberAir 3 DX | N+2→N+1 · **R-410A GWP 2088** · 200→180 kW |
| 3 | LV Switchgear | ABB MNS | Icw 65→50 kA · Form 4b→3b · IEC 61641 omission |
| 4 | Fire suppression | FM-200 / Novec | **FM-200 GWP 3220** |
| 5 | Chiller | Carrier-class | **R-134a GWP 1430** |
| 6 | Battery | EUROBAT VRLA | life 10→3–5 yr · monitoring omission |
| 7 | Transformer | IEC 60076-11 dry-type | **harmonic rating K-13→K-1** |
| 8 | Cabling | NFPA 75 / TIA-942 | **plenum rating CMP→CMR** |
| | **TOTAL** | **8 pairs** | **17 / 17 recovered** |

- **Recall = 17/17 = 1.000** on real, sourced datasheets, in one batch.
- **0 false positives** — every compliant/exceeding value was correctly cleared
  (IP54 ≥ IP42, 415 V, 10 s start, EC fans, 24 °C supply, Class-F insulation,
  Dyn11, 6% impedance, Cat6A, OM4/OS2). The model does **not** over-flag.
- **Genuine reasoning:** it derived `4000 ÷ 103 = 38.83 h` and recalled three
  refrigerant/agent GWPs (2088, 1430, 3220) the datasheets never stated.

## Baseline (LLM off) — "no silent zeros"
With the LLM disabled, the rule-based fallback still recovers the headline numeric
shortfalls (e.g. battery 10→7, efficiency 96→95.9) from real prose — the demo never
returns zero. The remaining findings (GWP recall, arithmetic, Form/Icw/K-factor,
CMP/CMR) require reasoning — exactly the value the LLM layer adds.

## Reproduce
```bash
export GEMINI_API_KEY=<key with quota>     # free tier = 20 req/day per model
export PRAMAAN_LLM=gemini GEMINI_MODEL=gemini-2.5-flash
python - <<'PY'
import pathlib; from backend.analyze import run_analysis
d=pathlib.Path("data/samples/real")
import os
pairs=sorted(set(p.name.replace("design_basis_","").replace("submittal_","")
        for p in d.glob("*.md")))  # see PROVENANCE.md for the 8 spec/submittal pairs
PY
```
> The 8 spec↔submittal filenames are listed in `PROVENANCE.md`. Each returned
> `mode:"llm"` in the batch run above.
