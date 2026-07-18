# Pramaan frontend design system — "The instrument of record"

This document is the working brief for the 2026-07 structural redesign. It records
what was studied, what was decided, and the rules every page follows, so the
interface reads as one deliberate system rather than accumulated screens.

## 1. Reference study (structure, not colors)

Six exceptional product sites were examined for *structural* patterns before any
code changed. What each contributed:

| Reference | Pattern adopted |
|---|---|
| Linear | Numbered workflow phases, each: headline → one line → demonstration → expandable depth. Small-caps labels as wayfinding. |
| Stripe | Complexity escalates down the page — outcomes first, infrastructure numbers deep. Proof woven into prose, not stat-tile walls. Footer as sitemap. |
| Ramp | Metrics presented as attributed narrative vignettes ("325 hours saved"), never bare tiles. Cascading detail: headline → mechanics → use case. |
| Vercel | Theme pairs are designed per-theme, not filtered. Monospace reserved for technical tokens. Case sections demonstrate, not describe. |
| Observable | The hero shows the artifact *and* the mechanism together (output + the code that made it). Depth deferred to links, momentum preserved. |
| Palantir | Restraint itself signals enterprise seriousness. |

Anti-patterns deliberately excluded: card-grid overload, glow blobs, ambient
gradients, glassmorphism, permanent sidebars, dashboards-for-their-own-sake,
scattered micro-animation.

## 2. Subject and thesis

Pramaan's world is the EPC document record: CSI-numbered spec sections
(26 33 53), stamped vendor submittals ("FOR APPROVAL · REV B"), red-pencil
review marks, commissioning scripts with week numbers, RFI logs, audit trails.

**Thesis: the interface is a beautifully typeset engineering dossier operated
like a modern instrument.** Typography does the authority work; documents are
the imagery; drawers pull records forward instead of navigating away.

Signature element: the **annotated document pair** in the overview hero — a spec
clause and a submittal line, typeset as real document fragments, with a
review-red annotation connecting the requirement to the non-conforming value and
its consequence. The product's exact job, shown in its own material, before any
copy.

## 3. Typography

IBM Plex — the one type family designed for technical documentation — used as a
trio with strict role separation:

- **IBM Plex Serif** (300/400/500): editorial display. Headlines, section
  statements. Large sizes at light weights = technical-manual gravitas.
- **IBM Plex Sans** (400/500/600): UI and body prose. 1rem/1.6, measure ≤ 62ch.
- **IBM Plex Mono** (400/500): every value, clause ref, hash, week number,
  kicker. If a number carries evidence, it is set in mono.

Kickers/eyebrows: mono, 0.72rem, uppercase, +0.14em tracking, clause-style
numbering ("01 · Trace") — justified because the overview *is* a sequence (the
judge journey) and spec documents are numbered.

## 4. Color

Two intentionally different rooms, not one palette filtered.

**Light — "Issued for review":** cool drafting-film white ground (a blue-gray
bond, not cream), blue-black drafting ink, faint cool hairlines. Accent =
**review red** (the reviewer's pencil), reserved for deviation marks, the brand
slash, and the primary stamp action. Approval green and hold amber exist only as
status inks. Paper logic: flat surfaces, hairline rules, one quiet shadow level.

**Dark — "Night shift":** deep blueprint slate (never pure black), luminance-
layered panels (the drafting-film logic inverts: documents read like microfiche
— light text on film). Accent shifts to **ember** — the same red family lifted
for dark contrast. Hairlines are low-contrast; elevation comes from surface
luminance steps, not shadows.

All colors are OKLCH tokens; no raw hex/rgb anywhere (enforced by
`scripts/check-design-system.mjs`).

## 5. Layout and rhythm

- Shell 1200px; text measure 720px. Sections breathe: `clamp(88px, 12vw, 148px)`
  vertical padding, separated by hairline rules, never boxed.
- Asymmetric editorial grid: section intros split kicker+headline (5/12) from
  supporting prose (7/12) — the spec-book "clause number | clause text" pattern.
- Information lives in **ledgers** (ruled dl/tables with mono values) and
  **document sheets** (typeset fragments), not card grids.

## 6. Layering and disclosure

- **Dossier drawer** (right panel): any register finding opens its full evidence
  chain — requirement, submittal, consequence, decision window, live blast
  radius from `/projects/{id}/blast-radius/{dev}` — without leaving the page.
- **Ask the record** (global drawer in the top nav): streaming copilot over the
  project record (`/copilot/stream`), with sources and prior-RFI matches, and an
  honest offline state.
- `<details>` disclosure for methodology and assumptions everywhere else.
  Depth is always one deliberate action away, never ambient.

## 7. Motion

Purposeful, sparse, and fully suppressed under `prefers-reduced-motion`:
- Hero annotation draws once on load (~600ms).
- Drawers translate+fade 240ms `cubic-bezier(0.22, 1, 0.36, 1)`.
- Hover states move ≤1px or change ink only. Nothing loops, nothing jitters.

## 8. Information architecture

Shared shell (single header/footer in `app/layout.tsx`):

- `/` **Overview** — thesis, annotated document pair, the 90-second judge
  journey strip, then Trace → Resolve → Register (interactive) → Verify.
- `/judge` **Analyze** — the live workbench: two document sheets, streamed
  reasoning, provenance-honest results, resolution loop.
- `/war-room` **Interventions** — priority brief, decision ledger, blast-radius
  explorer, schedule distribution, long-lead watch.
- `/evidence` **Evidence** — deployment truth, frozen benchmark, verification,
  limitations, sources; archive-index layout with sticky section nav.

Nav accessible names are stable contracts: Overview / Analyze / Interventions /
Evidence.

## 9. Quality floor (enforced by the suite)

One `h1` and one `main` per route; no skipped heading levels; every interactive
target ≥ 44×44px; skip-link first in focus order; keyboard-operable custom
controls; axe serious/critical = 0; no horizontal overflow at 360px; initial JS
≤ 200KB gzip per route; zero non-suppressed motion under reduced-motion; results
never relabel a fallback as live.
