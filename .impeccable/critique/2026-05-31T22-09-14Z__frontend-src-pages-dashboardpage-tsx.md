---
target: frontend/src/pages/DashboardPage.tsx
total_score: 28
p0_count: 0
p1_count: 2
timestamp: 2026-05-31T22-09-14Z
slug: frontend-src-pages-dashboardpage-tsx
---
## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Skeleton on first load is solid; streak loads on a separate query and flashes "0 días" before its real value |
| 2 | Match System / Real World | 3 | Spanish peruano, familiar icons; Sparkles icon overloaded (AI + level + empty), "Logros recientes" label used twice |
| 3 | User Control and Freedom | 3 | Read/navigate surface; "Ver todos" exits present; nothing to trap the user |
| 4 | Consistency and Standards | 3 | StatCard/section vocabulary consistent; gold accent semantics drift (stat card gold, chips use per-item color); one "Ver todos" has an icon, one doesn't |
| 5 | Error Prevention | 3 | Low-risk overview, no destructive paths to guard |
| 6 | Recognition Rather Than Recall | 4 | Everything labeled and visible; zero memory load |
| 7 | Flexibility and Efficiency | 3 | Recommendations + hero act as accelerators; no shortcuts, fine for a dashboard |
| 8 | Aesthetic and Minimalist Design | 3 | Mostly clean; redundant Logros stat, 0% progress bars on recommendations, and high color count add noise |
| 9 | Error Recovery | 1 | Dashboard fetch failure → infinite skeleton, no message, no retry |
| 10 | Help and Documentation | 2 | No contextual help on the surface itself (nudges/tutor live globally) |
| **Total** | | **28/40** | **Good (lower edge)** |

## Anti-Patterns Verdict

**Does this look AI-generated?** No. It reads as a real, on-brand product dashboard. It follows its own DESIGN.md (navy hero, earned-gold, gray→blue→green state, one typeface, flat-at-rest cards). It is not template-SaaS slop: no gradient text, no hero-metric template, no endless identical icon-heading-text grid, no side-stripe accents.

**LLM assessment:** The closest brush with slop is the 4-up StatCard row with uppercase tracked labels — but the project's own DESIGN.md explicitly permits uppercase for ≤4-word labels, and these are stat labels, not section eyebrows. It stays on the right side of the line. The bigger smell is *content redundancy* (a "Logros recientes" count card sitting directly above a full "Logros recientes" section) rather than visual slop.

**Deterministic scan:** `detect.mjs --json` on `DashboardPage.tsx` returned `[]` — zero findings. No gradient text, no >1px colored side borders, no banned eyebrow pattern, no glassmorphism. Clean.

**Visual overlays:** No browser-automation tool was available in this environment, so no live overlay was injected and no `[Human]` tab exists. Assessment B ran as CLI detector + source review only. This is the fallback signal, not a claimed overlay.

## Overall Impression

A confident, on-brand student dashboard that mostly does its job: it greets, shows the level, surfaces a clear "Retomar" hero, and tracks progress honestly. It earns trust. The single biggest opportunity is **resilience and forward-momentum on the unhappy/edge paths** — the surface is polished for the populated happy state but degrades poorly when the dashboard fetch fails or when the last topic is already completed. Both are core to the product's own principles ("Resilient by design", "never dead-ends a learner"), so they matter more here than cosmetic polish.

## What's Working

1. **The navy "Retomar" hero is the right primary.** It maps the One-Loud-Color / one-primary-action rule perfectly: a single, obvious next step with a high-contrast white button on the navy gradient, full-width on mobile (thumb-friendly). This is the dashboard's strongest moment.
2. **Honest, real-progress stats + earned-gold achievements.** Progress %, lessons completed (n/total), and streak are concrete units of progress, not vanity metrics, and the gold achievement chips reserve gold for genuinely earned things — exactly the "Momentum over decoration" principle.
3. **Accessibility scaffolding is already present.** `aria-labelledby` on sections, `aria-hidden` on decorative icons, visible `focus-visible` rings on the recommendation buttons, and a proper `<h1>`/`<h2>` spine. Good baseline.

## Priority Issues

**[P1] Dashboard fetch failure renders an infinite skeleton.**
- **Why it matters:** `if (isLoading || !data) return <skeleton>`. On a failed fetch, react-query sets `isLoading=false` and leaves `data` undefined, so the guard stays true and the skeleton renders forever — no message, no retry, no fallback. The global ErrorBoundary won't catch it (react-query doesn't throw by default). A student on flaky institute wifi sees a frozen loading screen. This directly violates Principle 5 ("Resilient by design") and is the lowest heuristic score (Error Recovery = 1).
- **Fix:** Branch on `isError`. Show a compact error card with a "Reintentar" button (`refetch()`), or render the degraded-cache state the backend already supports. Never let `!data` alone gate the skeleton.
- **Suggested command:** `/impeccable harden`

