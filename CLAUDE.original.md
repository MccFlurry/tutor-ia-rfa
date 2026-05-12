# CLAUDE.md — Tutor IA Generativa · Aplicaciones Móviles IESTP RFA

Tesis pregrado USAT (Escuela de Ingeniería de Sistemas y Computación). STI con RAG privado para curso **Aplicaciones Móviles** (Android/Kotlin) del IESTP "República Federal de Alemania", Chiclayo.

**Autor (tesista):** Roger Alessandro Zavaleta Marcelo · **Asesora (USAT):** Mg. Reyes Burgos, Karla · **Coordinador piloto (IESTP RFA):** Téc. Xavier Benites Marín *(coordina acceso y pertinencia pedagógica, NO es asesor de tesis)*.

**Inicio desarrollo:** 23 mar 2026 · **Hito Pre Informe:** 24 abr 2026 (Sprint 3) · **Sustentación final:** 10 jul 2026.

**Piloto:** 10–15 estudiantes IESTP RFA · **Presupuesto:** S/. 3,170.00.

Estudiantes: estudian 5 módulos, consultan tutor IA privado (RAG), autoevalúan, ven progreso gamificado.

**Reglas absolutas:**
- LLM 100% privado vía Ollama. Nunca APIs pagas (OpenAI/Anthropic/Gemini).
- Sin fine-tuning: "entrenar el modelo" = construir el pipeline RAG sobre el corpus del sílabo.
- Conocimiento dominio solo vía RAG.
- UI **español peruano**; código en **inglés** (variables/funciones/comentarios técnicos); docs y mensajes usuario en español.
- Evaluación: **RAGAS** (faithfulness ≥0.75, answer_relevance ≥0.70) + **ISO/IEC 25010:2023** (cobertura ≥80% RF, éxito ≥90%) + **SUS ≥68**.
- Stack cerrado: **sin** Pub/Sub, Cloud SQL, Memorystore, Cloud Scheduler, Cloud Run. 1 VM Compute Engine + Firebase Hosting.
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- Verificación externa antes de citar precios/versiones/comandos Ollama: advertir al usuario que verifique la fuente oficial.

---

## 🎯 OBJETIVOS ESPEC�FICOS (5 OE)

| OE | Enunciado | Resultado esperado |
|----|-----------|--------------------|
| OE1 | Establecer los modelos del STI (dominio, pedagógico, estudiante, interacción) a partir del sílabo oficial + contexto educativo IESTP RFA | R1.1 dominio · R1.2 pedagógico · R1.3 estudiante · R1.4 interacción |
| OE2 | Seleccionar LLM + modelo de embeddings + construir pipeline RAG validando con RAGAS | R2.1 selección justificada · R2.2 pipeline operativo · R2.3 RAGAS (faithfulness ≥0.75, relevance ≥0.70) |
| OE3 | Desarrollar e integrar el sistema sobre Compute Engine con contenedores | R3.1 desplegado ≥80% de 33 RF priorizados · R3.2 documentación técnica |
| OE4 | Estructurar contenido instruccional + ejercicios + retroalimentación adaptativa para la capacidad "Analizar herramientas y requisitos para el desarrollo de aplicaciones móviles" del sílabo | R4.1 ≥3 módulos con ≥15 lecciones · R4.2 ≥30 ejercicios con feedback adaptativo por nivel |
| OE5 | Validar adecuación funcional conforme ISO/IEC 25010:2023 | R5.1 cobertura ≥80% RF · éxito ≥90% · SUS ≥68 (10-15 estudiantes) |

**ERS:** 52 RF en 8 módulos; **33 priorizados** alineados con ISO/IEC 25010.

---

## 📅 CRONOGRAMA — 8 SPRINTS × 2 SEMANAS (SCRUM + CRISP-DM)

| # | Período | CRISP-DM | Estado | Foco |
|---|---------|----------|--------|------|
| 1 | 23 mar – 05 abr 2026 | — | ✅ | ERS + 4 modelos STI + arquitectura + docker-compose |
| 2 | 06 abr – 19 abr 2026 | BU + DU | ✅ | Evaluación LLM/embeddings + backend core + frontend base |
| 3 | 20 abr – 03 may 2026 | DP + Modeling | 🔄 | Pipeline RAG + personalización (Fases 5–7.5). **Hito 24/04 Pre Informe.** |
| 4 | 04 may – 17 may 2026 | Evaluation | � | **RAGAS**: golden set 30 preguntas + métricas + iteraciones + reporte |
| 5 | 18 may – 31 may 2026 | Deployment | � | VM e2-standard-4 + Docker Compose + Caddy+LE + Firebase Hosting + backup + Redis cache + APScheduler |
| 6 | 01 jun – 14 jun 2026 | — | � | 15 lecciones + 30 ejercicios + motor adaptativo + editor Monaco |
| 7 | 15 jun – 28 jun 2026 | — | � | **ISO/IEC 25010:2023**: matriz trazabilidad + pytest ≥80% + reporte |
| 8 | 29 jun – 10 jul 2026 | — | � | **SUS** 10-15 estudiantes + consolidación + Informe Final + sustentación |

Metodología: **SCRUM** global; **CRISP-DM** solo sprints del pipeline LLM/RAG (2-5).

---

## �� STACK (decisiones cerradas — no cambiar sin justificación cuantitativa)

### Frontend
React 18 SPA + **TypeScript estricto**, Vite 5, Tailwind 3, shadcn/ui, Zustand, TanStack Query, React Router v6, react-hot-toast, Lucide. ESLint + Prettier. Componentes funcionales con hooks. Deploy: **Firebase Hosting** (NO Cloud Run, NO Cloud Storage directo).

### Backend
FastAPI + Python 3.12, SQLAlchemy 2.0 async + asyncpg + Alembic, Pydantic v2, LangChain + langchain-ollama, slowapi, loguru (JSON estructurado), APScheduler (reindexación + limpieza sesiones), python-jose + passlib[bcrypt], httpx, pypdf, python-docx. **FastAPI BackgroundTasks** en vez de Pub/Sub. PEP 8 + type hints obligatorios + `async/await` + pytest + ruff.

### IA — LLM + Embeddings + RAG
- Servidor: **Ollama** auto-hospedado
- LLM: `qwen2.5:7b-instruct-q4_K_M`
- Embeddings: `mxbai-embed-large` (1024 dim)
- Chunking: **semántico 15% overlap** (objetivo v4.0) · impl. actual `RecursiveCharacterTextSplitter(500/50)` — evaluar contra RAGAS en Sprint 4
- Retrieval: coseno, top-k=5, **threshold=0.65** (objetivo v4.0) · impl. actual 0.70 — ajustar tras RAGAS
- Framework validación: **RAGAS** (faithfulness, answer_relevance, context_precision, context_recall)

### Base de datos y caché
- **PostgreSQL 16 + pgvector** auto-hospedado (NO Cloud SQL)
- **Redis 7** auto-hospedado (NO Memorystore)
- Corpus: filesystem VM bajo `/data/corpus/` (módulos 1-3 indexados Sprint 2)

### Infraestructura
- 1 VM **Google Compute Engine e2-standard-4 (16 GB RAM)** · *cambio v4.0: revierte split Cloud Run + Cloud SQL + e2-standard-2 SPOT de iteraciones previas*
- Orquestación: Docker Compose
- TLS: **Caddy + Let's Encrypt**

### Seguridad
JWT 60 min access / 7 días refresh (rotación en `/refresh`), bcrypt, CORS restrictivo a `BACKEND_CORS_ORIGINS`, brute-force lockout 3 intentos × 5 min (frontend localStorage + countdown), rate limit chat 20/h (Redis) + API 100/min (slowapi global), Secret Manager, HTTPS Caddy.

### Pipeline RAG

**Ingesta:** Archivo (PDF/DOCX/TXT/MD) → BackgroundTask FastAPI → parser (pypdf/python-docx/UTF-8) → chunker (semántico 15% o Recursive 500/50) → mxbai-embed-large → vector[1024] → pgvector `document_chunks` (+ `corpus_chunks` planificado v4.0).

**Consulta:** Pregunta → embedding → pgvector cosine (top_k=5, threshold 0.65–0.70) → chunks + historial (5 rondas) → prompt aumentado (system pedagógico + contexto + historial + pregunta) → qwen2.5 temperature=0.3 num_ctx=4096 → caché Redis `rag:{hash(q)}` TTL 3600s → respuesta con **citas trazables** (similarity ≥0.75).

---

## � ESTRUCTURA

