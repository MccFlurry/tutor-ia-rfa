# CLAUDE.md — Tutor con IA Generativa para Aplicaciones Móviles (IESTP "RFA")

> **Versión:** v3.2 (alineada con matriz V.2.1 — OE4 preexperimental)
> **Fecha:** 28 de abril de 2026
> **Tesista:** Roger Alessandro Zavaleta Marcelo (USAT)
> **Asesora:** Mg. Karla Reyes Burgos (USAT)
> **Coordinador del piloto:** Téc. Xavier Benites Marín (IESTP "RFA")

---

## 0. Cómo usar este documento

Este archivo es la guía de construcción para Claude Code. Define el qué, el cómo y el alcance del sistema. **Antes de empezar cualquier tarea de código, lee este documento completo y confirma que has entendido el alcance, las restricciones y la arquitectura objetivo.**

Restricciones críticas (NO violar):
- El LLM debe ser privado, auto-hospedado vía Ollama. No usar APIs pagas (OpenAI/Anthropic/Gemini).
- "Entrenar el modelo" en este proyecto significa **construir el pipeline RAG**, no fine-tuning.
- No proponer cambios al stack ya cerrado (sección 4) sin justificación cuantitativa fuerte.
- Toda respuesta del tutor debe traer trazabilidad explícita de fuentes (id_modulo / id_tema / id_subtema).
- Cierre del desarrollo: **10 de julio de 2026**. Sustentación: **17 de julio de 2026**.

---

## 1. Contexto y problema

Tutor con IA generativa para apoyar el aprendizaje en la asignatura **Aplicaciones Móviles** del IESTP "República Federal de Alemania" (RFA), Chiclayo. Población piloto: 10–15 estudiantes voluntarios. Curso de 16 semanas, 5 módulos. El piloto se delimita a los Módulos 1–3 (Capacidad 1 del sílabo).

Problema: bajo rendimiento académico debido a base lógico-matemática débil, falta de tutoría personalizada, procrastinación y ansiedad computacional.

---

## 2. Objetivos específicos (matriz V.2.1)

- **OE-1.** Establecer los modelos del sistema de tutoría inteligente (dominio, pedagógico, estudiante e interacción) a partir del sílabo oficial y del análisis del contexto educativo del IESTP "RFA".
- **OE-2.** Seleccionar el modelo de lenguaje grande y el modelo de embeddings adecuados para la generación de respuestas en español sobre el dominio de aplicaciones móviles.
- **OE-3.** Integrar el LLM seleccionado con el motor de conocimientos RAG en el sistema tutor con IA generativa desplegado sobre contenedores en Google Compute Engine, asegurando la trazabilidad de las respuestas al corpus instruccional asociado a la Capacidad 1.
- **OE-4.** Validar la mejora del rendimiento académico de los estudiantes en la Capacidad 1 mediante un diseño preexperimental con prueba de entrada y prueba de salida aplicado al grupo piloto.
- **OE-5.** Validar la adecuación funcional del tutor conforme a la norma ISO/IEC 25010:2023 y aplicar el cuestionario SUS al grupo piloto.

### Resultados e indicadores objetivamente verificables

