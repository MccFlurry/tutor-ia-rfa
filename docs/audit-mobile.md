# Auditoría Mobile 375px — Tier 3 UI/UX Polish

**Sprint:** Pre Sprint 5 (preparación SUS pilot Sprint 8)
**Fecha auditoría:** _(pendiente — completar tras run Lighthouse)_
**Viewport:** 375×667 (iPhone SE baseline)
**Tester:** _(nombre)_

---

## Resumen

Tier 3 Phase 1 aplicó fixes mobile 375px sobre 12 páginas. Commits relevantes (rama `feat/tier3-uiux-polish`):

- `91855a8c` — Login + Assessment
- `6a971da` — Dashboard + Modules
- `6365fd3` — ModuleDetail + Topic + ContentRenderer + CodeBlock
- `91e524be` — Quiz + Chat (sidebar drawer mobile)
- `b903fd6` — Coding + Progress + Achievements (Monaco responsive height)
- `8d47ce4` — Admin best-effort (CorpusTab overflow fix)

## Cómo ejecutar Lighthouse mobile

### 1. Instalar Lighthouse CLI (si no instalado)

```bash
npm i -g lighthouse
```

### 2. Levantar frontend + backend

```bash
# Terminal 1
cd backend && docker compose up

# Terminal 2
cd frontend && npm run dev
```

### 3. Correr Lighthouse mobile por página

Reemplazar `:id` por IDs reales del seed:

```bash
mkdir -p docs/lighthouse-reports

lighthouse http://localhost:5173/login --emulated-form-factor=mobile --only-categories=performance,accessibility,best-practices --output=json --output=html --output-path=docs/lighthouse-reports/login --quiet

lighthouse http://localhost:5173/dashboard --emulated-form-factor=mobile --only-categories=performance,accessibility,best-practices --output=json --output=html --output-path=docs/lighthouse-reports/dashboard --quiet

# Repetir para: /modules, /modules/1, /topics/1, /quiz/1, /chat, /coding/1, /progress, /achievements, /assessment
```

---

## Tabla resultados

Completar tras correr Lighthouse:

| # | Ruta | Performance | Accessibility | Best Practices | Issues encontrados | Status |
|---|------|-------------|---------------|-----------------|---------------------|--------|
| 1 | /login | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 2 | /assessment | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 3 | /dashboard | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 4 | /modules | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 5 | /modules/:id | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 6 | /topics/:id | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 7 | /quiz/:topicId | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 8 | /chat | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 9 | /coding/:id | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 10 | /progress | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 11 | /achievements | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 12 | /admin | _N/A_ | _N/A_ | _N/A_ | best-effort, admin desktop-first | _N/A_ |

## Umbrales Tier 3 DoD (Definition of Done)

- Accessibility ≥85 en todas páginas estudiante (rutas 1-11)
- Performance ≥70 en `/dashboard` y `/modules`
- Best Practices ≥85 todas
- Sin overflow horizontal en ninguna ruta estudiante a 375px

---

## Checklist manual de verificación (por página)

Por cada página estudiante, verificar en Chrome DevTools Device Toolbar 375×667:

- [ ] Sin scroll horizontal
- [ ] Touch targets interactivos ≥44×44px (botones, links, tabs, badges clicables)
- [ ] Texto body ≥14px, line-height ≥1.5
- [ ] Inputs font-size 16px (sin auto-zoom iOS al focus)
- [ ] Sticky bars (Quiz submit, Topic prev/next) no tapan contenido (main tiene pb-suficiente)
- [ ] Modal/Dialog se ajusta a viewport, scroll interno funciona
- [ ] Imágenes/iframes no overflow
- [ ] Chat: drawer abre/cierra suave; textarea con keyboard no rompe layout
- [ ] Coding: Monaco editor altura responsiva (320px mobile / 480px desktop)

## Screenshots (opcional)

Capturar antes/después de pasadas críticas si se quiere documentar para tesis:

```bash
mkdir -p docs/screenshots/mobile
```

Guardar como `docs/screenshots/mobile/{ruta}-{before|after}.png`.

---

## Próximos pasos

1. Ejecutar Lighthouse según sección "Cómo ejecutar Lighthouse mobile"
2. Llenar tabla resultados con scores reales
3. Marcar checklist manual
4. Si alguna métrica < umbral, abrir issue en backlog para iteración
5. Adjuntar este doc al reporte ISO/IEC 25010 final (Sprint 7)
