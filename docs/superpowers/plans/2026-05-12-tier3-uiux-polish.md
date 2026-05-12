# Tier 3 UI/UX Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish frontend before SUS pilot (Sprint 8) across 4 buckets: mobile 375px, loading/transitions, dark mode QA, empty/error states.

**Architecture:** 5 phases linear. Fase 0 builds reusable foundations. Fases 1-4 consume foundations per bucket. Fase 5 gate (build + Lighthouse + docs). Each task ends with TypeScript build verify + commit.

**Tech Stack:** React 18 + TypeScript 5.7 + Vite 5 + Tailwind 3 + framer-motion (new) + Lucide icons + react-router-dom v6. No test framework — manual QA + `tsc --noEmit` + Lighthouse mobile audit. Existing `EmptyState` and `ErrorBoundary` are reused/extended (not recreated).

**Spec:** `docs/superpowers/specs/2026-05-12-tier3-uiux-polish-design.md`

**Cap:** 5 days. If exceeded, stop + consult user per CLAUDE.md escalation protocol.

---

## Phase 0 — Foundations

### Task 0.1: Install framer-motion

**Files:**
- Modify: `frontend/package.json` (auto)
- Modify: `frontend/package-lock.json` (auto)

- [ ] **Step 1: Install dependency**

Run from `frontend/`:
```bash
npm install framer-motion
```
Expected: `framer-motion` added under `dependencies` in `package.json`.

- [ ] **Step 2: Verify install**

Run from `frontend/`:
```bash
npx tsc --noEmit
```
Expected: PASS (no errors).

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "build(tier3): add framer-motion dependency"
```

---

### Task 0.2: Extend EmptyState to support illustration

Existing `EmptyState` only takes `icon: LucideIcon`. Tier 3 needs SVG illustration variant. Extend interface to accept either `icon` OR `illustration` (string path or ReactNode).

**Files:**
- Modify: `frontend/src/components/common/EmptyState.tsx`

- [ ] **Step 1: Replace EmptyState content**

Replace entire file contents with:

```tsx
import * as React from 'react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: LucideIcon
  illustration?: string | React.ReactNode
  illustrationAlt?: string
  title: string
  description?: React.ReactNode
  action?: React.ReactNode
  className?: string
}

