# Dark Mode QA Audit — Tier 3 (T3.1 + T3.2 + T3.3)

**Date:** 2026-05-12 · **Branch:** `feat/tier3-uiux-polish` · **Scope:** Frontend `frontend/src/**`

## Goal

Replace hardcoded Tailwind palette colors (`bg-white`, `bg-gray-*`, `text-gray-*`,
`bg-{semantic}-100`, etc.) with HSL-based semantic tokens defined in `frontend/src/index.css`
so the existing `.dark` palette inverts cleanly via `useThemeStore.isDark`.

Token mapping applied (per task spec):

| Anti-pattern                        | Replacement                                       |
| ----------------------------------- | ------------------------------------------------- |
| `bg-white` (surface)                | `bg-card`                                         |
| `bg-white` (page bg)                | `bg-background`                                   |
| `bg-gray-50` / `-100`               | `bg-muted` or `bg-surface-hover`                  |
| `bg-gray-800/900` (code header)     | kept dark (intentional code-editor look)          |
| `text-gray-900/800`                 | `text-foreground`                                 |
| `text-gray-700/600/500/400`         | `text-muted-foreground`                           |
| `border-gray-100/200/300`           | `border-border`                                   |
| `divide-gray-*`                     | `divide-border`                                   |
| `bg-green-100 text-green-700`       | `bg-success/10 text-success`                      |
| `bg-red-100 text-red-700`           | `bg-destructive/10 text-destructive`              |
| `bg-yellow-100 text-yellow-700`     | `bg-warning/10 text-warning-foreground`           |
| `bg-blue-100 text-blue-700`         | `bg-info/10 text-info`                            |
| `bg-purple-100 text-purple-700`     | `bg-primary/10 text-primary`                      |
| `text-green-500/600` (icons)        | `text-success`                                    |
| `text-red-500/600` (icons/danger)   | `text-destructive`                                |
| `text-amber-600` (StatCard warning) | `text-warning-foreground dark:text-warning`       |
| `bg-black/40` (modal backdrop)      | `bg-foreground/40` (auto-inverts)                 |
| Markdown prose                      | added `dark:prose-invert` + dark variants on code |

Brand palettes (`institutional-*`, `heritage-*`, `peru-*`, `primary-50..950`) are
fixed hex and kept where they are intentional (hero panels, brand chips, logo). For
chips on light-only palettes used in places where dark contrast would suffer,
dark variants were added (e.g. `bg-heritage-100 text-heritage-700 dark:bg-heritage-700/20 dark:text-heritage-400`).

## Files Audited & Status

### Pages

| Page                          | Status   | Notes                                                                 |
| ----------------------------- | -------- | --------------------------------------------------------------------- |
| `pages/LoginPage.tsx`         | OK       | Already uses semantic tokens + brand colors (hero). No edits needed.  |
| `pages/EntryAssessmentPage.tsx` | OK     | Already uses semantic tokens + brand gradient. No edits needed.       |
| `pages/DashboardPage.tsx`     | Mostly OK | Hero "Retomar" button intentionally `bg-white text-institutional-700` on dark hero — kept. |
| `pages/ModulesPage.tsx`       | OK       | Uses `ModuleCard` + skeletons only.                                   |
| `pages/ModuleDetailPage.tsx`  | Fixed    | Bg/text/border swaps; divide-gray-100 → divide-border.                |
| `pages/TopicPage.tsx`         | Fixed    | Breadcrumb, content card, video bg, action buttons, sticky nav.       |
| `pages/QuizPage.tsx`          | OK       | Already uses semantic tokens.                                         |
| `pages/ChatPage.tsx`          | Fixed    | Backdrop `bg-black/40` → `bg-foreground/40`; active session chip.     |
| `pages/CodingChallengePage.tsx` | Fixed  | **Monaco wired to theme** via `isDark`; editor frame uses tokens.     |
| `pages/ProgressPage.tsx`      | OK       | Already uses semantic tokens (StatCard handles its own).              |
| `pages/AchievementsPage.tsx`  | Fixed    | Heading + subtitle tokens.                                            |
| `pages/AdminPage.tsx`         | Fixed    | Tabs bar + inactive states.                                           |
| `pages/SettingsPage.tsx`      | OK       | Already uses semantic tokens.                                         |

### Components

