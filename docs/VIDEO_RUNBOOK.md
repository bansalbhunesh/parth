# Pramaan — 3–4 Minute Pitch Video Runbook

> You speak; this document runs the shoot. The words are in [`PITCH.md`](../PITCH.md)
> (timed to ~3:30) — rehearse them twice out loud before recording anything.

## 0. Go / no-go (do not record before all three)

1. `make verify-live` → **`GREEN -- demo away.`** (If the LLM path is red, the
   star scene will silently record the reduced rule-fallback result instead of the
   full reasoning moment — the exact failure this gate exists to catch.)
2. One warm-up Analyze in the UI (absorbs the Render cold start).
3. Close everything else: notifications off (Win+N → focus assist), spare tabs
   closed, browser at 100% zoom, 1920×1080 display.

## 1. Recorder settings

- **OBS Studio** (or Xbox Game Bar Win+Alt+R if OBS is overkill):
  Display Capture · 1920×1080 · 30 fps · mic input checked against a 10-second
  test clip (listen back — laptop fans and keyboard clicks are the usual spoilers).
- Record in one take if you can; otherwise cut at the scene boundaries below —
  they're written to be splice-safe.
- Have water. Speak ~10% slower than feels natural.

## 2. Scene map (screen action ↔ script section)

| # | Time | On screen | You say (PITCH.md §) | Splice-safe cut |
|---|---|---|---|---|
| 1 | 0:00–0:20 | Title slide of `presentation.html` (slide 1, full screen) | §[0:00–0:20] Problem / stakes | ✂ |
| 2 | 0:20–0:50 | Slide 2–4 (the three-documents problem, the requirement→deviation→Cx→window solution) | §[0:20–0:50] What Pramaan does | ✂ |
| 3 | 0:50–1:30 | **THE STAR**: `/judge` → Load deviation demo ★ → Analyze → let the stream visibly run → point (cursor) at: the 2N→N+1 redundancy drop, the battery-autonomy shortfall (10→8 min), each cited to the clause and mapped to the Cx test; then the provenance chip (live-model vs rule floor). Then Load compliant demo ✓ → zero deviations | §[0:50–1:30] Live demo flow | do NOT cut inside |
| 4 | 1:30–2:00 | Scroll the findings; trace requirement → deviation → Cx test → schedule risk; flash `PROVENANCE.md` in a second tab | §[1:30–2:00] Evidence chain | ✂ |
| 5 | 2:00–2:35 | Switch to `/evidence` (or slide 7): the frozen v1.2 benchmark card — 53 pairs, 129 labels, recall 0.862 vs rule baseline 0.111 | §[2:00–2:35] Benchmark result | ✂ |
| 6 | 2:35–3:05 | Architecture slide / interactive diagram (one LLM core + deterministic services + 2 cycles); flash `/llm-check` for the failover story | §[2:35–3:05] Architecture and reliability | ✂ |
| 7 | 3:05–3:30 | Slide 8 (Trust & limitations) → end on Judge Mode / `/evidence` with the limitation labels visible. Say the safe line verbatim | §[3:05–3:30] Limitations, roadmap, close | ✂ |

**Scene 3 insurance:** record the star scene (scene 3) TWICE before judging the
take. If the LLM path degrades mid-recording (429), STOP — re-run `make verify-live`,
swap key if needed, redo. Never ship a take where the fallback banner is visible
unless you're narrating the resilience story on purpose.

**Scene 6 setup (optional):** if you want the green scoreboard on camera for the
reliability beat, start `make verify` in a visible terminal ~90 s before scene 6
so it catches the final green summary, not the wait — alongside the `/llm-check`
failover status.

## 3. After the take

1. Trim lead-in/out; export 1080p H.264, target < 500 MB.
2. Watch it once end-to-end with audio. Check: no notification popped during
   scene 3; the **2N→N+1 redundancy drop** and the **10→8 min battery-autonomy
   shortfall** are legible, and the provenance chip is readable.
3. Upload: YouTube → **Unlisted** → title
   `Pramaan — EPC Deviation Intelligence (ET AI Hackathon 2.0, PS4)`.
4. Paste the link into:
   - README "⚡ Judges: start here" §3 (replace the placeholder),
   - `docs/SUBMISSION_CHECKLIST.md` row 2,
   - the Unstop form field.

## 4. Fallback plan

If the live LLM path cannot be made green on recording day (key exhausted,
gateway down): record scene 3 against a **local backend** (`make run` with a
working key in `.env`) — same UI, same documents, honest footage — and say
"running locally" out loud. Never splice stale footage of a different build.
