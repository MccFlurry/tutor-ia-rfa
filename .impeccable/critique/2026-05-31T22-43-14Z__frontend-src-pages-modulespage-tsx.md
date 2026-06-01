---
target: frontend/src/pages/ModulesPage.tsx
total_score: 37
p0_count: 0
p1_count: 0
timestamp: 2026-05-31T22-43-14Z
slug: frontend-src-pages-modulespage-tsx
---
## Design Health Score (re-run after fixes)

| # | Heuristic | Score | Δ | Key Issue |
|---|-----------|-------|----|-----------|
| 1 | Visibility of System Status | 4 | +1 | Loading, error, and per-card progress/status all communicate now |
| 2 | Match System / Real World | 4 | +1 | State colors now conventional: green = done, blue = current step |
| 3 | User Control and Freedom | 4 | +1 | Cards are links (new-tab / middle-click / back); failed load offers retry |
| 4 | Consistency and Standards | 4 | +2 | Now matches the DESIGN.md route-state system exactly (muted → blue → green + check) |
| 5 | Error Prevention | 3 | — | Locked modules gated; nothing destructive (scope cap) |
| 6 | Recognition Rather Than Recall | 4 | — | Status, progress, locked reason all visible per card |
| 7 | Flexibility and Efficiency | 3 | — | Links allow new-tab; no filter/shortcuts (fine for 5 modules) |
| 8 | Aesthetic and Minimalist Design | 4 | +1 | Locked cards cleaned up (no redundant bar, muted not dimmed); completed reads distinct from in-progress |
| 9 | Error Recovery | 4 | +2 | Failed fetch → error state + Reintentar, no longer "no modules" |
| 10 | Help and Documentation | 3 | — | Locked-reason note + assessment CTA (contextual, not full docs) |
| **Total** | | **37/40** | **+8** | **Excellent — minor polish only** |

## Anti-Patterns Verdict

No AI slop. `detect.mjs --json` → `[]` on both files. The module grid is the legitimate signature affordance; per-card color/icon/progress/state differentiate it. No gradient, eyebrow, side-stripe, or glass.

**Visual overlays:** No browser-automation tool in this environment → CLI detector + source review only (fallback signal, no overlay claimed).

## Overall Impression

Trend 29 → 37. Both holes from the first pass are closed: the module cards now speak their own design system's color-state language (green + check for done, blue for the current step), and a failed fetch recovers with a retry instead of lying about "no modules". The page is resilient, consistent, accessible, and on-brand. The three heuristics still at 3 are scope ceilings for a module index, not defects.

## What's Working

1. **State colors finally match the route-state system.** Completado is green with a check, En progreso is blue (the step to resume), No iniciado is a neutral outline, Bloqueado is muted, and the progress bar turns green at 100%. A returning student can now spot "where was I?" and "what's done?" at a glance.
2. **Resilient load.** `isError` → an error EmptyState with a working "Reintentar"; the misleading "Sin módulos disponibles" is reserved for a genuinely empty list.
3. **Cards are real links.** Non-locked modules render as `<Link>` — middle/cmd-click opens in a new tab, screen readers announce a link, and the keyboard activation is native. Locked cards stay non-interactive with full-contrast muted text instead of a dimmed `opacity-70` block.

## Priority Issues

No P0/P1/P2 remain. One trivial nitpick:

**[P3] Loading renders 6 skeleton cards for a 5-module course.**
- **Why it matters:** Purely cosmetic; the count is a guess made before data loads. A brief layout shift from 6 → 5 on first paint.
- **Fix (optional):** Drop the skeleton count to a number closer to the typical module count, or accept it.
- **Suggested command:** `/impeccable polish`

## Persona Red Flags

All clear.
- **Valentina (returning student):** the in-progress module is now the blue (prominent) card; completed modules are green with a check — "where was I?" and "what's done?" read instantly.
- **Sam (screen reader / low vision):** locked text keeps full-opacity muted contrast; cards announce as links; state carries label + icon, not color alone.
- **Alex (power user):** module cards are links → middle/cmd-click opens in a new tab.

## Minor Observations

- The three heuristics at 3 (Error Prevention, Flexibility, Help) are scope-appropriate for a module index: nothing destructive to guard, no need for power-user filters across 5 modules, and the locked-reason + assessment CTA are proportionate help.

## Questions to Consider

- Is a module index "done" at Excellent, or would per-module last-activity / estimated-time metadata help a student choose what to open next?
- Should the skeleton count adapt to the known module count once cached, to avoid the 6 → 5 paint shift?