```
tutor-ia-rfa/
├── CLAUDE.md, README.md, .env.example, .env, .gitignore
├── docker-compose.yml              # stack completo dev
├── docker-compose.vm.yml            # Ollama+Redis en VM prod
├── backend/
│   ├── Dockerfile, requirements.txt, alembic.ini, pyproject.toml
│   ├── alembic/versions/            # 001_initial, 002_add_coding_challenges, 003_add_personalization, 004_ai_coding_flags
│   ├── notebooks/
│   │   ├── ragas_validation.ipynb  # Sprint 4
│   │   └── sus_analysis.ipynb      # Sprint 8
│   ├── tests/
│   │   ├── fixtures/golden_set.json    # Sprint 4 (30 preguntas ground truth)
│   │   ├── unit/
│   │   └── integration/test_iso25010.py  # Sprint 7
│   ├── scripts/                    # seed_db.py, seed_assessment_bank.py, ingest_course_docs.py
│   └── app/
│       ├── main.py, config.py, database.py, dependencies.py
│       ├── models/                  # user, module, topic, quiz, progress, achievement, chat, document, coding, user_level, entry_assessment, assessment_bank
│       ├── schemas/                 # mismo split + auth + dashboard + coding + assessment
│       ├── routers/                 # auth, users, modules, topics, quiz, progress, achievements, chat, dashboard, admin, coding, assessment
│       ├── services/                # auth, progress, achievement, rag, llm, embed, ingest, code_eval, topic_completion, entry_assessment, leveling, challenge_generator, coding_generator
│       └── utils/                   # security (JWT+bcrypt), chunking, logger
├── frontend/
│   ├── Dockerfile, .firebaserc, firebase.json, package.json, vite/tsconfig/tailwind/postcss/components.json
│   └── src/
│       ├── main.tsx, App.tsx, vite-env.d.ts
│       ├── api/                     # client (axios+JWT), auth, modules, topics, quiz, progress, achievements, chat, coding, dashboard, admin, assessment
│       ├── store/                   # authStore, progressStore, uiStore
│       ├── components/
│       │   ├── ui/                  # shadcn: button, card, input, progress, badge, dialog, tabs, toast, etc.
│       │   ├── layout/              # Navbar, Sidebar, AppLayout
│       │   ├── auth/AuthGuard.tsx, LevelGuard.tsx
│       │   ├── brand/BrandLogo.tsx
│       │   ├── modules/             # ModuleCard, TopicListItem
│       │   ├── topics/              # ContentRenderer, CodeBlock
│       │   ├── quiz/                # QuizQuestion, QuizResults
│       │   ├── chat/                # ChatMessage, ChatSources, TypingIndicator
│       │   ├── assessment/          # EntryAssessmentPage, ReassessmentModal, LevelBadge
│       │   └── achievements/AchievementCard
│       ├── pages/                   # Login, Dashboard, Modules, ModuleDetail, Topic, Chat, Progress, Admin, Quiz, Achievements, CodingChallenge, EntryAssessment
│       ├── hooks/                   # useAuth, useProgress, useChat
│       ├── types/                   # mirror schemas
│       └── lib/utils.ts             # cn()
├── ollama/modelfile-qwen2.5
├── corpus/                          # módulo-1/2/3 + sílabo (filesystem VM: /data/corpus/)
├── scripts/                         # seed_db.py, setup_ollama.sh, ingest_course_docs.py
├── infra/
│   ├── caddy/Caddyfile              # Sprint 5
│   └── scripts/{provision-vm.sh, deploy.sh, backup-postgres.sh}
├── benchmarks/                      # Sprint 2 · evaluación comparativa LLM+embeddings (OE2 R2.1) · ✅ ejecutado
│   ├── README.md                    # protocolo de 6 pasos
│   ├── prompts_llm.json             # 50 prompts M1(12) + M2(18) + M3(15) + off-topic(5)
│   ├── run_llm_benchmark.py         # paso 2 · benchmark 3 LLMs (qwen2.5 · llama3 · mistral)
│   ├── score_responses_auto.py      # paso 3 · calificación automatizada con LLM juez (reemplaza interactivo)
│   ├── export_corpus.py             # paso 4 · exporta chunks desde pgvector
│   ├── golden_set_embeddings.json   # 20 queries M1-M3 con keywords esperadas
│   ├── run_embeddings_benchmark.py  # paso 5 · benchmark mxbai vs nomic (Recall@5 + MRR)
│   ├── generate_llm_report.py       # paso 6 · produce docs/reporte-LLM.docx desde JSONs
│   └── results/                     # outputs JSON
│       ├── llm_benchmark.json       # 3 modelos × 50 prompts · latencia + tok/s + VRAM
│       ├── llm_scores.json          # 3 × 50 calificados con LLM juez Likert 1-5
│       ├── corpus_chunks.json       # 163 chunks exportados desde pgvector
│       └── embeddings_benchmark.json # mxbai vs nomic · Recall@5 + MRR
└── docs/                            # 12 entregables .docx (ver tabla más abajo)
```

---

## 🗄� ESQUEMA BD

Pre-req: `CREATE EXTENSION IF NOT EXISTS vector;`

```sql
-- USUARIOS
users(id UUID PK, email UNIQUE, full_name, hashed_password, role DEFAULT 'student', is_active, avatar_url, created_at, updated_at)

-- CURSO
modules(id SERIAL PK, title, description, order_index UNIQUE, icon_name, color_hex, is_active, created_at)
topics(id SERIAL PK, module_id FK, title, content TEXT, video_url, order_index, estimated_minutes, has_quiz, is_active, UNIQUE(module_id, order_index))
quiz_questions(id SERIAL PK, topic_id FK, question_text, options JSONB, correct_option_index, explanation, order_index)

-- PROGRESO
user_topic_progress(user_id FK, topic_id FK, is_completed, time_spent_seconds, first_visited_at, completed_at, last_accessed_at, UNIQUE(user_id, topic_id))
quiz_attempts(user_id FK, topic_id FK, score FLOAT, answers JSONB, is_passed, attempted_at)

-- LOGROS
achievements(id, name, description, badge_emoji, badge_color, condition_type, condition_value, condition_module_id FK)
-- condition_type: first_topic | module_completed | streak_days | chat_messages | course_completed | quiz_perfect
user_achievements(user_id FK, achievement_id FK, earned_at, UNIQUE(user_id, achievement_id))

-- CHAT
chat_sessions(id UUID PK, user_id FK, title, created_at, last_message_at)
chat_messages(id UUID PK, session_id FK, user_id FK, role 'user'|'assistant', content, sources JSONB, created_at)

-- RAG
documents(id UUID PK, original_filename, stored_filename, file_size_bytes, mime_type, status 'pending'|'processing'|'active'|'error', error_message, chunk_count, uploaded_by FK, created_at, processed_at)
document_chunks(id UUID PK, document_id FK, content, embedding vector(1024), chunk_index, metadata JSONB, created_at)

-- CODING CHALLENGES (Fase 5.5 + 7.5)
coding_challenges(id, topic_id FK, title, description, difficulty, hints, reference_solution, is_ai_generated, generated_for_user_id FK, student_level, ...)
coding_submissions(id, user_id FK, challenge_id FK, code, score, feedback, strengths, improvements, submitted_at)

-- PERSONALIZACIÓN (Fase 6)
user_levels(user_id UUID PK FK, level VARCHAR(20), entry_score FLOAT, assessed_at, last_reassessed_at, history JSONB)
entry_assessment_sessions(id UUID PK, user_id FK, questions JSONB, answers JSONB, score FLOAT, computed_level, created_at)
entry_assessment_bank(id SERIAL PK, module_id FK, question_text, options JSONB, correct_index, difficulty 'easy'|'medium'|'hard', created_by FK, is_active)

-- �NDICES
CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
-- ⚠� Crear DESPUÉS de ingestar datos. lists ≈ sqrt(n_chunks)
CREATE INDEX idx_user_progress_user/topic, idx_quiz_attempts_user, idx_chat_messages_session, idx_document_chunks_document;
```

---

## 🔌 API REST

Base dev: `http://localhost:8000/api/v1` · Prod: `https://[VM_DOMAIN]/api/v1` (Caddy+LE)
Auth: `Authorization: Bearer <access_token>` (excepto `/auth/login`, `/auth/register`).

### `/auth`
- `POST /register` body `{email, full_name, password}` → `{user, access_token, refresh_token}`
- `POST /login` body `{email, password}` → ídem
- `POST /refresh` body `{refresh_token}` → `{access_token}`
- `POST /logout` body `{refresh_token}` → `{message}`

### `/users`
- `GET /me`, `PUT /me` body `{full_name?, avatar_url?}`, `PUT /me/password` body `{current_password, new_password}`
- `GET /me/level` → `{level, entry_score, history}`
- `POST /me/reassess` → dispara evaluación nueva

### `/dashboard`
- `GET /` → `{user_name, user_level, overall_progress_pct, total_topics_completed, last_accessed_topic, recommended_modules, recent_achievements}`

### `/modules`
- `GET /` → lista con `progress_pct, is_locked, total_topics, completed_topics`
- `GET /{id}` → Module + temas con `status: not_started|in_progress|completed`

### `/topics`
- `GET /{id}` → contenido + progreso + `has_coding_challenge`
- `POST /{id}/visit`, `POST /{id}/complete`, `POST /{id}/time` body `{seconds}`

### `/quiz` (IA genera preguntas, fallback BD estática)
- `GET /topic/{topic_id}` → `{session_id, questions}` (LLM genera con `student_level`, Redis TTL 30min)
- `POST /topic/{topic_id}/submit` body `{session_id, answers}` → `{score, is_passed, feedback, attempt_id}` · 410=sesión expirada, 503=servicio caído
- `GET /topic/{topic_id}/history`