export default function EmptyState({
  icon: Icon,
  illustration,
  illustrationAlt,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  const showIllustration = !!illustration
  const showIcon = !showIllustration && !!Icon

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
    >
      {showIllustration && (
        <div className="mb-6 max-w-[280px] w-full">
          {typeof illustration === 'string' ? (
            <img
              src={illustration}
              alt={illustrationAlt ?? ''}
              className="w-full h-auto select-none"
              loading="lazy"
              draggable={false}
            />
          ) : (
            illustration
          )}
        </div>
      )}
      {showIcon && Icon && (
        <div
          className="w-14 h-14 bg-primary-50 rounded-full flex items-center justify-center mb-4"
          aria-hidden="true"
        >
          <Icon className="w-7 h-7 text-primary-500" />
        </div>
      )}
      <h3 className="text-base font-semibold text-foreground mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-md mb-4">{description}</p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
```

- [ ] **Step 2: TypeScript verify**

Run from `frontend/`:
```bash
npx tsc --noEmit
```
Expected: PASS. No callers break (existing `icon` prop still works).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/common/EmptyState.tsx
git commit -m "feat(tier3): extend EmptyState to accept illustration prop"
```

---

### Task 0.3: Create Skeleton component

**Files:**
- Create: `frontend/src/components/common/Skeleton.tsx`

- [ ] **Step 1: Write Skeleton component**

Create `frontend/src/components/common/Skeleton.tsx`:

```tsx
import * as React from 'react'
import { cn } from '@/lib/utils'

type SkeletonVariant = 'text' | 'rect' | 'circle' | 'card'

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: SkeletonVariant
  width?: string
  height?: string
}

const variantClass: Record<SkeletonVariant, string> = {
  text: 'h-4 rounded',
  rect: 'rounded-lg',
  circle: 'rounded-full',
  card: 'rounded-2xl',
}

export default function Skeleton({
  variant = 'text',
  width,
  height,
  className,
  style,
  ...rest
}: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'bg-muted motion-safe:animate-pulse',
        variantClass[variant],
        className
      )}
      style={{ width, height, ...style }}
      {...rest}
    />
  )
}

export function SkeletonLine({
  width = '100%',
  className,
}: {
  width?: string
  className?: string
}) {
  return <Skeleton variant="text" width={width} className={className} />
}

export function SkeletonCard({ className }: { className?: string }) {
  return <Skeleton variant="card" className={cn('h-32 w-full', className)} />
}
```

- [ ] **Step 2: TypeScript verify**

```bash
cd frontend && npx tsc --noEmit
```
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/common/Skeleton.tsx
git commit -m "feat(tier3): add Skeleton component for loading states"
```

---

### Task 0.4: Create PageTransition component

**Files:**
- Create: `frontend/src/components/common/PageTransition.tsx`

- [ ] **Step 1: Write PageTransition component**

Create `frontend/src/components/common/PageTransition.tsx`:

```tsx
import * as React from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { useLocation } from 'react-router-dom'

interface PageTransitionProps {
  children: React.ReactNode
}

export default function PageTransition({ children }: PageTransitionProps) {
  const location = useLocation()
  const prefersReducedMotion = useReducedMotion()

  if (prefersReducedMotion) {
    return <>{children}</>
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}
```

- [ ] **Step 2: TypeScript verify**

```bash
cd frontend && npx tsc --noEmit
```
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/common/PageTransition.tsx
git commit -m "feat(tier3): add PageTransition wrapper with framer-motion"
```

---

### Task 0.5: Download + recolor 6 undraw SVGs

undraw.co is open-source MIT-style license. Download these illustrations to `frontend/src/assets/empty/`. Then replace primary fill (default `#6c63ff`) with brand `#1e3a8a` (institutional-700).

**Files:**
- Create: `frontend/src/assets/empty/welcome.svg`
- Create: `frontend/src/assets/empty/locked.svg`
- Create: `frontend/src/assets/empty/chat-empty.svg`
- Create: `frontend/src/assets/empty/progress-empty.svg`
- Create: `frontend/src/assets/empty/achievements-empty.svg`
- Create: `frontend/src/assets/empty/upload.svg`

- [ ] **Step 1: Create assets folder**

```bash
mkdir -p frontend/src/assets/empty
```

- [ ] **Step 2: Download illustrations**

Visit https://undraw.co/illustrations and download these (or equivalents):

| Asset | Search term | Save as |
|-------|-------------|---------|
| welcome.svg | "welcome" or "starting" | `frontend/src/assets/empty/welcome.svg` |
| locked.svg | "locked" or "secure" | `frontend/src/assets/empty/locked.svg` |
| chat-empty.svg | "chat" or "messaging" | `frontend/src/assets/empty/chat-empty.svg` |
| progress-empty.svg | "progress" or "growth" | `frontend/src/assets/empty/progress-empty.svg` |
| achievements-empty.svg | "achievement" or "trophy" | `frontend/src/assets/empty/achievements-empty.svg` |
| upload.svg | "upload" or "files" | `frontend/src/assets/empty/upload.svg` |

undraw default color: `#6c63ff` (some variants `#7367f0`). Choose color via undraw color picker → set hex `#1e3a8a` before download.

- [ ] **Step 3: Verify recolor**

Open each SVG in editor, search `6c63ff`, `7367f0`. Replace remaining occurrences with `1e3a8a`. Search `7e22ce`, `4338ca` (rare variants) too.

```bash
cd /c/tutor-ia-rfa && grep -l "6c63ff\|7367f0" frontend/src/assets/empty/*.svg
```
Expected: empty output (no matches).

- [ ] **Step 4: Vite build verify**

```bash
cd frontend && npm run build
```
Expected: SVGs bundled correctly, build green.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/assets/empty/
git commit -m "feat(tier3): add undraw illustrations for empty states (brand-recolored)"
```

---

## Phase 1 — Mobile 375px Refino

Each task: open page in Chrome DevTools Device Toolbar at 375×667 (iPhone SE), audit checklist, apply fixes, screenshot before/after, commit.

Common checklist (apply to every page):
- No horizontal overflow
- Touch targets ≥44×44px
- Body text ≥14px line-height ≥1.5
- Forms input `font-size: 16px` minimum (iOS)
- Sticky bars use `pb-{height}` on main content
- Tables stack or scroll horizontal explicit
- Use `dvh` not `vh` if keyboard interferes (Chat)

### Task 1.1: LoginPage + EntryAssessmentPage mobile

**Files:**
- Modify: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/pages/EntryAssessmentPage.tsx`

- [ ] **Step 1: Audit LoginPage at 375px**

Open `npm run dev` → http://localhost:5173/login → DevTools 375×667. Note issues:
- Split 2-col hero collapses correctly?
- Form inputs `font-size: 16px`?
- Submit button height ≥44px?
- Error messages visible without scroll?

Take screenshot `docs/screenshots/mobile-before-login.png`.

- [ ] **Step 2: Fix LoginPage**

Common fixes (verify each):
- Inputs: add `text-base` (16px) or set `font-size: 16px` explicitly
- Buttons: ensure `min-h-[44px]` on submit and toggle
- Hero panel: hide on `< lg` if blocks form (Tier 1 likely already done — verify)
- Padding: `px-4` on mobile, `px-8` on `sm:`

Apply fixes inline as needed. Save.

- [ ] **Step 3: Audit EntryAssessmentPage at 375px**

Navigate /assessment in browser (or modify URL). Verify:
- Radio buttons each ≥44px tap target
- Progress bar visible without scroll
- Wizard nav buttons (Anterior/Siguiente) tap-reach bottom

Screenshot `docs/screenshots/mobile-before-assessment.png`.

- [ ] **Step 4: Fix EntryAssessmentPage**

Apply fixes inline.

- [ ] **Step 5: Verify build**

```bash
cd frontend && npx tsc --noEmit
```
Expected: PASS.

- [ ] **Step 6: Take after screenshots**

Capture `docs/screenshots/mobile-after-login.png` and `mobile-after-assessment.png`.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/LoginPage.tsx frontend/src/pages/EntryAssessmentPage.tsx docs/screenshots/
git commit -m "fix(tier3): mobile 375px refinements for LoginPage and EntryAssessmentPage"
```

---

### Task 1.2: DashboardPage + ModulesPage mobile

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/pages/ModulesPage.tsx`

- [ ] **Step 1: Audit DashboardPage at 375px**

Verify:
- 4-col stats grid stacks to 1-col on mobile (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-4` — already configured per Tier 2)
- Hero card text wraps, CTA button accessible
- 3 recommended modules stack vertically
- Recent achievements grid stacks

Screenshot before.

- [ ] **Step 2: Fix DashboardPage**

Apply fixes inline. Likely already fine post-Tier 2; just verify.

- [ ] **Step 3: Audit ModulesPage at 375px**

Verify:
- ModuleCard grid stacks to 1-col on mobile
- Locked module banner readable
- Card touch targets ≥44px

- [ ] **Step 4: Fix ModulesPage**

Apply fixes inline.

- [ ] **Step 5: Verify + screenshots + commit**

```bash
cd frontend && npx tsc --noEmit
```
After capture:
```bash
git add frontend/src/pages/DashboardPage.tsx frontend/src/pages/ModulesPage.tsx docs/screenshots/
git commit -m "fix(tier3): mobile 375px refinements for Dashboard and ModulesPage"
```

---

### Task 1.3: ModuleDetailPage + TopicPage mobile

**Files:**
- Modify: `frontend/src/pages/ModuleDetailPage.tsx` (verify path)
- Modify: `frontend/src/pages/TopicPage.tsx` (verify path)

- [ ] **Step 1: Audit ModuleDetailPage at 375px**

Verify:
- Breadcrumb wraps gracefully
- Topic list items: tap target ≥44px (entire row clickable)
- Status badge (✅/🔵/⬜) visible

- [ ] **Step 2: Fix ModuleDetailPage**

Apply fixes inline.

- [ ] **Step 3: Audit TopicPage at 375px**

Verify:
- Markdown content readable (font-size ≥16px ideal)
- Code blocks scroll horizontal on overflow (not break layout)
- YouTube iframe 16:9 maintains aspect ratio (`aspect-video` class)
- Sticky Anterior/Siguiente bar — main content has `pb-20` or similar to clear it
- "Consultar Tutor IA" modal triggers correctly
- "Marcar completado" button ≥44px

- [ ] **Step 4: Fix TopicPage**

Common fix: ensure markdown `prose` has `prose-sm sm:prose-base`. Add `pb-24` to main content if sticky bar present.

- [ ] **Step 5: Verify + screenshots + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/ModuleDetailPage.tsx frontend/src/pages/TopicPage.tsx docs/screenshots/
git commit -m "fix(tier3): mobile 375px refinements for ModuleDetail and TopicPage"
```

---

### Task 1.4: QuizPage + ChatPage mobile

**Files:**
- Modify: `frontend/src/pages/QuizPage.tsx`
- Modify: `frontend/src/pages/ChatPage.tsx`

- [ ] **Step 1: Audit QuizPage at 375px**

Verify:
- Question text wraps
- 4 options: each ≥44px tap target
- Sticky submit button bottom, main has `pb-20`
- Progress indicator visible

- [ ] **Step 2: Fix QuizPage**

Apply fixes inline.

- [ ] **Step 3: Audit ChatPage at 375px**

Critical mobile considerations:
- 2-col layout (sidebar + chat) MUST collapse: sidebar becomes drawer or full-screen toggle
- Textarea: input `font-size: 16px`, autogrow works
- Keyboard appears: use `dvh` units not `vh` for chat container height
- Send button ≥44px
- Sources collapsible

- [ ] **Step 4: Fix ChatPage**

If layout is `grid-cols-[280px_1fr] lg:grid-cols-[280px_1fr]`, change to `grid-cols-1 lg:grid-cols-[280px_1fr]` and add drawer toggle for sessions on mobile.

If chat container uses `h-screen`, replace with `h-dvh` or `min-h-dvh`.

- [ ] **Step 5: Verify + screenshots + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/QuizPage.tsx frontend/src/pages/ChatPage.tsx docs/screenshots/
git commit -m "fix(tier3): mobile 375px refinements for Quiz and ChatPage"
```

---

### Task 1.5: CodingChallengePage + ProgressPage + AchievementsPage mobile

**Files:**
- Modify: `frontend/src/pages/CodingChallengePage.tsx`
- Modify: `frontend/src/pages/ProgressPage.tsx`
- Modify: `frontend/src/pages/AchievementsPage.tsx`

- [ ] **Step 1: Audit CodingChallengePage at 375px**

Verify:
- Split 2-col (descripción + editor) collapses to stacked
- Monaco editor: min-height ~300px on mobile, no horizontal expansion
- "Regenerar con IA" + "Enviar" buttons ≥44px
- AI chip visible

- [ ] **Step 2: Fix CodingChallengePage**

If layout uses `grid-cols-2`, change to `grid-cols-1 lg:grid-cols-2`. Monaco needs explicit height attribute (e.g., `height="320"` on mobile, `"500"` on desktop — use `useMediaQuery` or fixed).

- [ ] **Step 3: Audit ProgressPage at 375px**

Verify:
- 4 StatCards stack
- Module progress bars span full width
- Achievement grid stacks 2-col → 1-col

- [ ] **Step 4: Fix ProgressPage**

Apply fixes inline.

- [ ] **Step 5: Audit AchievementsPage at 375px**

Verify:
- Badge grid 2-col on mobile, 3-col `sm:`
- Earned vs locked states visible

- [ ] **Step 6: Fix AchievementsPage**

Apply fixes inline.

- [ ] **Step 7: Verify + screenshots + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/CodingChallengePage.tsx frontend/src/pages/ProgressPage.tsx frontend/src/pages/AchievementsPage.tsx docs/screenshots/
git commit -m "fix(tier3): mobile 375px refinements for Coding, Progress, AchievementsPage"
```

---

### Task 1.6: AdminPage mobile (best-effort)

**Files:**
- Modify: `frontend/src/pages/AdminPage.tsx` (verify path)

- [ ] **Step 1: Audit AdminPage at 375px**

Verify minimum: tabs visible (5 tabs), no horizontal overflow, tables scroll horizontal if needed.

- [ ] **Step 2: Apply minimal fixes**

Best-effort. If tabs overflow, allow horizontal scroll on TabsList. Tables: wrap in `<div class="overflow-x-auto">`.

- [ ] **Step 3: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/AdminPage.tsx docs/screenshots/
git commit -m "fix(tier3): mobile 375px best-effort refinements for AdminPage"
```

---

### Task 1.7: Lighthouse mobile audit + docs

**Files:**
- Create: `docs/audit-mobile.md`

- [ ] **Step 1: Install Lighthouse CLI if missing**

```bash
npm i -g lighthouse
```

- [ ] **Step 2: Run Lighthouse mobile audit per page**

Start dev server: `cd frontend && npm run dev`. For each student page:

```bash
lighthouse http://localhost:5173/login --emulated-form-factor=mobile --only-categories=performance,accessibility,best-practices --output=json --output-path=./lighthouse-login.json --quiet
```
Repeat for: /dashboard, /modules, /modules/1, /topics/1, /quiz/1, /chat, /coding/1, /progress, /achievements (use real IDs from seeded data).

- [ ] **Step 3: Write docs/audit-mobile.md**

Template per page:

```markdown
## /dashboard

**Lighthouse Mobile:**
- Performance: 78
- Accessibility: 92
- Best Practices: 87

**Issues found:** Touch target on sidebar collapse <44px (fixed). Status badge wrapped to 2 lines on narrow viewport (fixed).

**Screenshots:**
- Before: ![dashboard-before](screenshots/mobile-before-dashboard.png)
- After: ![dashboard-after](screenshots/mobile-after-dashboard.png)
```

- [ ] **Step 4: Verify thresholds met**

Confirm:
- Accessibility ≥85 on all student pages
- Performance ≥70 on /modules and /dashboard

- [ ] **Step 5: Commit**

```bash
git add docs/audit-mobile.md docs/screenshots/
git commit -m "docs(tier3): mobile 375px audit results and Lighthouse reports"
```

---

## Phase 2 — Loading + Transitions

### Task 2.1: Add PageTransition to AppLayout

**Files:**
- Modify: `frontend/src/components/layout/AppLayout.tsx`

- [ ] **Step 1: Wrap Outlet with PageTransition**

Locate `<Outlet />` in `AppLayout.tsx`. Wrap with `<PageTransition>`:

```tsx
import PageTransition from '@/components/common/PageTransition'

// inside JSX, replace <Outlet /> with:
<PageTransition>
  <Outlet />
</PageTransition>
```

- [ ] **Step 2: Verify route transitions**

`npm run dev` → navigate between /dashboard ↔ /modules ↔ /progress. Verify fade+slide 200ms.

DevTools → Rendering → "Emulate CSS media feature prefers-reduced-motion: reduce" → confirm transitions disabled.

- [ ] **Step 3: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/components/layout/AppLayout.tsx
git commit -m "feat(tier3): wrap routes with PageTransition in AppLayout"
```

---

### Task 2.2: Dashboard + Modules skeletons

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/pages/ModulesPage.tsx`

- [ ] **Step 1: Replace Dashboard loading state with skeleton**

Locate `if (isLoading) return <spinner-or-loading />` in DashboardPage. Replace with skeleton matching final shape:

```tsx
import Skeleton, { SkeletonCard, SkeletonLine } from '@/components/common/Skeleton'

// inside the page
if (isLoading) {
  return (
    <div className="space-y-6">
      <Skeleton variant="card" className="h-32 w-full" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <SkeletonCard /><SkeletonCard /><SkeletonCard />
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Replace Modules loading state with skeleton**

```tsx
if (isLoading) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <SkeletonCard key={i} className="h-48" />
      ))}
    </div>
  )
}
```

- [ ] **Step 3: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/DashboardPage.tsx frontend/src/pages/ModulesPage.tsx
git commit -m "feat(tier3): Dashboard and Modules skeleton loading states"
```

---

### Task 2.3: TopicPage + QuizPage skeletons

**Files:**
- Modify: `frontend/src/pages/TopicPage.tsx`
- Modify: `frontend/src/pages/QuizPage.tsx`

- [ ] **Step 1: TopicPage skeleton**

```tsx
if (isLoading) {
  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <SkeletonLine width="40%" />
      <SkeletonLine width="80%" />
      <Skeleton variant="rect" className="h-48 w-full" />
      <SkeletonLine /><SkeletonLine /><SkeletonLine width="90%" />
    </div>
  )
}
```

- [ ] **Step 2: QuizPage skeleton**

```tsx
if (isLoading) {
  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <SkeletonLine width="30%" />
      <Skeleton variant="rect" className="h-20 w-full" />
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} variant="rect" className="h-14 w-full" />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/TopicPage.tsx frontend/src/pages/QuizPage.tsx
git commit -m "feat(tier3): Topic and Quiz skeleton loading states"
```

---

### Task 2.4: ChatPage + CodingChallengePage skeletons

**Files:**
- Modify: `frontend/src/pages/ChatPage.tsx`
- Modify: `frontend/src/pages/CodingChallengePage.tsx`

- [ ] **Step 1: ChatPage sessions skeleton**

When sessions list is loading:
```tsx
{sessionsLoading ? (
  <div className="space-y-2 p-3">
    {Array.from({ length: 4 }).map((_, i) => (
      <Skeleton key={i} variant="rect" className="h-12 w-full" />
    ))}
  </div>
) : ...}
```

When messages loading inside active session:
```tsx
{messagesLoading ? (
  <div className="space-y-4 p-4">
    <Skeleton variant="rect" className="h-16 w-3/4" />
    <Skeleton variant="rect" className="h-20 w-2/3 ml-auto" />
    <Skeleton variant="rect" className="h-16 w-3/4" />
  </div>
) : ...}
```

- [ ] **Step 2: CodingChallengePage skeleton**

```tsx
if (isLoading) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="space-y-3">
        <SkeletonLine width="40%" />
        <SkeletonLine /><SkeletonLine /><SkeletonLine width="80%" />
        <Skeleton variant="rect" className="h-24 w-full" />
      </div>
      <Skeleton variant="rect" className="h-96 w-full" />
    </div>
  )
}
```

- [ ] **Step 3: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/ChatPage.tsx frontend/src/pages/CodingChallengePage.tsx
git commit -m "feat(tier3): Chat and Coding skeleton loading states"
```

---

### Task 2.5: Progress + Achievements skeletons

**Files:**
- Modify: `frontend/src/pages/ProgressPage.tsx`
- Modify: `frontend/src/pages/AchievementsPage.tsx`

- [ ] **Step 1: ProgressPage skeleton**

```tsx
if (isLoading) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} className="h-24" />
        ))}
      </div>
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} variant="rect" className="h-12 w-full" />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: AchievementsPage skeleton**

```tsx
if (isLoading) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <SkeletonCard key={i} className="h-40" />
      ))}
    </div>
  )
}
```

- [ ] **Step 3: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/ProgressPage.tsx frontend/src/pages/AchievementsPage.tsx
git commit -m "feat(tier3): Progress and Achievements skeleton loading states"
```