**[P1] No persistent "next step" when the last topic is already completed.**
- **Why it matters:** The hero only renders when `last_accessed_topic && !is_completed`. A student who *just finished* a topic returns to a dashboard with no primary forward action — the page's whole job (point to the next foothold on "La Ruta del Aprendiz") silently disappears, and recommendations downgrade to a secondary section. It dead-ends the core learning loop at a high-progress moment (an emotional valley right after an accomplishment). Violates Principle 2 ("never dead-ends a learner") and Principle 4 ("one primary job per screen").
- **Fix:** Always render a hero. When the last topic is completed, switch its copy to "Continúa con lo siguiente" and point to the next topic/module (or celebrate completion + next-module CTA). The primary action should never vanish.
- **Suggested command:** `/impeccable onboard`

**[P2] The "Logros recientes" stat card duplicates the section below it and carries almost no information.**
- **Why it matters:** The 4th StatCard shows `recent_achievements.length` (a capped list, so always ≤3) under the exact same label as the full chip section lower on the page. Same words twice; the number is near-meaningless. It's filler in a slot that could carry a real metric.
- **Fix:** Replace with a metric the student doesn't already see — total achievements earned, quizzes passed, or current module progress — or drop the 4th card and let the row be a 3-up.
- **Suggested command:** `/impeccable distill`

**[P2] Recommendation cards conflate "start this" with a progress bar.**
- **Why it matters:** Each recommended module renders a progress bar + "X% completado". For a recommendation (a thing to start), a 0% bar reads as noise or even as "you're behind", muddying whether this is a suggestion or a resumption.
- **Fix:** Hide the bar when `progress_pct === 0` (show a "Empezar" affordance instead), or drop progress from recommendations entirely and keep it to the reason + a clear start action.
- **Suggested command:** `/impeccable layout`

**[P2] Streak stat flashes "0 días" and reads as discouraging when empty.**
- **Why it matters:** The streak runs on its own `useQuery`, not gated by the page `isLoading`. On load it renders `0` then flips to the real value (a content flash). For a real returning user, "Racha actual: 0 días" with no streak is a flat, slightly demotivating value at a glance.
- **Fix:** Gate the card on the streak query's own loading (tiny skeleton/`—` placeholder), and soften the zero state ("¡Empieza tu racha hoy!" instead of a bare "0 días").
- **Suggested command:** `/impeccable harden`

## Persona Red Flags

**Valentina (project persona — mixed-skill IESTP student, on a phone, motivated by visible progress):**
- Returns after finishing a topic → no "Retomar" hero, no obvious next step. She has to hunt in "Recomendaciones" to keep going.
- "Racha actual: 0 días" and 0% progress bars on recommendations read as "you're behind", undercutting the encouraging voice for exactly the learner the system is meant to reassure.

**Sam (accessibility / screen reader + keyboard):**
- The 4-up stats block is a bare grid with no labelled region or group heading — it's announced as four loose `<article>`s with no "Tu progreso" landmark to anchor them.
- The streak value updates after initial render with no `aria-live`, so the "0 → real value" change is silent to a screen reader. (Focus rings and section labels elsewhere are good.)

**Casey (distracted mobile, one-handed, flaky connection):**
- On a dropped/failed request she gets the infinite skeleton with no retry — the worst case for exactly her network conditions.
- The "Retomar" button is reachable and full-width (good), but it sits above the fold only when the hero exists; on the completed-topic path there's no thumb-zone primary action at all.

## Minor Observations

- **Color count on a populated screen:** navy hero + institutional blue + up to 3 per-module `color_hex` + N per-achievement `badge_color` + gold + success + warning. Module/achievement colors are data-driven identity (defensible), but it nudges the One-Loud-Color rule; watch it as the page grows.
- **Sparkles icon is overloaded** — it marks the level chip, the empty state, and reads as the generic "AI" glyph. Level is an assessment result, not AI magic; consider a distinct icon (e.g. a tier/medal glyph) for the level chip.
- **"Ver todos" inconsistency:** the recommendations one has a `BookOpen` icon, the achievements one has none. Pick one.
- **Hero title `sm:truncate`:** the single most important "continue" target truncates with an ellipsis on desktop; long topic titles lose information at the exact spot the user most needs to read it.
- **Gold semantics drift:** the achievements StatCard uses the gold/`heritage` accent, but the actual achievement chips below use each achievement's own `badge_color`, not gold — the "gold = earned" signal is applied to the count but not the items.

## Questions to Consider

- When a student lands here having just completed their last topic, what is the *one* thing you want them to do next — and is it visible without scrolling?
- Does the dashboard need a "Logros" stat at all, or is the achievements section below enough? What's the metric a student actually checks every day?
- If Ollama or the API is down, what should this page feel like? The product promises fallbacks "feel intentional, not broken" — does the dashboard honor that yet?
- Would the dashboard be calmer with a 3-up stat row instead of 4, freeing the eye for the hero and recommendations?
