---
name: Tutor IA RFA
description: Private RAG tutor for the IESTP RFA mobile-apps course — a calm, institutional learning surface.
colors:
  institutional-blue: "#2563eb"
  deep-navy: "#172554"
  heritage-gold: "#f59e0b"
  andean-red: "#dc2626"
  success-green: "#16a34a"
  info-sky: "#0ea5e9"
  ink: "#0f172a"
  muted-ink: "#64748b"
  surface: "#ffffff"
  hairline: "#e2e8f0"
  locked-gray: "#9ca3af"
typography:
  display:
    fontFamily: "Plus Jakarta Sans, system-ui, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Plus Jakarta Sans, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Plus Jakarta Sans, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "Plus Jakarta Sans, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Plus Jakarta Sans, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    letterSpacing: "0.02em"
  mono:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  xl: "16px"
  full: "9999px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.institutional-blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "0.5rem 1rem"
  button-outline:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0.5rem 1rem"
  button-destructive:
    backgroundColor: "{colors.andean-red}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "0.5rem 1rem"
  input-default:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "0.5rem 1rem"
    height: "2.75rem"
  card-default:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "1.5rem"
  badge-default:
    backgroundColor: "{colors.institutional-blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.full}"
    padding: "0.125rem 0.625rem"
---

# Design System: Tutor IA RFA

## 1. Overview

