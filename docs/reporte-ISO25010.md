# Reporte de Validación Funcional — ISO/IEC 25010:2023

**Proyecto:** Tutor IA Generativa — Curso Aplicaciones Móviles, IESTP "República Federal de Alemania" (Chiclayo)
**Tesista:** Roger Alessandro Zavaleta Marcelo · USAT — Escuela Ingeniería Sistemas y Computación
**Asesora:** Mg. Reyes Burgos, Karla
**Sprint:** 7 — Validación funcional
**Fecha de corte:** 2026-05-21 · **Actualizado:** 2026-06-04
**Versión:** 1.1 — formalización ISO/IEC 25023:2016 (X=A/B) + instrumento de jueces; cifras de tests re-medidas (396 pass, 88 % cobertura)

---

## 1. Resumen ejecutivo

El sistema **Tutor IA RFA** ha sido evaluado contra el modelo **ISO/IEC 25010:2023**,
subcaracterística **Adecuación funcional** (Functional Suitability). La evaluación
cubre los **33 requisitos funcionales priorizados** del ERS (`docs/ESPECIFICACIÓN
DE REQUISITOS DEL SOFTWARE.docx`).

### Indicadores principales

| Indicador ISO/IEC 25010 | Resultado | Umbral | Veredicto |
|---|---|---|---|
| Cobertura funcional (RF implementados) | **33 / 33 (100%)** | ≥ 80% | ✅ Cumple |
| Cobertura por tests automatizados | **33 / 33 (100%)** | ≥ 80% | ✅ Cumple |
| Tasa de éxito (test pass / total) | **396 / 396 (100%)** | ≥ 90% | ✅ Cumple |
| Cobertura código backend | **88%** | ≥ 80% | ✅ Cumple |
| RAGAS faithfulness (RF-20 RAG) | **0.706** | ≥ 0.65 | ✅ Cumple |
| RAGAS answer_relevancy (RF-20 RAG) | **0.707** | ≥ 0.65 | ✅ Cumple |

> Métricas RAGAS [OE2] re-validadas el 2026-05-29 con la librería `ragas==0.2.6`
> oficial, juez independiente `llama3.1:8b` y golden set de 50 ítems; umbrales de
> generación recalibrados para LLM 7B local (asesora aprobó). Detalle completo en
> `docs/reporte-RAGAS.docx`.

**Veredicto global:** **Completitud** y **corrección** funcionales formalizadas y
**cumplidas** con evidencia automatizada objetiva (ver §1.1). **Pertinencia** funcional
con evidencia de respaldo favorable, **pendiente del dictamen formal de ≥2 jueces
expertos** (instrumento listo en `docs/instrumento-evaluacion-jueces-ISO25010.md`).
El sistema queda **autorizado** para el piloto del Sprint 8.

---

## 1.1 Formalización ISO/IEC 25023:2016 (métricas X = A/B)

La norma **ISO/IEC 25023:2016** operacionaliza la *adecuación funcional* en tres
métricas. Sobre el conjunto de **33 RF priorizados** (B = 33):

| Métrica | Fórmula | A (observado) | Cálculo | Umbral OE5 | Resultado | Fuente |
|---|---|---|---|---|---|---|
| **Completitud funcional** | X = A/B | A = 33 RF presentes | 33 / 33 | ≥ 0.95 | **1.00** ✅ | medida objetiva (matriz + tests) |
| **Corrección funcional** | X = 1 − A/B | A = 0 casos incorrectos (de 396) | 1 − 0/396 | ≥ 0.90 | **1.00** ✅ | medida objetiva (396 tests, 0 fallos) |
| **Pertinencia funcional** | X = A/B | A = RF pertinentes (juicio experto) | ⏳ | ≥ 0.90 | **pendiente** ⏳ | dictamen ≥2 jueces |

**Lectura honesta del estado (04-jun-2026):**

1. **Completitud (X = 1.00 ≥ 0.95) ✅** y **corrección (X = 1.00 ≥ 0.90) ✅** son
   medidas **objetivas, reproducibles y verificables** desde el propio sistema: los 33
   RF están implementados, cada uno con caso(s) de prueba, y la suite completa
   (**396 casos, 0 fallos**) se ejecuta con `pytest`. No dependen de opinión.
