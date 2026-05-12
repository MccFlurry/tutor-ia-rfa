# Tier 3 UI/UX Polish — Design Spec

**Proyecto:** tutor-ia-rfa
**Fecha:** 2026-05-12
**Autor:** Roger Alessandro Zavaleta Marcelo (tesis USAT)
**Estado:** Aprobado para implementación
**Vinculación:** Pre-SUS pilot Sprint 8 · Sprint 5 deploy se hará DESPUÉS de Tier 3

---

## 1. Contexto

Tier 1 y Tier 2 UI/UX completados (commit pendiente). Tier 3 cierra polish antes de pilotaje SUS (objetivo ≥68 con 10-15 estudiantes IESTP RFA). 4 buckets aprobados profundidad exhaustiva:

1. Mobile 375px refino
2. Loading + skeletons + transiciones
3. Dark mode QA por página
4. Empty states + error states

Decisiones cerradas:
- Librería animaciones: **Framer Motion** (~50KB gzip aceptado)
- Empty illustrations: **undraw.co** assets (4-6, recoloreados a brand)
- Orden ejecución: **Tier 3 PRIMERO, Sprint 5 deploy después**
- Estrategia: **Foundations primero (Fase 0) → vertical por bucket**

---

## 2. Arquitectura

5 fases lineales. Cada fase cierra con build verde (TypeScript + Vite) antes de avanzar.

```
Fase 0: Foundations (componentes + assets + framer-motion)
   ↓
Fase 1: Bucket 1 Mobile 375px (12 páginas)
   ↓
Fase 2: Bucket 2 Loading + transiciones (skeletons + page transitions + micro-interactions)
   ↓
Fase 3: Bucket 3 Dark mode QA (12 páginas verificación)
   ↓
Fase 4: Bucket 4 Empty + error states (8 empty + 4 error fallbacks)
   ↓
Fase 5: Gate DoD (Lighthouse + manual QA + docs)
```

Cada fase produce: code diff + docs auditoría per bucket. Build verde es prerrequisito de avance.

---

## 3. Fase 0 — Foundations

### 3.1 Dependencias

- Instalar `framer-motion` (versión más reciente estable).
- Verificar `package-lock.json` commit incluido.

### 3.2 Assets undraw.co

Carpeta destino: `frontend/src/assets/empty/`

Lista assets requeridos (mínimo 6):
- `welcome.svg` — Dashboard sin actividad
- `locked.svg` — Modules todos bloqueados
- `chat-empty.svg` — Chat sin sesiones
- `progress-empty.svg` — Progress sin temas completados
- `achievements-empty.svg` — Achievements sin earned
- `upload.svg` — Admin Corpus sin documentos

Recolor: reemplazar fill primary undraw (default naranja/azul) por `institutional-700` (`#1e3a8a` u equivalente del token brand). Método: edit SVG fill atribute manualmente o vía CSS filter (no preferido por flexibilidad).

### 3.3 Componentes nuevos

`frontend/src/components/common/Skeleton.tsx`:
- Props: `variant: 'text' | 'card' | 'avatar' | 'list', count?, className?`
- Implementación base: `bg-muted animate-pulse rounded`
- Respeta `motion-reduce:animate-none`

`frontend/src/components/common/EmptyState.tsx`:
- Props: `illustration: string | ReactNode, title: string, description?: string, action?: { label: string, onClick?: () => void, to?: string }`
- Centrado vertical, max-width 480px
- Si `to` provided usa `<Link>`, sino `<Button onClick>`
- Imagen max-height 240px, alt text desde `title`

`frontend/src/components/common/PageTransition.tsx`:
- Wrapper con framer `<AnimatePresence mode="wait">`
- Variants: `initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}`
- Duration 200ms ease-out
- Usa `useReducedMotion()` → si reduce, omite animación

`frontend/src/components/common/RouteErrorBoundary.tsx`:
- Class component (React requirement) implementa `componentDidCatch`
- Props: `fallback: ReactNode, onReset?: () => void`
- Log error a consola con prefix `[RouteError]`
- Reset state cuando ruta cambia (via key prop o location listener)

### 3.4 Variables CSS / Tailwind

- Verificar `tailwind.config.js` ya tiene `motion-safe` y `motion-reduce` variants (built-in v3+, sí).
- Sin nuevos tokens. Reusar existentes.

### 3.5 Definition of Done Fase 0

- `framer-motion` en `package.json` dependencies
- 6 SVG assets en `frontend/src/assets/empty/` recoloreados
- 4 componentes creados, exportados, con tipos TypeScript estrictos
- `npx tsc --noEmit` verde
- Sin cambios visibles en páginas existentes (foundations no consumidas todavía)

