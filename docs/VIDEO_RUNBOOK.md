# Pramaan — 3-Minute Pitch Video Runbook

> You speak; this document runs the shoot. The words are in [`PITCH.md`](../PITCH.md)
> (timed to ~3:00) — rehearse them twice out loud before recording anything.

## 0. Go / no-go (do not record before all three)

1. `make verify-live` → **`GREEN -- demo away.`** (If the LLM path is red, the
   star scene will silently record the 2-finding rule fallback instead of the
   5-finding reasoning moment — the exact failure this gate exists to catch.)
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
| 1 | 0:00–0:20 | Title slide of `presentation.html` (slide 1, full screen) | "The stakes" | ✂ |
| 2 | 0:20–0:40 | Slide 2 (three-documents problem) | "Why it's hard" | ✂ |
| 3 | 0:40–0:55 | Switch to browser: `parth-tan.vercel.app/judge`, already loaded | "What Pramaan is" | ✂ |
| 4 | 0:55–1:50 | **THE STAR**: Load real document ★ → Analyze → let the stream visibly run → point (cursor) at: fuel-autonomy derivation, EPA Tier 2, battery 7v10, efficiency 96v95.9 | "The live demo" | do NOT cut inside |
| 5 | 1:50–2:15 | Scroll the findings; hover the provenance link; flash `PROVENANCE.md` in a second tab | "It's real, and it's honest" | ✂ |
| 6 | 2:15–2:35 | Split view: terminal running `make verify` (started earlier, now at the green summary) beside the dashboard | "Built for the bad day" | ✂ |
| 7 | 2:35–3:00 | Dashboard ROI section → end on Judge Mode with the metric cards | "Impact + close" | ✂ |

**Scene 4 insurance:** record scene 4 TWICE before judging the take. If the
LLM path degrades mid-recording (429), STOP — re-run `make verify-live`, swap
key if needed, redo. Never ship a take where the fallback banner is visible
unless you're narrating the resilience story on purpose.

**Scene 6 setup:** start `make verify` in a visible terminal ~90 s before you
begin scene 6 so the camera catches the final green scoreboard, not the wait.

## 3. After the take

1. Trim lead-in/out; export 1080p H.264, target < 500 MB.
2. Watch it once end-to-end with audio. Check: no notification popped during
   scene 4; the derived **38.8 h** number is legible.
3. Upload: YouTube → **Unlisted** → title
   `Pramaan — EPC Deviation Intelligence (ET AI Hackathon 2.0, PS4)`.
4. Paste the link into:
   - README "⚡ Judges: start here" §3 (replace the placeholder),
   - `docs/SUBMISSION_CHECKLIST.md` row 2,
   - the Unstop form field.

## 4. Fallback plan

If the live LLM path cannot be made green on recording day (key exhausted,
gateway down): record scene 4 against a **local backend** (`make run` with a
working key in `.env`) — same UI, same documents, honest footage — and say
"running locally" out loud. Never splice stale footage of a different build.
