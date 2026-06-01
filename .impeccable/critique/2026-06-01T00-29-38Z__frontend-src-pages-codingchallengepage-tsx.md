---
target: frontend/src/pages/CodingChallengePage.tsx
total_score: 39
p0_count: 0
p1_count: 0
timestamp: 2026-06-01T00-29-38Z
slug: frontend-src-pages-codingchallengepage-tsx
---
## Design Health Score (re-run after fixes)

| # | Heuristic | Score | Δ | Key Issue |
|---|-----------|-------|----|-----------|
| 1 | Visibility of System Status | 4 | +1 | Result now scrolls into view + takes focus after submit; best score refreshes |
| 2 | Match System / Real World | 4 | — | Clear Spanish, difficulty labels, breadcrumb, familiar editor |
| 3 | User Control and Freedom | 4 | +1 | Draft persists across reloads; reset is confirmed; load failure retries |
| 4 | Consistency and Standards | 4 | +1 | Reset now confirms like regenerate; score color + difficulty chip on-system |
| 5 | Error Prevention | 3 | — | Reset confirmed + autosave added; resubmitting identical code is still unguarded and submit isn't confirmed |
| 6 | Recognition Rather Than Recall | 4 | — | Description, hints, results, best score visible |
| 7 | Flexibility and Efficiency | 4 | — | Ctrl+Enter, Monaco, regenerate |
| 8 | Aesthetic and Minimalist Design | 4 | +1 | "Difícil" off destructive-red; mid-band score contrast fixed |
| 9 | Error Recovery | 4 | +1 | Load failure → Reintentar; 404 distinct; draft survives reloads |
| 10 | Help and Documentation | 4 | — | Description + hints + AI feedback + nudges |
| **Total** | | **39/40** | **+5** | **Excellent — minor polish only** |

## Anti-Patterns Verdict

No AI slop. `detect.mjs --json` → `[]`. No gradient, eyebrow, side-stripe, or glass.

**Visual overlays:** No browser-automation tool in this environment → CLI detector + source review only (fallback signal, no overlay claimed).

## Overall Impression

Trend 34 → 39. The work-protection gaps are closed: the editor draft now survives reloads (localStorage, like the quiz), and the one button that discarded code is relabeled "Reiniciar a la plantilla" and asks for confirmation. Load failure recovers with a retry instead of mislabeling itself "no encontrado", and the AI feedback is brought into view after submit. The single remaining 3 (Error Prevention) is a genuine, minor residual, not a defect.

## What's Working

1. **The student's work is protected.** The editor draft is saved per challenge and rehydrated on load, so a reload, accidental back, or tab close no longer costs effort. The destructive "reset to template" is now an explicit, confirmed action — matching the care the regenerate flow already had.
2. **Resilient load + visible feedback.** A failed fetch shows a real error with "Reintentar" (refetch), a genuine 404 stays "no encontrado", and after submit the AI evaluation scrolls into view and takes focus so it's actually read (it rendered above the editor on mobile before).
3. **Editor ergonomics stay strong** — lazy Monaco, light/dark theme, Ctrl+Enter — now without the color nits (neutral "Difícil", higher-contrast mid-band score) and with a fresh best-score after each submit.

## Priority Issues

No P0/P1/P2 remain. Optional polish:

**[P3] Resubmitting unchanged code is unguarded.** After a result, "Reenviar código" re-runs the AI evaluation even if the code is identical, spending an LLM call for a near-identical (and, given LLM nondeterminism, possibly different) score. A light guard ("no has cambiado el código") or disabling resubmit until an edit would save calls. `/impeccable harden`

**[P3] Only the best *score* is recoverable, not the best *code*.** The draft holds the current editor content; a student's highest-scoring attempt isn't retrievable if overwritten. A "ver mi mejor envío" affordance would help. `/impeccable craft` (small feature)

**[P3] EditorFallback contrast.** While Monaco loads, `bg-foreground/90` + `text-muted-foreground` is low-contrast (brief). `/impeccable polish`

## Persona Red Flags

All clear.
- **Valentina (effort):** her code survives a reload, and resetting to the template now asks first — no more silent loss.
- **Casey (mobile):** after submit the evaluation scrolls into view, so she sees her score and feedback without hunting.
- **Alex (power user):** Ctrl+Enter and Monaco intact; a mid-problem reload restores the draft.

## Minor Observations

- The two post-result buttons are now clearly distinct (outline "Reiniciar a la plantilla" with confirm vs primary "Reenviar código").
- Draft TTL is 7 days; old drafts expire on their own.

## Questions to Consider

- Should "Reenviar código" be disabled until the code changes, to avoid spending an AI evaluation on identical input?
- Is showing the best *score* enough, or should a student be able to view/restore their best-scoring submission?