---

### Task 2.6: Global micro-interactions

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Add motion-safe utilities + ensure focus rings smooth**

Add to `frontend/src/index.css` (within `@layer utilities` if exists, else top-level):

```css
@layer utilities {
  .interactive-card {
    @apply transition-all duration-150 motion-safe:hover:-translate-y-0.5 motion-safe:hover:shadow-brand-md;
  }

  .interactive-button {
    @apply transition-all duration-150 motion-safe:hover:scale-[1.02] motion-safe:active:scale-[0.98];
  }

  .focus-ring-smooth {
    @apply transition-shadow duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2;
  }
}
```

- [ ] **Step 2: Apply utilities to existing components**

Modify `frontend/src/components/ui/button.tsx` (or wherever button variants live) — add `interactive-button focus-ring-smooth` to base variant.

Modify `ModuleCard.tsx` — add `interactive-card` to root article element where unlocked.

- [ ] **Step 3: Verify visual + reduced-motion respect**

`npm run dev` → hover/focus interactive elements → see micro-interaction. Toggle DevTools "prefers-reduced-motion: reduce" → confirm no transform animations, only color/opacity.

- [ ] **Step 4: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/index.css frontend/src/components/ui/button.tsx frontend/src/components/modules/ModuleCard.tsx
git commit -m "feat(tier3): global micro-interactions for buttons and cards"
```

---

## Phase 3 — Dark Mode QA

### Task 3.1: Dark mode audit pages 1-6

**Files:**
- Create: `docs/audit-darkmode.md` (start)

- [ ] **Step 1: Set up audit table**

Create `docs/audit-darkmode.md`:

```markdown
# Dark Mode Audit — Tier 3

