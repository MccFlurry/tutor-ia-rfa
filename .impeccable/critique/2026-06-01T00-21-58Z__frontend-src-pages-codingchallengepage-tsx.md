---
target: frontend/src/pages/CodingChallengePage.tsx
total_score: 34
p0_count: 0
p1_count: 0
timestamp: 2026-06-01T00-21-58Z
slug: frontend-src-pages-codingchallengepage-tsx
---
## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Loading, "evaluando…", score, toasts are good; the eval result isn't scrolled into view after submit |
| 2 | Match System / Real World | 4 | Clear Spanish, difficulty labels, breadcrumb, familiar editor |
| 3 | User Control and Freedom | 3 | Regenerate confirms; but "Intentar de nuevo" silently wipes the student's code, and nothing persists a draft |
| 4 | Consistency and Standards | 3 | "Intentar de nuevo" resets here but regenerates on QuizPage; score uses `text-warning` vs `text-warning-foreground` elsewhere |
| 5 | Error Prevention | 3 | Empty-code check + regenerate confirm are good; the destructive reset has no confirm and there's no autosave |
| 6 | Recognition Rather Than Recall | 4 | Description, hints, results, best score all visible |
| 7 | Flexibility and Efficiency | 4 | Ctrl+Enter submit, Monaco, regenerate — strong accelerators |
| 8 | Aesthetic and Minimalist Design | 3 | Clean two-column; difficulty "hard" in destructive red, mid-band score color is low-contrast |
| 9 | Error Recovery | 3 | ErrorState exists but conflates error with not-found and offers only "Volver" (no Reintentar) |
| 10 | Help and Documentation | 4 | Description + hints + AI feedback with strengths/improvements + nudges |
| **Total** | | **34/40** | **Good (upper-mid)** |

## Anti-Patterns Verdict

**AI-generated?** No. `detect.mjs --json` → `[]`. A genuinely capable coding surface: Monaco lazy-loaded behind Suspense with a fallback, a real Ctrl+Enter command, a regenerate **confirmation dialog** that warns about losing code, AI evaluation with a score, markdown feedback, and structured strengths/improvements. No gradient, eyebrow, side-stripe, or glass.

**LLM assessment:** The problems aren't slop; they're about **protecting the student's work** (a mislabeled reset wipes code, and nothing persists a draft), plus the familiar resilience and result-visibility gaps.

**Visual overlays:** No browser-automation tool in this environment → CLI detector + source review only (fallback signal, no overlay claimed).

## Overall Impression