---

## 4. Fase 1 — Bucket 1 Mobile 375px

### 4.1 Páginas a verificar (orden ejecución)

Prioridad estudiante (10):
1. `/login`
2. `/assessment`
3. `/dashboard`
4. `/modules`
5. `/modules/:id`
6. `/topics/:id`
7. `/quiz/:topicId`
8. `/chat`
9. `/coding/:id`
10. `/progress`
11. `/achievements`

Admin (1, best-effort):
12. `/admin`

### 4.2 Checklist per página

- [ ] Touch targets interactivos ≥44×44px (botones, links, tabs, badges clicables)
- [ ] No horizontal overflow viewport 375px (DevTools Device Toolbar)
- [ ] Texto body ≥14px, line-height ≥1.5, contraste WCAG AA
- [ ] CTAs principales accesibles zona inferior pulgar (60% inferior pantalla)
- [ ] Sidebar drawer: abre con tap hamburger, overlay cierra al tap fuera, no atrapa scroll body
- [ ] Sticky bars (Topic prev/next, Quiz submit) no tapan contenido — `pb-{altura-sticky}` en main
- [ ] Tablas/grids reflow: stack vertical o scroll horizontal explícito con indicador
- [ ] Imágenes y `<iframe>` 16:9 ratio sin overflow
- [ ] Forms: inputs `font-size: 16px` mínimo (iOS evita zoom automático)
- [ ] Chat textarea: viewport keyboard no rompe layout (`dvh` units, no `vh`)
- [ ] Modal/Dialog: max-height pantalla, scroll interno funciona

### 4.3 Herramientas

- Chrome DevTools → Device Toolbar → 375×667 (iPhone SE baseline)
- Lighthouse mobile audit per página → guardar JSON
- Tap targets visualizer (DevTools Rendering tab)

### 4.4 Salida

- Code diffs por página en branch `feat/tier3-uiux-polish`
- `docs/audit-mobile.md` con tabla per página:
  - Pre-fix screenshots (3-4 críticos)
  - Issues encontrados
  - Fixes aplicados
  - Post-fix screenshots
  - Lighthouse mobile score (Performance, A11y, Best Practices)

### 4.5 Definition of Done Fase 1

- 10 páginas estudiante: sin overflow horizontal, touch targets ≥44px, Lighthouse A11y ≥85
- Admin: sin overflow horizontal mínimo
- `docs/audit-mobile.md` completo

---

## 5. Fase 2 — Bucket 2 Loading + Transiciones

### 5.1 Page Transitions

- Integrar `PageTransition` en `AppLayout.tsx` envolviendo `<Outlet />` de React Router
- `AnimatePresence mode="wait"` con `key={location.pathname}`
- Duration 200ms, ease-out
- `useReducedMotion()` omite animación si usuario lo prefiere

### 5.2 Skeletons por página (9 shapes)

Reemplazan estados `isLoading` con spinner genérico. Cada skeleton replica shape final aproximado:

- `DashboardPage` — Hero card + 4 StatCard skeletons + 3 module recommendation card skeletons
- `ModulesPage` — Grid 6 module card skeletons (1/2/3 cols responsive)
- `ModuleDetailPage` — Header skeleton + lista 5 topic skeletons
- `TopicPage` — Markdown skeleton (3 párrafos texto + 1 image placeholder rectangle)
- `QuizPage` — Pregunta header skeleton + 4 opciones skeleton
- `ProgressPage` — 4 StatCards + 5 barras módulo skeleton
- `AchievementsPage` — Grid 6 badge skeletons
- `ChatPage` — Sesiones sidebar 4 items skeleton + área mensajes con bubble skeletons
- `CodingChallengePage` — Descripción skeleton (header + 2 párrafos + hints) + editor placeholder rectangle

### 5.3 Micro-interacciones

Aplicar globalmente vía Tailwind utilities + framer donde necesario:

- Button hover: `motion-safe:hover:scale-[1.02] motion-safe:hover:shadow-brand-md transition-all duration-150`
- Card hover lift: `motion-safe:hover:-translate-y-0.5 motion-safe:hover:shadow-brand-md transition-all duration-150`
- Focus-visible ring transitions: `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 transition-all`
- Active scale tap: `motion-safe:active:scale-[0.98]`

### 5.4 Toast + AILoadingState

- Toast (`react-hot-toast`) — validar timings actuales (4s default), polish slide direction (top-right)
- `AILoadingState` (existente) — pulse dots 1.5s loop, fade-in 200ms al mount

### 5.5 Definition of Done Fase 2

