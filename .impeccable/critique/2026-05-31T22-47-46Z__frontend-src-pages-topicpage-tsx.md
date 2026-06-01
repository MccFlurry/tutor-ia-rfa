---
target: frontend/src/pages/TopicPage.tsx
total_score: 31
p0_count: 0
p1_count: 0
timestamp: 2026-05-31T22-47-46Z
slug: frontend-src-pages-topicpage-tsx
---
## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Skeleton, completion chip, AI "Preparando…" loading, toasts are good; the not-found/error state gives no real status |
| 2 | Match System / Real World | 4 | Clear Spanish, breadcrumb, "min de lectura", familiar icons |
| 3 | User Control and Freedom | 3 | Breadcrumb + prev/next are solid, but the not-found/error state is a dead-end (no escape but browser back) |
| 4 | Consistency and Standards | 3 | Action emphasis varies; the progression action (quiz/complete) isn't consistently the one primary |
| 5 | Error Prevention | 3 | Quiz gating prevents skipping; nothing destructive |
| 6 | Recognition Rather Than Recall | 4 | Header chips, breadcrumb, prev/next labels + position |
| 7 | Flexibility and Efficiency | 3 | Prev/next nav present; no keyboard shortcuts for a long-read page |
| 8 | Aesthetic and Minimalist Design | 3 | Clean reading surface, but action-row hierarchy is ambiguous and one state renders an empty action row |
| 9 | Error Recovery | 2 | `!topic` → "Tema no encontrado" with no retry, no escape, and network error conflated with 404 |
| 10 | Help and Documentation | 3 | TutorNudgeList + ResourceList give real contextual help; quiz-gated completion isn't explained |
| **Total** | | **31/40** | **Good (mid-band)** |

## Anti-Patterns Verdict

**AI-generated?** No. `detect.mjs --json` → `[]`. The lesson layout is content-first and appropriate (breadcrumb → header → video → content card → actions → resources → prev/next). ContentRenderer is a highlight: it downshifts authored headings (`#`→`<h2>`) so the page keeps one `<h1>`, and holds prose text at full-contrast `text-foreground` (no light-gray body). No gradient, eyebrow, side-stripe, or glass.

**Visual overlays:** No browser-automation tool in this environment → CLI detector + source review only (fallback signal, no overlay claimed).

## Overall Impression

A focused, on-brand reading surface that mostly disappears into the task of learning, with genuinely good content rendering and navigation. Two things hold it back: the not-found/error state is a dead-end with no retry or escape (the same resilience gap seen elsewhere, plus a missing way back), and the action hierarchy is ambiguous, so the *progression* action a student should take next isn't always the visually primary one. Fix those and it lands in the mid-30s.

## What's Working

1. **Content rendering is excellent.** ContentRenderer keeps the single-`<h1>` landmark, downshifts markdown headings, renders code blocks / tables / blockquotes, holds full contrast in light and dark. The lesson reads cleanly — the tool disappears into the content.
2. **Orientation and navigation are strong.** A real breadcrumb (Módulos → module → topic), header chips (time, quiz, completed), and a sticky mobile prev/next with truncation and safe bottom padding. A student always knows where they are and how to move.
3. **Resilient AI path.** The coding challenge fetch shows a "Preparando desafío con IA…" loading state and, if Ollama is down, toasts "Usando desafío del banco" and still navigates — the fallback feels intentional, exactly the product's promise.

## Priority Issues

**[P2] The not-found / error state is a dead-end with no retry or escape.**
- **Why it matters:** `if (!topic) return <p>Tema no encontrado.</p>`. On a network/API failure this misreports a transient error as "topic doesn't exist", and on a genuine 404 it strands the student — the breadcrumb sits *below* this guard, so there's no "Volver a módulos" and no "Reintentar". The only way out is the browser back button. Violates "never dead-end a learner" and the resilience principle.
- **Fix:** Split `isError` (error EmptyState with `tone="error"` + Reintentar/refetch) from a true not-found (a clear message + a "Volver a módulos" link). Always give an escape.
- **Suggested command:** `/impeccable harden`

**[P2] The progression action isn't consistently the visual primary.**
- **Why it matters:** For a quiz topic, "Ir a la Autoevaluación" (how the student actually completes/progresses) is an `outline` button; if the topic also has a coding challenge, it sits as a second `outline` (gold) button — two equal outlines, no filled primary, so the key next step doesn't stand out. Meanwhile a no-quiz topic's "Marcar como completado" is a filled green button. The one action that advances the student should always read as the primary.
- **Fix:** Make the progression action the single filled primary per state (quiz → primary when present; otherwise complete). Keep coding as the clearly-secondary option.
- **Suggested command:** `/impeccable layout`

**[P3] Green "Marcar como completado" uses a state color as an action, leaving the page with no institutional-blue primary.**
- **Why it matters:** DESIGN.md reserves green for the *completed* state and institutional blue for the one primary action. The complete button is `bg-success` green, so action and state share a color and the page has no blue primary.
- **Fix:** Consider institutional-blue for the primary "complete/continue" action; reserve green for the completed indicator (which the header already shows).
- **Suggested command:** `/impeccable colorize`

**[P3] One state renders an empty action row.**
- **Why it matters:** When a topic is completed and has no quiz and no coding challenge, the action `<div>` renders with no children but keeps its `mb-8` — an empty gap.
- **Fix:** Render the action row only when it has at least one button.
- **Suggested command:** `/impeccable distill`

**[P3] Video iframe loads eagerly; mobile hides the "X de N" position.**
- **Why it matters:** The YouTube iframe has no `loading="lazy"`, so it loads on slow connections before the student scrolls to it; and the "X de N" position indicator is `hidden sm:block`, so mobile users (the sticky-nav case) lose their place-in-module context.
- **Fix:** Add `loading="lazy"` to the iframe; show a compact position indicator on mobile too.
- **Suggested command:** `/impeccable optimize`

## Persona Red Flags

**Jordan (first-timer):** On a quiz topic there's no "Marcar como completado" and no text explaining that passing the autoevaluación is what finishes the topic — Jordan may read the page, find only an "Ir a la Autoevaluación" button, and wonder how to mark it done.

**Casey (distracted mobile, slow connection):** Loses the "X de N" position indicator on mobile (hidden below `sm`), and the video iframe loads eagerly even before scrolling to it. Sticky prev/next and the pb-24 safe area are good for her, though.

**Riley (stress tester):** A stale or bad topic id, or an API blip, lands on "Tema no encontrado" with no retry and no link back — a dead-end that only the browser back button escapes.

## Minor Observations

- Time tracking is coarse: `setInterval(+30s)` means a visit under 30s records 0, and background tabs throttle the interval. Fine for rough analytics, but not precise.
- Prev/next are `<Button onClick=navigate>`, not links — no middle/cmd-click to open a sibling topic in a new tab (same pattern just fixed on ModuleCard).

## Questions to Consider

- When a topic is quiz-gated, how should the page tell a student "pass the autoevaluación to complete this"? Right now it's implicit.
- Should the action that advances the student always be the one blue primary, with coding/secondary actions clearly subordinate?
- When a topic fails to load, what's the escape hatch — retry, back to module, or both?