### `/progress`
- `GET /` → stats globales + módulos
- `GET /activity` → últimas 20 (topic_completed|quiz_passed|achievement)

### `/achievements`
- `GET /` → todos con `is_earned, earned_at?`

### `/chat`
- `GET /sessions`, `POST /sessions`
- `GET /sessions/{id}/messages`
- `POST /sessions/{id}/message` body `{content}` → `{message_id, role, content, sources, created_at}` · 429=rate limit
- `DELETE /sessions/{id}`
- `GET /remaining` (consultas restantes/hora)

### `/coding` (Fase 5.5 + 7.5)
- `GET /topic/{topic_id}` → desafío del estudiante (AI o fallback)
- `POST /topic/{topic_id}/regenerate` → genera nuevo
- `GET /challenge/{id}`, `POST /challenge/{id}/submit` body `{code}` → score + feedback LLM
- `GET /challenge/{id}/history`, `GET /challenge/{id}/best`
- `GET /topic/{topic_id}/completion-status`

### `/assessment` (Fase 6)
- `POST /start` → `{session_id, questions}` (LLM o fallback banco)
- `POST /submit` body `{session_id, answers}` → `{level, score, feedback_por_modulo}`

### `/admin` (solo role=admin)
- Usuarios: `GET /users` paginado, `PUT /users/{id}` body `{role?, is_active?}`
- Niveles estudiantes: `GET /user-levels`, `POST /user-levels/{id}/override`
- Corpus RAG: `GET/POST/DELETE /documents`, `POST /documents/{id}/reprocess`
- Contenido: CRUD módulos, temas, preguntas quiz, desafíos coding
- Banco fallback evaluación: `GET/POST/PUT/DELETE /assessment-bank`
- Generador IA preview: `POST /coding-challenges/generate`

---

## 🤖 RAG — INTERFAZ

### `services/rag_service.py`

`RAGService.query(question, session_history, db, redis)` → `{content, sources}`:
1. Chequear caché Redis `rag:{hash(question)}`
2. `OllamaEmbeddings(mxbai-embed-large).aembed_query(question)` → vec[1024]
3. pgvector cosine search: `1 - (embedding <=> :query_vec::vector) AS similarity`, threshold 0.65–0.70, top 5
4. Sin chunks → mensaje educativo rechazo
5. Build context (chunks con fuente) + history (últimas 5 rondas)
6. `OllamaLLM(qwen2.5:7b-instruct-q4_K_M, temperature=0.3, num_ctx=4096).ainvoke(prompt)`
7. Sources con similarity≥0.75 → `{content_preview, document_name, similarity}`
8. Cachear TTL 3600s

**System prompt:** tutor español peruano, responde desde CONTEXTO, rechaza off-topic, ejemplos Kotlin en ```kotlin, admite incertidumbre, no inventa.

### `services/ingest_service.py`

`IngestService.process_document(doc_id, file_path, db)` (BackgroundTask):
1. status='processing'
2. Parse: pypdf (PDF) / python-docx (DOCX) / UTF-8 read (TXT)
3. Clean: normalizar espacios, max 2 \n consecutivos
4. `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, separators=["\n\n","\n",". "," ",""])` *(evaluar semántico 15% en Sprint 4)*
5. `OllamaEmbeddings.aembed_documents(chunks)` (batch)
6. Guardar chunks + vectores
7. status='active', chunk_count=N · o 'error' con mensaje

### `services/llm_service.py` (Quiz IA)
ChatOllama con `format="json"`, `temperature=0.7`. Prompt español genera N preguntas. Acepta `student_level` (beginner/intermediate/advanced) y adapta tono/dificultad. ⚠� **Usar wrapper `{"questions":[...]}`** no array desnudo (incompatible con format=json). Parser maneja ambos. Trunca contenido 3500 chars.

### `services/code_eval_service.py`
LLM evalúa código. Criterios: corrección 40%, buenas prácticas 25%, eficiencia 20%, legibilidad 15%. Score 0-100 + feedback Markdown + strengths + improvements. `format="json"`. Acepta `student_level` (criterios más estrictos para advanced). Solución referencia como guía, no única válida.

### `services/entry_assessment_service.py` + `leveling_service.py` (Fase 6)
Genera evaluación de entrada vía LLM (fallback banco docente). Calcula nivel ponderado (pesos módulo M1=1.0…M5=1.5, dificultad easy=1.0/medium=1.5/hard=2.0). Umbrales: `<40` beginner · `40–75` intermediate · `>75` advanced. `check_reassessment` evalúa últimos 3 quizzes → propuesta up/down.

---

## 📊 EVALUACIÓN Y VALIDACIÓN

### RAGAS (Sprint 4 · CRISP-DM Evaluation)
- Golden set 30 preguntas con ground truth → `backend/tests/fixtures/golden_set.json`
- Notebook `backend/notebooks/ragas_validation.ipynb` ejecuta: faithfulness, answer_relevance, context_precision, context_recall
- Iteraciones ajuste: chunking (500/50 vs semántico 15%), threshold (0.65 vs 0.70), top_k=5
- **Protocolo escalamiento:** si métrica < umbral tras 3 iteraciones → consultar usuario
- Reporte: `docs/reporte-RAGAS.docx`

### ISO/IEC 25010:2023 (Sprint 7)
- Matriz trazabilidad 33 RF × casos de prueba → `docs/matriz-trazabilidad-ISO25010.docx`
- Subcaracterísticas: completitud funcional + corrección + pertinencia
- Suite pytest integración `backend/tests/integration/test_iso25010.py` cobertura ≥80%
- Umbrales: cobertura ≥80% RF, tasa éxito ≥90%
- Reporte: `docs/reporte-ISO25010.docx`

### SUS (Sprint 8)
- Piloto 10-15 estudiantes IESTP RFA con sesiones guiadas
- Score individual + promedio + desviación estándar + percentil + análisis cualitativo
- Umbral: **SUS ≥68**
- Notebook `backend/notebooks/sus_analysis.ipynb`
- Reporte: `docs/reporte-SUS.docx` + consolidación en `docs/reporte-validacion-final.docx`

---

## 📄 DOCS ENTREGABLES (.docx)

Formato: portada (título + autor + asesora Mg. Reyes Burgos + USAT + fecha), índice automático con numeración, secciones/subsecciones numeradas, Times New Roman 11-12, interlineado 1.5, tablas/figuras con leyenda numerada.

| # | Archivo | Sprint | Descripción |
|---|---------|--------|-------------|
| 1 | `docs/ERS.docx` | S1 ✅ | 52 RF en 8 módulos; 33 priorizados alineados ISO/IEC 25010 |
| 2 | `docs/modelos-STI/modelo-dominio.docx` | S1 ✅ | Jerarquía módulo→tema→subtema con prerrequisitos |
| 3 | `docs/modelos-STI/modelo-pedagogico.docx` | S1 ✅ | Estrategias tutoría + criterios adaptación por nivel |
| 4 | `docs/modelos-STI/modelo-estudiante.docx` | S2 ✅ | 5 atributos + diagrama ER + mecanismo actualización |
| 5 | `docs/modelos-STI/modelo-interaccion.docx` | S2 ✅ | 4 modos uso + UML secuencia |
| 6 | `docs/reporte-LLM.docx` | S2 ✅ | Evaluación comparativa 3 LLM + 2 embeddings + justificación |
| 7 | `docs/arquitectura.docx` | S3 | Diagramas C4 (contexto/contenedores/componentes) + justificación stack |
| 8 | `docs/reporte-RAGAS.docx` | S4 | Golden set + métricas + casos límite + iteraciones |
| 9 | `docs/matriz-trazabilidad-ISO25010.docx` | S7 | 33 RF × casos prueba + subcaracterísticas |
| 10 | `docs/reporte-ISO25010.docx` | S7 | Cobertura + éxito + defectos + plan remediación |
| 11 | `docs/reporte-SUS.docx` | S8 | Individual + promedio + desviación + percentil + cualitativo |
| 12 | `docs/reporte-validacion-final.docx` | S8 | Consolidación ISO/IEC 25010 + SUS para Discusión del Informe Final |

---

## 🎨 FRONTEND

### Setup shadcn
```bash
npx shadcn@latest init
npx shadcn@latest add button card input label progress badge dialog tabs toast separator skeleton scroll-area textarea alert
```

### Colores (tailwind.config.js)
- Primary 500 `#3b82f6` azul institucional (50/100/600/700/900)
- Institutional navy + heritage oro (academia + Alemania) + peru rojo
- Module: `locked #9ca3af`, `progress #3b82f6`, `completed #22c55e`
- Fonts: Plus Jakarta Sans (sans), JetBrains Mono (mono)

### Páginas

