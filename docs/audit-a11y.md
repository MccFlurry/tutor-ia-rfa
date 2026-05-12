# Guía de auditoría A11y + Performance — Sprint 7 (ISO/IEC 25010) + Sprint 8 (SUS)

Proyecto: Tutor IA — IESTP "República Federal de Alemania" · Tesis pregrado USAT
Vinculación: OE5 · `docs/reporte-ISO25010.docx` · `docs/reporte-SUS.docx`

---

## 1. Preparación

### 1.1 Levantar el frontend en modo dev

```bash
cd frontend
npm install        # si aún no
npm run dev        # http://localhost:5173
```

Asegurar backend levantado (`docker compose up backend`) para que las páginas autenticadas no fallen.

### 1.2 Cuentas de prueba

- Estudiante piloto: `estudiante.test@iestprfa.edu.pe` / `Test123!`
- Admin: `admin@iestprfa.edu.pe` / `Admin123!`

---

## 2. Herramientas

| Herramienta | Uso | Instalación |
|---|---|---|
| **Lighthouse CLI** | Performance + A11y + Best Practices automatizado por página | `npm i -g lighthouse` |
| **axe DevTools** | Escaneo a11y interactivo en navegador | Extensión Chrome/Firefox · Deque Systems |
| **NVDA** (Windows) | Lector de pantalla — anuncios + foco | https://www.nvaccess.org |
| **WebAIM Contrast Checker** | Validar pares foreground/background dudosos | https://webaim.org/resources/contrastchecker/ |
| **Chrome DevTools → Issues / Rendering** | Forzar `prefers-reduced-motion`, `prefers-color-scheme`, viewport 375px | Nativo |

---

## 3. Páginas a auditar (orden recomendado)

| # | Ruta | Estado autenticación | Foco de auditoría |
|---|---|---|---|
| 1 | `/login` | Sin auth | Form + brute-force lockout + responsive 375px |
| 2 | `/assessment` | Auth sin nivel | Wizard radiogroup + AILoadingState + progressbar |
| 3 | `/dashboard` | Estudiante | Hero + StatCards + recomendaciones + logros |
| 4 | `/modules` | Estudiante | Grid responsivo + estado bloqueado |
| 5 | `/modules/:id` | Estudiante | Lista temas + breadcrumb |
| 6 | `/topics/:id` | Estudiante | Markdown + video iframe + acciones |
| 7 | `/quiz/:topicId` | Estudiante | RadioGroup + AILoadingState + sticky submit |
| 8 | `/chat` | Estudiante | Textarea + sessions sidebar + sources |
| 9 | `/coding/:id` | Estudiante | Monaco + Dialog regenerar |
| 10 | `/progress` | Estudiante | 4× StatCard + grids logros |
| 11 | `/achievements` | Estudiante | Grid + estado earned/locked |
| 12 | `/admin` | Admin | 5 tabs + tablas |

---

## 4. Lighthouse — comando por página

```bash
# Reemplazar TOKEN si la ruta requiere auth; usa --view para abrir el reporte
lighthouse http://localhost:5173/dashboard \
  --only-categories=performance,accessibility,best-practices \
  --form-factor=mobile \
  --throttling-method=simulate \
  --output=html --output-path=./reports/lh-dashboard.html

# Repetir por ruta → guardar en frontend/reports/
```

**Umbrales tesis (CLAUDE):**
- Performance ≥ 70 en ModulesPage + DashboardPage
- Accessibility ≥ 85 en todas las rutas autenticadas

**Para rutas autenticadas:** abrir el sitio en Chrome, iniciar sesión, luego DevTools → Lighthouse → "Mobile" + "Accessibility/Performance" → Generate.

---

## 5. axe DevTools — pasos por página

1. Abrir página en Chrome.
2. DevTools (F12) → pestaña **axe DevTools** → "Scan all of my page".
3. Resolver issues `serious` y `critical`. Reportar `moderate` aceptados (justificar en `reporte-ISO25010.docx`).
4. Capturar pantalla del panel cuando 0 issues serious/critical.

