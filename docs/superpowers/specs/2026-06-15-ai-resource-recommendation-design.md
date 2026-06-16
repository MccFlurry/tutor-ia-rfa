# Diseño — Acompañamiento Proactivo Fase 6: Recomendación IA de recursos sobre el banco curado

**Fecha:** 2026-06-15 · **Rama:** `feat/ai-resource-recommendation` · **Estado:** aprobado por tesista

## 1. Contexto y motivación

El asesor (y el jurado en la defensa preliminar) pidió que el sistema sea un **tutor que acompaña
al estudiante en todo momento, en todos los aspectos**, con retroalimentación y **recomendaciones de
videos/libros «dadas por la IA»** desde el primer módulo.

Estado actual: el banco de recursos curados (`learning_resources`, Fase 3) ya existe y se muestra en
Dashboard (vía companion) y TopicPage, pero el orden es **fijo por `order_index`, igual para todos
los estudiantes**. El companion ya calcula **nivel** (`UserLevel`) y **temas débiles**
(`build_diagnostic`), pero no los usa para priorizar recursos.

Esta fase añade una **capa de IA que reordena y justifica** los recursos curados según el nivel y la
debilidad del estudiante, **sin inventar URLs ni títulos**: el LLM solo elige entre IDs de recursos
que ya existen en el banco. Reconcilia el «todo dado por la IA» con el principio núcleo
*«el tutor no inventa»*.

**Encuadre tesis:** fuera de la matriz ISO 25010 (los 33 RF quedan congelados). Mejora de
acompañamiento documentada, igual que las Fases 1-5. No toca OE1-OE5 ni los tests del guardián ISO.
No modifica el pipeline RAG validado (OE2) ni el banco/admin. Operacionaliza el modelo de
interacción del STI (insumo de OE3/OE5, sin crear OE nuevo).

## 2. Decisiones cerradas

| Decisión | Valor |
|---|---|
| Qué produce la IA | **Ranking + «por qué»** (1 línea por recurso). Sin punteros al corpus, sin plan narrativo. |
| Mecanismo de ranking | **Enfoque A — re-rank constreñido**: el LLM devuelve orden de IDs reales + razón. |
| Garantía anti-invención | El LLM **nunca emite URLs/títulos**: solo permuta IDs del conjunto candidato (validación pura). |
| Superficies | **Dashboard** (nivel módulo) **+ TopicPage** (nivel tema). |
| Integración con companion | Endpoint **nuevo e independiente**; el companion sigue **sin LLM** (preserva testabilidad ISO). |
| Resiliencia | Todo fallo del path IA → **fallback al orden curado determinista** (`ai_ranked=false`). |
| Encuadre OE5 | **Fuera de matriz** — mejora documentada, no RF formal. |

## 3. Arquitectura y flujo

```
GET /api/v1/resources/recommended?module_id= | ?topic_id=
  → resolver candidatos (recursos curados de BD)
  → resolver señal del estudiante (nivel + tema débil)
  → caché Redis  resource_rec:{user_id}:{scope}
       hit  → devolver
       miss → ChatOllama (format=json, temp 0.3) re-rank
              → merge_ranking (función PURA) valida/mergea → cachear → devolver
       LLM/parse falla, <2 candidatos, Ollama caído → fallback determinista (orden curado)
```

Servicio nuevo `services/resource_recommender_service.py`, aislado del companion.

## 4. Backend

### 4.1 `backend/app/services/resource_recommender_service.py`

Mismo patrón que `tutor_service.py`/`companion_service.py`: funciones puras + un `gather` que
resuelve estado desde BD + invoca LLM.

- **`merge_ranking(candidates, llm_ranking) -> list[RankedResource]`** — **función pura**, núcleo
  testeable. `candidates` = recursos curados (orden original). `llm_ranking` = lista
  `[{"id", "reason"}]` parseada del LLM. Reglas:
  - Descarta IDs que **no** estén en `candidates` (anti-invención).
  - Deduplica IDs (conserva la primera aparición).
  - Recorta `reason` a ≤ 120 chars; vacía/nula → `None`.
  - **Anexa** al final cualquier candidato omitido por el LLM, en su `order_index` original, con
    `reason=None`.
  - → la salida es **siempre una permutación de recursos reales** (mismo conjunto, sin pérdidas).
- **`select_candidates(db, module_id, topic_id) -> list[LearningResource]`** — uno de:
  - `module_id`: recursos activos con `module_id == M`.
  - `topic_id`: recursos activos con `topic_id == T` **OR** `module_id == (módulo de T)` (porque el
    seed asigna solo `module_id`; sin esto la tarjeta del tema quedaría vacía).
  - Orden base `order_index, id`. Cap configurable (p. ej. 6 candidatos máx. al LLM).
- **`build_student_signal(user, db, module_id, topic_id) -> StudentSignal`** — nivel
  (`UserLevel.level`, default `beginner` si no hay) + contexto de debilidad:
  - módulo: tema más débil del módulo actual (reutiliza `companion_service.build_diagnostic`).
  - tema: `best_score`/intentos del estudiante en ese tema (banda igual que companion:
    `<60` débil · `[60,80)` afianzar · `≥80` dominado; recordar normalizar `QuizAttempt.score`
    fracción 0-1 → 0-100).
- **`gather_recommendations(user, db, redis, module_id, topic_id) -> RecommendationResponse`** —
  orquesta: caché → candidatos → señal → LLM → `merge_ranking` → cachear. Cualquier excepción del
  path LLM/parse o `<2` candidatos → fallback: candidatos en orden curado, `ai_ranked=false`.