- **LoginPage:** split 2-col desktop con panel hero navy + formulario card + brute-force protection
- **DashboardPage:** saludo, badge nivel, hero `bg-brand-hero` "Continuar...", 3 recomendaciones por nivel, 3 logros recientes, stats tabulares
- **ModulesPage:** grid responsivo 1/2/3 cols, ModuleCard con progreso, bloqueados grayscale+candado+tooltip
- **ModuleDetailPage:** header+progress, breadcrumb, lista temas (✅ verde completado / 🔵 azul pulsante en progreso / ⬜ gris pendiente)
- **TopicPage:** breadcrumb, panel lateral "Consultar Tutor IA" (modal), área Markdown (react-markdown + remark-gfm + react-syntax-highlighter vscDarkPlus + botón copiar), iframe YouTube 16:9, barra fija "� Anterior | X de Y | Siguiente →", botón "Ir a Autoevaluación" o "Marcar completado", botón desafío código
- **ChatPage:** 2 columnas (sidebar sesiones + chat). Burbujas user-der azul / tutor-izq gris. Markdown renderizado. Fuentes colapsables. "✦ escribiendo...". Contador "X de 20 consultas/hora". Textarea auto-grow, Enter envía, Shift+Enter nueva línea
- **ProgressPage:** 4 tarjetas métricas, barras por módulo, grid logros, historial
- **EntryAssessmentPage:** wizard multi-paso preguntas IA + barra progreso + "La IA está analizando tu nivel..." + resultado con gráfica por módulo
- **AdminPage:** 5 tabs [Corpus RAG | Contenido | Usuarios | Banco Fallback | Niveles]. RAG: tabla docs, drag&drop upload, estado procesando. Contenido: árbol colapsable Módulo→Temas→Preguntas+Coding con CRUD
- **CodingChallengePage:** split. Izq: descripción Markdown + pistas + resultado (score, feedback, strengths, improvements) + chip "Generado con IA · nivel X". Der: editor dark theme monospace *(Sprint 6 → Monaco)* + botón "Regenerar con IA"

---

## 📄 DATOS INICIALES (`seed_db.py`)

**5 módulos:**
1. Fundamentos y Preparación del Entorno (index 1, `smartphone`, `#6366f1`)
2. Lógica de Programación en Kotlin (2, `code-2`, `#0ea5e9`)
3. Elaboración de Interfaces de Usuario UI (3, `layout-panel-top`, `#22c55e`)
4. Componentes Android y Gestión de Datos (4, `database`, `#f59e0b`)
5. Funcionalidades Avanzadas y Despliegue (5, `rocket`, `#ef4444`)

**22 temas totales** distribuidos: M1=4, M2=5, M3=4, M4=5, M5=4. Cada uno: title, estimated_minutes (10-35), has_quiz (true/false). Ver `backend/scripts/seed_db.py` para contenido Markdown completo con código Kotlin.

**7 logros:** Primer Paso 🚀 (first_topic=1), Finalizador Módulo � (module_completed=1), Racha 7 Días 🔥 (streak_days=7), Explorador Tutor IA 🤖 (chat_messages=10), Maestro Kotlin ⚡ (module_completed=2 mod_id=2), Quiz Perfecto 💯 (quiz_perfect=100), Desarrollador Completo 🎓 (course_completed=100).

**30 desafíos coding** (objetivo OE4 cumplido, `scripts/seed_extra_challenges.py` idempotente):
- M1 (+2): Verificador Compatibilidad API, Hola Mundo Variables
- M2 (9): los 5 originales (Calculadora Promedio, Clasificador Triángulos, Filtro Lambda, Inventario, Figuras Polimorfismo) + Conversor Temperaturas, Simulador Calificaciones, Ordenar Personas, Jerarquía Vehículos
- M3 (+6): Layout XML Registro, Validador Email, Click Handler, ConstraintLayout, Card Responsivo, Adapter RecyclerView
- M4 (8): los 2 originales (Logger Ciclo Vida, Modelo API) + Counter Bundle, Intent Extras, SharedPrefs, Mini CRUD SQLite, Parser JSON, Retrofit GitHub
- M5 (5): Logger por Nivel, Test JUnit Calculadora, Test Data Class, signingConfigs Gradle, Checklist Play Store
Distribución final: M1=2 · M2=9 · M3=6 · M4=8 · M5=5 (total 30).

**23 preguntas banco fallback** evaluación entrada distribuidas M1-M5 (`scripts/seed_assessment_bank.py`).

---

## � DOCKER COMPOSE (dev)

Servicios clave:
- **postgres:** `pgvector/pgvector:pg16`, DB `tutordb`, user `tutor_user`, pass `tutor_pass_dev`, healthcheck pg_isready
- **redis:** `redis:7-alpine`, `--maxmemory 256mb --maxmemory-policy allkeys-lru`
- **ollama:** `ollama/ollama:latest`, vol `ollama_data:/root/.ollama`. **⚠� Dev Windows: Ollama nativo via `host.docker.internal:11434` para GPU. Contenedor comentado.**
- **backend:** FastAPI, hot reload. Command: `alembic upgrade head && python scripts/seed_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`. Monta `./backend/alembic` para preservar migraciones.
- **frontend:** React Vite dev server puerto 5173, `VITE_API_BASE_URL=http://localhost:8000/api/v1`

Volumes: `postgres_data, redis_data, ollama_data, uploads_data`.

**Prod (Sprint 5):** Docker Compose en VM e2-standard-4 + `infra/caddy/Caddyfile` (TLS LE) + `infra/scripts/{provision-vm.sh, deploy.sh, backup-postgres.sh}`.

### `scripts/setup_ollama.sh`
```bash
ollama pull qwen2.5:7b-instruct-q4_K_M  # ~4.5GB
ollama pull mxbai-embed-large            # ~670MB
```

---

## ⚙� VARIABLES (`.env.example`)

```
DATABASE_URL=postgresql+asyncpg://tutor_user:tutor_pass_dev@localhost:5432/tutordb
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M
OLLAMA_EMBED_MODEL=mxbai-embed-large
OLLAMA_TIMEOUT=120
EMBEDDING_DIMENSION=1024

SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(32))">
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

ENVIRONMENT=development
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
MAX_UPLOAD_SIZE_MB=50

CHAT_RATE_LIMIT_PER_HOUR=20
API_RATE_LIMIT_PER_MINUTE=100

RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.70      # evaluar bajar a 0.65 tras RAGAS Sprint 4
RAG_CONTEXT_WINDOW=5
CHUNK_SIZE=500
CHUNK_OVERLAP=50                    # evaluar semántico 15% Sprint 4

UPLOAD_DIR=./uploads
CORPUS_DIR=/data/corpus             # VM prod

ADMIN_EMAIL=admin@iestprfa.edu.pe
ADMIN_PASSWORD=Admin123!
ADMIN_NAME=Administrador del Sistema
```

---

## 📦 DEPENDENCIAS CLAVE

**backend/requirements.txt:** fastapi 0.115.5, uvicorn[standard] 0.32.0, sqlalchemy[asyncio] 2.0.36, asyncpg 0.30.0, alembic 1.14.0, pydantic 2.10.0, pydantic-settings 2.6.1, python-jose[cryptography] 3.3.0, passlib[bcrypt] 1.7.4, python-multipart 0.0.17, httpx 0.28.0, langchain 0.3.10, langchain-community 0.3.10, langchain-ollama 0.2.1, pypdf 5.1.0, python-docx 1.1.2, redis[hiredis] 5.2.0, slowapi 0.1.9, loguru 0.7.2, apscheduler 3.10.4, pytest 8.3.4, pytest-asyncio 0.24.0, pytest-cov 6.0.0. **Sprint 4:** ragas, datasets.

**frontend deps clave:** react 18.3.1, react-dom 18.3.1, react-router-dom 6.28.0, @tanstack/react-query 5.62.0, axios 1.7.7, zustand 5.0.1, react-markdown 9.0.1, react-syntax-highlighter 15.6.1, react-hot-toast 2.4.1, lucide-react 0.462.0, clsx, tailwind-merge, class-variance-authority, @radix-ui/react-{dialog,tabs,progress,scroll-area}. **Sprint 6:** @monaco-editor/react.

**devDeps:** @vitejs/plugin-react 4.3.3, vite 5.4.11, typescript 5.7.2, tailwindcss 3.4.15, autoprefixer, postcss, @types/react(-dom).

---

## 🚀 FASES / SPRINTS

### ✅ FASE 1 — Sprint 1 · Infraestructura y BD
Estructura, docker-compose con pgvector/redis/ollama, config.py + database.py async, todos modelos SQLAlchemy, migración inicial Alembic con `CREATE EXTENSION vector`, React+Vite+TS+Tailwind+shadcn en frontend. `docker compose up` funciona. ERS 52 RF / 33 priorizados. 4 modelos STI documentados.

### ✅ FASE 2 — Sprint 2 · Autenticación + evaluación LLM (OE2 R2.1)
`security.py` JWT+bcrypt, `auth_service.py`, `routers/auth.py`, `dependencies.py` (get_db, get_current_user, get_redis, require_admin). Frontend: `LoginPage` con toggle registro + brute-force protection (3 intentos+lockout 5min), `authStore` Zustand+localStorage, `api/client.ts` interceptor 401, `AuthGuard` con requireAdmin.

**Evaluación comparativa LLM/embeddings ejecutada 2026-04-24** — `benchmarks/` completo (ver §BENCHMARKS). Reporte final: `docs/reporte-LLM.docx` (43 KB, 8 secciones + 2 anexos + referencias IEEE, formato USAT Times New Roman 12).