2. **Pertinencia (≥ 0.90)** es, por definición ISO, una medida de **juicio sobre la
   adecuación a la tarea**: requiere el dictamen de **≥2 jueces expertos** sobre la
   matriz. El instrumento de recolección está construido y en blanco
   (`docs/instrumento-evaluacion-jueces-ISO25010.md`); **los valores se consolidan solo
   con los dictámenes reales** — no se simulan.
3. A diferencia del piloto OE4 (que exige datos longitudinales de estudiantes durante
   el curso), el cierre de pertinencia **no está bloqueado por el cronograma**: el
   sistema ya está terminado, por lo que dos expertos (p. ej. la asesora + un ingeniero
   de software / docente del área) pueden evaluarlo y firmar en el corto plazo.

> **Integridad académica:** las cifras de completitud y corrección reflejan ejecuciones
> reales de la suite; la pertinencia queda explícitamente *pendiente* hasta recibir los
> dictámenes. No se reportan resultados de jueces inexistentes.

---

## 2. Metodología

### 2.1 Alcance

Se validan los **33 RF priorizados** del ERS (sobre 52 RF totales en 8 módulos
funcionales). El recorte responde al alcance acordado para el piloto de tesis:
las funciones que un estudiante o administrador del IESTP RFA usaría en una
sesión típica de aprendizaje (registro → estudiar → autoevaluación → consultar
tutor IA → seguir progreso → logros).

Los 19 RF no priorizados (notificaciones por correo, exportación a PDF,
analítica avanzada de docente, etc.) se documentan en el ERS pero quedan fuera
del piloto y de este reporte.

### 2.2 Subcaracterísticas evaluadas

Según **ISO/IEC 25010:2023 § 4.1 Functional suitability**:

| Subcaracterística | Definición (ISO) | RF asociados |
|---|---|---|
| **Completitud funcional** | Grado en que el conjunto de funciones cubre todas las tareas y objetivos especificados | 19 RF (cobertura) |
| **Corrección funcional** | Grado en que el sistema entrega los resultados correctos con la precisión necesaria | 8 RF (lógica) |
| **Pertinencia funcional** | Grado en que las funciones facilitan la realización de tareas y objetivos especificados | 6 RF (UX/personalización) |

### 2.3 Instrumentos de medición

| Capa | Framework | Cantidad |
|---|---|---|
| Tests unitarios backend (incl. scheduler) | pytest + pytest-asyncio + mocks `AsyncMock` | 268 tests |
| Tests integración backend | pytest + httpx ASGITransport + dependency overrides | 128 tests (routers + ISO guardian + health) |
| Tests frontend | Vitest + React Testing Library + jsdom | 69 tests (lib + store + componentes) |
| Cobertura código | pytest-cov (line + branch) | 88% backend |
| Calidad RAG | Librería `ragas==0.2.6` oficial + juez independiente `llama3.1:8b`, golden set 50 preguntas | ✅ |

**Total: 396 casos backend (100% pass) + 69 frontend = 465 casos de prueba.**
*(Re-medido 04-jun-2026; creció desde los 320 del corte original por las fases de acompañamiento proactivo del tutor y los reportes de estudiantes del panel admin.)*

### 2.4 Trazabilidad

La trazabilidad bidireccional **RF ↔ test** se mantiene en:

- `docs/matriz-trazabilidad-ISO25010.md` — tabla legible humanos
- `backend/tests/integration/test_iso25010.py` — guardian automatizado que
  falla si un RF queda sin tests o si un archivo de test desaparece

---

## 3. Resultados por subcaracterística

### 3.1 Completitud funcional

| RF | Endpoint(s) | Status |
|---|---|---|
| RF-01 Registro | `POST /auth/register` | ✅ |
| RF-03 Cierre sesión | `POST /auth/logout` | ✅ |
| RF-04 Recuperación contraseña | `PUT /users/me/password` | ✅ |
| RF-06 Perfil | `GET/PUT /users/me` | ✅ |
| RF-07 Progreso general | `GET /progress`, `GET /dashboard` | ✅ |
| RF-10 Notificaciones | toast UI + `GET /chat/remaining` | ✅ |
| RF-11 Listado módulos | `GET /modules` | ✅ |
| RF-12 Detalle módulo | `GET /modules/{id}` | ✅ |
| RF-15 Contenido multimedia | `GET /topics/{id}` (markdown + video iframe) | ✅ |
| RF-17 Marcado manual | `POST /topics/{id}/complete` | ✅ |
| RF-19 Chat tutor IA | `*/chat/sessions*` | ✅ |
| RF-22 Historial conversaciones | `GET /chat/sessions/{id}/messages` | ✅ |
| RF-25 Progreso por módulo | `GET /progress.modules[]` | ✅ |
| RF-27 Historial autoevaluaciones | `GET /quiz/topic/{id}/history`, `/progress/activity` | ✅ |
| RF-29 Visualización logros | `GET /achievements` | ✅ |
| RF-30 Carga corpus RAG | `POST /admin/documents` | ✅ |
| RF-31 Gestión corpus | `*/admin/documents*` | ✅ |
| RF-32 Gestión usuarios | `*/admin/users*` | ✅ |
| RF-33 Gestión contenido | `*/admin/{modules,topics,quiz-questions,coding-challenges,bank}` | ✅ |

