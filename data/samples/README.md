# Real-Document Demo Samples

These are **realistic engineering documents written in natural prose + table
format** — deliberately unlike the structured generator corpus
(`**UPS-02** — battery_runtime_min: shall be **10 min**`). They prove Pramaan's
reconciliation generalises to documents outside the structured generator corpus,
in formats no regex was tuned for. Drop them into the **Live Analysis** panel (or POST to
`/analyze/upload`) and the LLM recovers the buried non-compliances from scratch.

> Requires an LLM key (the deterministic regex fallback is corpus-specific and
> will **not** parse these natural-language documents — that is the point: only
> real reasoning catches these).

## Pair 1 — UPS (`design_basis_ups.md` vs `vendor_submittal_ups.md`)

| # | Buried deviation | Design basis | Vendor offered | Why a human misses it |
|---|------------------|-------------|----------------|------------------------|
| 1 | **Redundancy topology** | 2N mandatory (Tier IV) | N+1 per bus | Vendor's spec table says "N+1" plainly, but the submittal's cover prose claims it is "**fully compliant**" — the contradiction is two pages apart. |
| 2 | **Battery autonomy** | ≥ 10 min at **end of life**, one string out | **8 min** at *beginning of life* @ 25 °C | 8 < 10 already; worse, it's quoted at BoL/25 °C, so real EoL autonomy is even lower. The design basis explicitly forbids BoL-only evidence. |

**Compliant rows (must NOT be flagged — precision check):** efficiency 96.5% ≥ 96.0%,
input THD < 3%, acoustic 71 ≤ 72 dB(A), module rating 1000 kW.

Expected result: **2 deviations caught, 0 false positives.**

## How to demo it

**In the dashboard (easiest):** open the **Live Analysis** section →
click **"Load deviation demo ★"** → **Analyze**. The LLM streams its reasoning
and surfaces the buried deviations. (The plain **"Load example"** button uses
the structured corpus format — a regex can catch that; a realistic prose submittal
needs reasoning. Showing both, in that order, is a strong narrative: *"a regex catches
the clean example — but a realistic vendor submittal? Only reasoning finds this."*)

**Via the API:**
```bash
curl -X POST $API/analyze -H "Content-Type: application/json" \
  -d "{\"spec_text\": \"$(cat data/samples/design_basis_ups.md)\",
       \"submittal_text\": \"$(cat data/samples/vendor_submittal_ups.md)\"}"
```

> **Demo prerequisite:** the backend serving the demo must have LLM credentials
> in its environment (`GEMINI_API_KEY`, or the `PRAMAAN_LLM=openai` + `OPENAI_*`
> gateway vars — see `render.yaml`). Without a key the analyzer degrades to a
> deterministic regex that is corpus-specific and returns **0** on these prose
> documents. For judging, set the key on the deployed backend, or run locally
> with the key exported.

## Pair 2 — REAL vendor datasheet vs `design_basis_edge.md`

For the strongest "is this real data?" answer, pair an **actual downloaded
vendor UPS datasheet** (the submittal) against `design_basis_edge.md` (the spec).
`design_basis_edge.md` is scaled for an edge / network-room UPS (≤ 6 kW,
single-phase), so a real compact UPS datasheet pairs cleanly without a
scale mismatch. The deviations Pramaan flags are then **genuinely real** — the
product's own published specs fall short of the requirement.

Typical real shortfalls a compact UPS datasheet will trigger against this basis:
- **Topology / mode (2.1, 2.4):** headline efficiency quoted in ECO or line-
  interactive mode, not online double-conversion.
- **Efficiency (2.4):** online efficiency below 96%.
- **Autonomy (2.5):** internal-battery runtime under 10 min at full load.
- **Redundancy (2.7):** a single tower unit is not N+1.

Download a real datasheet (e.g. Vertiv Liebert GXT MT+ / MTX+ / ITA), drop it in
as the **submittal**, use `design_basis_edge.md` as the **spec**, and Analyze.
Open the datasheet's own spec table first and note which one or two numbers you
want to highlight — then the demo is verifiably real, end to end.

## Pair 3 — Standby Diesel Generator (`design_basis_generator` vs `vendor_submittal_generator`)

A second self-contained demo pair (markdown + PDF), different domain, same idea:
a realistic design basis vs a vendor datasheet that stamps itself "fully
compliant" while burying real shortfalls.

| # | Buried deviation | Design basis | Vendor offered |
|---|------------------|-------------|----------------|
| 1 | **Emissions tier** | EPA Tier 4 Final / Stage V | EPA Tier 2 |
| 2 | **On-site fuel autonomy** | ≥ 24 hours @ 100% | 8 hours (sub-base tank) |
| 3 | **Start / load acceptance** | ≤ 10 seconds | 30 seconds |
| 4 | **Redundancy** | N+1 | Single set (N) |

**Compliant rows (must NOT be flagged):** rated power 2000 kW, 11 kV / 50 Hz,
acoustic 82 ≤ 85 dB(A), governor ±0.25%.

Expected: **4 deviations, 0 false positives.** Upload the two PDFs (or paste the
two markdown files) into Live Analysis → Analyze.

## Why this matters for judging

- The 12-project synthetic corpus proves *breadth and reproducibility* — it
  recovers all seeded deviations by construction (a breadth check, not an accuracy
  score). The accuracy signal is the frozen ps4_external_v1 benchmark (v1.2):
  recall 0.862, precision 0.953, FAR 0.000.
- **These samples prove it works on a document a vendor would actually send** —
  marketing language, a false "fully compliant" claim, a beginning-of-life vs
  end-of-life trap. That is the question every judge asks: *"does it work on
  realistic data?"* — and you can answer it live.