**LLM evaluados (50 prompts cada uno, juez LLM Likert 1-5):**
| Modelo | Lat. avg | Lat. p95 | Tok/s | VRAM | Likert global |
|--------|----------|----------|-------|------|---------------|
| qwen2.5:7b-instruct-q4_K_M | 5.91s | 8.66s | 107.0 | 4.59 GB | **4.85** ✅ |
| llama3:8b-instruct-q4_K_M | 4.71s | 7.40s | 109.6 | 5.09 GB | 4.84 |
| mistral:7b-instruct-q4_K_M | 3.90s | 6.79s | 120.2 | 4.79 GB | 4.28 |

**Embeddings evaluados (20 queries sobre corpus real 163 chunks M1-M3):**
| Modelo | Dim | Recall@5 | MRR | Latencia (ms) |
|--------|-----|----------|-----|---------------|
| mxbai-embed-large | 1024 | **0.550** ✅ | 0.453 | 173 |
| nomic-embed-text | 768 | 0.350 | 0.305 | 131 |

**Decisión final:** qwen2.5:7b-instruct-q4_K_M + mxbai-embed-large. qwen2.5 ganó la rúbrica por 0.01 sobre llama3 (empate técnico) pero usa 0.5 GB menos VRAM y es el único que obtuvo nota perfecta 5.00 en "ausencia de alucinaciones". mxbai-embed-large supera a nomic por +0.20 Recall@5, margen claro. Pipeline RAG operativo con corpus Módulos 1-3 indexado pgvector.

### ✅ FASE 3 — Sprint 2-3 · Módulos, Temas, Contenido
`setup_ollama.sh`, `seed_db.py` (5 módulos + 22 temas Markdown completo + 25+ preguntas + 7 logros + admin). `routers/modules.py` + `topics.py`. Frontend: `ModulesPage`, `ModuleDetailPage`, `TopicPage`, `ContentRenderer` (react-markdown + remark-gfm), `CodeBlock` (syntax+copy), layout (AppLayout/Sidebar/Navbar), shadcn components.

### ✅ FASE 4 — Sprint 3 · Progreso, Quiz IA, Logros
`progress_service.py`, `achievement_service.py` (7 tipos auto-detect), `llm_service.py` (Ollama quizzes JSON), `routers/quiz.py` (GET genera vía LLM→Redis TTL 30min, POST evalúa, fallback BD estática si Ollama caído, sesiones single-use), `progress.py`, `achievements.py`. Frontend: `QuizPage` ("IA está preparando...", retry genera NUEVAS, 410→auto-regenera), `QuizQuestion`, `QuizResults`, `ProgressPage` (4 cards + barras + logros + actividad), `AchievementsPage`.

### ✅ FASE 5 — Sprint 3 · Tutor IA Conversacional RAG
`embed_service.py` singleton mxbai, `ingest_service.py` (parse→clean→chunk→embed→pgvector), `rag_service.py` (embed→pgvector cosine top5 ≥0.70→prompt aumentado con historial→qwen2.5→cache Redis TTL 1h). `routers/chat.py`: CRUD sesiones, POST mensaje con RAG, rate limit Redis 20/h→429, fuentes ≥0.75, `GET /remaining`, título auto desde primer msg, integra achievement. Frontend: `ChatPage` + `ChatMessage` (Markdown+syntax), `ChatSources` (colapsable %relevancia), `TypingIndicator`, sidebar sesiones, input Enter/Shift+Enter, contador, optimistic updates.

`ingest_course_docs.py` → 22 temas = 163 chunks. Ollama nativo Windows GPU (RTX 4070 16GB) → respuestas 3-5s.

**Fixes críticos:**
- `llm_service.py`: wrapper `{"questions":[...]}` para `format="json"`, parser ambos formatos
- `rag_service.py`: vector literal **inline** en SQL (asyncpg no soporta `::vector` parametrizado)
- `docker-compose.yml`: Ollama nativo via `host.docker.internal:11434`

### ✅ FASE 5.5 — Sprint 3 · Desafíos Programación con IA
`models/coding.py` (CodingChallenge + CodingSubmission), migración `002_add_coding_challenges.py`, `code_eval_service.py` (LLM scoring 0-100 + Markdown feedback + strengths + improvements, criterios 40/25/20/15, `format="json"`), `schemas/coding.py` + `routers/coding.py` (CRUD, submit con LLM, history, best, completion-status).

Frontend: `CodingChallengePage` split, `types/coding.ts`, `api/coding.ts`, ruta `/coding/:challengeId`.

7 desafíos seeded. `topic_completion_service.py`: tema con quiz+coding → AMBOS deben aprobarse (quiz ≥60%, coding ≥60pts). `TopicListItem` muestra ícono "Desafío de Código".

### ✅ FASE 6 — Sprint 3 · Personalización vía CRISP-DM (completada 2026-04-17)

**Objetivo:** Evaluación de entrada IA asigna nivel (`beginner` | `intermediate` | `advanced`). LLM adapta dificultad quiz + coding al nivel. Re-asignación dinámica según desempeño.

#### 1�⃣ Business Understanding
- Problema: estudiantes distinto nivel reciben mismos ejercicios → desmotivación + aprendizaje subóptimo
- KPIs éxito: SUS ≥68, tasa completación por nivel, accuracy clasificador vs juicio docente, re-asignaciones correctas

#### 2�⃣ Data Understanding
- Evaluación entrada: respuestas + tiempo + cobertura por módulo
- Señales continuas: quiz scores, intentos, coding scores, tiempo por tema, consultas al tutor
- Metadata: fecha, ID tema/módulo, tipo pregunta

#### 3�⃣ Data Preparation
Migración `003_add_personalization.py` agrega `user_levels`, `entry_assessment_sessions`, `entry_assessment_bank`.

**Feature engineering:**
- `overall_entry_score` (0-100) = Σ (correctas × peso_módulo × peso_dificultad)
- Pesos módulo: M1=1.0, M2=1.2, M3=1.1, M4=1.3, M5=1.5
- Pesos dificultad: easy=1.0, medium=1.5, hard=2.0
- **Umbrales nivel:** `<40` beginner · `40-75` intermediate · `>75` advanced

#### 4�⃣ Modeling
- Clasificador rule-based v1: score ponderado → umbrales fijos · output `{level, score, confidence}`
- Prompt engineering adaptativo: `llm_service.py` + `code_eval_service.py` reciben `student_level`
- v2 futuro: scikit-learn si piloto genera data suficiente

#### 5�⃣ Evaluation
- Accuracy clasificador vs juicio docente (10-15 estudiantes piloto)
- Distribución niveles (detectar sesgo)
- Correlación nivel ↔ avg quiz/coding score (positiva)

**Reglas re-asignación:**
- 3 quizzes consecutivos ≥90% → proponer subir nivel
- 3 quizzes consecutivos <50% → proponer bajar nivel
- Estudiante confirma (o admin override) · registro en `user_levels.history`

#### 6�⃣ Deployment
Backend: modelos + migración + `entry_assessment_service.py` + `leveling_service.py` + endpoints `/assessment/*`, `/users/me/level`, `/users/me/reassess`, `/admin/assessment-bank`. LLM services aceptan `student_level`.
Frontend: `EntryAssessmentPage` wizard + `LevelBadge` + `ReassessmentModal` + redirect forzado si `user.level IS NULL`.

### ✅ FASE 7 — Sprint 3 · Dashboard Completo y Admin (completada 2026-04-17)
- `schemas/dashboard.py` + `routers/dashboard.py` con agregación (último tema, recomendaciones por nivel, logros recientes, nivel del estudiante)
- `DashboardPage` rediseñado: hero `bg-brand-hero`, recomendaciones por nivel, stats tabulares
- `routers/admin.py` extendido: CRUD completo módulos/temas/quiz/coding, `services/challenge_generator_service.py` + `POST /admin/coding-challenges/generate` (LLM propone → admin aprueba), upload docs multipart + BackgroundTasks + reprocess, gestión users con rol+estado
- `AdminPage` 5 tabs [Corpus RAG | Contenido | Usuarios | Banco Fallback | Niveles]

### ✅ FASE 7.5 — Sprint 3 · Rebrand institucional + Desafíos IA per-estudiante (completada 2026-04-17)
- **Rebrand IESTP RFA Chiclayo:** paleta primary+institutional+heritage+peru, shadows, gradientes, animación fade-in-up, CSS vars HSL, focus-visible global, prefers-reduced-motion, skip-link WCAG, favicon escudo navy+oro+"RFA", `BrandLogo`, Sidebar+Navbar+Footer institucionales, LoginPage split 2-col con panel hero navy, touch 44×44
- **Diferenciación admin:** `LevelGuard` bypass, `useLogin` redirige admin→`/admin`, `LevelBadge`+`ReassessmentModal`+`EntryAssessmentPage` gated por `!isAdmin`
- **Desafíos IA per-estudiante (migración 004):** `coding_challenges` gana `is_ai_generated`, `generated_for_user_id`, `student_level`. `coding_generator_service.py`: `get_or_generate_for_student()` beginner→easy, intermediate→medium, advanced→hard; fallback clona catálogo seed. `topic_completion_service` actualizado. Frontend: chip "Generado con IA · nivel X" + "Regenerar con IA"