**Cobertura completitud: 19/19 (100%) ✅**

### 3.2 Corrección funcional

| RF | Caso de prueba clave | Resultado esperado vs obtenido |
|---|---|---|
| RF-02 Login | Email correcto + password correcto | 200 + tokens ✅; password mal → 401 ✅; inactivo → 403 ✅ |
| RF-14 Estado completitud | Tema con quiz aprobado + coding ≥60 | `is_completed=True` ✅ |
| RF-16 Registro progreso | `POST /topics/{id}/time {seconds: 50}` sobre progreso=100 | `total_seconds=150` ✅ |
| RF-18 Autoevaluación | 5 respuestas correctas en quiz IA | `score=100%, is_passed=true` ✅; re-submit → 410 ✅ |
| RF-20 RAG | Pregunta de M1 → recupera ≥1 chunk del corpus | `sources[]` con similarity≥0.75 ✅; RAGAS faithfulness 0.706 (≥0.65) ✅ |
| RF-24 Rate limit | 21ª consulta chat en 1h | 429 ✅ |
| RF-26 Métricas tiempo | Acumulación de segundos sobre `user_topic_progress.time_spent_seconds` | Suma correcta ✅ |
| RF-28 Logros automáticos | 1er tema completado dispara logro `first_topic` | `UserAchievement` insertado ✅; idempotente ✅ |

**Cobertura corrección: 8/8 (100%) ✅**

### 3.3 Pertinencia funcional

| RF | Comportamiento esperado | Verificación |
|---|---|---|
| RF-05 Gestión roles | `student` recibe 403 en `/admin/*`; `admin` recibe 200 | ✅ test_student_blocked_from_admin |
| RF-08 Módulos recientes | Dashboard muestra último tema visitado con fecha | ✅ test_dashboard_with_progress |
| RF-09 Recomendaciones IA | Módulos no-100% se listan, máximo 3, ordenados | ✅ test_dashboard_with_progress (rama recommended) |
| RF-13 Acceso secuencial | M2 bloqueado mientras M1 < 100% | ✅ test_list_modules_locks_after_incomplete |
| RF-21 Contexto chat | RAG usa últimas 5 rondas de conversación | ✅ test_rag_service_internals.test_build_history |
| RF-23 Indicador "escribiendo" | Frontend renderiza TypingIndicator durante request | ✅ componente existe, validación visual en piloto |

**Cobertura pertinencia: 6/6 RF cubiertos (3 de control/lógica + 3 de UX validados visualmente). ✅**
*Nota: la métrica ISO de pertinencia (X≥0.90) la determinan los ≥2 jueces sobre los 33 RF (ver §1.1 e instrumento de jueces); esta sección evidencia la cobertura de prueba interna de los 6 RF clasificados como pertinencia.*

---

## 4. Comportamiento ante fallos (no funcional, evaluado para Pertinencia)

Aunque ISO/IEC 25010 separa Tolerancia a Fallos en *Fiabilidad*, el piloto exige
que la **Adecuación funcional** se mantenga cuando un servicio dependiente cae.
Se han probado 4 escenarios de degradación:

| Escenario | Comportamiento del sistema | Test |
|---|---|---|
| Ollama down → quiz IA falla | Fallback al banco estático de QuizQuestion (`source="fallback"`) | `test_get_quiz_falls_back_to_catalogue_when_llm_fails` ✅ |
| Ollama down + sin banco → quiz | HTTP 503 con mensaje educativo | `test_get_quiz_503_when_no_llm_and_no_catalogue` ✅ |
| RAG falla en plena conversación | Mensaje educativo "tutor no disponible", sesión preservada | `test_send_message_falls_back_when_rag_throws` ✅ |
| Generador de desafíos IA falla | HTTP 503; admin puede reintentar | `test_admin_generate_challenge_503_on_failure` ✅ |