Tested via ThemeToggle (themeStore). All pages must work in `pref=dark` mode.

| # | Página | Status | Issues | Fix aplicado |
|---|--------|--------|--------|--------------|
```

- [ ] **Step 2: Audit /login, /assessment, /dashboard**

For each:
1. Toggle dark mode
2. axe DevTools scan (filter: color-contrast)
3. Hunt hardcoded colors: search file for `bg-white`, `text-gray-9`, `text-black`, `bg-gray-`, `border-gray-`
4. Fix inline (replace with `bg-card`, `text-foreground`, `border-border`, etc.)
5. Add row to audit table

- [ ] **Step 3: Audit /modules, /modules/:id, /topics/:id**

Same pattern.

- [ ] **Step 4: Commit progress**

```bash
git add docs/audit-darkmode.md frontend/src/pages/
git commit -m "fix(tier3): dark mode QA pages 1-6 (auth + modules + topic)"
```

---

### Task 3.2: Dark mode audit pages 7-12

- [ ] **Step 1: Audit /quiz, /chat, /coding**

Verify special components:
- `QuizQuestion` feedback colors (green/red)
- `ContentRenderer` markdown (light vs dark code blocks)
- Monaco editor — set `theme={isDark ? 'vs-dark' : 'light'}` prop
- Chat sources collapsible borders

- [ ] **Step 2: Audit /progress, /achievements, /admin**

Verify:
- `AchievementCard` condition_type color variants
- Admin tables borders/headers
- StatCards numbers

- [ ] **Step 3: Apply fixes inline + update audit table**

- [ ] **Step 4: Commit**

```bash
git add docs/audit-darkmode.md frontend/src/pages/ frontend/src/components/
git commit -m "fix(tier3): dark mode QA pages 7-12 (quiz, chat, coding, progress, achievements, admin)"
```

---

### Task 3.3: Dark mode follow-up fixes

**Files:**
- Modify: various component files identified in audit

- [ ] **Step 1: Apply remaining fixes from audit tables**

Examples:
- `AchievementCard` — replace `bg-yellow-50` with `bg-warning/10` (or equivalent semantic token)
- Quiz feedback success → `bg-success/10 text-success` (assuming success token exists, else create)
- Status badge in module list → `text-success` not `text-green-600`

- [ ] **Step 2: Verify build + audit doc final**

```bash
cd frontend && npx tsc --noEmit && npm run build
```
Audit doc: confirm all rows show ✅ status for student pages.

- [ ] **Step 3: Commit**

```bash
git add docs/audit-darkmode.md frontend/src/
git commit -m "fix(tier3): finalize dark mode hardcoded color replacements"
```

---

## Phase 4 — Empty + Error States

### Task 4.1: Dashboard + Modules empty states

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/pages/ModulesPage.tsx`

