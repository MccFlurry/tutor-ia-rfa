---
target: frontend/src/pages/ModulesPage.tsx
total_score: 29
p0_count: 0
p1_count: 1
timestamp: 2026-05-31T22-36-12Z
slug: frontend-src-pages-modulespage-tsx
---
## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Skeletons + per-card progress/status are good; a failed fetch gives no error feedback |
| 2 | Match System / Real World | 3 | Clear Spanish labels, but the status *colors* contradict convention (completed reads blue, not green) |
| 3 | User Control and Freedom | 3 | Locked gating + all-locked → assessment exit; can't open a module in a new tab (card is a button, not a link) |
| 4 | Consistency and Standards | 2 | Module state colors violate the project's own DESIGN.md route-state system (gray→blue→green) |
| 5 | Error Prevention | 3 | Locked modules are gated; nothing destructive to guard |
| 6 | Recognition Rather Than Recall | 4 | Status, progress, and the locked reason are all visible per card |
| 7 | Flexibility and Efficiency | 3 | Keyboard-operable cards; no new-tab, no filter (fine for 5 modules) |
| 8 | Aesthetic and Minimalist Design | 3 | Clean grid, but locked cards show a redundant 0% bar and 100% looks like in-progress |
| 9 | Error Recovery | 2 | Fetch error shows "Sin módulos disponibles" (wrong cause) with no retry |
| 10 | Help and Documentation | 3 | Locked-reason note + assessment CTA are genuinely helpful contextual guidance |
| **Total** | | **29/40** | **Good (lower edge)** |

## Anti-Patterns Verdict

**AI-generated?** No. `detect.mjs --json` → `[]` on both `ModulesPage.tsx` and `ModuleCard.tsx`. No gradient text, no eyebrow, no side-stripe, no glassmorphism. The module grid leans on uniform cards, but that's the legitimate signature affordance here (a list of modules, each differentiated by color, icon, progress, and status) — not the banned "identical icon-heading-text" filler.

**LLM assessment:** This is a competent, on-brand module index. The problems aren't visual slop; they're (a) a resilience gap shared with the old dashboard, and (b) a self-inconsistency: the page doesn't speak its own design system's color-state language.

**Visual overlays:** No browser-automation tool in this environment → CLI detector + source review only (fallback signal, no overlay claimed).

## Overall Impression

Functionally solid and accessible (keyboard-operable cards, aria labels, locked reasons). Two real holes hold it back: a failed fetch is misreported as "no modules published" with no way to retry, and the module state colors invert the route-state system that DESIGN.md explicitly defines (blue = current step, green = completed). Fix those two and this jumps into the low-to-mid 30s.

## What's Working

1. **Locked state is handled with care.** Padlock icon, "Bloqueado" badge, an inline reason note, `aria-disabled`, `tabIndex=-1`, and a title tooltip — plus an all-locked empty state that routes to the entry assessment. That's the "never dead-end a learner" principle done right.
2. **Per-card status is recognizable, not recalled.** Every card shows progress %, "X de N temas", and a status badge, so a returning student reads state at a glance.
3. **Clean, on-brand grid.** Responsive 1/2/3 columns, module color used as identity (icon tint), flat cards that lift on hover. No decoration competing with the content.

## Priority Issues

**[P1] A failed module fetch masquerades as "no modules".**
- **Why it matters:** `isLoading ? … : !modules || length === 0 ? <EmptyState "Sin módulos disponibles"> : …`. On a network/API error, `modules` is undefined → the user is told "Aún no hay módulos publicados… contacta al administrador." That misdiagnoses a transient failure as a content problem, and there's no retry. Same resilience gap the dashboard just fixed, manifesting as wrong information instead of an infinite skeleton.
- **Fix:** Pull `isError` / `refetch` from `useQuery`; on error render an error EmptyState (the new `tone="error"`) with a "Reintentar" button. Keep the empty copy only for a genuine empty list.
- **Suggested command:** `/impeccable harden`

**[P2] Module state colors contradict the project's own design system.**
- **Why it matters:** DESIGN.md's Traffic-Light-Free Rule and the signature Module Card both state: locked = gray, in-progress = blue (the current step), completed = green + a check. The implementation does the opposite: "Completado" uses the blue `default` badge, "En progreso" uses a low-emphasis `outline` badge, and there's no green anywhere (Badge has no success variant). So a finished module and an in-progress one barely differ, and the *current* step a student should resume wears the quietest badge. The progress bar is also always blue, even at 100%.
- **Fix:** Add a `success` (green) Badge variant; map Completado→green + a check icon, En progreso→blue, No iniciado→muted, Bloqueado→muted. Turn the progress bar green at 100%.
- **Suggested command:** `/impeccable colorize`

**[P2] Locked cards rely on blanket `opacity-70`, risking text contrast.**
- **Why it matters:** `opacity-70` on the whole `<article>` dims already-muted text (the description and the `muted-foreground` reason note) — muted-on-card at 70% opacity likely drops below the 4.5:1 body bar, exactly the audience (students on phones) who can least afford it.
- **Fix:** Style the locked state with explicit muted tokens (muted bg, `muted-foreground` kept at full opacity) instead of dimming the whole card; reserve opacity for the icon/illustration only.
- **Suggested command:** `/impeccable harden`

**[P3] Locked cards show a redundant 0% progress block.**
- **Why it matters:** A locked module already carries the reason note; the "0 de N temas / 0%" bar below it is noise that competes with the message.
- **Fix:** Hide the progress section when `is_locked`.
- **Suggested command:** `/impeccable distill`

**[P3] Module cards are buttons, not links.**
- **Why it matters:** `<article role="button" onClick=navigate>` can't be cmd/ctrl/middle-clicked to open a module in a new tab, and screen readers announce "button" for what is navigation.
- **Fix:** Wrap the card in a `<Link>` (or render an anchor) for non-locked modules; keep the keyboard/aria handling.
- **Suggested command:** `/impeccable polish`

## Persona Red Flags

**Valentina (IESTP student, returning to continue):** The module she's mid-way through (her current step) wears the quietest badge ("En progreso", outline), while completed modules wear loud blue — she can't quickly spot "where was I?". With no green for done, finished and in-progress modules blur together.

**Sam (screen reader + keyboard):** Locked cards' `opacity-70` likely fails contrast on the muted reason text. Status is carried by badge *label* (not color alone, good), but the blue=completed mapping is unconventional for a sighted low-vision user scanning by color.

**Alex (power user):** Can't middle-/cmd-click a module to open it in a new tab — the card is a `role="button"`, not a link. No shortcut to jump between modules.

## Minor Observations

- `description` is nullable; a null renders an empty `<p>` that still occupies its `mb-4` margin (a small gap with no content).
- The loading state renders 6 skeleton cards while the course has 5 modules — harmless, but could match.

## Questions to Consider

- Should the *current* (in-progress) module be the most visually prominent card, since "continue where I was" is the most common intent on this page?
- Is the blue "Completado" badge a deliberate choice, or should completed modules finally carry the green + check that DESIGN.md describes?
- When the API is down, what should this page say — and does "contacta al administrador" send students down the wrong path?
