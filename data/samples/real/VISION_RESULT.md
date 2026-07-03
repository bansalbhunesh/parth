# Vision Result — Pramaan reads a datasheet *image*, not text

> **The claim:** Pramaan doesn't only parse text and OCR. Given a vendor
> submittal **as an image** — a datasheet page, a table, a drawing — it reads
> the values *directly from the picture* with Gemini vision and reconciles them
> against the spec. This is the capability, proven on a real document, verified
> 2026-07-03.

## What was run

- **Spec (text):** [`design_basis_switchgear.md`](design_basis_switchgear.md) —
  the Tier IV LV-switchgear design basis (Icw ≥ 65 kA/1 s, Form 4b, IEC 61641
  arc test, IP42 minimum).
- **Submittal (image):** [`vision/submittal_abb_mns.png`](vision/submittal_abb_mns.png)
  — the ABB MNS submittal **rendered as a stamped datasheet page**. Pramaan was
  given *only the image*; no text transcript. Every value in it is the same
  published ABB MNS figure sourced in [`PROVENANCE.md`](PROVENANCE.md) (pair 3).
- **Path:** `run_vision_analysis()` → `complete_vision()` (Gemini vision,
  `gemini-2.5-flash`). Reproduce: `GET /analyze/vision` (multipart: spec text +
  submittal image), or the snippet at the bottom.

## What it caught — reading from the image (19.4 s, mode `vision`)

| # | Parameter | Required (spec) | Read from the image | Severity |
|---|-----------|-----------------|---------------------|----------|
| 1 | Short-circuit withstand (Icw) | ≥ 65 kA / 1 s | **50 kA / 1 s** | Critical |
| 2 | Internal separation | Form 4b | **Form 3b** | Major |
| 3 | Internal arc containment | Type-tested to IEC 61641 | **"Not included in this proposal"** | Critical |

**3 of 3 genuine deviations recovered from the image** — including finding #3,
a *missing-capability omission* the model had to reason about from the sentence
"…is available as the MNS arc-proof variant but is **not included**." And it did
**not** false-positive on the IP54 rating, which *exceeds* the IP42 requirement
— the no-cry-wolf property holds in vision mode too.

This matches the independently-authored ground truth for this pair exactly (the
same 3 deviations the text path recovers, see `PROVENANCE.md`), so the image
path is not weaker on this document: it reads the picture and reaches the same
verdict.

## Why it's an image, honestly

Real EPC submittals arrive as datasheet pages, tables, and single-line
drawings — often as images inside a PDF. The text and OCR paths handle the
text-bearing cases; **this proves Pramaan also reasons over the pixel content
directly** when the values live in a figure. The rendered page here uses only
already-sourced ABB values so the *result* is verifiable; the *capability* is
general.

## Honest limits

- **Vision is Gemini-only.** Qwen and Groq (the text-failover legs) are not
  multimodal, so a vision call has no LLM failover — if Gemini vision is
  unreachable the path returns `mode: vision-unavailable` (no findings) and the
  caller degrades to the text/OCR path. We therefore ship vision as a **proven
  capability + optional endpoint**, not as a load-bearing live-demo step.
- On free-tier quota, space vision calls like any other (see the demo runbook).

## Reproduce

```python
from backend.analyze import run_vision_analysis
spec = open("data/samples/real/design_basis_switchgear.md").read()
img = open("data/samples/real/vision/submittal_abb_mns.png", "rb").read()
res = run_vision_analysis(spec, img, "image/png", "SWGR")   # needs GEMINI_API_KEY
print(res.mode, len(res.deviations))   # → vision 3
```