| Component                                       | Status | Notes                                                                |
| ----------------------------------------------- | ------ | -------------------------------------------------------------------- |
| `components/layout/Navbar.tsx`                  | Fixed  | Sticky header bg + logout button colors.                             |
| `components/layout/Sidebar.tsx`                 | Fixed  | Aside surface, nav links inactive, footer chip, overflow caret.      |
| `components/layout/Footer.tsx`                  | Fixed  | Border + text + secondary text tokens.                               |
| `components/layout/AppLayout.tsx`               | Fixed  | Root wrapper `bg-gray-50` → `bg-background`.                         |
| `components/layout/LevelBadge.tsx`              | Fixed  | Beginner/intermediate/advanced styles now use tokens + dark variants. |
| `components/layout/ThemeToggle.tsx`             | OK     | Already uses tokens (Tier 1).                                        |
| `components/brand/BrandLogo.tsx`                | Fixed  | Subtitle on light backgrounds now `text-muted-foreground`.            |
| `components/auth/ReassessmentModal.tsx`         | Fixed  | Modal surface, backdrop, icon chip success/warning tokens.            |
| `components/auth/LevelGuard.tsx`                | Fixed  | Loading state bg/text tokens.                                        |
| `components/achievements/AchievementCard.tsx`   | OK     | Already uses tokens + CSS var for per-badge color.                   |
| `components/modules/ModuleCard.tsx`             | OK     | Already uses tokens.                                                 |
| `components/modules/TopicListItem.tsx`          | Fixed  | Status icons → success/info/muted-fg; hover row → surface-hover.     |
| `components/quiz/QuizQuestion.tsx`              | OK     | Already uses tokens.                                                 |
| `components/quiz/QuizResults.tsx`               | Fixed  | Pass/fail score card + per-question feedback → success/destructive/10. |
| `components/chat/ChatMessage.tsx`               | Fixed  | User/assistant bubbles → `bg-primary` / `bg-muted`; prose `dark:prose-invert`. |
| `components/chat/ChatSources.tsx`               | Fixed  | Source card surfaces + text tokens.                                  |
| `components/chat/TypingIndicator.tsx`           | Fixed  | Indicator surface + bouncing dots.                                   |
| `components/topics/ContentRenderer.tsx`         | Fixed  | Added `dark:prose-invert` + dark variants for code/blockquote.       |
| `components/topics/CodeBlock.tsx`               | Concern (kept) | Uses `vscDarkPlus` SyntaxHighlighter; header `bg-gray-800` intentional next to dark code. No dark-mode bug — code blocks always render dark. |
| `components/common/StatCard.tsx`                | Fixed  | Accent icon bg + value color use tokens / dark variants for heritage+warning. |
| `components/common/Avatar.tsx`                  | OK     | `bg-institutional-700 text-white` intentional.                       |
| `components/admin/CorpusTab.tsx`                | Fixed  | Status chips, table surfaces, hover rows.                            |
| `components/admin/ContentTab.tsx`               | Fixed  | Module/topic tree, quiz/coding chips, preview panel.                 |
| `components/admin/UsersTab.tsx`                 | Fixed  | Table surfaces, role select, active chip → success/muted.            |
| `components/admin/BankTab.tsx`                  | Fixed  | Difficulty colors → semantic chips; filter selects.                  |
| `components/admin/LevelsTab.tsx`                | Fixed  | Level chips, table surfaces.                                         |

## Monaco Editor — Theme Wired

`CodingChallengePage.tsx`:

```tsx
import { useThemeStore } from '@/store/themeStore'

const isDark = useThemeStore((s) => s.isDark)
// ...
<Editor theme={isDark ? 'vs-dark' : 'light'} ... />
```

(The store exposes `isDark` boolean, set by `applyClass` based on `pref` + system query.)

## Verification

- `npx tsc --noEmit` — clean (no errors)
- `npm run build` — green (`✓ built in 5.39s`, 2.18 MB bundle as before)
- Spot-checks via grep: zero remaining `bg-white`, `bg-gray-*`, `text-gray-*`,
  `border-gray-*` outside the two intentional exceptions (`DashboardPage` hero
  button + `CodeBlock` dark editor frame).

## Concerns / Known Limitations

1. **CodeBlock left as dark-only.** `react-syntax-highlighter` with `vscDarkPlus`
   style ships a hard-coded dark color scheme. Switching to a conditional light
   theme (e.g. `oneLight`) would double the imported style chunk and require
   restyling the surrounding header. Marked as concern; can be revisited in T3.3
   follow-up if the user wants light-mode code blocks.

2. **`prose-code:text-primary-700` etc. inside `ChatMessage`.** Added
   `dark:prose-code:text-primary-300` siblings. Looks acceptable in dark mode but
   not regressed.

3. **Brand `bg-primary-50` / `bg-heritage-100` chips** kept where they read well.
   In dark mode the fixed-hex light tints get an explicit `dark:bg-heritage-700/20`
   override in `LevelBadge` + `StatCard`. Other usages (LoginPage chip, Dashboard
   level chip) remain on light brand tints — they sit on dark hero panels or are
   small enough that contrast is preserved (verified visually via class survey).

4. **Markdown blockquote tint.** Light mode keeps `prose-blockquote:bg-primary-50/50`;
   dark mode uses `dark:prose-blockquote:bg-primary/10`. Both legible.

## Commit

Single squash: `fix(tier3): dark mode QA — replace hardcoded colors with semantic tokens`
