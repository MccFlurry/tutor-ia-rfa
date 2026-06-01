---
target: frontend/src/pages/TopicPage.tsx
total_score: 37
p0_count: 0
p1_count: 0
timestamp: 2026-05-31T22-56-06Z
slug: frontend-src-pages-topicpage-tsx
---
## Design Health Score (re-run after fixes)

| # | Heuristic | Score | Δ | Key Issue |
|---|-----------|-------|----|-----------|
| 1 | Visibility of System Status | 4 | +1 | Loading, error, completion, AI loading, and toasts all communicate now |
| 2 | Match System / Real World | 4 | — | Clear Spanish, breadcrumb, familiar icons |
| 3 | User Control and Freedom | 4 | +1 | Error/not-found now offer retry + "Volver a módulos"; prev/next are links |
| 4 | Consistency and Standards | 4 | +1 | One blue primary per state; coding is consistently the secondary action |
| 5 | Error Prevention | 3 | — | Quiz gating; nothing destructive (scope cap) |
| 6 | Recognition Rather Than Recall | 4 | — | Header chips, breadcrumb, prev/next labels + position |
| 7 | Flexibility and Efficiency | 3 | — | Prev/next links allow new-tab; no arrow-key shortcuts for a long read |
| 8 | Aesthetic and Minimalist Design | 4 | +1 | Action hierarchy resolved; empty action row gone |
| 9 | Error Recovery | 4 | +2 | Failed/missing topic → clear state + Reintentar + back link |
| 10 | Help and Documentation | 3 | — | Nudges + resources + the new quiz-completion hint; still no page-level docs |
| **Total** | | **37/40** | **+6** | **Excellent — minor polish only** |

## Anti-Patterns Verdict

No AI slop. `detect.mjs --json` → `[]`. ContentRenderer remains the highlight (single-`<h1>` landmark, downshifted headings, full-contrast prose). No gradient, eyebrow, side-stripe, or glass.

**Visual overlays:** No browser-automation tool in this environment → CLI detector + source review only (fallback signal, no overlay claimed).

## Overall Impression

Trend 31 → 37. Both P2 holes are closed: a failed or missing topic now recovers (retry) or escapes (back to módulos) instead of dead-ending, and the advancing action reads as the single institutional-blue primary with coding clearly secondary. The page is a focused, resilient reading surface. The two heuristics still at 3 (Error Prevention, Flexibility) are scope ceilings for a lesson page; Help at 3 is honest (contextual help is strong, but there's no page-level documentation).

## What's Working

1. **Resilient and never-dead-ended.** `isError` → error EmptyState with Reintentar; a true not-found → a clear message with "Volver a módulos". The breadcrumb-below-the-guard dead-end is gone.
2. **Clear primary action.** The step that advances the student (complete, or the autoevaluación) is the single blue primary; coding stays a secondary outline; completed quiz topics get an outline "Repasar autoevaluación". Green is now reserved for the completed indicator, as DESIGN.md intends.
3. **Content + navigation still excellent**, now with links for prev/next (new-tab/middle-click), a lazy-loaded video, a mobile position indicator, and an inline hint that the autoevaluación completes a quiz-gated topic.

## Priority Issues

No P0/P1/P2 remain. One optional polish item:

**[P3] No keyboard shortcuts for prev/next on a long-read page.**
- **Why it matters:** A reader moving through a module must reach for the mouse/tap target each time; ←/→ (or J/K) would speed sequential reading. Minor, and only relevant to power readers.
- **Fix (optional):** Bind ArrowLeft/ArrowRight to prev/next when no input is focused.
- **Suggested command:** `/impeccable animate` (or a small keydown handler)

## Persona Red Flags

All clear.
- **Jordan (first-timer):** the inline "Aprueba la autoevaluación para completar este tema" now explains how a quiz-gated topic is finished.
- **Casey (mobile, slow conn):** keeps the "X de N" position on mobile; the video iframe lazy-loads; sticky nav + safe area intact.
- **Riley (stress):** a bad/stale topic id or API blip lands on a recoverable state (retry + back link), not a dead-end.

## Minor Observations

- Time tracking remains coarse (`setInterval(+30s)`): a sub-30s visit records 0 and background tabs throttle. Analytics precision, not a UX defect.
- Quiz/coding remain buttons (correct — they trigger a navigation-with-side-effects and an AI mutation, respectively).

## Questions to Consider

- Is keyboard sequential navigation (←/→) worth adding for students who read several topics in a row?
- Should time-on-topic be tracked more precisely (visibilitychange + timestamps) if it feeds the pre/post analysis, or is rough enough fine?