- 9 page skeletons reemplazan spinner loading states
- `PageTransition` activa en `AppLayout`
- Micro-interacciones aplicadas global (button/card/focus)
- `prefers-reduced-motion: reduce` respetado (testear DevTools Rendering → Emulate CSS media)
- Sin animación >300ms en flows críticos

---

## 6. Fase 3 — Bucket 3 Dark Mode QA

### 6.1 Proceso per página (12 total)

1. Activar dark mode via `ThemeToggle` (`themeStore`)
2. Screenshot full page
3. Inspeccionar con axe DevTools dark scan
4. Buscar colores hardcoded en page: `bg-white`, `text-gray-900`, `text-black`, `bg-gray-50/100/200`, etc.
5. Validar contraste WCAG AA con WebAIM Contrast Checker (pares dudosos)
6. Verificar estados componente: hover, focus, active, disabled
7. Validar componentes específicos:
   - Monaco editor en `CodingChallengePage` (theme dark prop?)
   - Markdown syntax highlight en `ContentRenderer` (vscDarkPlus siempre activo, verificar light también funciona)
   - Toast colors (success green, error red — legibles ambos modos)
   - Dialog overlay opacity
   - Badges con `bg-{color}-100` (color-100 invisible en dark típicamente)

### 6.2 Componentes con riesgo conocido

- `ContentRenderer` — syntax highlight forzado dark theme, light no testeado
- `AchievementCard` — colores condition_type hardcoded
- `Quiz feedback` — verde/rojo confirmación
- Admin tablas — borders, headers row
- `Avatar` fallback — `bg-institutional-700` (visible ambos modos, OK)
- Loading spinners residuales (si quedan post-Fase 2) — colores hardcoded

### 6.3 Salida

`docs/audit-darkmode.md` tabla por página:
| Página | Status | Issues | Fix aplicado |
|--------|--------|--------|--------------|
| /dashboard | ✅ pass / ⚠ contraste / 🔴 broken | descripción | selector + cambio |

Screenshots pre/post per página con issue.

### 6.4 Definition of Done Fase 3

- 12 páginas auditadas en dark
- 0 colores hardcoded restantes en páginas estudiante (admin: best-effort)
- Contraste WCAG AA: ≥4.5:1 texto normal, ≥3:1 UI components y texto large
- `docs/audit-darkmode.md` completo con tabla

---

## 7. Fase 4 — Bucket 4 Empty States + Error States

### 7.1 Empty States (8 ubicaciones)

Usar componente `EmptyState` (Fase 0) con assets undraw recoloreados.

| # | Página/Ubicación | Trigger | Illustration | CTA |
|---|------------------|---------|--------------|-----|
| 1 | DashboardPage | `total_topics_completed === 0 && !last_accessed_topic` | `welcome.svg` | "Comenzar primer módulo" → `/modules` |
| 2 | ModulesPage | edge: todos bloqueados (sin level asignado) | `locked.svg` | "Completar evaluación" → `/assessment` |
| 3 | ChatPage sidebar | sessions.length === 0 | `chat-empty.svg` | "Iniciar conversación" (createSession action) |
| 4 | ChatPage área mensajes | sesión activa sin mensajes | icono `MessageCircle` + tip texto | (no action, tip primera pregunta) |
| 5 | ProgressPage | `total_topics_completed === 0` | `progress-empty.svg` | "Explorar módulos" → `/modules` |
| 6 | AchievementsPage | `earned.length === 0` | `achievements-empty.svg` | "Ver módulos" → `/modules` |
| 7 | Admin Corpus tab | documents.length === 0 | `upload.svg` | "Subir primer documento" (open modal) |
| 8 | CodingChallenge history | submissions.length === 0 | icono `Code` + texto | "Resolver desafío" (focus editor) |

### 7.2 Error States (RouteErrorBoundary por ruta)

Wrapper integrado en `App.tsx`:

```tsx
<Route path="/chat" element={
  <RouteErrorBoundary fallback={<ChatErrorFallback />}>
    <ChatPage />
  </RouteErrorBoundary>
} />
```

Fallback components contextuales:

- `ChatErrorFallback` — "Error en el chat. Tus sesiones están seguras." + botón "Reintentar" (reset boundary) + link "Volver al dashboard"
- `QuizErrorFallback` — "Error generando el quiz. Puedes intentar de nuevo o volver al tema." + 2 botones
- `CodingErrorFallback` — "Error cargando el desafío. Reintenta o regresa al tema." + 2 botones
- `GenericErrorFallback` — Icono `AlertTriangle` + mensaje + "Recargar página" + "Ir al inicio"

### 7.3 Integración App.tsx