- [ ] **Step 1: Dashboard empty state**

In DashboardPage, after `isLoading` skeleton, check if user has no activity:

```tsx
import EmptyState from '@/components/common/EmptyState'
import welcomeImg from '@/assets/empty/welcome.svg'
import { Link } from 'react-router-dom'

// after data loads
if (dashboard.total_topics_completed === 0 && !dashboard.last_accessed_topic) {
  return (
    <div className="max-w-3xl mx-auto">
      <PageHeader title={`Hola, ${dashboard.user_name}`} />
      <EmptyState
        illustration={welcomeImg}
        illustrationAlt="Ilustración de bienvenida"
        title="¡Comencemos tu aprendizaje!"
        description="Aún no has iniciado ningún módulo. Cuando comiences, verás aquí tu progreso, logros y recomendaciones."
        action={
          <Link
            to="/modules"
            className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold"
          >
            Comenzar primer módulo
          </Link>
        }
      />
    </div>
  )
}
```

- [ ] **Step 2: Modules empty state (edge case: all locked)**

```tsx
import lockedImg from '@/assets/empty/locked.svg'

// if all modules are locked (rare: user without level assigned)
if (modules.every((m) => m.is_locked)) {
  return (
    <EmptyState
      illustration={lockedImg}
      illustrationAlt="Ilustración de candado"
      title="Necesitas completar tu evaluación"
      description="Para desbloquear los módulos, primero realiza la evaluación inicial."
      action={
        <Link
          to="/assessment"
          className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold"
        >
          Ir a evaluación
        </Link>
      }
    />
  )
}
```