**Creative North Star: "La Ruta del Aprendiz" (The Apprentice's Path)**

The interface is a guided climb. A student logs in somewhere on a route — modules are stages, topics are steps, and the system always shows the next foothold rather than the whole mountain at once. Deep institutional navy is the rock of the route: headers, the dashboard hero, the structure you trust. Institutional blue is the path itself and the *current* step — primary actions, the active selection, links, the focus ring. Heritage gold is reserved for what you have **earned**: an achievement unlocked, a milestone reached. It is rare on purpose, so it still means something when it appears. The surface underfoot is a calm, near-white plane (or a deep navy-black in dark mode) that never competes with the content.

This is a **product** surface: design serves the task of learning, not a marketing pitch. Familiarity is a feature here — a student fluent in any modern app should sit down and trust it immediately. The voice is *warm institutional confidence*: a real institute (IESTP RFA), thesis-grade, but human and encouraging, never cold and never childish. Progress is framed as a journey with momentum, not a scoreboard of points.

It explicitly rejects the cluttered Moodle-style LMS (everything-everywhere navigation, content buried under nested tabs), generic template-SaaS slop (hero-metric blocks, endless identical card grids, gradient text), and loud childish gamification (cartoon mascots, neon badges, confetti). These are tertiary-level technical students; the encouragement is respectful and tied to real progress.

**Key Characteristics:**
- Register: product — the tool disappears into the act of learning.
- Identity: institutional navy + *earned* heritage gold + Andean red accent, on a clean white / deep-navy surface.
- One typeface (Plus Jakarta Sans) carrying everything; JetBrains Mono for code and data only.
- Flat at rest; a navy-tinted lift appears only on interaction.
- Progress reads as a route with milestones — blue = current, green = done, gold = earned.
- WCAG 2.1 AA, full light + dark parity, mobile-first down to 375px.

## 2. Colors

A disciplined institutional palette: one trustworthy blue does the work, navy gives weight, gold is the scarce reward, and a single warm red carries both danger and national identity. Everything else is a calibrated neutral. (Canonical tokens live as HSL channels in `src/index.css` `:root` / `.dark`; hex here is the sRGB equivalent for tooling.)

### Primary
- **Institutional Blue** (`#2563eb`, `hsl(217 91% 42%)` light / `hsl(217 91% 60%)` dark): the path and the current step. Primary buttons, active nav, links, the `:focus-visible` ring, in-progress module state. The single loudest color the eye should track.

### Secondary
- **Deep Navy** (`#172554`): the rock of the route. The dashboard hero gradient (`#172554 → #1e3a8a → #1e40af`), institutional headers, and the source of every shadow's tint. Authority, not action.

### Tertiary
- **Heritage Gold** (`#f59e0b`): the earned-reward accent (academic honor + a nod to the institute's German heritage). Achievement badges, milestone markers, the `.heritage-accent` bar. Also serves as `warning`. Used on a sliver of any screen.
- **Andean Red** (`#dc2626`): destructive actions and a deliberate Peruvian-identity accent. Shared with `destructive`; never used to mean "incomplete".

### Neutral
- **Ink** (`#0f172a`): primary text and headings. The default body color — never substitute a lighter gray for "elegance".
- **Muted Ink** (`#64748b`): secondary text, captions, placeholders. The lightest text permitted on white and still ≥4.5:1.
- **Surface White** (`#ffffff`) / **Dark Surface** (`hsl(222 47% 9%)`): cards and panels. The page background sits one step cooler.
- **Hairline** (`#e2e8f0`): borders, dividers, the default 1px card outline.
- **Locked Gray** (`#9ca3af`): locked modules only (grayscale + padlock).

### Semantic feedback
- **Success Green** (`#16a34a`), **Info Sky** (`#0ea5e9`), **Warning** = Heritage Gold, **Destructive** = Andean Red. Desaturated/lightened in dark mode, never hue-inverted.

### Named Rules
**The Earned-Gold Rule.** Heritage gold marks only what the student has *earned* — achievements, completed milestones, the accent bar. Never use it as decoration or for a generic highlight. Its scarcity is the reward.

**The Traffic-Light-Free Rule.** Module and topic state is gray (locked) → blue (in progress) → green (completed). Red is *never* "not done"; it is reserved for destructive actions and the Peru accent. State must also carry an icon + label, never color alone.

**The One-Loud-Color Rule.** Institutional blue is the only saturated color allowed to carry weight on a working screen. Gold and red appear in slivers. If two colors are fighting for the eye, one is wrong.

## 3. Typography

**Display / Body / Label Font:** Plus Jakarta Sans (with `system-ui, sans-serif`)
**Mono Font:** JetBrains Mono (with `ui-monospace, monospace`)

**Character:** One humanist-geometric sans carries the entire product; hierarchy comes from weight and a fixed rem scale, not from a second display face. Plus Jakarta Sans is friendly enough to feel encouraging and structured enough to read as institutional. Stylistic sets are enabled globally (`font-feature-settings: 'cv02','cv03','cv04','cv11'`) for cleaner letterforms. JetBrains Mono appears only where monospacing carries meaning: Kotlin code blocks, the Monaco editor, and tabular data.

### Hierarchy
- **Display** (700, 2.25rem, lh 1.1, ls −0.02em): page/hero titles. Fixed rem — no fluid clamp, since users view at consistent DPI.
- **Headline** (600, 1.5rem, lh 1.2): section and card titles (`CardTitle`, `text-2xl tracking-tight`).
- **Title** (600, 1.125rem, lh 1.3): sub-section headings, list-group labels.
- **Body** (400, 1rem, lh 1.6): prose and lesson content; cap measure at 65–75ch.
- **Label** (600, 0.75rem, ls 0.02em): badges, chips, short metadata. Uppercase only for ≤4-word labels, never sentences.
- **Code/Data** (JetBrains Mono, 400, 0.875rem, lh 1.55): code blocks and dense tables (tables may run denser than 75ch).

### Named Rules
**The One-Voice Rule.** Plus Jakarta Sans carries headings, buttons, labels, body, and data. Do not add a second display typeface; create contrast with weight and size. JetBrains Mono is the only exception, and only for code/data.

**The No-Shout Rule.** No all-caps body copy. Uppercase is for short labels and badges only. The display ceiling is 2.25rem in-app; the page is guiding, not shouting.

## 4. Elevation

The system is **flat at rest, lifted on interaction**. Surfaces sit on a single 1px hairline border with a whisper of shadow (`shadow-sm`); depth is a *response to state*, not standing chrome. On hover/focus, interactive cards rise (`.interactive-card`: `-translate-y-0.5` + a navy-tinted medium shadow). All shadows are tinted with navy (`rgba(23, 37, 84, …)`) rather than neutral black, so elevation reads as part of the institutional identity rather than a generic drop shadow.

### Shadow Vocabulary
- **brand-sm** (`box-shadow: 0 1px 2px 0 rgba(23,37,84,0.08)`): the resting card shadow; barely-there.
- **brand-md** (`box-shadow: 0 4px 12px -2px rgba(23,37,84,0.12), 0 2px 4px -1px rgba(23,37,84,0.06)`): hover/active lift on interactive cards and popovers.
- **brand-lg** (`box-shadow: 0 20px 40px -12px rgba(23,37,84,0.25)`): modals and the dashboard hero only.

### Named Rules
**The Flat-at-Rest Rule.** Surfaces are flat (hairline + `brand-sm`) at rest. The `brand-md` lift appears only on hover/focus as feedback. A page full of pre-elevated cards is a smell — depth should mean "this responded to you".

## 5. Components

Components are **calm and confident**: quiet defaults, one decisive primary action per view, subtle 150ms micro-interactions (a slight `scale(0.98)` on press), and a consistent shape vocabulary. Affordances are standard — no reinvented scrollbars, no novelty form controls.

### Buttons
- **Shape:** moderately rounded (`rounded-md`, 8px). Heights `h-10` (default, 40px), `h-9` (sm), `h-11` (lg, 44px touch).
- **Primary:** institutional blue fill, white text, `px-4 py-2`. Hover dims to ~90% opacity; press scales to 0.98.
- **Outline / Ghost:** 1px hairline (or transparent) over the surface; hover fills with the muted `accent` tint. The default for everything that isn't *the* next step.
- **Destructive:** Andean red fill, white text. Reserved for delete/irreversible actions.
- **Focus:** always a 2px `ring-ring` (institutional blue) with a 2px offset. Never removed.

### Chips / Badges
- **Shape:** fully pill (`rounded-full`), `px-2.5 py-0.5`, `text-xs font-semibold`.
- **Use:** student level (`beginner/intermediate/advanced`), "Generado con IA · nivel X", counts. Default = blue; gold only when it marks something earned.

### Cards / Containers
- **Corner Style:** `rounded-lg` (10px).
- **Background:** `surface` over a one-step-cooler page background.
- **Shadow Strategy:** `brand-sm` at rest, `brand-md` on hover for interactive cards (see Elevation).
- **Border:** 1px `hairline`. No colored side-stripe accents, ever.
- **Internal Padding:** `1.5rem` (`p-6`); header/content/footer share the rhythm.

### Inputs / Fields
- **Style:** `h-11` (44px touch target), `rounded-lg`, 1px `hairline`, `px-4`, `text-base`.
- **Focus:** 2px institutional-blue ring + border shifts to `primary`.
- **Disabled:** `opacity-50`, `cursor-not-allowed`, muted fill. **Error:** destructive border + a text message and icon (never color alone).
- **Placeholder:** `muted-ink` — held to the same ≥4.5:1 bar as body.

### Chat Bubbles
- **Shape:** a larger 16px radius (`rounded-2xl`, token `{rounded.xl}`) with one squared corner toward the avatar (`rounded-tr-md` for the student, `rounded-tl-md` for the tutor). A deliberate chat affordance, distinct from the 10px card radius.
- **Student:** institutional-blue fill, white text, right-aligned. **Tutor:** muted surface, markdown + code + collapsible sources, left-aligned. Each bubble carries a subtle 11px timestamp (`muted-ink`, or `primary-foreground/70` on the student bubble).

### Navigation
- App-shell layout: persistent side nav (collapses to a drawer below `md`), top bar with level badge and the floating tutor. Active item carries the institutional-blue accent + an icon; hover uses the `accent` tint. A skip-link jumps to `<main>` for keyboard users.

### Signature Component — The Module / Step Card
The route made visible: a module card shows progress (`progress_pct`), a state ring (gray/blue/green), and a lock for gated modules. It is the recurring "step on the path" — completed steps carry green and a check, the current step carries blue, earned milestones flash gold. This is where momentum is felt; keep it honest (it must reflect real progress) and never decorate it into a generic stat tile.

## 6. Do's and Don'ts

### Do:
- **Do** keep exactly one primary (institutional-blue) action per view — the next step on the path. Everything else is outline or ghost.
- **Do** reserve heritage gold (`#f59e0b`) for *earned* achievements and milestone markers only (the Earned-Gold Rule).
- **Do** convey module/topic state with gray → blue → green **plus** an icon and label, never color alone (WCAG AA, color-blind safe).
- **Do** keep cards flat at rest (`brand-sm`) and let them lift (`brand-md`) on hover via `.interactive-card`.
- **Do** hold body text at ≥4.5:1 — `ink` (`#0f172a`) or `muted-ink` (`#64748b`) on white; the same bar for placeholders.
- **Do** keep one shape vocabulary: buttons `rounded-md` (8px), cards & inputs `rounded-lg` (10px), chips & badges `rounded-full`.
- **Do** honor `prefers-reduced-motion` and keep transitions 150–250ms; motion conveys state, not decoration.
- **Do** make every AI surface degrade gracefully — a fallback (DB quiz bank, coding catalog) must look intentional, never broken.

### Don't:
- **Don't** build a cluttered Moodle-style LMS: no everything-everywhere navigation, no content buried under nested tabs. One primary job per screen.
- **Don't** ship generic template-SaaS slop: no hero-metric template (big number + label + supporting stats), no endless identical icon-heading-text card grids, no gradient text.
- **Don't** tip "encouraging" into childish gamification: no cartoon mascots, neon badges, or confetti spam. These are adult technical students.
- **Don't** use a `border-left`/`border-right` greater than 1px as a colored accent stripe on cards, alerts, or list items. Use a full border, a background tint, or a leading icon.
- **Don't** put a tiny uppercase tracked eyebrow above every section, or `01 / 02 / 03` numbered markers as default scaffolding. Number only a real sequence.
- **Don't** introduce a second display font, new palette hues, or glassmorphism-by-default. Contrast comes from weight and the existing palette.
- **Don't** use light gray for body text "for elegance" — it fails AA and is the top reason a design reads as hard to read.
- **Don't** use red to mean "incomplete" — red is destructive + Peru accent only (the Traffic-Light-Free Rule).