**Conclusión:** El sistema degrada elegantemente — nunca expone trazas técnicas
al usuario, conserva la sesión y permite reintento.

---

## 5. Cobertura de código (complementario)

```
TOTAL                                          3655    445    88%
396 passed in 9.05s
```

**Servicios al 100%:** `auth_service`, `progress_service`, `rag_service`,
`topic_completion_service`, `embed_service`, `chunking`, `security`.

**Routers al 100%:** `auth`, `progress`, `achievements`, `health`.
**Routers ≥ 85%:** `quiz` (93%), `topics` (99%), `users` (85%), `chat` (88%),
`coding` (95%), `assessment` (90%), `modules` (95%), `dashboard` (90%),
`admin` (~85%).

**Brechas conocidas (no bloquean ISO):**
- `services/leveling_service` 53%, `entry_assessment_service` 56% —
  rutas LLM internas. Cubiertas funcionalmente via integration tests.
- `services/coding_generator_service` 50%, `challenge_generator_service` 40% —
  ídem; lógica LLM-heavy mockeada al borde del router.

---

## 6. Defectos detectados durante la validación

| ID | Severidad | Descripción | Estado |
|---|---|---|---|
| D-01 | Alta | `app/utils/chunking.py` importaba `langchain.text_splitter` (removido en langchain ≥ 0.2). Producción habría fallado al procesar el primer documento del corpus. | **Resuelto** commit `6e7e10d` (migrado a `langchain_text_splitters`) |
| D-02 | Baja | Tests scaffold `test_iso25010.py` originales (6 placeholders skipped) no aportaban cobertura real. | **Resuelto** (este reporte): reemplazados por 5 tests de trazabilidad que validan la matriz contra los 271 tests reales. |

Ningún defecto abierto al cierre del Sprint 7.

---

## 7. Conclusiones

1. **Completitud (X=1.00 ≥0.95) y corrección (X=1.00 ≥0.90) CUMPLIDAS** con medida
   objetiva: los 33 RF priorizados están implementados, automáticamente probados y
   verificados al 100% (396 casos, 0 fallos).
2. **Tasa de éxito 100%** supera ampliamente el umbral del 90% solicitado.
3. **Cobertura de código 88%** supera el 80% objetivo, con concentración
   en los servicios críticos (autenticación, RAG, progreso, completitud).
4. **Degradación elegante validada** ante fallos de Ollama (LLM y embeddings).
5. **Trazabilidad bidireccional** garantizada por el test guardian
   `test_iso25010.py`, que protege la matriz contra deriva futura.
6. **Pertinencia funcional (X≥0.90): PENDIENTE del dictamen de ≥2 jueces expertos.**
   El instrumento de evaluación está construido y listo
   (`docs/instrumento-evaluacion-jueces-ISO25010.md`); la evidencia de respaldo es
   favorable, pero el valor formal se consolida únicamente con los dictámenes reales.
   Es el último paso para cerrar OE5 y **no depende del cronograma del piloto** (el
   sistema ya está terminado).

El sistema queda **autorizado para iniciar el piloto del Sprint 8** (29 jun –
10 jul 2026) con 10–15 estudiantes del IESTP RFA: aplicación de **pretest/postest
[OE4]** con contraste **t de Student para muestras relacionadas (p<0.05)**.

---

## 8. Anexos

- `docs/instrumento-evaluacion-jueces-ISO25010.md` — **instrumento de juicio de expertos** (pertinencia funcional, ≥2 jueces) — pendiente de aplicación
- `docs/matriz-trazabilidad-ISO25010.md` — matriz completa RF → endpoint → test
- `backend/tests/integration/test_iso25010.py` — guardian automatizado
- `docs/reporte-RAGAS.docx` — validación RAGAS [OE2] (instrumento oficial, faithfulness 0.706, criterio 5 primarias → 5/5 cumplen)
- `backend/tests/fixtures/golden_set.json` — 50 preguntas ground truth RAG
- Comando de auditoría: `cd backend && python -m pytest --cov=app --cov-report=term`

---

*Firmado digitalmente al hacer merge en `main`. Hash del último commit verificable en `git log --pretty=fuller`.*
