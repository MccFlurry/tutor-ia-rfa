---
target: frontend/src/pages/ChatPage.tsx
total_score: 34
p0_count: 0
p1_count: 0
timestamp: 2026-05-31T21-49-01Z
slug: frontend-src-pages-chatpage-tsx
---
# Critique — ChatPage (RAG Tutor) — re-run after harden + polish

Target: `frontend/src/pages/ChatPage.tsx` (+ `ChatMessage`, `TypingIndicator`, sessions sidebar). Register: product.

## Design Health Score

| # | Heuristic | Score | Δ | Key Issue |
|---|-----------|-------|----|-----------|
| 1 | Visibility of System Status | 4 | +1 | Now comprehensive: send-error alert, SR live region, low-quota amber, timestamps. |
| 2 | Match System / Real World | 4 | — | Clear Spanish peruano. |
| 3 | User Control and Freedom | 3 | +1 | Cancel + ESC + confirm-cancel + retry. No true undo on delete (backend has no soft-delete). |
| 4 | Consistency and Standards | 4 | +1 | Radii on token scale (send `rounded-md`), shared `<Button>` where it fits. |
| 5 | Error Prevention | 3 | +1 | Destructive delete now confirmed; sends guarded. No textarea maxlength. |
| 6 | Recognition Rather Than Recall | 3 | — | Session/message timestamps help; still no session search/jump. |
| 7 | Flexibility and Efficiency | 3 | — | Enter/Shift+Enter, cancel; no Cmd+K-style accelerators. |
| 8 | Aesthetic and Minimalist Design | 4 | +1 | Stronger title, smoother motion, token-consistent. |
| 9 | Error Recovery | 3 | +2 | Failure restores the question + inline Reintentar + toast. Message still generic for non-429. |
| 10 | Help and Documentation | 3 | — | Teaching empty states + input hint. |
| **Total** | | **34/40** | **+7** | **Good (top of band)** — was 27/40 Acceptable. |

## Anti-Patterns Verdict

**Does this look AI-generated? No.** On-brand product chat; no bans triggered.

**Deterministic scan (`detect.mjs`):** **0 findings** (was 3 `bounce-easing`). The `animate-bounce` typing dots were replaced with a smooth `typing-dot` keyframe (`ease-in-out`, `motion-reduce:animate-none`), so the detector is now clean across the page and chat components.

**Visual overlays:** none — no browser automation this session. Review is source + detector.

## Overall Impression

The unhappy path is now handled, which was the whole point: a failed send preserves the student's question and offers an in-context retry, a slow local response can be cancelled, and the destructive delete is guarded. Combined with the consistency + motion polish, the surface moved from "competent happy-path chat" to "resilient and on-system." The remaining gaps are refinements, not holes.

## What's Working

1. **Resilient send.** AbortController-backed cancel, question-restore on failure, inline `Reintentar`, hook toast, SR live region. The exact failure modes this audience hits (Ollama down/slow, 429, network) now degrade visibly and recoverably.
2. **On-system consistency.** Send button on the token radius scale, shared `<Button>` in the sidebar empty-state, semantic-token prose (no hardcoded `prose-gray`), smooth typing motion with a reduced-motion fallback.
3. **Comprehensive status + recall.** Skeletons, typing, optimistic echo, low-quota amber warning, session recency + message timestamps for orientation.

## Remaining Issues

- **[P2] Generic failure copy.** The inline error reads "No se pudo enviar tu mensaje" for every non-429 failure. For the IESTP context where Ollama-down is an *expected* state, a tailored message ("El tutor no está disponible ahora, intenta en un momento") for 503/network would be clearer than a catch-all. → `/impeccable clarify`
- **[P3] No session search / jump.** With many conversations, the student scans the list. Timestamps help, but a filter or jump would close the recall gap. → `/impeccable layout` (minor)
- **[P3] No keyboard accelerators beyond Enter.** No new-chat shortcut (e.g. Ctrl+K). Acceptable for the audience. → minor
- **Minor:** textarea has no `maxLength` (a huge paste is unbounded); chat bubble `rounded-2xl` (16px) is an intentional chat affordance but isn't a documented token — worth a line in DESIGN.md if it spreads.

## Persona Red Flags (largely resolved)

- **Sam (a11y):** SR live region added (`role=status`), Escape closes the mobile drawer, dark-mode code contrast verified ≥4.5:1. Clean.
- **Casey (mobile, slow net):** The failed-send question-loss that hit Casey hardest is fixed — text is preserved and re-sendable.
- **Estudiante IESTP (project persona):** When the local model is down, the surface now responds (error + retry + cancel) instead of going silent. The only residual is the generic message above (P2).

## Minor Observations

- Quota now warns amber at ≤3 (was silent until 0).
- Message timestamps are subtle (`text-[11px]`), aligned per side.
- Session recency uses `Intl.RelativeTimeFormat('es')`.

## Questions to Consider

- Worth distinguishing "Ollama down" from a generic network error in the failure copy?
- Should the in-flight Stop also drop a "Generación detenida" confirmation, or stay silent?