- [ ] **Step 3: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/DashboardPage.tsx frontend/src/pages/ModulesPage.tsx
git commit -m "feat(tier3): empty states for Dashboard and Modules"
```

---

### Task 4.2: Chat + Progress + Achievements empty states

**Files:**
- Modify: `frontend/src/pages/ChatPage.tsx`
- Modify: `frontend/src/pages/ProgressPage.tsx`
- Modify: `frontend/src/pages/AchievementsPage.tsx`

- [ ] **Step 1: Chat sessions sidebar empty**

```tsx
import chatEmptyImg from '@/assets/empty/chat-empty.svg'

// in sessions sidebar where map is empty
{sessions.length === 0 ? (
  <EmptyState
    illustration={chatEmptyImg}
    illustrationAlt="Ilustración de chat"
    title="Sin conversaciones"
    description="Inicia tu primera conversación con el tutor IA."
    action={
      <button
        onClick={handleCreateSession}
        className="inline-flex items-center justify-center min-h-[44px] px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-sm"
      >
        Nueva conversación
      </button>
    }
    className="py-6"
  />
) : ...}
```

- [ ] **Step 2: Chat messages area empty (active session, no messages)**

```tsx
import { MessageCircle } from 'lucide-react'

// inside messages area, before any messages
{messages.length === 0 && (
  <EmptyState
    icon={MessageCircle}
    title="¿Sobre qué quieres aprender?"
    description="Pregúntale al tutor sobre los temas del curso. Por ejemplo: '¿Qué es Jetpack Compose?'"
  />
)}
```

- [ ] **Step 3: Progress empty state**

```tsx
import progressEmptyImg from '@/assets/empty/progress-empty.svg'

