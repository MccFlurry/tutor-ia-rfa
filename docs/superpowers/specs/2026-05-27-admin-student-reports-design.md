# Spec — Admin Student Reports Screen

- **Fecha:** 2026-05-27
- **Autor:** Roger Alessandro Zavaleta Marcelo (con asistencia de Claude)
- **Solicitante:** Asesora Mg. Reyes Burgos, Karla
- **Estado:** Diseño aprobado, pendiente de implementación
- **Sprint relacionado:** Extensión admin entre Sprint 7 (cerrado) y Sprint 8 (SUS, 29 jun – 10 jul 2026). Debe estar lista antes del piloto.
- **Branch sugerido:** `feat/admin-student-reports`

---

## 1. Contexto y motivación

La asesora del proyecto solicitó que el rol **admin** disponga de una pantalla dedicada para revisar a todos los estudiantes inscritos en el sistema. Hoy `AdminPage` tiene 5 tabs (Corpus, Contenido, Usuarios, Banco, Niveles) y `UsersTab` solo muestra rol/nivel/estado sin métricas pedagógicas, sin comparativas ni reportes generados por IA. Para el pilotaje SUS y para la sustentación se necesita visibilidad pedagógica completa.

### Objetivo

Agregar una nueva tab **"Reportes"** al panel admin y una **página dedicada por estudiante**, todo restringido a `role=admin`, que permita:

1. Ver tabla con todos los estudiantes (sortable + filtrable) — nivel, progreso, promedios, última actividad, última ubicación dentro de la app.
2. Drilldown por estudiante: detalle completo (nivel + historial, progreso global y por módulo, últimos quizzes/coding, uso de chat, logros, tiempo, última actividad y ubicación).
3. Generar **reporte IA dinámico** por estudiante: resumen narrativo, fortalezas, debilidades, riesgo de abandono y recomendaciones de intervención docente (1 llamada LLM única, salida JSON estructurada).
4. Generar **reporte IA comparativo de cohorte** (2 a 15 estudiantes seleccionados).
5. Exportar a PDF mediante diálogo nativo del navegador (`window.print()` + CSS `@media print`).

### Restricciones (heredadas de CLAUDE.md)

- LLM 100% privado vía Ollama (`qwen2.5:7b-instruct-q4_K_M`). **Sin APIs externas.**
- Sin migraciones nuevas — toda la información ya existe en tablas actuales.
- UI en español peruano. Código y comentarios técnicos en inglés.
- Cache Redis 1h para los reportes IA (LLM ~10-30 s). Degraded mode si Redis cae.
- Mantener cobertura backend ≥80% (actualmente 86%).

---

## 2. Arquitectura

> Nota sobre `cached_json`: el helper existente en `app/utils/cache.py` no expone si el valor vino del cache o se computó. Para mantener el flag `cached: bool` que el frontend muestra, los endpoints de reporte IA hacen `redis.get` + `redis.setex` explícitos envueltos en wrappers de degraded mode (`_safe_redis_get` / `_safe_redis_setex` definidos dentro de `student_report_service.py`). El helper `cached_json` se sigue usando en endpoints de tabla (`GET /admin/students`) donde no se necesita el flag.

### 2.1 Backend (FastAPI)

**Nuevo router:** `app/routers/admin_reports.py` (se mantiene separado de `admin.py` para evitar que el archivo crezca por encima de 700 líneas).

| Método | Ruta | Descripción |
|---|---|---|
| `GET`  | `/admin/students` | Lista enriquecida para la tabla |
| `GET`  | `/admin/students/{user_id}` | Detalle agregado del estudiante |
| `POST` | `/admin/students/{user_id}/ai-report` | Genera reporte narrativo (cache Redis) |
| `POST` | `/admin/students/cohort/ai-report` | Reporte comparativo de cohorte |

Todos los endpoints exigen `Depends(require_admin)` (ya existente en `app/dependencies.py`).

**Nuevo servicio:** `app/services/student_report_service.py` con responsabilidades:

- `get_students_overview(db) -> list[StudentRow]` — agrega progreso, promedios quiz/coding, última actividad/ubicación, en una sola query con JOINs.
- `get_student_detail(db, user_id) -> StudentDetail` — todo el detalle del estudiante (nivel + historial, módulos, últimos quizzes/coding, chat, logros, tiempo).
- `generate_ai_report(db, redis, user_id) -> AIReport` — construye prompt, llama LLM `format="json"` con `temperature=0.3`, valida, cachea Redis (`student_report:{user_id}:{detail_hash}` TTL 3600s). Reintento 1× con `temperature=0.1` si parseo JSON falla. Devuelve campo `cached: bool`.
- `generate_cohort_report(db, redis, user_ids) -> CohortAIReport` — comparativa grupal. Cache key `cohort_report:{sha256(sorted user_ids + their detail_hashes)}` TTL 3600s.

**Reutiliza:**
- `app/services/llm_service.py` — patrón Ollama JSON (`ChatOllama` con `format="json"`, `temperature` configurable, truncado a 3 500 chars, parser tolerante a wrapper `{ "report": {...} }` o JSON desnudo). Para los reportes se agrega una función nueva `generate_student_report_text(detail_serialized, prompt_kind)` siguiendo el mismo patrón que `generate_quiz_questions`.
- `app/utils/cache.py::cached_json(redis_client, key, *, ttl, loader)` — helper Redis con degraded mode (sigue funcionando sin cache). Se reutiliza tal cual.

### 2.2 Frontend (React + TS)

- Nueva tab **"Reportes"** en `frontend/src/pages/AdminPage.tsx` (icono `BarChart3` de Lucide).
- Componente `frontend/src/components/admin/StudentsReportTab.tsx` — tabla sortable + filtros + botón cohort.
- Nueva ruta `/admin/students/:userId` registrada en el router principal (protegida por el wrapper admin actual).
- Página `frontend/src/pages/AdminStudentReportPage.tsx` — detalle + reporte IA + botón imprimir.
- Cliente API `frontend/src/api/adminReports.ts`.
- Tipos `frontend/src/types/adminReports.ts`.
- CSS print agregado a `frontend/src/index.css` bajo `@media print`.

### 2.3 Datos — **sin migraciones nuevas**

Toda la información se computa desde tablas existentes:

| Métrica | Fuente |
|---|---|
| Nivel + historial + entry_score | `user_levels` |
| Progreso por tema | `user_topic_progress` |
| Quizzes | `quiz_attempts` |
| Coding | `coding_submissions` |
| Chat usage | `chat_messages` JOIN `chat_sessions` |
| Logros | `user_achievements` JOIN `achievements` |
| Última actividad/ubicación | `MAX(updated_at|completed_at|attempted_at|submitted_at|created_at)` cruzado con título del tema |

---

## 3. Componentes y contratos

