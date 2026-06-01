---
target: frontend/src/pages/QuizPage.tsx
total_score: 35
p0_count: 0
p1_count: 0
timestamp: 2026-05-31T22-59-49Z
slug: frontend-src-pages-quizpage-tsx
---
## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 4 | AILoadingState, "X de Y respondidas", "Enviando…", toasts, results all signal |
| 2 | Match System / Real World | 4 | Clear Spanish, "60% para aprobar", breadcrumb, "progreso se guarda" |
| 3 | User Control and Freedom | 4 | Retry, back-to-topic, regenerate, and localStorage resume — leave and return safely |
| 4 | Consistency and Standards | 3 | AILoadingState `animate-bounce` contradicts the no-bounce rule + the `typing-dot` token; fail uses destructive red |
| 5 | Error Prevention | 3 | Unanswered check + persistence are good; submit stays enabled and only toasts the blocker |
| 6 | Recognition Rather Than Recall | 3 | Results review says "Opción N" with no option text and never shows the correct answer |
| 7 | Flexibility and Efficiency | 3 | Radio keyboard nav + resume; no jump-to-unanswered, no submit shortcut |
| 8 | Aesthetic and Minimalist Design | 4 | Clean, focused quiz + sticky submit + clear results |
| 9 | Error Recovery | 3 | Infra errors recover well (ErrorState/retry/410); the unanswered case is toast-only, no pinpoint |
| 10 | Help and Documentation | 4 | Pass threshold, autosave note, AI note, per-question explanations, reinforcement nudges |
| **Total** | | **35/40** | **Good (top edge)** |

## Anti-Patterns Verdict

**AI-generated?** No. `detect.mjs --json` → `[]`. This is the most robust surface reviewed this session: a dedicated `AILoadingState`, a real `ErrorState` (with a `serviceUnavailable` variant, retry, and back-to-topic), localStorage persistence that survives reloads, 410-expiry → regenerate, and full cache invalidation on submit. Proper radio semantics (radix `RadioGroup` + `aria-labelledby`), color-plus-icon feedback. No gradient, eyebrow, side-stripe, or glass.

**LLM assessment:** The problems aren't slop or fragility; they're learning-value and feedback-precision gaps in the *results* and *validation* moments, plus two small consistency nits (bounce easing, fail-state red).

**Visual overlays:** No browser-automation tool in this environment → CLI detector + source review only (fallback signal, no overlay claimed).

## Overall Impression

The best-engineered page critiqued so far: resilient, accessible, and persistent. What holds it back is the two moments that matter most pedagogically. The **results review withholds the right answer** (it labels the student's pick "Opción N" with no option text and never shows what was correct), and **submitting with blanks is flagged only by a transient toast** with no way to find the gaps. Tighten those two and it's clearly Excellent.

## What's Working

1. **Resilience and persistence are exemplary.** AI loading state, a typed ErrorState with a service-unavailable variant + retry + back, localStorage that rehydrates in-progress answers, and 410-expiry that quietly regenerates. A student is never blocked or loses work — exactly the product's "resilient by design" promise.
2. **Accessible question UI.** Each question is a radix `RadioGroup` labelled by its prompt, so it's arrow-key navigable and screen-reader correct; results pair color with `CheckCircle2`/`XCircle` icons, never color alone.
3. **Honest, contextual framing.** The header states the 60% pass bar and that progress autosaves; results carry per-question explanations and reinforcement nudges (`quiz_result`).

## Priority Issues

**[P2] The results review withholds the correct answer and the option text.**
- **Why it matters:** For a wrong question, `QuizResults` shows "Tu respuesta: Opción {selected_index + 1}" — a bare number with no option text — and never shows which option was correct. A self-assessment's whole job is learning from mistakes; this forces the student to recall what "Opción 2" even was and leaves them guessing the right answer. (Recognition-not-recall, and the core pedagogical purpose.)
- **Fix:** In the per-question feedback, render the option texts, mark the correct option (green check) and the student's wrong pick (red), and keep the explanation. Requires the submit response to include the options + correct index (extend the API/`feedback` item if needed).
- **Suggested command:** `/impeccable clarify` (or a small results redesign)

**[P2] Submitting with unanswered questions is flagged only by a toast.**
- **Why it matters:** `handleSubmit` toasts "Tienes N pregunta(s) sin responder" and returns, but nothing marks *which* questions are blank or moves the student to them. On a multi-question quiz they scroll hunting; a keyboard/screen-reader user gets a count with no target.
- **Fix:** Mark unanswered questions (border/badge), scroll to and focus the first unanswered on a blocked submit. Keep the submit enabled, but make the gap findable.
- **Suggested command:** `/impeccable harden`

**[P3] The failed-quiz result uses destructive red.**
- **Why it matters:** A big red `XCircle` + red "No alcanzaste el puntaje mínimo" is harsh for an encouraging tutor, and red brushes the Traffic-Light-Free Rule (red is destructive/Peru, not "not yet"). The reinforcement nudge softens it, but the score card itself lands hard.
- **Fix:** Use the heritage/`warning` amber for a not-passed result ("Aún no alcanzaste el 60%"), reserving destructive red for truly destructive actions. Keep green for pass.
- **Suggested command:** `/impeccable colorize`

**[P3] AILoadingState uses `animate-bounce`.**
- **Why it matters:** Bounce easing contradicts the project's "no bounce, no elastic" motion rule, and it's inconsistent with the `typing-dot` token the team created specifically to replace bounce in the chat TypingIndicator. (Reduced-motion is safe — the global `prefers-reduced-motion` rule neutralizes it.)
- **Fix:** Swap the three `animate-bounce` dots for the existing `animate-[typing-dot]` token (or a gentle staggered fade), matching chat.
- **Suggested command:** `/impeccable animate`

## Persona Red Flags

**Valentina (student learning from the result):** fails the quiz, sees a big red X, and the review tells her "Tu respuesta: Opción 2" with no option text and no correct answer — she can't actually learn what she got wrong, which defeats the self-assessment.

**Jordan (first-timer):** taps "Enviar respuestas" with three blanks, gets a toast count, and has no idea which questions to revisit — scrolls up and down hunting.

**Sam (screen reader + keyboard):** question radios and result icons are well-built; the gap is the blocked submit — the toast announces a count but focus isn't moved to the first unanswered question, so finding it is manual tabbing.

## Minor Observations

- The breadcrumb ends in "Autoevaluación" and the `<h1>` is also "Autoevaluación" — mild redundancy.
- There's a "X de Y respondidas" count but no visual progress bar; fine, but a slim bar would read faster on a long quiz.
- After a fail, the primary button is "Volver al tema" while "Intentar de nuevo" is the outline — for an encouraging retry-friendly flow, retry could be the primary on a fail.

## Questions to Consider

- When a student gets a question wrong, what do they most need to see — the correct option, their pick, and why? Right now they see the least useful version (a number).
- On a blocked submit, should the page take the student to the first unanswered question instead of just counting?
- Does a failed self-assessment deserve destructive red, or amber "not yet" that matches the encouraging voice?