if (progress.total_topics_completed === 0) {
  return (
    <EmptyState
      illustration={progressEmptyImg}
      illustrationAlt="Ilustración de progreso"
      title="Tu progreso aparecerá aquí"
      description="Cuando completes temas, verás aquí tu avance por módulo, tiempo de estudio y logros."
      action={
        <Link
          to="/modules"
          className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold"
        >
          Explorar módulos
        </Link>
      }
    />
  )
}
```

- [ ] **Step 4: Achievements empty state**

```tsx
import achievementsEmptyImg from '@/assets/empty/achievements-empty.svg'

if (earned.length === 0) {
  return (
    <EmptyState
      illustration={achievementsEmptyImg}
      illustrationAlt="Ilustración de logros"
      title="Tus logros aparecerán aquí"
      description="Completa módulos, mantén tu racha de estudio y obtén logros desbloqueables."
      action={
        <Link
          to="/modules"
          className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold"
        >
          Ir a módulos
        </Link>
      }
    />
  )
}
```

- [ ] **Step 5: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/ChatPage.tsx frontend/src/pages/ProgressPage.tsx frontend/src/pages/AchievementsPage.tsx
git commit -m "feat(tier3): empty states for Chat, Progress, AchievementsPage"
```

---

### Task 4.3: Admin + Coding history empty states

**Files:**
- Modify: `frontend/src/pages/AdminPage.tsx` (or relevant admin tabs)
- Modify: `frontend/src/pages/CodingChallengePage.tsx`

- [ ] **Step 1: Admin Corpus tab empty**

```tsx
import uploadImg from '@/assets/empty/upload.svg'

// inside Corpus tab where documents is empty
{documents.length === 0 ? (
  <EmptyState
    illustration={uploadImg}
    illustrationAlt="Ilustración de carga"
    title="Sin documentos cargados"
    description="Sube documentos PDF, DOCX o MD para alimentar el corpus RAG."
    action={
      <button
        onClick={openUploadModal}
        className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold"
      >
        Subir documento
      </button>
    }
  />
) : <table>...</table>}
```

- [ ] **Step 2: Coding submissions history empty**

```tsx
import { Code2 } from 'lucide-react'

{submissions.length === 0 && (
  <EmptyState
    icon={Code2}
    title="Sin intentos previos"
    description="Resuelve el desafío y tu progreso aparecerá aquí."
    className="py-6"
  />
)}
```

- [ ] **Step 3: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/AdminPage.tsx frontend/src/pages/CodingChallengePage.tsx
git commit -m "feat(tier3): empty states for Admin Corpus and Coding history"
```

---

### Task 4.4: RouteErrorBoundary contextual fallbacks

The existing `ErrorBoundary` accepts a `fallback` render prop `(error, reset) => ReactNode`. Reuse it per route with contextual content.

**Files:**
- Create: `frontend/src/components/common/RouteErrorFallbacks.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create contextual fallback components**

Create `frontend/src/components/common/RouteErrorFallbacks.tsx`:

```tsx
import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

interface FallbackProps {
  error: Error
  reset: () => void
}

function FallbackShell({
  title,
  message,
  primaryAction,
  secondaryAction,
}: {
  title: string
  message: string
  primaryAction: React.ReactNode
  secondaryAction: React.ReactNode
}) {
  return (
    <div className="max-w-md mx-auto py-12 px-4 text-center">
      <div
        className="w-14 h-14 mx-auto bg-destructive/10 rounded-full flex items-center justify-center mb-4"
        aria-hidden="true"
      >
        <AlertTriangle className="w-7 h-7 text-destructive" />
      </div>
      <h2 className="text-lg font-bold text-foreground mb-2" role="alert">
        {title}
      </h2>
      <p className="text-sm text-muted-foreground mb-6">{message}</p>
      <div className="flex flex-col sm:flex-row gap-2 justify-center">
        {primaryAction}
        {secondaryAction}
      </div>
    </div>
  )
}

export function ChatErrorFallback({ reset }: FallbackProps) {
  return (
    <FallbackShell
      title="Error en el chat"
      message="Tus sesiones están seguras. Reintenta para continuar la conversación."
      primaryAction={
        <button
          onClick={reset}
          className="inline-flex items-center justify-center gap-2 min-h-[44px] px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Reintentar
        </button>
      }
      secondaryAction={
        <Link
          to="/dashboard"
          className="inline-flex items-center justify-center gap-2 min-h-[44px] px-4 rounded-lg border border-input bg-background hover:bg-accent text-foreground font-semibold text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al inicio
        </Link>
      }
    />
  )
}

export function QuizErrorFallback({ reset }: FallbackProps) {
  return (
    <FallbackShell
      title="Error generando el quiz"
      message="Puedes intentarlo de nuevo o regresar al tema."
      primaryAction={
        <button
          onClick={reset}
          className="inline-flex items-center justify-center gap-2 min-h-[44px] px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Reintentar
        </button>
      }
      secondaryAction={
        <Link
          to="/modules"
          className="inline-flex items-center justify-center gap-2 min-h-[44px] px-4 rounded-lg border border-input bg-background hover:bg-accent text-foreground font-semibold text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Ir a módulos
        </Link>
      }
    />
  )
}

export function CodingErrorFallback({ reset }: FallbackProps) {
  return (
    <FallbackShell
      title="Error cargando el desafío"
      message="Reintenta o regresa al tema asociado."
      primaryAction={
        <button
          onClick={reset}
          className="inline-flex items-center justify-center gap-2 min-h-[44px] px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Reintentar
        </button>
      }
      secondaryAction={
        <Link
          to="/modules"
          className="inline-flex items-center justify-center gap-2 min-h-[44px] px-4 rounded-lg border border-input bg-background hover:bg-accent text-foreground font-semibold text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Ir a módulos
        </Link>
      }
    />
  )
}
```

