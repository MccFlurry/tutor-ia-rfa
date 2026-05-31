---
target: frontend/src/pages/DashboardPage.tsx
total_score: 35
p0_count: 0
p1_count: 0
timestamp: 2026-05-31T22-23-22Z
slug: frontend-src-pages-dashboardpage-tsx
---
## Design Health Score (re-run after fixes)

| # | Heuristic | Score | Δ | Key Issue |
|---|-----------|-------|----|-----------|
| 1 | Visibility of System Status | 4 | +1 | Loading skeleton, error state, and streak now all communicate; aria-live on the async value |
| 2 | Match System / Real World | 4 | +1 | Duplicate "Logros" label gone; Signal icon reads as a level/tier; "Empezar" is plain |
| 3 | User Control and Freedom | 3 | — | Retry recovers a failed load; exits present; no destructive paths to escape |
| 4 | Consistency and Standards | 4 | +1 | "Ver todos" consistent, gold-on-count drift resolved, stats now a labelled region |
| 5 | Error Prevention | 3 | — | Low-risk overview; nothing destructive to guard |
| 6 | Recognition Rather Than Recall | 4 | — | Everything visible; the next step is always on screen |
| 7 | Flexibility and Efficiency | 3 | — | Hero + recommendations accelerate; no shortcuts, fine for a dashboard |
| 8 | Aesthetic and Minimalist Design | 4 | +1 | Redundant card gone, 0% bars gone, 3-up is calmer; color count is the only remaining watch |
| 9 | Error Recovery | 4 | +3 | Failed fetch → clear message + Reintentar; no more infinite skeleton |
| 10 | Help and Documentation | 2 | — | Still no on-surface help affordance (nudges/tutor live globally) |
| **Total** | | **35/40** | **+7** | **Good (top edge)** |

## Anti-Patterns Verdict

**AI-generated?** No, and cleaner than before. `detect.mjs --json` → `[]` on the rewritten file. The two prior content smells (redundant "Logros" count card; 0% progress bars on recommendations) are gone. No gradient text, no hero-metric template, no side-stripe, no glassmorphism.

**LLM assessment:** The surface now reads as a calm, on-brand student dashboard with a single clear primary action that never disappears. Remaining texture concern is purely the number of data-driven hues on a fully-populated screen (per-module + per-achievement colors alongside gold/green/warning) — defensible as identity, but the ceiling to watch as content grows.

**Visual overlays:** No browser-automation tool available → no live overlay/`[Human]` tab. CLI detector + source review only (fallback signal, not a claimed overlay).

## Overall Impression

The two P1s are closed and it shows: the dashboard is now resilient (fails into a retry, not a frozen screen) and always points forward (the hero never vanishes, even right after completing a topic). Score moved 28 → 35. What's left is genuinely minor — a help affordance gap, a couple of semantic nits, and color discipline to monitor. This is shippable.

## What's Working

1. **Resilience is real now.** `isLoading` → skeleton, `isError || !data` → an EmptyState with a working "Reintentar" (`refetch()`). The infinite-skeleton failure mode is gone — the single biggest fix, and it lifts Error Recovery from 1 to 4.
2. **The path never dead-ends.** The hero always renders: resume an active topic, or — when the last topic is completed — celebrate it (`CheckCircle2`, "Completaste X…") and point to the next module. One primary action, always present.
3. **Calmer and more honest stats.** Dropping the duplicate "Logros" card to a 3-up row removed both the redundancy and the gold-on-count drift; the streak no longer flashes "0" and its empty state encourages instead of discouraging.

## Priority Issues

**[P2] No help affordance on the surface itself.**
- **Why it matters:** Heuristic 10 stays at 2. Contextual guidance exists globally (proactive nudges, the floating tutor), but a first-timer scanning *this* page has no in-context "¿No sabes por dónde empezar?" cue tying the dashboard to the tutor.
- **Fix:** A single, quiet inline pointer (e.g. a one-line hint near the hero or an empty-recommendations nudge) that routes to the tutor/modules. Low effort; closes the last sub-3 heuristic.
- **Suggested command:** `/impeccable onboard`

**[P3] Error-state icon semantics.**
- **Why it matters:** The error EmptyState uses `AlertTriangle`, but the shared EmptyState renders its icon inside a primary-blue tinted circle — a warning glyph in the "everything's fine" blue reads slightly off.
- **Fix:** Allow EmptyState an accent/tone prop (or a muted/destructive icon treatment) for error vs. empty contexts.
- **Suggested command:** `/impeccable polish`

**[P3] Color count on a fully-populated screen.**
- **Why it matters:** Navy + blue + up to 3 module colors + N achievement colors + gold + green + warning still all coexist. Defensible as identity, but it nudges the One-Loud-Color rule as the lists grow.
- **Fix:** Consider muting per-module avatar color to a tint (keep the hue as an outline/accent, not a full fill) so institutional blue stays the one loud color.
- **Suggested command:** `/impeccable quieter`

## Persona Red Flags

Most prior flags are resolved; remaining ones are minor.

**Valentina (IESTP student, phone, progress-motivated):** ✅ Now gets a next-step hero after completing a topic (with a small celebration), and the streak no longer greets her with a discouraging "0 días". No remaining red flags on the core loop.

**Sam (screen reader + keyboard):** ✅ Stats sit in a labelled "Tu progreso" region; the streak value carries `aria-live`; the failed-load retry is keyboard-reachable. Minor: confirm the EmptyState error icon stays decorative (`aria-hidden`) so the message text carries the meaning.

**Casey (distracted mobile, flaky connection):** ✅ A dropped request now yields a retry button, not a frozen skeleton; the full-width hero CTA is always present in the thumb zone. No remaining red flags.

## Minor Observations

- **Hero ↔ first recommendation can duplicate.** On the just-completed path the hero targets `recommended_modules[0]`, which also renders first in the recommendations grid. Acceptable (the hero elevates one as primary), but worth a glance if it feels repetitive.
- **Help/docs ceiling** is the only heuristic left below 3; everything else is 3-4.

## Questions to Consider

- Is the dashboard's job done once the hero + progress are solid, or is a lightweight "what is this?" pointer for first-timers worth the small addition?
- As achievement and module lists grow, will the data-driven colors stay legible, or should per-module color become a tint rather than a full fill?