The most feature-complete surface this session — and it clearly *thought about* code loss in one place (the regenerate dialog warns and confirms). But that care isn't applied consistently: the post-result "Intentar de nuevo" button silently resets the editor to the initial code, and a reload or navigation loses everything because the draft isn't persisted (QuizPage persists; this doesn't). Add work-protection and the resilience/visibility fixes and it's clearly Excellent.

## What's Working

1. **Serious editor ergonomics.** Monaco is lazy-loaded (kept off the initial bundle) behind a Suspense fallback, themed to light/dark, with a real Ctrl+Enter submit command and a visible hint. That's power-user respect done right (Flexibility = 4).
2. **The regenerate flow is careful.** A confirmation dialog explicitly warns "Perderás el código que has escrito" before regenerating, and the AI-vs-fallback outcome is toasted. This is exactly the work-protection the rest of the page needs.
3. **Rich, structured feedback.** The AI evaluation shows a score, markdown feedback, and separate "Puntos fuertes" / "Áreas de mejora" lists, plus a reinforcement nudge — genuinely useful for learning.

## Priority Issues

**[P2] "Intentar de nuevo" silently discards the student's code.**
- **Why it matters:** After a result, `handleRetry` does `setCode(challenge.initial_code)` — it wipes whatever the student wrote back to the starter code, with no confirmation. A student who scored 70 and wants to improve will reasonably click "Intentar de nuevo" and lose their work; the button that *keeps* their code is the other one ("Reenviar código"). The label invites the destructive action. (Regenerate confirms code loss; this doesn't.)
- **Fix:** Don't reset on retry — keep the student's code and just clear the result (let them edit and resubmit). If a true "reset to starter" is wanted, make it a separate, clearly-labelled action with a confirm.
- **Suggested command:** `/impeccable clarify`

**[P2] The typed code isn't persisted — a reload or navigation loses it.**
- **Why it matters:** Unlike QuizPage (localStorage), the editor content lives only in component state. A refresh, an accidental back, or a tab close discards real effort. The regenerate dialog warns about loss, but the much more common reload does not.
- **Fix:** Persist the draft per challenge in localStorage (debounced), rehydrate on load, and clear it on a successful submit — mirroring `quizPersistence`.
- **Suggested command:** `/impeccable harden`

**[P2] The AI evaluation isn't brought into view after submit.**
- **Why it matters:** On mobile (single column) the result renders in the first column, *above* the editor; the student submits from the button at the bottom and the feedback appears far up the page. A toast fires, but the detailed score/strengths/improvements (the whole point) are off-screen.
- **Fix:** On a successful submit, scroll the result card into view (and/or move focus to it) so the feedback is seen.
- **Suggested command:** `/impeccable harden`

**[P2] Load failure is reported as "Desafío no encontrado" with no retry.**
- **Why it matters:** `isError || !challenge` → a `notFound` ErrorState with only "Volver" (`navigate(-1)`). A transient/network failure is mislabeled as missing, there's no "Reintentar", and `navigate(-1)` can land anywhere. This is an expensive AI surface where a retry matters.
- **Fix:** Expose `refetch`; on `isError` show a generic/serviceUnavailable error with a "Reintentar"; reserve "no encontrado" for a genuine 404, with a deterministic back target.
- **Suggested command:** `/impeccable harden`

**[P3] Difficulty "hard" uses destructive red; mid-band score color is low-contrast.**
- **Why it matters:** `hard` → `text-destructive` brushes the red-reservation rule (red = destructive/Peru, not a difficulty), and the 60-79 score uses bare `text-warning` (amber) which is low-contrast on the light card, unlike the `text-warning-foreground` used for the "Áreas de mejora" heading.
- **Fix:** Give "hard" a non-red treatment (heritage or a neutral strong tint); use `text-warning-foreground dark:text-warning` for the mid-band score.
- **Suggested command:** `/impeccable colorize`

**[P3] Best score can read stale after a new submission.**
- **Why it matters:** Submit success doesn't invalidate `['coding-best', cid]`, so "Mejor puntuación" won't reflect a new high score until a refetch.
- **Fix:** Invalidate the best-score query in the submit `onSuccess`.
- **Suggested command:** `/impeccable harden`

## Persona Red Flags

**Valentina (student investing effort):** writes a solution, scores 70, clicks "Intentar de nuevo" to improve — and her code is wiped to the starter. The expensive part (her work) is the easiest to lose.

**Casey (distracted mobile):** submits from the bottom button; the AI evaluation appears far above the editor with only a toast to hint at it — she may never scroll up to read why she scored what she did.

**Alex (power user):** loves Ctrl+Enter and Monaco, but a mid-problem reload wipes everything — no draft persistence on the one page where work is most valuable.

## Minor Observations

- The EditorFallback uses `bg-foreground/90` with `text-muted-foreground`, which is low-contrast while the editor chunk loads (brief).
- Two action buttons after a result ("Intentar de nuevo" / "Reenviar código") are equal-weight; once retry stops wiping code, their roles should be clearly distinct.

## Questions to Consider

- What should "Intentar de nuevo" do after a result — keep the student's code (edit + resubmit) or reset to starter? Today it resets, which is the surprising, lossy choice.
- Should the editor autosave a draft per challenge like the quiz does, so a reload never costs work?
- After the AI returns a score, how do we guarantee the student actually sees the feedback, especially on mobile?
