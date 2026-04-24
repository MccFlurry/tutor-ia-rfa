# CLAUDE.md — Tutor con IA Generativa para Aplicaciones Móviles

> **Guía de construcción y contexto para Claude Code en el desarrollo del proyecto de tesis.**
>
> **Versión:** v4.0
> **Última actualización:** 23 de abril de 2026
> **Autor (tesista):** Roger Alessandro Zavaleta Marcelo — USAT, Escuela de Ingeniería de Sistemas y Computación
> **Asesora de tesis (USAT):** Mg. Reyes Burgos, Karla
> **Coordinador del piloto (IESTP "RFA"):** Téc. Xavier Benites Marín — coordina el acceso al piloto y la pertinencia pedagógica del contenido; NO es asesor de tesis
> **Inicio del desarrollo:** 23 de marzo de 2026 · **Fin y sustentación final:** 10 de julio de 2026

---

## 0. Propósito de este archivo

Este documento es la fuente única de verdad para que Claude Code continúe el desarrollo del sistema sin necesidad de re-explicar el contexto en cada sesión. Al iniciar cualquier trabajo, Claude Code debe:

1. Leer completamente este archivo.
2. Consultar la sección del sprint activo en el cronograma (§ 3).
3. Antes de tocar código de producción, proponer un plan breve al usuario.
4. Mantener actualizado el estado del sistema (§ 9) después de cada tarea significativa.

---

## 1. Resumen del proyecto

Sistema web para tutoría inteligente de la asignatura **Aplicaciones Móviles** del IESTP "RFA" en Chiclayo. Combina:

- Módulos didácticos interactivos
- Tutor IA privado basado en RAG (LLM auto-hospedado)
- Quizzes de autoevaluación
- Seguimiento de progreso y modelo del estudiante
- Gamificación (logros y badges)

**Restricción central:** el LLM debe ser privado y auto-hospedado (Ollama), sin APIs pagas.

**Población piloto:** 10–15 estudiantes del IESTP "RFA".
**Presupuesto:** S/. 3,170.00.

---

## 2. Objetivos específicos (5 OE)

| OE  | Enunciado                                                                                                                                                                                                                                          |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OE1 | Establecer los modelos del sistema de tutoría inteligente (dominio, pedagógico, estudiante e interacción) a partir del sílabo oficial y del análisis del contexto educativo del IESTP "RFA".                                                       |
| OE2 | Seleccionar los modelos de lenguaje grande y de embeddings, y construir el pipeline RAG, validando su rendimiento con el framework RAGAS.                                                                                                          |
| OE3 | Desarrollar e integrar el sistema tutor con IA generativa sobre infraestructura de contenedores en Google Compute Engine.                                                                                                                          |
| OE4 | Estructurar el contenido instruccional, los ejercicios de práctica guiada y los mecanismos de retroalimentación adaptativa del tutor para apoyar el desarrollo de la capacidad "Analizar herramientas y requisitos para el desarrollo de aplicaciones móviles" del sílabo. |
| OE5 | Validar la adecuación funcional del tutor con IA generativa conforme a la norma ISO/IEC 25010:2023.                                                                                                                                                |

**Resultados esperados por OE:**
- **OE1:** R1.1 dominio · R1.2 pedagógico · R1.3 estudiante · R1.4 interacción.
- **OE2:** R2.1 selección justificada LLM/embeddings · R2.2 pipeline RAG operativo · R2.3 validación RAGAS (faithfulness ≥ 0.75; answer relevance ≥ 0.70).
- **OE3:** R3.1 sistema desplegado (≥ 80% de 33 RF priorizados) · R3.2 documentación técnica completa.
- **OE4:** R4.1 ≥ 3 módulos didácticos con ≥ 15 lecciones · R4.2 ≥ 30 ejercicios con retroalimentación adaptativa por nivel.
- **OE5:** R5.1 reporte ISO/IEC 25010:2023 (cobertura ≥ 80% RF; éxito ≥ 90%) + SUS ≥ 68 con 10–15 estudiantes piloto.

---

## 3. Cronograma — 8 sprints de 2 semanas

