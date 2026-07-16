# Pramaan — 2:50 Pitch Video Runbook

> You speak; this document runs the shoot. The words are in [`PITCH.md`](../PITCH.md)
> (timed to 2:50) — rehearse them twice out loud before recording anything.

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
| 1 | 0:00–0:12 | Title slide, full screen | §[0:00–0:12] Stakes | ✂ |
| 2 | 0:12–0:25 | Requirement → deviation → Cx → decision-window slide | §[0:12–0:25] Promise | ✂ |
| 3 | 0:25–0:55 | **THE STAR**: `/judge` → Load deviation demo ★ → Analyze. Point at 2N→N+1, 10→8 minutes, clauses, Cx tests, provenance, and cache-replay chip if this exact input was warmed up | §[0:25–0:55] Live finding | do NOT cut inside |
| 4 | 0:55–1:25 | In the same result: persist the actual finding → name owner → draft/issue RFI → re-analyze prefilled Revision C → show read-back closure and audit count | §[0:55–1:25] Consequence to closure | do NOT cut inside |
| 5 | 1:25–1:50 | `/evidence`: frozen benchmark card and limitation labels | §[1:25–1:50] Measured evidence | ✂ |
| 6 | 1:50–2:15 | Architecture slide: one LLM reasoning core, deterministic services, cache, rule floor; flash `/llm-check` | §[1:50–2:15] Architecture | ✂ |
| 7 | 2:15–2:38 | Trust/limitations slide: team-authored fixtures, single-author labels, omission and conversion misses | §[2:15–2:38] Boundaries | ✂ |
| 8 | 2:38–2:50 | End on the resolved finding and audit evidence | §[2:38–2:50] Close | ✂ |

**Scenes 3–4 insurance:** record the full analysis-to-closure flow twice. A warm-up
may produce a **Verified cache replay**; that is truthful and safe to narrate, but
never call it a fresh model call. If the provider degrades and the deterministic
floor answers, say so. Never relabel cached or fallback output as live reasoning.

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