| OE | Resultado | Indicador / umbral |
|---|---|---|
| OE-1 | R1.1: Cuatro modelos del STI documentados | Documentos en `docs/modelos-STI/` con cobertura del 100 % del sílabo |
| OE-2 | R2.1: Reporte comparativo LLM y embeddings | `docs/reporte-LLM.docx` con justificación cuantitativa |
| OE-2 | R2.2: Validación RAGAS del pipeline RAG | faithfulness ≥ 0.75; answer_relevancy ≥ 0.70 |
| OE-3 | R3.1: Despliegue productivo en GCP | uptime ≥ 95 % durante el piloto |
| OE-3 | R3.2: Integración LLM ↔ RAG con trazabilidad | ≥ 90 % de respuestas con cita; latencia P95 ≤ 8 s |
| OE-3 | R3.3: Documentación técnica | C4 niveles 1–3 + README desplegable; trazabilidad ≥ 80 % de los 33 RF |
| OE-4 | R4.1: Instrumento pretest/postest | V de Aiken ≥ 0.80 por ítem, ≥ 3 jueces expertos |
| OE-4 | R4.2: Aplicación del pretest y postest | ≥ 10 estudiantes pareados |
| OE-4 | R4.3: Análisis estadístico Wilcoxon | p < 0.05; r ≥ 0.5 o Cohen d ≥ 0.5 |
| OE-5 | R5.1: Plan de pruebas ISO/IEC 25010:2023 | cobertura ≥ 80 % de los 33 RF priorizados |
| OE-5 | R5.2: Reporte de ejecución de pruebas funcionales | tasa de éxito ≥ 90 % en pytest |
| OE-5 | R5.3: Resultado SUS del grupo piloto | SUS ≥ 68; ≥ 10 estudiantes |

---

## 3. Cronograma (12 sprints en 6 iteraciones CRISP-DM)

| Iter | Sprint | Fechas | Foco | Estado |
|---|---|---|---|---|
| 1 — Comprensión del negocio | 1 | 23–29 mar | ERS + arquitectura C4 + 2 modelos STI iniciales | ✅ |
| 2 — Comprensión de los datos | 2 | 30 mar – 05 abr | 4 modelos STI completos + selección LLM/embeddings | ✅ |
| 3 — Preparación + modelado | 3 | 06–12 abr | Pipeline RAG (chunking, embeddings, pgvector) | ✅ |
| 3 | 4 | 13–17 abr | Backend FastAPI + JWT + 25+ endpoints | ✅ |
| 3 | 5 | 18–22 abr | Frontend React SPA + integración E2E | ✅ |
| 3 | 6 | 23–24 abr | Validación preliminar RAGAS | ✅ |
| 4 — Evaluación | 7 | 27 abr – 08 may | Validación formal RAGAS sobre 30 preguntas | ⏳ |
| 5 — Despliegue | 8 | 11–24 may | Redis + APScheduler + provisión VM | ⏳ |
| 5 | 9 | 25 may – 07 jun | Docker Compose + Caddy TLS + Firebase | ⏳ |
| 5 | 10 | 08–21 jun | 15 lecciones + 30 ejercicios + **instrumento pretest/postest validado por V de Aiken** | ⏳ |
| 6 — Validación con usuarios | 11 | 22 jun – 05 jul | **Pretest aplicado** + ISO/IEC 25010 + inicio piloto | ⏳ |
| 6 | 12 | 06–10 jul | **Postest + Wilcoxon + Cohen d + SUS + Informe Final** | ⏳ |

AVANCE 100 %: 10 jul. Sustentación: 17 jul.

---

## 4. Stack tecnológico (cerrado — NO cambiar)

### Frontend
- **React 18** (SPA) + **TypeScript estricto** + **shadcn/ui** + **Tailwind CSS** + **Vite**
- Editor de código: `@monaco-editor/react` (Kotlin/Java)
- Hospedaje: **Firebase Hosting** (free tier)

### Backend
- **Python 3.11** + **FastAPI**
- ORM: **SQLAlchemy 2.x async** + **Alembic**
- Autenticación: **JWT (PyJWT)** + **passlib[bcrypt]**
- Tareas asíncronas: **FastAPI BackgroundTasks** (NO Pub/Sub)
- Programación: **APScheduler** (NO Cloud Scheduler)
- Rate limiting: **slowapi**
- Logging: **loguru** con formato JSON estructurado
- Validación: **Pydantic v2**

### LLM privado y embeddings
- **Ollama** servido en GCP Compute Engine vía Docker Compose
- LLM: `qwen2.5:7b-instruct-q4_K_M` (mejor soporte en español)
- Embeddings: `mxbai-embed-large` (1024 dim)
- Orquestación RAG: **LangChain**