### 4.2 Contrato del LLM

- Cliente `ChatOllama(model=settings.OLLAMA_MODEL, format="json", temperature=0.3)` (mismo patrón que
  `llm_service`).
- **Prompt:** tutor español peruano. Entrada = nivel + contexto de debilidad + lista candidata
  `[{id, kind, title, description}]`. Se le pide **ordenar de más a menos útil para ESTE estudiante**
  y dar una razón breve. **Prohibido** inventar recursos, URLs o títulos; solo puede usar los IDs
  provistos.
- **Salida (wrapper objeto, no array desnudo — regla `format=json` del proyecto):**
  `{"ranking": [{"id": <int>, "reason": "<≤120 chars, ES>"}]}`. Parser robusto (acepta también
  array desnudo por compatibilidad), luego `merge_ranking`.

### 4.3 `backend/app/routers/resources.py`

- `GET /resources/recommended` (auth estudiante). Query: exactamente uno de `module_id` | `topic_id`
  (422 si ambos o ninguno). Llama `gather_recommendations`.
- **Respuesta** (`schemas/learning_resource.py`):
  ```
  RecommendationResponse {
    ai_ranked: bool,
    level: str,
    recommendations: [ LearningResourceResponse + { reason: str | None } ]
  }
  ```

### 4.4 Caché e invalidación

- Key `resource_rec:{user_id}:{scope}` con `scope = m{module_id}` | `t{topic_id}`. TTL 1800s.
- Redis caído → modo degradado vía `app/utils/cache` (sin caché, sigue respondiendo), igual que el
  companion.
- **Invalidación:** los mismos eventos que invalidan el companion (submit de quiz/coding, completar
  tema, re-nivelación) deben invalidar también las keys `resource_rec:{user_id}:*`, porque cambian la
  señal de debilidad/nivel. Se añade junto a `invalidate_companion` (patrón de punto único de
  invalidación). Se borra por patrón/prefijo el namespace `resource_rec:{user_id}:`.

## 5. Frontend

### 5.1 `frontend/src/components/resources/RecommendedResources.tsx` (nuevo)

- Props: `{ moduleId?: number; topicId?: number }`. Hook `useRecommendedResources` (TanStack Query,
  `staleTime` 0, key `['resources-recommended', moduleId, topicId]`).
- Reutiliza `ResourceCard`; añade la línea de `reason` bajo cada tarjeta y un chip
  **«Recomendado por IA · nivel X»** (coherente con el chip de coding IA) cuando `ai_ranked=true`.
- `ai_ranked=false` → oculta el chip y las razones, muestra orden curado sin fricción (resiliente).
- Vacío → no renderiza (igual que `ResourceList`).

### 5.2 Puntos de montaje

- **`DashboardPage.tsx`:** monta `<RecommendedResources moduleId={position.module_id} />` y se
  **retira el sub-bloque de recursos del `CompanionPanel`** (evita duplicado; el companion conserva
  posición + diagnóstico, sigue determinista). El backend del companion puede seguir devolviendo
  `resources` (sin cambio), pero el Dashboard ya no los renderiza.
- **`TopicPage.tsx:312`:** reemplaza `<ResourceList topicId={topicId} />` por
  `<RecommendedResources topicId={topicId} />`.

### 5.3 API/tipos

- `frontend/src/api/resources.ts`: `recommended({ moduleId?, topicId? })`.
- `frontend/src/types/resource.ts`: `RecommendedResource` (= `LearningResource` + `reason: string|null`)
  y `RecommendationResponse`.

## 6. Pruebas

- **Unit puras (backend):** `merge_ranking` — descarta IDs inventados, anexa faltantes en orden
  curado, deduplica, recorta `reason`; `select_candidates` por `module_id` y por `topic_id`
  (incluye recursos del módulo del tema); `build_student_signal` bandas + normalización de score.
- **Unit fallback:** salida LLM vacía/inválida → orden determinista, `ai_ranked=false`.
- **Integration:** endpoint con Ollama mockeado (`ai_ranked=true`, orden permutado, razones) y con
  Ollama caído (`ai_ranked=false`, orden curado); 422 si `module_id` y `topic_id` juntos/ausentes.
- **Frontend:** `RecommendedResources` renderiza razones + chip cuando `ai_ranked`; oculta chip y
  razones en fallback; no renderiza si vacío.

## 7. Fuera de alcance (YAGNI)

Sin punteros al corpus/RAG, sin plan de estudio narrativo, sin generación de recursos, sin tocar el
CRUD admin ni el banco, sin tocar el pipeline RAG ni la matriz ISO (33 RF congelados). El companion
no recibe LLM.

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| LLM inventa un recurso/URL | Imposible por construcción: `merge_ranking` solo acepta IDs del conjunto candidato. |
| Latencia LLM en Dashboard/Topic | Caché Redis 1800s + fallback inmediato; endpoint separado del path crítico del companion. |
| Calendario (sustentación 10/07) | Superficie acotada, reutiliza `ResourceCard`/patrones existentes; no toca OE ni ISO. |
| Duplicación de recursos en Dashboard | Se retira el bloque de recursos del `CompanionPanel`. |
| `QuizAttempt.score` escala 0-1 vs bandas 0-100 | Normalizar ×100 antes de bandear (trampa ya documentada en el proyecto). |