- [ ] **Step 2: Integrate per-route in App.tsx**

In `App.tsx`, import:

```tsx
import ErrorBoundary from '@/components/common/ErrorBoundary'
import { ChatErrorFallback, QuizErrorFallback, CodingErrorFallback } from '@/components/common/RouteErrorFallbacks'
```

Wrap specific routes:

```tsx
<Route path="/chat" element={
  <ErrorBoundary fallback={(error, reset) => <ChatErrorFallback error={error} reset={reset} />}>
    <ChatPage />
  </ErrorBoundary>
} />

<Route path="/quiz/:topicId" element={
  <ErrorBoundary fallback={(error, reset) => <QuizErrorFallback error={error} reset={reset} />}>
    <QuizPage />
  </ErrorBoundary>
} />

<Route path="/coding/:id" element={
  <ErrorBoundary fallback={(error, reset) => <CodingErrorFallback error={error} reset={reset} />}>
    <CodingChallengePage />
  </ErrorBoundary>
} />
```

The outermost `<ErrorBoundary>` (Tier 1 global) wraps the whole app and uses default fallback for any uncaught route error.

- [ ] **Step 3: Manual test each boundary**

Temporarily add `throw new Error('test')` inside ChatPage component (in render). Verify ChatErrorFallback appears. Remove throw. Repeat for Quiz, Coding.

- [ ] **Step 4: Verify + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/components/common/RouteErrorFallbacks.tsx frontend/src/App.tsx
git commit -m "feat(tier3): per-route ErrorBoundary fallbacks for Chat, Quiz, Coding"
```

---

## Phase 5 — Gate Definition of Done

### Task 5.1: Final build verification

- [ ] **Step 1: TypeScript clean**

```bash
cd frontend && npx tsc --noEmit
```
Expected: PASS, zero errors.

- [ ] **Step 2: Vite production build**

```bash
cd frontend && npm run build
```
Expected: PASS, no errors. Note bundle size; if `framer-motion` pushes total >500KB gzip, consider dynamic import (skip if within budget).

- [ ] **Step 3: Lint**

```bash
cd frontend && npm run lint
```
Expected: no new warnings.

- [ ] **Step 4: Manual reduced-motion check**

`npm run dev` → DevTools Rendering → "prefers-reduced-motion: reduce" → navigate routes → confirm page transitions disabled, skeletons pulse stops.

- [ ] **Step 5: Re-run Lighthouse spot check**

Run Lighthouse mobile on /dashboard and /modules. Confirm:
- Performance ≥70
- Accessibility ≥85

---

### Task 5.2: Update CLAUDE.md + final commit

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add Tier 3 entry to CLAUDE.md**

In the SPRINTS RESUMEN section, after Sprint 4 entry, add (or under appropriate UI/UX subsection):

```markdown
### Tier 3 UI/UX Polish ✅ (12 may 2026)
4 buckets ejecutados completos antes de Sprint 5:
- Mobile 375px: 12 páginas auditadas, fixes aplicados, Lighthouse mobile ≥85 a11y, ≥70 perf
- Loading/transiciones: framer-motion + PageTransition + 9 page skeletons + micro-interacciones globales
- Dark mode QA: 12 páginas verificadas, hardcoded colors reemplazados por semantic tokens
- Empty + error states: 8 empty states con assets undraw + 3 RouteErrorBoundary fallbacks contextuales
Documentación: `docs/audit-mobile.md`, `docs/audit-darkmode.md`. Spec: `docs/superpowers/specs/2026-05-12-tier3-uiux-polish-design.md`.
```

- [ ] **Step 2: Verify CLAUDE.md still parses (no markdown issues)**

```bash
grep -c "^##" CLAUDE.md
```
Expected: section count consistent with before.

- [ ] **Step 3: Final commit**

```bash
git add CLAUDE.md
git commit -m "docs(tier3): mark Tier 3 UI/UX polish complete in CLAUDE.md"
```

- [ ] **Step 4: Tag commit (optional)**

```bash
git tag tier3-complete
```

---

## Self-Review Notes (writer)

**Spec coverage check:**
- Foundations Fase 0 ✅ (Tasks 0.1-0.5)
- Mobile bucket 1 ✅ (Tasks 1.1-1.7)
- Loading bucket 2 ✅ (Tasks 2.1-2.6)
- Dark mode bucket 3 ✅ (Tasks 3.1-3.3)
- Empty + error bucket 4 ✅ (Tasks 4.1-4.4)
- Gate DoD ✅ (Tasks 5.1-5.2)

**Out of scope honored:**
- No new backend endpoints
- No state management changes (consumes existing `themeStore`)
- No new tests (no test infra; manual QA per task)
- Admin mobile = best-effort (Task 1.6)

**Risks (per spec §10):**
- Bundle inflation from framer-motion checked in Task 5.1 Step 2
- Undraw recolor fallback (icons) implicit in Task 0.5 retry path
- Escalation protocol referenced (CLAUDE.md), to invoke if Phase 1+2 exceed 5 days