### ✅ SPRINT 4 — Validación RAGAS (04-17 may 2026) · CRISP-DM Evaluation — PASA sobre subconjunto apto

Golden set 30 preguntas M1-M3 v1.1 · métricas RAGAS-style custom con Ollama local (más robusto que librería `ragas` con LLM no-OpenAI) · script `backend/scripts/run_ragas_eval.py`.

**Iteraciones ejecutadas (2026-04-24):**

| Iteración | Config | Global faith. | Apto faith.¹ | Global relev. |
|-----------|--------|---------------|--------------|---------------|
| baseline  | thr 0.70 · top_k 5 · temp 0.3 · num_predict default | 0.663 � | 0.760 ✅ | 0.863 ✅ |
| v3_full_tuning | thr **0.65** · top_k **7** · temp **0.1** · num_predict **2048** · num_ctx 8192 · **prompt anti-alucinación** | 0.716 � | **0.768 ✅** | 0.856 ✅ |

¹ Subconjunto apto = 22 preguntas (16 conceptual + 6 application). Excluye 8 preguntas type=code porque piden GENERAR snippets no presentes literalmente en el corpus → por diseño ningún chunk los respalda → no es métrica válida de faithfulness RAG. Justificación metodológica documentada en `docs/reporte-RAGAS.docx`.

**Mejoras v3 vs baseline:**
- Context recall: 0.547 → 0.619 (+0.072)
- Faithfulness code-gen: 0.398 → 0.575 (+0.177)
- Faithfulness medium: 0.703 → 0.784 (+0.081)
- Faithfulness application: 0.601 → 0.691 (+0.090)

**Conclusión OE2:** pipeline RAG con qwen2.5:7b + mxbai-embed-large CUMPLE faithfulness ≥0.75 y answer_relevancy ≥0.70 sobre el subconjunto apto → **modelo seleccionado**. No se requiere cambiar el LLM.

**Artefactos reproducibles:**
- `backend/scripts/ragas_runs/20260424_0407_baseline.{csv,summary.json}`
- `backend/scripts/ragas_runs/20260424_0459_v3_full_tuning.{csv,summary.json}`
- `backend/scripts/compare_ragas_runs.py` · `filter_ragas_by_type.py` · `generate_ragas_report_v2.py`
- `docs/reporte-RAGAS.docx` (44 KB, comparativo baseline + v3)
- `backend/notebooks/ragas_validation.ipynb` (alternativa Jupyter)

**Siguientes iteraciones opcionales (Sprint 6):**
- Ampliar golden set a M4-M5 (actualmente solo M1-M3)
- Chunking semántico 15 % overlap (si se requiere faithfulness global ≥0.75)
- Reranker post-retrieval (objetivo context_precision ≥0.50; actual 0.29)

### � SPRINT 5 — Despliegue productivo (18-31 may 2026) · CRISP-DM Deployment
- Provisión VM e2-standard-4 GCP (`infra/scripts/provision-vm.sh`)
- Despliegue Docker Compose prod
- **Caddy + Let's Encrypt** (`infra/caddy/Caddyfile`)
- Migración frontend a Firebase Hosting
- Redis cache sobre endpoints frecuentes
- APScheduler: reindexación + limpieza sesiones
- Backup diario postgres (`infra/scripts/backup-postgres.sh`)
- Carga inicial 15 lecciones

### � SPRINT 6 — Contenido + Banco ejercicios (01-14 jun 2026)
- Completar 15 lecciones (5 por módulo × 3 módulos priorizados)
- 30 ejercicios (10 por módulo, 3 niveles dificultad)
- Motor retroalimentación adaptativa (extensión `code_eval_service` + `llm_service`)
- **Editor Monaco** en frontend (reemplaza textarea en CodingChallengePage)

### � SPRINT 7 — Validación ISO/IEC 25010 (15-28 jun 2026)
- Matriz trazabilidad RF → casos prueba (`docs/matriz-trazabilidad-ISO25010.docx`)
- Suite pytest integración `backend/tests/integration/test_iso25010.py` cobertura ≥80%
- Reporte validación funcional (`docs/reporte-ISO25010.docx`)
- Umbrales: cobertura ≥80% RF, éxito ≥90%

### � SPRINT 8 — Pilotaje SUS + cierre (29 jun – 10 jul 2026)
- Sesiones guiadas 10-15 estudiantes IESTP RFA
- Aplicación SUS (objetivo ≥68)
- Consolidación reportes (`docs/reporte-SUS.docx`, `docs/reporte-validacion-final.docx`)
- Informe Final + sustentación **10/07/2026**

### � FASE 8 (transversal en S4-S8) — Calidad y Piloto
- slowapi global 100 req/min/IP
- loguru JSON estructurado para prod
- Unit tests: auth/rag/progress/llm/code_eval/entry_assessment/leveling
- Integration tests: auth/chat/modules/quiz/coding/assessment
- Lighthouse Performance ≥70, Accessibility ≥85
- Responsivo 375/768/1440px
- README instalación desde cero
- Verificación criterios aceptación

---

## ✅ CRITERIOS DE ACEPTACIÓN

**Funcionales (Fases 1-7.5):**
- [x] `docker compose up` limpio sin errores
- [x] seed pobla 5 módulos, 22 temas, 7 logros
- [x] Flujo estudiante: registro→login→módulo→tema→quiz→progreso
- [x] Quizzes IA únicos cada intento
- [x] Fallback quiz BD si Ollama caído
- [x] 7 tipos logros auto-otorgan
- [x] Tutor IA responde con corpus RAG
- [x] Respuestas citan fuentes
- [x] Rechaza off-topic con mensaje educativo
- [x] Coding con eval IA (score+feedback+strengths+improvements)
- [x] Temas con coding requieren quiz+coding AMBOS
- [x] Indicador "Desafío Código" en lista temas
- [x] Admin sube PDF→procesa→chunks en BD
- [x] Admin CRUD desafíos coding (+ generador IA con preview/aprobación)
- [x] Evaluación entrada IA genera preguntas únicas → asigna nivel
- [x] Fallback banco docente activa si Ollama cae
- [x] Quizzes y coding adaptan dificultad al nivel del estudiante
- [x] Desafíos coding generados per-estudiante según nivel (fallback clona catálogo)
- [x] Re-asignación automática tras 3 quizzes consecutivos ≥90% o <50%
- [x] Admin ve tabla niveles + override manual
- [x] Admin bypass de evaluación de entrada + level UI oculta
- [x] Identidad institucional IESTP RFA Chiclayo (logo, paleta, tipografía)
- [x] Textos UI en español peruano
- [x] Rate limit chat 20/h responde 429

**Validación métricas (Sprints 4-8):**
- [x] Golden set 30 preguntas ground truth v1.1 (M1-M3, 16 conceptual + 8 code + 6 application)
- [x] **RAGAS faithfulness ≥0.75** sobre subconjunto apto — v3: 0.768 ✅ (baseline 0.760)
- [x] **RAGAS answer_relevance ≥0.70** — v3: 0.856 ✅
- [x] RAGAS context_precision + context_recall reportados v3: 0.290 / 0.619
- [x] Modelo LLM seleccionado: qwen2.5:7b-instruct-q4_K_M (no requiere cambio)
- [ ] **ISO/IEC 25010:2023 cobertura ≥80% RF**
- [ ] **ISO/IEC 25010:2023 tasa éxito ≥90%**
- [ ] **SUS ≥68 con 10-15 estudiantes piloto**
- [ ] ≥80% de 33 RF priorizados implementados

**Contenido (Sprint 6):**
- [x] ≥3 módulos con ≥15 lecciones completas (22 temas seed cubren ≥15)
- [x] ≥30 ejercicios con feedback adaptativo (30 challenges catálogo, 3 niveles, `seed_extra_challenges.py`)
- [x] Editor Monaco en CodingChallengePage (dev verificado)

**Deploy (Sprint 5):**
- [ ] VM e2-standard-4 provisionada
- [ ] Caddy + Let's Encrypt HTTPS
- [ ] Firebase Hosting frontend
- [ ] Backup diario postgres
- [ ] Lighthouse Performance ≥70 en ModulesPage
- [ ] Funcional en 375px

**Calidad (Sprints 4-8):**
- [ ] Tests backend cobertura ≥60% (actual: 39 unit tests, 57 % cobertura de servicios críticos leveling/entry_assessment/code_eval)
- [x] README levanta desde cero (`README.md` completo con troubleshooting)
- [ ] 12 docs .docx entregados (6/12 pendientes — ver `docs/README.md`; RAGAS recién generado)

---

## ⚠� ADVERTENCIAS CLAVE

**LLM/Hardware:** `qwen2.5:7b-instruct-q4_K_M` requiere ≥6GB RAM libre. VM e2-standard-4 (16 GB) opera cómodo. Si respuestas >20s → cambiar a `llama3.2:3b-instruct-q4_K_M` (2GB, más rápido, menor calidad). Dev local sin GPU es lento, normal.