### Base de datos y caché
- **PostgreSQL 16** + **pgvector** (auto-hospedado en la misma VM, NO Cloud SQL)
- **Redis 7** auto-hospedado (NO Memorystore)
- Almacenamiento de documentos: filesystem en `/data/corpus/` (NO Cloud Storage)

### Infraestructura
- 1 VM en GCP Compute Engine: **e2-standard-4** (16 GB RAM, 50 GB SSD)
- Orquestación: **Docker Compose**
- Reverse proxy + TLS: **Caddy** + **Let's Encrypt**

### Evaluación
- Pipeline RAG: framework **RAGAS** (faithfulness, answer_relevancy, context_recall)
- Sistema: **ISO/IEC 25010:2023** (Adecuación Funcional) + **SUS**
- Rendimiento académico: **scipy.stats.wilcoxon** + tamaño del efecto (Cohen d)

---

## 5. Arquitectura (C4 nivel 2 — contenedores)

```
┌──────────────────────────────────────────────────────────────────┐
│  Internet                                                         │
└─────────────────────────────────┬────────────────────────────────┘
                                  │ HTTPS
                ┌─────────────────┴───────────────────┐
                │                                     │
        ┌───────▼────────┐                ┌──────────▼──────────┐
        │ Firebase       │                │ GCP VM e2-standard-4│
        │ Hosting        │                │ (us-central1)       │
        │ (frontend SPA) │                │                     │
        └────────────────┘                │  ┌────────────────┐ │
                                          │  │ Caddy (TLS)    │ │
                                          │  └───────┬────────┘ │
                                          │          │          │
                                          │  ┌───────▼────────┐ │
                                          │  │ FastAPI backend│ │
                                          │  └───┬───┬────┬───┘ │
                                          │      │   │    │     │
                                          │   ┌──▼─┐ │ ┌──▼──┐  │
                                          │   │PG +│ │ │Redis│  │
                                          │   │vec │ │ └─────┘  │
                                          │   └────┘ │          │
                                          │       ┌──▼──────┐   │
                                          │       │ Ollama  │   │
                                          │       │ (LLM)   │   │
                                          │       └─────────┘   │
                                          │  /data/corpus/      │
                                          │  /data/backups/     │
                                          └─────────────────────┘
```

Componentes desplegados con `docker compose up -d` desde la VM. Backups diarios con `pg_dump` hacia `/data/backups/`.

---

## 6. Esquema de base de datos (PostgreSQL 16 + pgvector)

### Tablas principales

```sql
-- Identidad y autenticación
users(id, email UNIQUE, password_hash, full_name, role, created_at)
user_levels(user_id, level, history JSONB, updated_at)
user_achievements(user_id, achievement_id, unlocked_at)
achievements(id, name, description, criteria JSONB)

-- Modelo del dominio (sílabo)
modules(id, num, title, description, scope_pilot BOOLEAN)
topics(id, module_id, code, title, description, indicador_logro CHAR(1))
subtopics(id, topic_id, code, title, content_md TEXT, prerequisites TEXT[])

-- Lecciones, ejercicios, quizzes
lessons(id, subtopic_id, title, content_md TEXT, order_index, scope_pilot BOOLEAN)
exercises(id, subtopic_id, statement_md TEXT, difficulty, expected_solution TEXT,
          hints JSONB, test_cases JSONB)
exercise_attempts(id, user_id, exercise_id, code TEXT, score, feedback TEXT,
                  attempt_no, submitted_at)
quizzes(id, topic_id, questions JSONB, generated_by, created_at)
quiz_attempts(id, user_id, quiz_id, answers JSONB, score, completed_at)

-- Progreso
user_topic_progress(user_id, topic_id, percent, last_activity_at,
                    first_visited_at, completed_at)

-- Tutor RAG
chat_sessions(id, user_id, title, created_at, last_msg_at)
chat_messages(id, session_id, role, content TEXT, sources JSONB, created_at)
document_chunks(id, source_path, id_modulo, id_tema, id_subtema,
                content TEXT, embedding VECTOR(1024), metadata JSONB)
-- Índice IVFFlat sobre embedding con vector_cosine_ops, lists=100

-- Validación preexperimental (R4.1, R4.2, R4.3)
assessment_instrument(id, version, type ENUM('pretest','postest'),
                      items JSONB, total_points INT, validated_by_aiken BOOLEAN)
assessment_responses(id, instrument_id, user_id, answers JSONB, score NUMERIC(4,2),
                     applied_at)
```

