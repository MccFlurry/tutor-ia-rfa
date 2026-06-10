# Diseño — Acompañamiento Proactivo Fase 5: «El sistema sigue al estudiante» (Companion)

**Fecha:** 2026-06-09 · **Rama:** `feat/companion-seguimiento` · **Estado:** aprobado por tesista

## 1. Contexto y motivación

El asesor pidió que el sistema «siga» verdaderamente al estudiante desde la primera pantalla:
retroalimentación activa según el módulo en que se encuentra, materiales contextuales y un tutor
que habla primero. Las Fases 1-4 de acompañamiento (nudges deterministas, FloatingTutor, banco de
recursos, refuerzo post-resultado) cubren momentos puntuales; falta una noción central de
**posición del estudiante** (módulo actual + diagnóstico de desempeño) que alimente todas las
superficies.

**Encuadre tesis:** fuera de la matriz ISO 25010 (los 33 RF quedan congelados). Se documenta como
mejora de acompañamiento, igual que las Fases 1-4. No toca OE1-OE5 ni los tests del guardián ISO.
Operacionaliza el modelo de interacción/pedagógico del STI (insumo de OE3/OE5, sin crear OE nuevo).

## 2. Decisiones cerradas

| Decisión | Valor |
|---|---|
| Motor de diagnóstico | **Determinista** (reglas + plantillas, sin LLM) — testeable, sin latencia, no inventa |
| Intrusividad «tutor habla primero» | **Burbuja + preview**: globo pequeño sobre FloatingTutor, 1 vez por sesión; clic abre el chat |
| Encuadre OE5 | **Fuera de matriz** — mejora documentada, no RF formal |
| Alcance | Diagnóstico por módulo + panel «Tu ruta» en Dashboard + saludo contextual + recursos que siguen al módulo actual |

## 3. Backend

### 3.1 `backend/app/services/companion_service.py`

Mismo patrón que `tutor_service.py`: funciones puras + un `gather` que resuelve estado desde BD.

- **`resolve_position(user, db) -> StudentPosition`** — módulo actual = primer módulo
  **desbloqueado e incompleto**, consultando `module_service.compute_locks` (invariante
  centralizado; nunca re-derivar la regla de desbloqueo secuencial). Si todo está completo →
  estado `course_completed`.
- **`build_diagnostic(stats) -> ModuleDiagnostic`** — función pura. Entrada: stats por tema del
  módulo actual (mejor score de quiz, nº intentos, aprobado, completado, mejor score coding).
  Clasificación por tema:
  - **Repasar (weak):** mejor score < 60, o ≥ 2 intentos fallidos
  - **Afianzar (practice):** aprobado con mejor score 60–79
  - **Dominado:** mejor score ≥ 80
  - **Pendiente:** tema no visitado
  - **`next_action`** por prioridad: (1) reintentar tema débil → (2) siguiente tema pendiente en
    orden → (3) desafío coding sin resolver del módulo. Sin candidatos → CTA al módulo.
- **`build_greeting(position, diagnostic) -> str`** — plantillas en español peruano. Ejemplo:
  *«Estás en M3: Interfaces de Usuario — 60% completado. Veo que te cuesta “Layouts”, ¿lo
  repasamos?»*. Variantes: sin nivel, recién empieza, con tema débil, sin tema débil, curso
  completo.

### 3.2 Endpoint `GET /api/v1/tutor/companion`

En `routers/tutor.py` existente. Auth requerida. Respuesta:

```json
{
  "needs_assessment": false,
  "position": {
    "module_id": 3, "module_title": "Interfaces de Usuario",
    "icon_name": "...", "color_hex": "...",
    "progress_pct": 60.0, "topics_done": 3, "topics_total": 5,
    "course_completed": false
  },
  "greeting": "Estás en M3...",
  "diagnostic": {
    "weak":     [{"topic_id": 12, "title": "Layouts", "best_score": 45, "attempts": 2}],
    "practice": [{"topic_id": 13, "title": "Intents", "best_score": 70, "attempts": 1}],
    "next_action": {"kind": "retry_quiz", "label": "Repasar Layouts", "route": "/topics/12"}
  },
  "resources": []
}
```