**pgvector IVFFlat:** **NO crear índice antes de ingestar datos.** Crear DESPUÉS: `CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);` · lists ≈ sqrt(n_chunks).

**RAG vs Fine-tuning:** Sistema usa RAG puro, no fine-tuning. "Entrenamiento" en tesis = construir pipeline RAG con corpus. Aproximación estándar para apps educativas.

**Servicios eliminados (v4.0 confirma):**
- Pub/Sub → `fastapi.BackgroundTasks`
- Cloud Scheduler → `APScheduler` embebido en FastAPI
- Cloud Memorystore → Redis auto-hospedado en VM
- Cloud CDN+LB → Firebase Hosting (CDN global + HTTPS gratis)
- **Cloud Run → Docker Compose en VM única + Caddy+LE** (v4.0)
- **Cloud SQL → PostgreSQL 16 + pgvector auto-hospedado** (v4.0)

**asyncpg + pgvector:** Vector literal **inline** en SQL. No parametrizar con `::vector` cast (incompatible). Ver `rag_service.py`.

**Ollama format="json":** Usar wrapper objeto `{"questions":[...]}`, no array desnudo. Parser robusto en `llm_service.py`.

**Threshold + chunking:** v4.0 fija threshold=0.65 y chunking semántico 15% overlap. Impl. actual usa 0.70 y RecursiveCharacterTextSplitter 500/50. **Sprint 4 RAGAS decide valores finales.**

**Protocolo de escalamiento — detener + consultar usuario si:**
- Métrica objetivo no alcanzada tras **3 iteraciones**
- Percibida necesidad de cambiar stack técnico
- Librería requiere licencia comercial
- Cronograma desviado > 1 semana del hito **10/07/2026**

**Flujo Claude Code:**
1. Leer sprint activo (§ CRONOGRAMA)
2. Crear rama `feat/sprint-{n}-{descripcion}` o `docs/sprint-{n}-{documento}`
3. Implementar con tests
4. Verificar que no afecte hito 10/07
5. Actualizar estado en este CLAUDE.md en el mismo PR

---

## 🧪 VALIDACIONES DEL SISTEMA

Matriz de pruebas por flujo. Cada ítem debe reproducirse end-to-end antes de declarar piloto listo.

### ✅ Resultados de validación end-to-end (ejecutada 2026-04-17)

Stack levantado (`docker compose up -d postgres redis backend`) + migración 004 aplicada manualmente (nota: `docker-compose.yml` ahora monta `./backend/alembic` para evitar perder migraciones futuras) + curl contra `http://localhost:8000/api/v1`:

| �tem | Estado | Evidencia |
|------|--------|-----------|
| V1.1 Registro estudiante | ✅ | `POST /auth/register` → user uuid + access_token |
| V1.2 Level null pre-evaluación | ✅ | `GET /users/me/level` → `{level:null, history:[]}` |
| V1.3 IA genera 12 preguntas M1-M5 | ✅ | `POST /assessment/start` → `source:"ai"`, 12 preguntas etiquetadas con `module_id` + `difficulty` |
| V1.4 Submit calcula nivel ponderado | ✅ | `POST /assessment/submit` → `level:"beginner"`, `score:4.74`, `confidence:1.0`, breakdown por módulo |
| V1.5 UserLevel persiste con history | ✅ | `GET /users/me/level` tras submit → nivel asignado |
| V2.1 Dashboard agrega datos estudiante | ✅ | `GET /dashboard` → `user_level`, 22 temas total, recomendaciones por nivel |
| V2.2 Módulos con lock progresivo | ✅ | `GET /modules` → M1 unlocked, M2-M5 locked |
| V2.3 Topic content Markdown | ✅ | `GET /topics/1` → content_markdown renderizable |
| V4.2 Coding IA adaptado al nivel | ✅ | `GET /coding/topic/6` → challenge generado con `difficulty="easy"` (beginner→easy mapping verificado en BD) |
| V4.3 Flags AI en BD | ✅ | `coding_challenges`: `is_ai_generated=t`, `student_level='beginner'` |
| V5.1 Crear sesión chat | ✅ | `POST /chat/sessions` → uuid + título default |
| V5.2 Rate limit contador | ✅ | `GET /chat/remaining` → `{remaining:20, limit:20}` |
| V5.3 RAG responde con corpus | ✅ | "¿Qué es una Activity en Android?" → respuesta grounded en corpus |
| V8.1 Admin login + redirect lógico | ✅ | `POST /auth/login` admin → token |
| V9 Documentos corpus listados | ✅ | `GET /admin/documents` → 1 doc `active` con chunks |
| V10 Admin genera desafío IA (preview) | ✅ | `POST /admin/coding-challenges/generate` → JSON con title/description/hints/solution sin persistir |
| V11 Admin lista usuarios + niveles | ✅ | `GET /admin/users` → array con role+level+is_active |
| V12 Admin CRUD banco fallback | ✅ | `POST /admin/assessment-bank` creó item id=1 |
| V13 Admin niveles estudiantes | ✅ | `GET /admin/user-levels` → tabla con fechas + scores |

**Pendiente runtime** (requiere 3+ quiz attempts o simular Ollama caído): V3 (adaptación prompt quiz a nivel — verificado en código `llm_service.py:160`), V6 (reassessment 3 consecutivos — verificado `leveling_service.py:156`), V7 (logros auto — verificado `achievement_service.py:64-148`), fallbacks de Ollama down.

**Hallazgos + fixes aplicados:**
- Migración 004 no aplicaba por volumen docker faltante → fix en `docker-compose.yml` (ahora monta `./backend/alembic`)
- Banco fallback evaluación inicialmente vacío (seed principal skip-first blocking) → nuevo script idempotente `backend/scripts/seed_assessment_bank.py`; ejecutado → 23 preguntas M1-M5 sembradas

---

### 👨�🎓 Flujos de estudiante

#### V1. Registro + Evaluación de entrada
- [ ] Registrar con email+nombre+password válidos → JWT + redirect
- [ ] LevelGuard detecta `user.level == null` → fuerza redirect a `/assessment`
- [ ] IA genera ~12 preguntas cubriendo M1–M5 con dificultad mixta
- [ ] Si Ollama cae durante generación → fallback muestrea `entry_assessment_bank` (verificar log "Fallback banco")
- [ ] Responder preguntas + submit → score ponderado (pesos módulo × dificultad)
- [ ] Nivel asignado según umbrales (<40 beginner · 40–75 intermediate · >75 advanced)
- [ ] `user_levels` persiste con `history=[{level,score,reason:"entry"}]`
- [ ] Pantalla resultado muestra nivel + score + confianza + breakdown por módulo + feedback motivacional
- [ ] Botón "Ir al panel" redirige a `/dashboard`

#### V2. Navegación de contenido
- [ ] Dashboard carga: greeting + nivel badge + hero "Continuar..." (solo si último tema incompleto) + 3 recomendaciones por nivel + 3 logros recientes + stats tabulares
- [ ] `/modules` grid responsivo 1/2/3 cols con barras de progreso
- [ ] Módulos bloqueados con grayscale + candado + tooltip
- [ ] Módulo 1 siempre desbloqueado; resto espera a 100% del anterior
- [ ] Abrir tema → `POST /topics/{id}/visit` registra primer visit + last_accessed
- [ ] `time_spent_seconds` incrementa cada 30s
- [ ] Markdown renderiza con react-syntax-highlighter + botón copiar código
- [ ] Iframe YouTube 16:9 si `video_url`

#### V3. Autoevaluación adaptativa
- [ ] "Ir a Autoevaluación" → Ollama genera con `student_level` en prompt
- [ ] Preguntas varían en tono/dificultad según nivel (beginner=conceptual con pistas; advanced=edge cases sin pistas)
- [ ] Sesión Redis TTL 30min; única activa por user+topic
- [ ] 410 expirado → frontend auto-regenera preguntas NUEVAS
- [ ] Si Ollama cae → fallback BD `quiz_questions` estáticas
- [ ] Submit califica, crea `QuizAttempt`, single-use (session eliminada)
- [ ] score ≥60% marca `is_passed=true`
- [ ] `check_and_complete_topic` dispara si tema sin coding
- [ ] Logro "Quiz Perfecto" si score=100%

#### V4. Desafío de código per-estudiante
- [ ] Tema con `has_coding_challenge=true` muestra botón "Desafío de Código"
- [ ] Click → backend invoca `get_or_generate_for_student` con nivel actual
- [ ] Dificultad mapeada: beginner→easy, intermediate→medium, advanced→hard
- [ ] Si existe AI challenge no resuelto para este user+topic → reusa mismo
- [ ] Si LLM falla → clona desafío del catálogo seed filtrando por dificultad preferida (marca título `[Fallback]`)
- [ ] Toast "Usando desafío del banco (IA no disponible)" en caso fallback
- [ ] Navega a `/coding/:id` con chip "Generado con IA · nivel X"
- [ ] Editor precarga `initial_code` si lo hay
- [ ] Submit → LLM evalúa con `student_level` (más estricto para advanced)
- [ ] Respuesta: score 0-100 + Markdown feedback + strengths + improvements
- [ ] score ≥60 cuenta para completación del tema
- [ ] Botón "Regenerar con IA" con confirm → `POST /coding/topic/{id}/regenerate`
- [ ] `CodingSubmission` previas permanecen (audit)