### Migración

```bash
alembic upgrade head
# Migraciones críticas:
# 001_initial.py             — esquema base
# 002_pgvector.py            — extensión + índice IVFFlat (lists=100)
# 003_personalization.py     — user_levels, achievements, progress
# 004_assessment.py          — assessment_instrument + responses (Sprint 10)
```

---

## 7. Pipeline RAG

### Configuración v2 (validada en Sprint 6 con RAGAS)

| Parámetro | Valor |
|---|---|
| Estrategia de chunking | RecursiveCharacterTextSplitter (500 / 50) |
| Modelo de embeddings | `mxbai-embed-large` |
| Modelo LLM | `qwen2.5:7b-instruct-q4_K_M` |
| Top-k retrieval | 7 |
| Umbral de similitud (coseno) | 0.65 |
| `num_ctx` del LLM | 8192 |
| `num_predict` | 2048 |
| Temperatura | 0.1 |
| TTL caché Redis | 3600 s |
| Prompt anti-alucinación | Sí (cláusula explícita en system prompt) |

### Flujo de una consulta

1. `RAGService.query(user_question, session_id)` recibe la consulta del estudiante
2. Embebido con `LLMService.embed(question)` → vector 1024-dim
3. Búsqueda en pgvector: `SELECT * FROM document_chunks ORDER BY embedding <=> $1 LIMIT 7`
4. Filtrado por umbral 0.65; si menos de 2 chunks pasan, retornar mensaje de "no tengo info"
5. Construcción del prompt: system + chunks recuperados + historial de la sesión + pregunta
6. Generación con `LLMService.generate(prompt)`
7. Persistencia en `chat_messages` con `sources = [chunk.id_modulo/id_tema/id_subtema]`
8. Caché de la respuesta por hash(question + chunk_ids) con TTL 3600

### Ingesta del corpus

`IngestService.ingest(path)` se dispara como BackgroundTask:
1. Parseo: pypdf / python-docx / markdown
2. Segmentación: RecursiveCharacterTextSplitter
3. Generación de embeddings
4. Upsert en `document_chunks` con metadatos jerárquicos (id_modulo / id_tema / id_subtema)

---

## 8. API REST (FastAPI v1)

10 routers en `backend/app/api/v1/`:

| Router | Endpoints clave |
|---|---|
| `auth.py` | POST /register, /login, /refresh; GET /me |
| `users.py` | GET/PUT /users/{id}; GET /users/{id}/level |
| `modules.py` | GET /modules, /modules/{id}, /modules/{id}/topics |
| `lessons.py` | GET /lessons/{id}; POST /lessons/{id}/visit |
| `exercises.py` | GET /exercises/{id}; POST /exercises/{id}/attempt |
| `quizzes.py` | GET /quizzes/{id}; POST /quizzes/{id}/attempt |
| `chat.py` | POST /chat/sessions; POST /chat/sessions/{id}/messages |
| `progress.py` | GET /progress/me; GET /progress/users/{id} |
| `admin.py` | POST /admin/ingest; GET /admin/health |
| `assessment.py` (Sprint 10) | GET /assessment/instrument; POST /assessment/responses |

Servicios de dominio en `backend/app/services/`:
- `AuthService`, `RAGService`, `LLMService`, `IngestService`, `ProgressService`,
  `LevelingService`, `ChallengeGenerator`, `AssessmentService`

Decorador transversal `@cache(ttl)` en `core/cache.py` para los endpoints de tutor.

---

## 9. Frontend (React + shadcn/ui)

Páginas en `frontend/src/pages/`:

- `LoginPage`, `RegisterPage`, `DashboardPage`
- `ModulesListPage`, `TopicDetailPage`
- `LessonView` (Markdown renderer + syntax highlighting de Kotlin)
- `ExerciseView` (Monaco + sistema de pistas progresivas)
- `QuizView` (autoevaluación, 3–10 preguntas)
- `ChatTutor` (chat con citaciones de fuentes)
- `ProgressPanel` (logros + módulos completados + nivel)
- `AssessmentRunner` (Sprint 10: aplica el instrumento pretest/postest)

Hooks personalizados: `useAuth`, `useApi`, `useChat`, `useProgress`.
Estado global: Zustand (sin Redux).

---

## 10. Validación preexperimental (OE-4 — nuevo en v3.2)

### R4.1 — Instrumento pretest/postest (Sprint 10)

- Documento `docs/instrumento-pretest-postest.docx` con tabla de especificaciones por indicador de logro.
- Versiones equivalentes pretest y postest, escala vigesimal (0–20).
- Operacionalización:
  - Indicador (a) de la Capacidad 1 → 8 puntos (selección múltiple + desarrollo corto).
  - Indicador (b) → 12 puntos (lectura/completado de código Kotlin + resolución de problema).
- Validación por **juicio de expertos** con coeficiente **V de Aiken** (Aiken, 1985):
  - ≥ 3 jueces (incluido el Téc. Xavier Benites Marín).
  - Criterios: claridad, coherencia, relevancia.
  - Umbral: V ≥ 0.80 por ítem.

### R4.2 — Aplicación del pretest y postest (Sprints 11–12)

- Población piloto: 10–15 estudiantes voluntarios del IESTP "RFA".
- Pretest aplicado al inicio del Sprint 11, antes de las primeras sesiones del piloto.
- Periodo de uso del tutor: Sprints 11–12 sobre los Módulos 1–3.
- Postest aplicado al cierre del piloto en el Sprint 12.
- Datos brutos en `data/pretest-postest/raw/` con consentimientos informados firmados.

### R4.3 — Análisis estadístico (Sprint 12)

Notebook reproducible: `notebooks/wilcoxon-pretest-postest.ipynb`

```python
import pandas as pd
from scipy.stats import wilcoxon, shapiro

df = pd.read_csv('data/pretest-postest/processed/scores.csv')
diff = df['postest'] - df['pretest']

# Prueba de normalidad (Shapiro-Wilk, n pequeño)
W, p_norm = shapiro(diff)
# Prueba de hipótesis (no paramétrica si normalidad rechazada)
stat, p = wilcoxon(df['postest'], df['pretest'], alternative='greater')
# Tamaño del efecto: r = |Z| / sqrt(N)
import numpy as np
n = len(diff)
z = stat  # para Wilcoxon, z se obtiene de la aproximación normal
# Cohen d
d = diff.mean() / diff.std(ddof=1)

# Criterios de decisión:
# - Mejora significativa si p < 0.05
# - Magnitud media o superior si r >= 0.5 o d >= 0.5
```

Reporte final: `docs/reporte-rendimiento-academico.docx`.

---

## 11. Trazabilidad ERS — OE (matriz V.2.1)

| OE | RF directos | RNF |
|---|---|---|
| OE-1 | RF-08, RF-09, RF-10, RF-15 (modelo del estudiante y dominio) | RNF-05, RNF-06 |
| OE-2 | (estudio comparativo fuera del software) | RNF-02.3, RNF-03.6, RNF-07.2 |
| OE-3 | RF-07 a RF-29, RF-33 (todo el sistema con trazabilidad) | RNF-01, RNF-02, RNF-05, RNF-06 |
| OE-4 | (instrumentos fuera del software) | — |
| OE-5 | RF-18, RF-25, RF-27, RF-29, RF-32 | RNF-01 (SUS ≥ 68), RNF-02, RNF-03, RNF-04 |