| Sprint | Período                   | CRISP-DM aplica          | Estado          |
| ------ | ------------------------- | ------------------------ | --------------- |
| 1      | 23 mar – 05 abr 2026      | —                        | ✅ Completado    |
| 2      | 06 abr – 19 abr 2026      | BU + DU                  | ✅ Completado    |
| 3      | 20 abr – 03 may 2026      | DP + Modeling            | 🔄 En curso      |
| 4      | 04 may – 17 may 2026      | Evaluation               | ⏳ Planificado   |
| 5      | 18 may – 31 may 2026      | Deployment               | ⏳ Planificado   |
| 6      | 01 jun – 14 jun 2026      | —                        | ⏳ Planificado   |
| 7      | 15 jun – 28 jun 2026      | —                        | ⏳ Planificado   |
| 8      | 29 jun – 10 jul 2026      | —                        | ⏳ Planificado   |

**Hito intermedio:** 24/04/2026 (durante Sprint 3) → presentación del Pre Informe.
**Sustentación final:** 10/07/2026.

> **Metodología:** SCRUM global; CRISP-DM solo en los sprints del pipeline LLM/RAG (2, 3, 4 y 5).

---

## 4. Stack tecnológico (decisiones cerradas — NO cambiar sin justificación cuantitativa)

### Frontend
- **Framework:** React 18 (SPA) + TypeScript estricto
- **UI:** shadcn/ui + Tailwind CSS
- **Bundler:** Vite
- **Hosting:** Firebase Hosting (NO Cloud Run, NO Cloud Storage directo)

### Backend
- **Lenguaje:** Python 3.11 + FastAPI
- **Tareas asíncronas:** FastAPI BackgroundTasks (NO Pub/Sub)
- **Programación de tareas:** APScheduler (NO Cloud Scheduler)
- **Rate limiting:** slowapi
- **Logging:** loguru (formato JSON estructurado)
- **Autenticación:** JWT (PyJWT + passlib[bcrypt])
- **ORM:** SQLAlchemy 2.x (async) + Alembic

### IA: LLM + Embeddings + RAG
- **Servidor LLM:** Ollama (auto-hospedado)
- **Modelo LLM:** `qwen2.5:7b-instruct-q4_K_M`
- **Modelo de embeddings:** `mxbai-embed-large` (1,024 dimensiones)
- **Chunking:** semántico con solapamiento del 15%
- **Retrieval:** similitud coseno, top-k=5, umbral=0.65
- **Framework de evaluación:** RAGAS

### Base de datos y caché
- **Relacional + vectorial:** PostgreSQL 16 + pgvector (auto-hospedado, NO Cloud SQL)
- **Caché:** Redis 7 (auto-hospedado, NO Memorystore)
- **Corpus:** filesystem de la VM bajo `/data/corpus/`

### Infraestructura
- **Hosting:** 1 VM de Google Compute Engine (e2-standard-4, 16 GB RAM)
- **Orquestación:** Docker Compose
- **TLS:** Caddy + Let's Encrypt

### Métricas y validación
- **RAG:** RAGAS (faithfulness ≥ 0.75; answer relevance ≥ 0.70)
- **Calidad funcional:** ISO/IEC 25010:2023 (completitud, corrección y pertinencia)
- **Usabilidad:** SUS ≥ 68

---

## 5. Estructura del repositorio