**Issues frecuentes a verificar:**
- Pares `text-muted-foreground` (gris 215/16/45 ≈ #6b7280) sobre fondos claros — contraste 4.5:1 mínimo
- `text-primary-200` sobre `bg-brand-hero` (DashboardPage hero) — verificar
- Chips difficulty `text-warning-foreground` sobre `bg-warning/15` — verificar en dark
- Editor Monaco sub-frame — ignorar (3rd party)

---

## 6. Checklist manual (mapeada a ISO/IEC 25010:2023)

### 6.1 Adecuación funcional (completitud + corrección)

- [ ] **F1** Registro nuevo estudiante → assessment → dashboard funciona sin errores
- [ ] **F2** Login con cuenta existente y nivel asignado va directo a `/dashboard`
- [ ] **F3** Quiz: si Ollama responde → preguntas IA; si cae → mensaje claro y opción Reintentar
- [ ] **F4** Coding challenge: enviar código vacío muestra error; código válido recibe score + feedback Markdown
- [ ] **F5** Chat tutor: pregunta on-topic devuelve fuentes con `similarity ≥ 0.75`; off-topic recibe rechazo cortés
- [ ] **F6** Logout y refresh preserva estado correctamente
- [ ] **F7** Rate limit chat (20/h) se respeta — banner amarillo + textarea disabled cuando `remaining=0`

### 6.2 Usabilidad — operabilidad teclado

- [ ] **K1** Tab order coincide con orden visual en cada página
- [ ] **K2** Skip-link "Saltar al contenido principal" funcional con Tab desde top + Enter
- [ ] **K3** Sidebar móvil: abrir con menu → cerrar con Esc o botón close → foco vuelve a menu trigger
- [ ] **K4** Quiz/Assessment: opciones navegables con flechas (`role=radiogroup` nativo); Space/Enter selecciona
- [ ] **K5** Dialog regenerar (Coding): foco atrapado dentro; Esc cierra y vuelve al trigger
- [ ] **K6** Logout botón alcanzable con Tab desde cualquier página
- [ ] **K7** Foco post-navegación: cambiar ruta mueve foco a `#main-content` (hook `useFocusMain`)

### 6.3 Usabilidad — operabilidad lector pantalla (NVDA)

- [ ] **SR1** NVDA anuncia titular de página `<h1>` al entrar a cada ruta
- [ ] **SR2** Errores form Login se anuncian (`role="alert"` + `aria-live`)
- [ ] **SR3** Toast react-hot-toast se anuncia sin robar foco
- [ ] **SR4** Progreso quiz: progressbar anuncia "Pregunta X de Y" con valores
- [ ] **SR5** Logros earned vs locked se distinguen (Lock icon + texto, no solo color)
- [ ] **SR6** Sources del chat colapsables — botón anuncia estado expandido/colapsado

### 6.4 Usabilidad — contraste + motion

- [ ] **C1** Modo claro: contraste texto cuerpo ≥ 4.5:1 en todas las páginas
- [ ] **C2** Modo claro: focus ring visible (2px ring-ring + ring-offset-2)
- [ ] **C3** Modo oscuro: idem contraste 4.5:1 (ThemeToggle → dark)
- [ ] **C4** `prefers-reduced-motion: reduce` desactiva spinners largos + transiciones (verificar DevTools → Rendering)
- [ ] **C5** Color nunca único portador de información: completed/pending tienen icono o texto

### 6.5 Eficiencia (performance)

- [ ] **P1** Lighthouse Performance ≥ 70 en `/modules` mobile
- [ ] **P2** Lighthouse Performance ≥ 70 en `/dashboard` mobile
- [ ] **P3** CLS < 0.1 en todas las páginas (Core Web Vitals)
- [ ] **P4** Imágenes con `width/height` o `aspect-ratio` declarados
- [ ] **P5** Fuentes con `display=swap` (verificado en index.html)
- [ ] **P6** No bloqueo main thread > 50ms durante interacción

### 6.6 Responsive design

- [ ] **R1** Funcional en viewport 375×667 (iPhone SE) sin scroll horizontal
- [ ] **R2** Funcional en viewport 768×1024 (tablet)
- [ ] **R3** Funcional en viewport 1440×900 (desktop)
- [ ] **R4** Touch targets ≥ 44×44px en mobile (verificado vía Inspector DevTools)
- [ ] **R5** Texto ≥ 16px base mobile (evita zoom iOS al enfocar inputs)
- [ ] **R6** Orientación landscape mobile usable

### 6.7 Compatibilidad navegadores

- [ ] **B1** Chrome 120+ — golden path completo
- [ ] **B2** Firefox 120+ — golden path
- [ ] **B3** Safari macOS — golden path (especial atención a `min-h-dvh`)
- [ ] **B4** Edge — golden path

---

## 7. Golden path piloto SUS (Sprint 8)

Cronometrar cada paso. Objetivo: < 20 min sin asistencia.

1. Login con cuenta provista (cred en sobre)
2. Completar evaluación entrada (~12 preguntas)
3. Ver dashboard + entender nivel asignado
4. Entrar a módulo recomendado
5. Leer 1 tema + marcar completado o aprobar quiz IA
6. Hacer 1 pregunta al tutor IA chat
7. Resolver 1 desafío código (puede fallar — observar reacción)
8. Revisar progreso

Tras completar el flujo: aplicar **cuestionario SUS** estándar (10 ítems Likert 1-5).

---

## 8. Reporte

Generar tabla resumen para `reporte-ISO25010.docx`:

| RF | Página | Lighthouse Perf | Lighthouse A11y | axe issues | Manual checks pasados |
|---|---|---|---|---|---|
| RF-XX | /dashboard | 78 | 92 | 0 critical, 1 moderate (justif.) | 12/12 |
| ... | | | | | |

**Cobertura:** ≥ 80% de 33 RF priorizados con al menos 1 escenario validado.
**Tasa éxito:** ≥ 90% de los escenarios sin defectos `serious`/`critical`.

---

## 9. Defectos conocidos a verificar tras fixes Fases A-C

- ✅ `text-gray-400/500` reemplazado por `text-muted-foreground` (semantic)
- ✅ Touch targets en Sidebar close, Navbar menu, Chat sidebar toggle, Chat delete fixed
- ✅ Foco post-navegación implementado (`useFocusMain`)
- ✅ Heading hierarchy: ContentRenderer downshift h1→h2
- ✅ Dark mode toggle disponible en Navbar
- ✅ ARIA radiogroup en Quiz + EntryAssessment
- ✅ Native confirm() reemplazado por Dialog accesible en CodingChallenge
- ⏳ Lighthouse baseline pendiente — ejecutar y guardar en `frontend/reports/`
- ⏳ axe DevTools scan pendiente — capturar screenshots

---

*v1.0 — Generado tras Fase C UI/UX. Insumo para Sprint 7 (ISO/IEC 25010) y Sprint 8 (SUS piloto IESTP RFA).*