### 3.1 Schemas Pydantic — `app/schemas/admin_reports.py`

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class StudentRow(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    level: str | None                  # beginner | intermediate | advanced | None
    entry_score: float | None
    overall_progress_pct: float        # 0..100
    avg_quiz_score: float | None       # 0..1 (escala existente)
    avg_coding_score: float | None     # 0..100
    last_activity_at: datetime | None
    last_location: str | None          # e.g. "M2 - Variables en Kotlin" o "Chat IA"
    is_active: bool

class ModuleProgress(BaseModel):
    module_id: int
    module_title: str
    topics_total: int
    topics_completed: int
    progress_pct: float                # 0..100
    avg_quiz_score: float | None       # 0..1
    avg_coding_score: float | None     # 0..100

class QuizAttemptRow(BaseModel):
    attempt_id: int
    topic_id: int
    topic_title: str
    score: float                       # 0..1
    is_passed: bool
    attempted_at: datetime

class CodingSubmissionRow(BaseModel):
    submission_id: int
    challenge_id: int
    challenge_title: str
    score: float                       # 0..100
    submitted_at: datetime

class AchievementRow(BaseModel):
    achievement_id: int
    name: str
    badge_emoji: str
    earned_at: datetime

class LevelHistoryEntry(BaseModel):
    level: str
    score: float
    changed_at: datetime
    reason: str | None = None

class StudentDetail(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    created_at: datetime
    is_active: bool
    level: str | None
    entry_score: float | None
    level_history: list[LevelHistoryEntry]
    overall_progress_pct: float
    modules: list[ModuleProgress]
    recent_quizzes: list[QuizAttemptRow] = Field(default_factory=list, max_length=10)
    recent_coding: list[CodingSubmissionRow] = Field(default_factory=list, max_length=10)
    chat_messages_count: int
    chat_last_at: datetime | None
    achievements_earned: list[AchievementRow]
    total_time_seconds: int
    last_activity_at: datetime | None
    last_location: str | None

class AIReport(BaseModel):
    summary: str                       # 3-4 párrafos en español
    strengths: list[str]
    weaknesses: list[str]
    risk_level: str                    # bajo | medio | alto
    risk_reason: str
    interventions: list[str]
    generated_at: datetime
    cached: bool

class CohortReportRequest(BaseModel):
    user_ids: list[UUID] = Field(min_length=2, max_length=15)

class CohortAIReport(BaseModel):
    narrative: str
    top_performers: list[str]          # full_name de estudiantes
    needs_support: list[str]
    common_gaps: list[str]             # patrones grupales: "M3 UI promedios coding bajos"
    recommendations: list[str]
    generated_at: datetime
    cached: bool
```

### 3.2 Servicio — pseudocódigo clave

```python
# app/services/student_report_service.py
async def get_students_overview(db: AsyncSession) -> list[StudentRow]:
    # Query única con JOINs:
    #   users LEFT JOIN user_levels
    #         LEFT JOIN (subquery progreso global por user)
    #         LEFT JOIN (subquery avg_quiz por user)
    #         LEFT JOIN (subquery avg_coding por user)
    #         LEFT JOIN (subquery last_activity_at por user = MAX over 4 tablas)
    # Resuelve last_location en una segunda query batch (1 más, no N+1).
    ...

async def get_student_detail(db: AsyncSession, user_id: UUID) -> StudentDetail:
    # Carga user + level + progreso por módulo + últimos 10 quizzes y coding
    # + chat counts + achievements + total_time = SUM(user_topic_progress.time_spent_seconds)
    ...

def _detail_hash(detail: StudentDetail) -> str:
    # sha256 sobre campos volátiles:
    #   overall_progress_pct, avg de modules, len(recent_quizzes), score último quiz,
    #   len(recent_coding), score último coding, chat_messages_count, last_activity_at iso.
    # Cambia cuando estudiante avanza → cache se invalida automáticamente.
    ...

async def generate_ai_report(
    db: AsyncSession, redis_client, user_id: UUID,
) -> AIReport:
    detail = await get_student_detail(db, user_id)
    if not _has_minimum_activity(detail):
        raise InsufficientActivityError("Sin actividad suficiente. Esperar primer quiz.")

    key = f"student_report:{user_id}:{_detail_hash(detail)}"

    # GET/SET explícito (no usamos cached_json aquí porque necesitamos exponer `cached` flag).
    # Degraded mode: si Redis lanza, se ignora silenciosamente con logger.warning.
    cached_raw = await _safe_redis_get(redis_client, key)
    if cached_raw:
        payload = json.loads(cached_raw)
        return AIReport(**payload, cached=True)

    prompt = _build_report_prompt(detail)
    try:
        raw = await llm_service.generate_student_report_text(prompt, temperature=0.3)
        parsed = _parse_report(raw)
    except (json.JSONDecodeError, ValidationError, LLMParseError):
        raw = await llm_service.generate_student_report_text(prompt, temperature=0.1)
        parsed = _parse_report(raw)  # si falla otra vez, propaga → router devuelve 503

    parsed["generated_at"] = datetime.utcnow().isoformat()
    await _safe_redis_setex(redis_client, key, 3600, json.dumps(parsed, default=str))
    return AIReport(**parsed, cached=False)

async def generate_cohort_report(
    db: AsyncSession, redis: Redis, user_ids: list[UUID],
) -> CohortAIReport:
    # Filtra solo role=student (admin/inactive → 400 si quedan <2).
    # Carga overview de cada uno (reutiliza get_students_overview filtrando IDs).
    # Hash = sha256(sorted(user_ids) + sorted(detail_hashes)). Cache 1h.
    # Prompt: comparativa, identifica top/bottom, patrones comunes, recomendaciones.
    ...
```

### 3.3 Prompts LLM

**Reporte individual (system):**

> Eres tutor pedagógico evaluador de estudiantes IESTP RFA del curso de Aplicaciones Móviles (Kotlin/Android). Respondes SOLO con un objeto JSON válido siguiendo el schema. Tu lenguaje es español peruano, profesional pero cercano. Basa toda inferencia en los datos provistos — nunca inventes números ni eventos no reportados. Si la evidencia es insuficiente para una categoría, indícalo en `risk_reason`.

**Reporte individual (user):** datos serializados de `StudentDetail` (truncados a 3 500 chars: solo lo más reciente y agregado) + ejemplo JSON esperado.

**Reporte cohorte (system):** análogo, énfasis en comparación y patrones grupales.

**Schema esperado en respuesta:**

```json
{
  "report": {
    "summary": "...",
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."],
    "risk_level": "bajo|medio|alto",
    "risk_reason": "...",
    "interventions": ["...", "..."]
  }
}
```

Parser tolera tanto `{"report": {...}}` como `{...}` directo (patrón existente en `llm_service.py`).

### 3.4 Frontend — componentes

**`StudentsReportTab.tsx`** — flujo:

- `useQuery(['admin','students-report'], adminReportsApi.list)` → tabla.
- Estado local: `sortBy`, `sortDir`, `filterLevel`, `searchQuery`, `showInactive`.
- Columnas sortables: Nombre, Email, Nivel, Progreso %, Promedio Quiz, Promedio Coding, Última actividad, Última ubicación.
- Filtros: select nivel, input búsqueda nombre/email (debounce 200 ms), checkbox "Incluir inactivos".
- Click fila → `navigate('/admin/students/${userId}')`.
- Botón "Reporte cohorte IA" → modal con multi-select (2-15 estudiantes filtrados) y, al confirmar, mutation que renderiza la narrativa en el mismo modal.

**`AdminStudentReportPage.tsx`** — flujo:

- Header: nombre + badge nivel + chip "Última actividad: <relativa> · <ubicación>".
- 4 secciones:
  1. Resumen (cards: progreso global, total tiempo, promedios quiz/coding).
  2. Progreso por módulo (barras + totales).
  3. Últimas 10 evaluaciones (tabla quizzes + tabla coding).
  4. Historial de nivel (timeline desde `level_history`).
- Panel colapsable "Reporte IA":
  - Botón "Generar reporte" → mutation `POST /admin/students/{id}/ai-report`.
  - Mientras carga: spinner + texto "La IA está analizando…".
  - Tras éxito: renderiza `summary` con `react-markdown`, chip de `risk_level` (verde/amarillo/rojo), listas de fortalezas/debilidades/intervenciones, sello "Generado con IA · cacheado" si `cached=true`.
- Botón "Imprimir / PDF" → `window.print()`. Anchor con clase `no-print` para los botones.

**CSS print** (`frontend/src/index.css`):

```css
@media print {
  .no-print { display: none !important; }
  .printable-report { max-width: 100% !important; box-shadow: none !important; }
  body { background: #fff !important; color: #000 !important; }
  /* Oculta sidebar/topbar globales que viven fuera de .printable-report */
  aside, header.app-header { display: none !important; }
}
```

### 3.5 Flujo de datos — reporte IA individual

```
Admin abre /admin/students/{id}
  → GET /admin/students/{id} (detalle agregado, ~150 ms)
Admin click "Generar reporte IA"
  → POST /admin/students/{id}/ai-report
       backend: get_student_detail → _detail_hash → Redis GET
         miss → build prompt → qwen2.5 format="json" temp=0.3
                parse → (fallback temp=0.1 si falla) → Redis SETEX 3600s
         hit  → return cached
  → frontend renderiza AIReport (≤30 s primera vez, instantáneo si cache)
```

---

## 4. Manejo de errores

**Backend:**

| Caso | Respuesta |
|---|---|
| Usuario no existe | 404 `Estudiante no encontrado` |
| Usuario no es `role=student` | 400 `Solo aplica a estudiantes` |
| Estudiante sin actividad mínima (sin quiz ni coding) | 422 `Sin actividad suficiente. Esperar primer quiz.` |
| Ollama caído | 503 `Servicio IA no disponible. Reintenta en unos minutos.` |
| LLM devuelve JSON malformado | Reintento 1× con `temperature=0.1`. Si falla → 503 genérico + log |
| Pydantic validation falla | 503 + log |
| Redis caído | Degraded mode (sin cache). Patrón existente en `app/utils/cache.py` |
| Cohort `user_ids` fuera de [2..15] | 400 `Selecciona entre 2 y 15 estudiantes` |
| Cohort después de filtrar no-estudiantes queda <2 | 400 con mensaje explicativo |

**Frontend:**

- React Query `onError` → toast rojo con `error.response.data.detail`.
- 503 reporte IA → toast "IA no disponible. Reintenta" y el botón "Generar" no se deshabilita.
- 404 detalle → `RouteErrorBoundary` con fallback "Estudiante no encontrado" + link volver.
- Loading skeleton durante generación: spinner + "La IA está analizando…".
- Estudiante sin actividad mínima → panel IA bloqueado con mensaje y CTA "Volver a tabla".

**Hardening LLM:**

- Prompt explícito: "responde SOLO JSON válido", schema embebido, 1 ejemplo.
- Parser tolera wrapper `{"report": {...}}` y JSON desnudo.
- `StudentDetail` serializado se trunca a ≤3 500 chars antes de pasarlo al prompt (mantener `recent_quizzes` y `recent_coding` últimas 10, módulos completos).

---

## 5. Testing

### 5.1 Backend unit — `backend/tests/unit/test_student_report_service.py`

- `test_get_students_overview_aggregates_correctly` — fixture: 2 estudiantes, progreso y notas distintas. Verifica que la lista devuelta tiene los promedios correctos.
- `test_get_student_detail_includes_level_history` — `UserLevel.history` JSONB se mapea a `LevelHistoryEntry[]`.
- `test_last_location_resolves_topic` — última actividad apunta al título del tema correcto.
- `test_last_location_none_for_inactive` — usuario recién creado → `None`.
- `test_ai_report_cache_hit` — mock LLM, primera llamada genera, segunda con mismo hash devuelve `cached=True` sin invocar LLM.
- `test_ai_report_cache_miss_on_progress_change` — modificar `user_topic_progress` cambia `_detail_hash` → nueva llamada al LLM.
- `test_ai_report_parses_wrapped_json` — `{"report":{...}}` válido.
- `test_ai_report_parses_bare_json` — `{...}` directo válido.
- `test_ai_report_malformed_then_retry_succeeds` — primera respuesta basura, segunda válida → éxito.
- `test_ai_report_malformed_twice_raises_503` — ambos fallan → `LLMReportError` que el router convierte en 503.
- `test_ai_report_insufficient_activity_raises_422` — estudiante sin quiz ni coding → `InsufficientActivityError`.
- `test_cohort_report_filters_non_students` — admin/inactive en lista → excluído.
- `test_cohort_report_size_bounds` — <2 o >15 → `ValueError` (router convierte en 400).
- `test_cohort_report_cache_key_stable_across_order` — `[u1,u2]` y `[u2,u1]` producen misma key.

### 5.2 Backend integration — `backend/tests/integration/test_admin_reports.py`

- `test_get_students_requires_admin` — student token → 403, admin token → 200.
- `test_get_students_returns_enriched_list` — seed 3 usuarios, GET → 3 filas con todos los campos esperados.
- `test_get_student_detail_admin_only` — student → 403; admin → 200.
- `test_ai_report_endpoint_success_mocked_llm` — monkeypatch `llm_service.invoke_json`, GET devuelve `AIReport`.
- `test_ai_report_endpoint_503_when_llm_fails` — mock LLM raise → 503.
- `test_ai_report_endpoint_422_insufficient_activity` — usuario nuevo → 422.
- `test_cohort_report_endpoint_validates_user_ids` — lista fuera de bounds → 400.
- `test_cohort_report_endpoint_success_mocked_llm` — 3 estudiantes seed + mock → 200 con `CohortAIReport`.

### 5.3 Frontend tests — Vitest + RTL

- `StudentsReportTab.test.tsx`:
  - Renderiza tabla con datos mock.
  - Ordena por columna al click (asc/desc/reset).
  - Filtra por nivel.
  - Búsqueda por nombre/email funciona con debounce.
  - Click fila → `useNavigate` llamado con `/admin/students/{id}` (mock router).
  - Botón cohort abre modal.
- `AdminStudentReportPage.test.tsx`:
  - Loading skeleton mientras query pendiente.
  - Renderiza 4 secciones cuando data está lista.
  - Click "Generar reporte" dispara mutation y muestra spinner.
  - Renderiza reporte tras success, chip de riesgo correcto.
  - "Imprimir / PDF" llama `window.print()` (spy).
  - Error 503 → toast visible, botón sigue habilitado.

### 5.4 Cobertura

- Mantener cobertura backend ≥80% (actual 86%).
- Sumar ~13 tests backend + ~6 frontend = ~19 nuevos.
- ISO/IEC 25010 — agregar fila correspondiente en `docs/matriz-trazabilidad-ISO25010.md` (nuevo RF "Reporte pedagógico admin").

---

## 6. Trazabilidad ISO/IEC 25010

Nuevo RF a registrar en `docs/matriz-trazabilidad-ISO25010.md`:

- **RF-NEW-RPT-01:** El administrador puede consultar reporte individual de cada estudiante con métricas pedagógicas.
  - Cobertura: `test_get_student_detail_*`, `test_ai_report_endpoint_*`.
- **RF-NEW-RPT-02:** El sistema genera reporte narrativo IA por estudiante con resumen, riesgo e intervenciones.
  - Cobertura: `test_ai_report_*_service`, `test_ai_report_endpoint_success_mocked_llm`.
- **RF-NEW-RPT-03:** El administrador puede generar reporte comparativo de cohorte (2-15 estudiantes).
  - Cobertura: `test_cohort_report_*`.
- **RF-NEW-RPT-04:** Los reportes IA se pueden exportar a PDF.
  - Cobertura: `AdminStudentReportPage.test.tsx::print button`.

Validar después con `backend/tests/integration/test_iso25010.py` (guardian existente).

---

## 7. Seguridad y privacidad

- Todos los endpoints exigen `Depends(require_admin)`.
- Sin exposición de hashes de password ni tokens en los responses.
- `chat_messages` ya pertenece al estudiante; el admin tiene acceso por rol (decisión institucional documentada en CLAUDE.md). Solo se expone **conteo y timestamp**, no el contenido textual del chat — privacidad mínima del estudiante.
- PDF generado client-side: nada se sube a terceros (cumple "Stack cerrado, LLM privado").
- Rate limit: los endpoints `*/ai-report` se incluyen en el límite global slowapi 100 req/min/IP (ya configurado).

---

## 8. YAGNI — fuera de alcance

- ✗ Tracking realtime/online (no se construye heartbeat ni WebSocket).
- ✗ Comparativa side-by-side de 2-4 estudiantes con cards apiladas (la comparativa se entrega vía reporte de cohorte IA + ordenamiento de la tabla).
- ✗ Heatmaps de actividad por día/hora.
- ✗ Exportar reporte como Markdown descargable (basta con PDF via print).
- ✗ Notificaciones push de riesgo (admin lo verá al generar reporte; sin email/Slack).
- ✗ Edición/anotación manual del reporte IA por parte del admin (puede regenerarse).

---

## 9. Plan de archivos a crear/modificar

**Crear:**

- `backend/app/routers/admin_reports.py`
- `backend/app/services/student_report_service.py`
- `backend/app/schemas/admin_reports.py`
- `backend/tests/unit/test_student_report_service.py`
- `backend/tests/integration/test_admin_reports.py`
- `frontend/src/api/adminReports.ts`
- `frontend/src/types/adminReports.ts`
- `frontend/src/components/admin/StudentsReportTab.tsx`
- `frontend/src/components/admin/CohortReportModal.tsx`
- `frontend/src/pages/AdminStudentReportPage.tsx`
- `frontend/src/components/__tests__/StudentsReportTab.test.tsx`
- `frontend/src/pages/__tests__/AdminStudentReportPage.test.tsx`

**Modificar:**

- `backend/app/main.py` — registrar `admin_reports.router`.
- `frontend/src/pages/AdminPage.tsx` — añadir tab "Reportes".
- `frontend/src/App.tsx` (o equivalente) — registrar ruta `/admin/students/:userId` con wrapper admin existente.
- `frontend/src/index.css` — bloque `@media print`.
- `docs/matriz-trazabilidad-ISO25010.md` — añadir RF-NEW-RPT-01..04.
- `CLAUDE.md` (sección "Sprint 6") — referenciar este spec.

---

## 10. Criterios de aceptación

- [ ] Admin abre tab "Reportes" y ve tabla con todos los estudiantes (≥1 fila por seed).
- [ ] Tabla ordena por cada columna y filtra por nivel + búsqueda + activos.
- [ ] Click en fila navega a `/admin/students/{id}` y muestra detalle completo.
- [ ] Botón "Generar reporte IA" produce respuesta narrativa con `risk_level` y `interventions`.
- [ ] Segunda llamada al mismo reporte sin cambios devuelve `cached=true` (verificado por test).
- [ ] Cambio en progreso del estudiante invalida cache automáticamente.
- [ ] Botón "Reporte cohorte IA" acepta 2-15 estudiantes y devuelve narrativa comparativa.
- [ ] `window.print()` produce PDF legible con header institucional y sin barras de navegación.
- [ ] Tests nuevos: ≥13 backend + ≥6 frontend, todos pass.
- [ ] Cobertura backend total ≥80%.
- [ ] Matriz ISO actualizada y guardian `test_iso25010.py` pasa.

---

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| LLM lento (>30 s) bloquea UI | Spinner explícito + texto "La IA está analizando…" + cache fuerte 1h |
| LLM produce JSON inválido frecuentemente | Reintento 1× con `temperature=0.1` + parser tolerante + ejemplos en prompt |
| Query de tabla con N estudiantes es lenta | Single-query con JOINs + LIMIT (piloto 10-15 estudiantes → no hay N grande). Si crece: paginación |
| Admin imprime contenido sensible del estudiante | Solo se exponen **conteo** de chats, no transcripción |
| Generación de reporte tras gran cantidad de actividad rompe context (>3500 chars) | Truncado del payload antes del prompt + uso de agregados, no eventos crudos |
| Mantener cache coherente cuando admin cambia nivel manualmente vía Override | Override existente toca `user_levels` → `_detail_hash` no cambia automáticamente. Mitigar: incluir `last_reassessed_at` en el hash (presente en detail) |

---

*Fin del spec.*