```
tutor-ia-generativa/
├── docker-compose.yml
├── .env.example
├── README.md
├── CLAUDE.md                          ← este archivo
├── docs/
│   ├── ERS.docx
│   ├── arquitectura.docx
│   ├── modelos-STI/
│   │   ├── modelo-dominio.docx
│   │   ├── modelo-pedagogico.docx
│   │   ├── modelo-estudiante.docx
│   │   └── modelo-interaccion.docx
│   ├── reporte-LLM.docx
│   ├── reporte-RAGAS.docx
│   ├── reporte-ISO25010.docx
│   ├── reporte-SUS.docx
│   ├── reporte-validacion-final.docx
│   └── matriz-trazabilidad-ISO25010.docx
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/                     # SQLAlchemy models
│   │   ├── schemas/                    # Pydantic schemas
│   │   ├── api/v1/                     # Routers: auth, modules, lessons, exercises, tutor, progress
│   │   ├── core/                       # security, rate_limit, logging, cache
│   │   ├── rag/                        # ingestor, retriever, generator, orchestrator, ragas_eval
│   │   ├── scheduler/                  # APScheduler tasks
│   │   └── seed/                       # seed_modules, seed_lessons, seed_exercises
│   ├── notebooks/
│   │   ├── ragas_validation.ipynb     # Sprint 4
│   │   └── sus_analysis.ipynb         # Sprint 8
│   └── tests/
│       ├── fixtures/golden_set.json
│       ├── unit/
│       └── integration/
│           └── test_iso25010.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── src/
│       ├── pages/                      # Login, Dashboard, Modules, Lesson, Exercise, Progress
│       ├── components/{ui, tutor, progress}/
│       ├── hooks/
│       ├── services/api.ts
│       └── types/
├── ollama/
│   └── modelfile-qwen2.5
├── corpus/
│   ├── modulo-1-fundamentos/
│   ├── modulo-2-logica-poo/
│   ├── modulo-3-interfaces/
│   └── silabo-2025-I.md
├── infra/
│   ├── caddy/Caddyfile
│   └── scripts/{provision-vm.sh, deploy.sh, backup-postgres.sh}
├── benchmarks/
│   ├── README.md                      ← este archivo
│   ├── CLAUDE_CODE_PROMPT.md          ← prompt final para Claude Code
│   ├── prompts_llm.json               ← 50 prompts en español (M1-M3 + off-topic)
│   ├── run_llm_benchmark.py           ← benchmark LLM (paso 2)
│   ├── score_responses.py             ← calificación interactiva (paso 3)
│   ├── export_corpus.py               ← exporta corpus desde pgvector (paso 4)
│   ├── golden_set_embeddings.json     ← 20 queries con keywords esperadas
│   ├── run_embeddings_benchmark.py    ← benchmark embeddings (paso 5)
│   └── results/
│       ├── llm_benchmark.json         ← salida del paso 2
│       ├── llm_scores.json            ← salida del paso 3
│       ├── corpus_chunks.json         ← salida del paso 4
│       └── embeddings_benchmark.json  ← salida del paso 5
```

---

## 6. Esquema de base de datos

```sql
-- Usuarios y autenticación
users (id, email, hashed_password, full_name, role, created_at, last_login)
user_profiles (user_id PK FK, level, preferences JSONB, current_module_id)

-- Estructura del curso
modules (id, code, title, description, order_index, syllabus_section)
lessons (id, module_id FK, title, content_md, order_index, estimated_minutes)
exercises (id, lesson_id FK, statement_md, difficulty, expected_solution, hints JSONB, test_cases JSONB)

-- Modelo del estudiante
progress (id, user_id FK, lesson_id FK, status, score, attempts, completed_at)
evaluations (id, user_id FK, lesson_id FK, score, answers JSONB, evaluated_at)
achievements (id, code, name, description, icon, criteria JSONB)
user_achievements (user_id FK, achievement_id FK, unlocked_at)

-- Tutor IA (RAG)
chat_sessions (id, user_id FK, started_at, context JSONB)
chat_messages (id, session_id FK, role, content, sources JSONB, created_at)

-- Corpus indexado (vectorial)
corpus_documents (id, source_path, module_id FK, ingested_at, chunk_count)
corpus_chunks (id, document_id FK, content TEXT, embedding vector(1024), metadata JSONB)
-- Índice: CREATE INDEX ON corpus_chunks USING ivfflat (embedding vector_cosine_ops);
```

---

## 7. Endpoints principales del API

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login              # → JWT
GET    /api/v1/auth/me

GET    /api/v1/modules
GET    /api/v1/modules/{id}/lessons
GET    /api/v1/lessons/{id}
POST   /api/v1/lessons/{id}/complete

GET    /api/v1/exercises/{id}
POST   /api/v1/exercises/{id}/attempt   # retroalimentación adaptativa por nivel

POST   /api/v1/tutor/sessions
POST   /api/v1/tutor/sessions/{id}/messages   # consulta RAG
GET    /api/v1/tutor/sessions/{id}/messages

GET    /api/v1/progress/me
GET    /api/v1/achievements
GET    /api/v1/achievements/me
```

---

## 8. Pipeline RAG — flujo de referencia

```
[Usuario pregunta]
      ↓