Rutas con boundary específico:
- `/chat` → ChatErrorFallback
- `/quiz/:topicId` → QuizErrorFallback
- `/coding/:id` → CodingErrorFallback

Resto rutas usan boundary global existente (Tier 1) con `GenericErrorFallback`.

### 7.4 Logging

`RouteErrorBoundary.componentDidCatch` log a consola con prefix:
```
[RouteError /chat] <error.message> <error.stack>
```

Sin logger externo todavía (out of scope).

### 7.5 Definition of Done Fase 4

- 8 empty states implementados consumiendo `EmptyState` + assets
- 4 error fallbacks contextuales + global existente
- 3 `RouteErrorBoundary` integrados en App.tsx (Chat, Quiz, Coding)
- Test manual: forzar error en cada ruta (e.g. throw en useEffect) confirma fallback se muestra sin crash app

---

## 8. Fase 5 — Gate Definition of Done

Sin avance a Sprint 5 deploy hasta que todos los items pasen:

### 8.1 Build

- [ ] `npx tsc --noEmit` sin errores
- [ ] `npm run build` (Vite) sin errores ni warnings nuevos
- [ ] Lint sin nuevos warnings

### 8.2 Auditoría Mobile (375px)

- [ ] 10 páginas estudiante verificadas manualmente
- [ ] `docs/audit-mobile.md` completo con screenshots before/after
- [ ] Sin overflow horizontal en ninguna ruta estudiante
- [ ] Touch targets ≥44×44px confirmados

### 8.3 Auditoría Dark Mode

- [ ] 12 páginas verificadas
- [ ] `docs/audit-darkmode.md` con tabla resultados
- [ ] Contraste WCAG AA cumplido páginas estudiante
- [ ] Cero colores hardcoded en páginas estudiante

### 8.4 Performance (Lighthouse Mobile)

- [ ] Performance ≥70 en `/modules` y `/dashboard`
- [ ] Accessibility ≥85 en todas páginas estudiante
- [ ] Best Practices ≥85

### 8.5 Empty + Error

- [ ] 8 empty states implementados
- [ ] 4 RouteErrorBoundaries con fallback contextual
- [ ] ErrorBoundary global Tier 1 sigue funcionando

### 8.6 Animaciones

- [ ] `prefers-reduced-motion: reduce` respetado (test DevTools emulate)
- [ ] Sin animaciones >300ms en interacciones críticas
- [ ] Page transitions ≤200ms

### 8.7 Artefactos

- [ ] 6 SVGs undraw en `frontend/src/assets/empty/` recoloreados
- [ ] `framer-motion` agregado a `package.json` + lockfile commiteado
- [ ] `package-lock.json` actualizado
- [ ] CLAUDE.md actualizado con Tier 3 status

---

## 9. Out of Scope (explícito)

- Sin redesign páginas — solo polish
- Sin nuevos endpoints backend
- Sin cambios store/state management (excepto consumir `themeStore` ya existente)
- Sin cambios stack (React 18 + Vite + Tailwind + shadcn permanecen)
- Admin page audit mobile = best-effort (no bloqueante SUS pilot)
- Sin tests E2E para Tier 3 (manual QA es suficiente para piloto)
- Sin logger externo (consola es suficiente)

---

## 10. Riesgos + mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| `framer-motion` bundle inflar Lighthouse Perf | Lazy-load animaciones no críticas; tree-shake imports específicos |
| Recolor undraw SVGs lento (manual) | Si lleva >2h, fallback a Lucide icons grandes para empty states pendientes |
| Dark mode regresiones masivas en componentes hardcoded | Priorizar páginas estudiante; admin acepta diferimiento |
| Sprint 5 deploy desplaza > 1 semana hito 10/07 | Aplicar protocolo escalamiento CLAUDE.md: detener Tier 3 y consultar usuario si Fase 1 + 2 exceden 5 días |

---

## 11. Estimación

- Fase 0 Foundations: 0.5 día
- Fase 1 Mobile 375px (12 páginas): 1.5 días
- Fase 2 Loading + transiciones: 1 día
- Fase 3 Dark mode QA: 0.5 día
- Fase 4 Empty + error: 0.5 día
- Fase 5 Gate DoD + docs: 0.5 día

**Total: ~4.5 días.** Tope: 5 días. Si excede, detener y consultar.

---

## 12. Referencias

- CLAUDE.md sección "🎨 FRONTEND"
- `docs/audit-a11y.md` — Guía A11y + Performance Sprint 7-8
- Memoria observaciones #84-105 — Tier 1 + Tier 2 completados
- undraw.co — https://undraw.co/illustrations (open-source, MIT-style license)
- Framer Motion docs — https://www.framer.com/motion/