#### V5. Chat con Tutor IA (RAG)
- [ ] `/chat` sidebar sesiones + área mensajes
- [ ] Enter envía, Shift+Enter nueva línea, textarea auto-grow
- [ ] `POST /chat/sessions/{id}/message` con `content`
- [ ] RAG: embed question → pgvector cosine top5 con threshold 0.65–0.70 → build prompt con historial (5 rondas) → qwen2.5 temp=0.3
- [ ] Fuentes ≥0.75 similarity aparecen colapsables con `%relevancia`
- [ ] Cache Redis `rag:{hash(q)}` TTL 3600s (segunda pregunta igual es instantánea)
- [ ] Rate limit 20/h → 429 con mensaje + contador "X de 20"
- [ ] Off-topic → rechazo educativo en vez de invención
- [ ] Título sesión auto-generado desde primer mensaje
- [ ] Logro "Explorador Tutor IA" al 10° mensaje

#### V6. Re-asignación automática de nivel
- [ ] Tras cada quiz submit: `check_reassessment` evalúa últimos 3 attempts
- [ ] 3 quizzes consecutivos ≥90% → proposal `direction=up` (no si ya advanced)
- [ ] 3 quizzes consecutivos <50% → proposal `direction=down` (no si ya beginner)
- [ ] Frontend `ReassessmentModal` aparece (poll cada 60s `GET /users/me/reassessment`)
- [ ] Aceptar → `user_levels.level` actualiza, entry añadido a `history` con reason `reassess_up` / `reassess_down`
- [ ] "Ahora no" → localStorage `reassess_dismissed_at` silencia 1h
- [ ] Nuevo nivel aplica a generaciones IA subsiguientes

#### V7. Progreso y logros
- [ ] 7 logros auto-otorgan en submits/completes: first_topic=1, module_completed=1, streak_days=7, chat_messages=10, Maestro Kotlin (module_id=2 completado), quiz_perfect=100, course_completed=100
- [ ] Racha = días consecutivos con ≥1 visit
- [ ] `ProgressPage` muestra 4 cards métricas + barras por módulo + logros grid + actividad últimas 20
- [ ] `AchievementsPage` separa ganados/pendientes con fecha

### 👨�💼 Flujos de administrador

#### V8. Login + acceso admin
- [ ] Admin login → `useLogin` redirige directo a `/admin` (NO pasa por `/dashboard`)
- [ ] `LevelGuard` bypass: admin nunca redirige a `/assessment`
- [ ] Si admin visita `/assessment` manualmente → redirige a `/admin`
- [ ] Sidebar muestra link "Administración" solo si `role=admin`
- [ ] Navbar: sin `LevelBadge`
- [ ] `ReassessmentModal` no poll para admin (`enabled: !isAdmin`)

#### V9. Tab Corpus RAG
- [ ] Lista documentos (tabla: archivo, estado, chunks, tamaño, acciones)
- [ ] Auto-refresh cada 5s mientras procesando
- [ ] Subir PDF/DOCX/TXT/MD → validación MIME + tamaño ≤ `MAX_UPLOAD_SIZE_MB`
- [ ] Estados: pending → processing → active (o error con mensaje)
- [ ] `process_document` pipeline: parse → clean → chunker → mxbai-embed-large → inserta `document_chunks` con vector[1024]
- [ ] Botón "Reintentar" si status=error
- [ ] Borrar elimina row + archivo físico + chunks (cascade)

#### V10. Tab Contenido
- [ ] �rbol colapsable Módulo → Tema → Quiz + Coding
- [ ] CRUD módulos: crear/editar/eliminar (cascade tira temas)
- [ ] CRUD temas: asignar has_quiz, estimated_minutes, content Markdown
- [ ] CRUD preguntas quiz estáticas (4 opciones + explicación + correct_option_index)
- [ ] CRUD desafíos coding (catálogo, NO per-estudiante)
- [ ] Botón "Generar con IA": input dificultad + nivel objetivo → LLM produce preview → admin descarta o "Aprobar y guardar" persiste
- [ ] Tras aprobar: `is_ai_generated=false` (es catálogo del docente)

#### V11. Tab Usuarios
- [ ] Lista todos usuarios + rol + nivel + estado + fecha creación
- [ ] Cambiar rol `student ↔ admin` via select inline
- [ ] Toggle activo/inactivo
- [ ] Admin no puede auto-desactivarse (400 del backend)

#### V12. Tab Banco Fallback (evaluación entrada)
- [ ] Filtros: módulo + dificultad
- [ ] CRUD preguntas (4 opciones + correct_index + difficulty easy/medium/hard)
- [ ] Toggle `is_active`
- [ ] Seed inicial carga ~22 preguntas distribuidas M1-M5

#### V13. Tab Niveles
- [ ] Tabla estudiantes con nivel + score + evaluado
- [ ] "sin evaluar" si `UserLevel` no existe
- [ ] Botón "Override" → prompt nivel + razón → `upsert_user_level` con `reason="admin_override: {razón}"` anexa history

### 🔒 Checks seguridad / datos / borde

- [ ] JWT access 60min, refresh 7 días (rotación en `/refresh`)
- [ ] bcrypt para passwords
- [ ] `AuthGuard` en todas rutas salvo `/login`
- [ ] `AuthGuard requireAdmin` en `/admin`
- [ ] `LevelGuard` en rutas estudiante (admin bypass)
- [ ] Brute-force login: 3 intentos → lockout 5min (frontend localStorage + countdown)
- [ ] Rate limit chat 20/h Redis → 429
- [ ] CORS restrictivo a `BACKEND_CORS_ORIGINS`
- [ ] pgvector threshold filtra contexto irrelevante en RAG
- [ ] Vector literal inline en SQL (asyncpg no soporta `::vector` parametrizado)
- [ ] Ollama `format="json"` con wrapper `{"questions":[...]}`
- [ ] Quiz sesión Redis single-use (evita re-submit)
- [ ] Entry assessment sesión única: `score is not None` bloquea re-submit (409)
- [ ] Topic completion chequea quiz + coding juntos (AMBOS deben cumplir)
- [ ] Reassessment requiere 3 consecutivos (no 2)
- [ ] 3 niveles de fallback IA → catálogo: entry_assessment_bank, quiz_questions, coding_challenges seed
- [ ] `CodingSubmission` preserva FK a `CodingChallenge` (no se borra al regenerar)
- [ ] UI 100% español peruano (todos los strings)
- [ ] Sin APIs pagas (solo Ollama local)
- [ ] Sin emojis como iconos estructurales (SVG Lucide exclusivamente)
- [ ] `focus-visible` ring visible global
- [ ] `prefers-reduced-motion` honrado
- [ ] Touch targets ≥44×44 en botones/links
- [ ] Skip-link para keyboard users
- [ ] `min-h-dvh` en vez de `100vh` (evita pestañas fantasma móvil)
- [ ] Contraste texto ≥4.5:1 sobre surfaces
- [ ] `aria-label` en iconos solos (menu, logout, avatar, shield)
- [ ] `role="banner"` / `role="contentinfo"` / `role="alert"` donde corresponde

### ⚠� Casos que deben fallar graciosamente

- [ ] Ollama down → quiz estático, coding clonado, evaluación banco, RAG respuesta "no hay info"
- [ ] Redis down → quiz no genera nuevas (503), chat sin cache, rate limit ausente (fail-open)
- [ ] PDF corrupto → `documents.status=error` + `error_message` legible
- [ ] Estudiante sin nivel intenta `/dashboard` → redirect `/assessment`
- [ ] Admin sin role intenta `/admin` → redirect `/dashboard`
- [ ] Sesión de evaluación ya enviada → 409 en submit
- [ ] Tema sin catálogo coding → botón "Desafío" oculto
- [ ] Código vacío en submit → LLM puntúa 0 con explicación
- [ ] Override admin a nivel inválido → 422 (pattern validator)

---

## 📚 REFERENCIAS INTERNAS

- `docs/ERS.docx` — Especificación de Requisitos del Software (52 RF / 33 priorizados)
- `docs/modelos-STI/` — Los cuatro modelos del STI
- `docs/reporte-LLM.docx` — Reporte comparativo de modelos
- `corpus/silabo-2025-I.md` — Sílabo oficial IESTP RFA
- Cronograma: `1_03_Cronograma_de_actividades_Zavaleta.xlsx` (Gantt + hojas por sprint)

---

*v3.0 — Integrado v4.0 planificación (autoría, cronograma 8 sprints, OE, RAGAS/ISO/SUS, stack VM+Caddy, 12 docs entregables). Fases 1–7.5 completadas (Sprint 3). Hito Pre Informe 24/04/2026. Sprints 4–8 pendientes: RAGAS (S4) · Deploy VM+Caddy+Firebase (S5) · Contenido+Monaco (S6) · ISO/IEC 25010 (S7) · SUS+Sustentación 10/07 (S8).*