[POST /tutor/sessions/{id}/messages]
      ↓
[orchestrator.py]
  ├─→ retriever.py:
  │     embedding(pregunta) con mxbai-embed-large
  │     búsqueda pgvector (top-k=5, coseno, umbral=0.65)
  │
  ├─→ Construcción del prompt aumentado:
  │     system prompt pedagógico + contexto + historial + pregunta
  │
  └─→ generator.py:
        llamada async a Ollama (qwen2.5:7b-instruct-q4_K_M)
        respuesta con citas trazables
      ↓
[Persistir en chat_messages (con sources JSONB)]
      ↓
[Cache Redis: hash(pregunta + chunks), TTL=1h]
      ↓
[Frontend: respuesta + SourceCitation]
```

---

## 9. Estado actual del sistema

### Ya implementado (Sprints 1-3 parciales)
- ✅ ERS con 52 RF (33 priorizados)
- ✅ 4 modelos del STI documentados (dominio, pedagógico, estudiante, interacción)
- ✅ Arquitectura microservicios con docker-compose.yml
- ✅ Evaluación comparativa de modelos LLM y embeddings (decisión: qwen2.5:7b + mxbai-embed-large)
- ✅ Pipeline RAG operativo con corpus Módulos 1-3 indexado en pgvector
- ✅ Backend FastAPI con auth JWT, rate limiting, logging, >15 endpoints REST
- ✅ Frontend React con 5 páginas: Login, Dashboard, Modules, Lesson, Progress
- ✅ Sistema funcional end-to-end en entorno de desarrollo

### Trabajo restante por sprint

**Sprint 4 (04-17 may) — Validación RAGAS**
- Construir golden set de 30 preguntas con ground truth
- Ejecutar notebook RAGAS (faithfulness, answer_relevance, context_precision, context_recall)
- Iteraciones de ajuste si métricas < umbral
- Redactar reporte RAGAS

**Sprint 5 (18-31 may) — Despliegue productivo**
- Integrar Redis como caché sobre endpoints frecuentes
- Configurar APScheduler (reindexación + limpieza de sesiones)
- Provisionar VM e2-standard-4 en GCP Compute Engine
- Desplegar con Docker Compose, HTTPS (Caddy + Let's Encrypt)
- Migrar frontend a Firebase Hosting
- Backup diario de PostgreSQL
- Carga inicial de 15 lecciones

**Sprint 6 (01-14 jun) — Contenido + Banco de ejercicios**
- Completar 15 lecciones interactivas (5 por módulo)
- Construir 30 ejercicios (10 por módulo, 3 niveles de dificultad)
- Motor de retroalimentación adaptativa
- Editor Monaco en frontend

**Sprint 7 (15-28 jun) — Validación ISO/IEC 25010**
- Matriz de trazabilidad RF → casos de prueba
- Suite pytest de integración (cobertura ≥ 80%)
- Reporte de validación funcional

**Sprint 8 (29 jun-10 jul) — Pilotaje SUS y cierre**
- Sesiones guiadas con 10-15 estudiantes
- Aplicación del SUS
- Consolidación de reportes
- Informe Final + sustentación

---

## 10. Documentación que Claude Code debe generar

Cada entregable de documentación debe producirse como archivo **.docx** en la ruta indicada. El formato debe incluir: portada con datos del proyecto (título, autor, asesora Mg. Reyes Burgos, institución USAT, fecha), índice automático con numeración, secciones y subsecciones numeradas, tipografía Times New Roman 11-12, interlineado 1.5, y tablas/figuras con leyenda numerada.

| # | Archivo a generar                               | Sprint responsable | Descripción resumida                                                                   |
| - | ----------------------------------------------- | ------------------ | -------------------------------------------------------------------------------------- |
| 1 | `docs/ERS.docx`                                 | S1 (ya hecho)      | 52 RF agrupados en 8 módulos; 33 priorizados alineados con ISO/IEC 25010               |
| 2 | `docs/modelos-STI/modelo-dominio.docx`          | S1                 | Jerarquía módulo → tema → subtema con relaciones de prerrequisito                      |
| 3 | `docs/modelos-STI/modelo-pedagogico.docx`       | S1                 | Estrategias de tutoría y criterios de adaptación por nivel                             |
| 4 | `docs/modelos-STI/modelo-estudiante.docx`       | S2                 | 5 atributos + diagrama ER + mecanismo de actualización                                 |
| 5 | `docs/modelos-STI/modelo-interaccion.docx`      | S2                 | 4 modos de uso con diagramas UML de secuencia                                          |
| 6 | `docs/reporte-LLM.docx`                         | S2                 | Evaluación comparativa de 3 LLM + 2 embeddings; justificación de la selección          |
| 7 | `docs/arquitectura.docx`                        | S3                 | Diagramas C4 (contexto, contenedores, componentes); justificación del stack            |
| 8 | `docs/reporte-RAGAS.docx`                       | S4                 | Golden set, métricas RAGAS, análisis de casos límite, iteraciones                      |
| 9 | `docs/matriz-trazabilidad-ISO25010.docx`        | S7                 | 33 RF × casos de prueba; subcaracterísticas cubiertas                                  |
| 10| `docs/reporte-ISO25010.docx`                    | S7                 | Cobertura, tasa de éxito, defectos encontrados, plan de remediación                    |
| 11| `docs/reporte-SUS.docx`                         | S8                 | Score individual y promedio, desviación estándar, percentil, análisis cualitativo      |
| 12| `docs/reporte-validacion-final.docx`            | S8                 | Consolidación de ISO/IEC 25010 + SUS para la Discusión del Informe Final               |

**Regla para generar cualquier .docx de la tabla:**
Cuando el usuario solicite generar uno de estos documentos, se debe producir el archivo `.docx` completo (no `.md`), con estructura formal, portada, índice, secciones numeradas, tablas y figuras donde corresponda, y guardarlo en la ruta indicada. El contenido debe cumplir los criterios del sprint asociado y referenciar los hallazgos técnicos reales del proyecto registrados en este CLAUDE.md.

---

## 11. Reglas de desarrollo para Claude Code

### Principios
- **No fine-tuning:** "entrenar el modelo" significa configurar el pipeline RAG, NO modificar pesos.
- **Privacidad del LLM:** todas las consultas pasan por la VM propia. **Prohibido** usar APIs pagas.
- **Consistencia con el stack:** no introducir Pub/Sub, Cloud SQL, Memorystore, Cloud Scheduler ni Cloud Run.
- **Idioma:** código en inglés (variables, funciones, comentarios técnicos); documentación y mensajes al usuario en español.
- **Verificación externa:** antes de citar precios, versiones o comandos de Ollama, advertir al usuario que verifique la fuente oficial.

### Convenciones de código
- **Backend:** PEP 8, type hints obligatorios, `async/await` donde aplique, tests con `pytest`, formateo con `ruff`.
- **Frontend:** TypeScript estricto, componentes funcionales con hooks, ESLint + Prettier.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

### Flujo de trabajo
1. Leer la sección del sprint activo en §3 y §9.
2. Crear rama `feat/sprint-{n}-{descripcion}` o `docs/sprint-{n}-{documento}`.
3. Implementar con tests.
4. Verificar que no se afecte el hito final del 10 de julio.
5. Actualizar §9 del CLAUDE.md con el progreso en el mismo PR.

### Protocolo de escalamiento
Detener y consultar al usuario si:
- Una métrica objetivo no se alcanza tras 3 iteraciones.
- Se percibe necesario cambiar el stack técnico.
- Alguna librería requiere licencia comercial.
- El cronograma empieza a desviarse > 1 semana.

---

## 12. Referencias internas

- `docs/ERS.docx` — Especificación de Requisitos del Software
- `docs/modelos-STI/` — Los cuatro modelos del STI
- `docs/reporte-LLM.docx` — Reporte comparativo de modelos
- `corpus/silabo-2025-I.md` — Sílabo oficial del IESTP "RFA"
- Cronograma: archivo Excel `1_03_Cronograma_de_actividades_Zavaleta.xlsx` (hoja Gantt + hojas por sprint)

---

**Final del CLAUDE.md v4.0 — actualizar al cierre de cada sprint o cuando cambien decisiones de arquitectura.**