- `resources`: máx 3 `LearningResource` activos del módulo actual (reusa query de Fase 3).
- Sin evaluación de entrada → `{"needs_assessment": true, "greeting": "...→ /assessment"}` y el
  resto en `null` (consistente con regla R1 de nudges).
- Caché Redis `companion:{user_id}` TTL 60s vía `app/utils/cache.py` (degraded mode si Redis cae).
- Sin LLM en ningún punto del flujo.
- Schemas nuevos en `app/schemas/companion.py` (Pydantic v2).

## 4. Frontend

### 4.1 Hook `useCompanion()`

TanStack Query sobre `GET /tutor/companion`, `staleTime` 60s. Única fuente para las 3 superficies.

### 4.2 `CompanionPanel` en Dashboard (`components/tutor/CompanionPanel.tsx`)

- Reemplaza/extiende el hero «Continuar…»: módulo actual (icono + color del módulo), barra de
  progreso X/Y temas, **chips de diagnóstico** clicables («Repasar: Layouts» → `/topics/12`),
  CTA primario = `next_action`, 2-3 recursos del módulo.
- `needs_assessment` → panel apunta a evaluación de entrada (comportamiento actual se conserva).
- `course_completed` → estado celebratorio + repaso libre.
- Skeleton matching shape; si el endpoint falla → hero actual sin diagnóstico (degradación
  silenciosa, principio de diseño 5).

### 4.3 Burbuja preview en `FloatingTutor`

- Al montar, globo pequeño con `greeting` + cerrar. Clic → abre el panel de chat existente.
- **1 vez por sesión** (flag en `sessionStorage`); auto-oculta ~12 s sin interacción.
- `motion-safe`, tokens semánticos (dark mode), `role="status"` (no roba foco), ESC cierra.

### 4.4 Franja diagnóstico en `ModuleDetailPage`

- Solo si `module_id` == módulo actual: chips repasar/afianzar sobre la lista de temas.
- Componente compartido `DiagnosticChips` (usado también por CompanionPanel).

### 4.5 Sin cambios

TopicPage (ya tiene ResourceList por tema + nudges), QuizPage/CodingChallengePage (Fase 4 cubre
post-resultado). Accesibilidad: touch ≥44 px, foco visible.

## 5. Testing

- **Unit backend** `tests/unit/test_companion_service.py`: bandas de `build_diagnostic`
  (<60 / 60-79 / ≥80, ≥2 fallidos, no visitado, módulo sin datos), `resolve_position`
  (nada iniciado → M1, intermedio, todo completo, sin nivel), prioridad de `next_action`,
  plantillas de `build_greeting`.
- **Integration** `tests/integration/test_companion.py`: 401 sin token, shape del payload,
  caso `needs_assessment`, caché hit/miss (mock Redis).
- **Frontend** (Vitest + RTL, smoke): `CompanionPanel` con mock (diagnóstico, needs_assessment,
  course_completed, error → degradación), burbuja preview (1 vez por sesión, cierre).

## 6. Resiliencia y errores

| Falla | Comportamiento |
|---|---|
| Endpoint companion cae | Dashboard degrada al hero actual; FloatingTutor sin globo |
| Redis caído | `cache.py` degraded mode → query directa a BD |
| Estudiante sin quizzes | Diagnóstico vacío legítimo: solo «Pendiente: siguiente tema» |
| Sin evaluación de entrada | `needs_assessment: true` → CTA a `/assessment` |

## 7. Documentación

- CLAUDE.md: nueva entrada «ACOMPAÑAMIENTO PROACTIVO (Fase 5)» + endpoint en sección API `/tutor`.
- No se toca: matriz ISO, reporte OE5, tests del guardián (los nuevos tests son adicionales).

## 8. Fuera de alcance (YAGNI)

Página dedicada «Mi Ruta», LLM en feedback, notificaciones push/email, re-cálculo de nivel
(auto-leveling ya existe), seguimiento entre módulos no actuales.