Los RFs trazables a OE-3 con citación de fuentes deben emitir log estructurado con `id_modulo / id_tema / id_subtema` para satisfacer el indicador R3.2 (≥ 90 % respuestas con cita).

---

## 12. Estructura del repositorio

```
.
├── CLAUDE.md                 ← este archivo
├── docker-compose.yml        ← orquestador productivo
├── docker-compose.dev.yml    ← entorno de desarrollo
├── infra/
│   ├── caddy/Caddyfile
│   └── scripts/
│       ├── provision-vm.sh
│       ├── deploy.sh
│       └── backup-postgres.sh
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/
│   │   ├── core/             ← config, cache, security
│   │   ├── models/           ← SQLAlchemy
│   │   ├── schemas/          ← Pydantic
│   │   ├── services/         ← AuthService, RAGService, LLMService, ...
│   │   ├── rag/              ← ingestor, retriever, generator, orchestrator
│   │   └── scheduler/        ← APScheduler tasks
│   ├── alembic/              ← migraciones
│   ├── tests/                ← unit + integration (incluye test_iso25010.py)
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/       ← shadcn/ui derivados
│   │   ├── hooks/
│   │   └── lib/
│   ├── package.json
│   └── vite.config.ts
├── corpus/
│   └── lecciones/modulo-{1,2,3}/*.md
├── docs/
│   ├── ERS.md / ESPECIFICACION_DE_REQUISITOS_DEL_SOFTWARE.docx
│   ├── arquitectura.docx
│   ├── modelos-STI/
│   ├── reporte-LLM.docx
│   ├── reporte-RAGAS.docx
│   ├── instrumento-pretest-postest.docx           ← Sprint 10
│   ├── matriz-trazabilidad-ISO25010.docx          ← Sprint 11
│   ├── reporte-ISO25010.docx                      ← Sprint 11–12
│   ├── reporte-SUS.docx                           ← Sprint 12
│   ├── reporte-rendimiento-academico.docx         ← Sprint 12
│   ├── reporte-validacion-final.docx              ← Sprint 12
│   └── matriz_V2_1.docx
├── data/
│   ├── pretest-postest/{raw,processed}/           ← Sprints 11–12
│   └── golden-set/                                ← Sprint 6 + 7
├── notebooks/
│   ├── ragas-eval.ipynb
│   └── wilcoxon-pretest-postest.ipynb             ← Sprint 12
└── README.md
```

---

## 13. Convenciones para Claude Code

### Antes de codificar
1. Lee este `CLAUDE.md` completo.
2. Lee la sección relevante del ERS (`docs/ERS.md`).
3. Verifica si ya existe el módulo o servicio que vas a crear.
4. Si la tarea no encaja con el alcance de la matriz V.2.1, pregunta antes de codificar.

### Estilo de código
- Backend: tipado completo (Pydantic + SQLAlchemy 2.x async), docstrings de una línea, ruff + black.
- Frontend: TypeScript estricto, componentes funcionales con hooks, props tipadas.
- Comentarios en español.
- Variables y funciones en inglés (convención Python/JS).

### Tests
- pytest para backend; mínimo cobertura del 80 % en módulos del tutor (RAGService, LLMService, IngestService).
- Tests de integración ISO/IEC 25010 en `backend/tests/integration/test_iso25010.py`.

### Commits
- Mensajes en español, formato Conventional Commits.
- Ejemplo: `feat(rag): añadir filtrado por umbral de similitud (0.65)`.

---

## 14. Recordatorios de cierre del proyecto

- **10 jul 2026 — AVANCE 100 %.** Todo el desarrollo y validaciones deben estar terminados.
- **17 jul 2026 — Sustentación.** Solo preparación de diapositivas y demo en vivo.
- Cada feature nueva debe evaluarse contra el cronograma comprimido. Si no cabe, no se construye.
- Toda decisión técnica debe trazarse a un OE de la matriz V.2.1.

---

*Final del CLAUDE.md v3.2 — actualizar cuando el estado del proyecto cambie significativamente o cuando se cierre cada Iteración CRISP-DM.*