---
target: frontend/src/pages/ChatPage.tsx
total_score: 27
p0_count: 0
p1_count: 2
timestamp: 2026-05-31T21-30-37Z
slug: frontend-src-pages-chatpage-tsx
---
# Critique — ChatPage (RAG Tutor)

Target: `frontend/src/pages/ChatPage.tsx` (+ `ChatMessage`, `TypingIndicator`, sidebar). Register: product.

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Strong (skeletons, typing, optimistic echo, quota, rate-limit alert). Gap: failed send shows nothing. |
| 2 | Match System / Real World | 4 | Clear Spanish peruano, natural domain language. |
| 3 | User Control and Freedom | 2 | No delete confirm/undo, no cancel of in-flight response, no ESC-to-close drawer. |
| 4 | Consistency and Standards | 3 | Mixes raw `<button>` and `<Button>`; send button `rounded-xl` off the token scale. |
| 5 | Error Prevention | 2 | Destructive delete fires immediately, no guard. |
| 6 | Recognition Rather Than Recall | 3 | Session list + active highlight + labeled actions. Good. |
| 7 | Flexibility and Efficiency | 3 | Enter/Shift+Enter documented, autogrow textarea; no other shortcuts. |
| 8 | Aesthetic and Minimalist Design | 3 | Clean, focused, max-w-3xl reading column. |
| 9 | Error Recovery | 1 | Send failure silently eats the question, no message, typed text already cleared. |
| 10 | Help and Documentation | 3 | Teaching empty states + input hint. |
| **Total** | | **27/40** | **Acceptable (upper edge of the band)** |

## Anti-Patterns Verdict

**Does this look AI-generated? No.** Conventional best-in-class chat patterns (ChatGPT/Claude-shaped), which is correct for a product surface — familiarity is a feature. No gradient text, no hero-metric, no eyebrow scaffolding, no glass, no side-stripe borders. On-brand: primary/muted bubbles, consistent avatars, institutional blue.

**Deterministic scan (`detect.mjs`):** 3 findings, all `bounce-easing` (warning) in `TypingIndicator.tsx:14/18/22` — the three `animate-bounce` typing dots. Bounce/elastic easing reads as dated per the skill's motion rules. Low impact (1.5px dots, tamed under the global `prefers-reduced-motion` cap) but trivially fixable to a smooth opacity/translate stagger. No other anti-patterns flagged across the page or chat components.

**Visual overlays:** none — no browser automation available this session. Review is source + detector only.

## Overall Impression

A competent, genuinely responsive chat that does the happy path well: it always tells you what's happening *when it works*, and the cited-source rendering directly serves "el tutor no inventa." The single biggest opportunity is the **unhappy path** — failed/slow/blocked responses are exactly the moments this audience hits (local 7B can be slow or down per CLAUDE.md), and right now those moments give the student nothing.

## What's Working

1. **Status visibility (happy path).** Skeletons for sessions + messages, `TypingIndicator`, optimistic user echo, live quota counter, smooth scroll-to-end, `aria-busy`. The surface narrates itself.
2. **Trust through citations.** Assistant bubbles render markdown + `CodeBlock` + collapsible `ChatSources` — the RAG's traceability is visible, not buried.
3. **Real mobile thought.** Overlay drawer + backdrop, `100dvh` height, `max-w-3xl` reading column, 44px touch targets, `text-base` input (no iOS zoom), responsive quota label.

## Priority Issues

- **[P1] Silent send failure eats the question.** `handleSend` clears `input` immediately, and on error `catch { setOptimisticMessages([]) }` removes the user bubble with no toast, no inline alert, and no restore of the typed text. A 503 (Ollama down — a documented state), a 429 race, or a network blip = the student's question vanishes with zero feedback. Directly violates the "Resilient by design" principle (a fallback must feel intentional, not broken). **Fix:** on catch, surface an error (toast or inline `role=alert`), keep the failed user bubble with a "Reintentar" action, and restore the input text. **Command:** `/impeccable harden`.
- **[P1] Destructive delete with no confirmation.** `handleDeleteSession` deletes the conversation immediately; the trash icon appears on hover/focus, so one misclick is irreversible. No confirm, no undo. **Fix:** confirm dialog or an undo toast. **Command:** `/impeccable harden`.
- **[P2] No cancel / retry for an in-flight response.** A slow local model (>20s is possible per CLAUDE.md) traps the user watching the typing indicator with no stop and no retry on the last turn. **Fix:** add a cancel affordance during pending + retry on the last message. **Command:** `/impeccable harden`.
- **[P2] Radius + element drift.** Send button is `rounded-xl` (12px), off the system scale (buttons = `rounded-md` 8px); the page mixes raw `<button>` with the `<Button>` component. Small, but it's exactly the "one shape vocabulary" drift DESIGN.md warns about. **Fix:** normalize radii to tokens, use `<Button>` consistently. **Command:** `/impeccable polish`.
- **[P3] Bouncy typing dots + weak page title.** `animate-bounce` (detector) is the dated-easing tell; swap to a smooth opacity/translate stagger. Separately, the `Tutor IA` h1 is visually tiny and sessions show title only (no timestamp/preview), making later recall harder. **Command:** `/impeccable polish` (+ `/impeccable animate` for the dots).

## Persona Red Flags

**Sam (accessibility-dependent):** Strong baseline — `aria-label` on icon buttons, `aria-current` on active session, `role=alert` on rate limit, focus-visible rings, 44px targets. Red flags: (1) send-failure state is never announced (no live region for request errors); (2) the mobile drawer has no Escape-to-close for keyboard users; (3) verify `prose-code:text-primary-300` on `bg-background/60` hits 4.5:1 in dark mode.

**Casey (distracted mobile, slow connection):** The worst-hit persona for the P1 silent-failure — Casey on 3G is the most likely to trigger a failed/slow send, and loses the typed question with no recovery. Otherwise well served (bottom input, drawer, 44px send).

**Estudiante IESTP (project persona — mixed level, phone, modest hardware, Ollama may be slow/down):** The P1 + P2 issues land squarely here. When the local model is down (a documented, expected state), this surface currently shows nothing — contradicting the "resilient fallback" principle the rest of the system honors.

## Minor Observations

- Sidebar empty-state uses a hand-styled raw `<button>` instead of `<Button>` — same look, divergent source.
- Quota counter only signals at 0; no low-threshold warning (e.g. amber at ≤3 remaining).
- No timestamps/relative time on messages or sessions.
- `prose-gray` on assistant bubbles is a hardcoded prose theme vs the semantic tokens used elsewhere (works, but inconsistent with the token discipline).

## Questions to Consider

- What does a student see when Ollama is down mid-question? (Today: nothing.)
- Should deleting a conversation be *undoable* rather than *confirmed*?
- Should a slow (>20s) local response be cancellable, with a retry on the last turn?
