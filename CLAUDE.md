# CLAUDE.md — Tutor IA Generativa · Aplicaciones Móviles IESTP RFA

Tesis pregrado USAT (Escuela Ingeniería Sistemas y Computación). STI con RAG privado para curso **Aplicaciones Móviles** (Android/Kotlin) del IESTP "República Federal de Alemania", Chiclayo.

**Autor (tesista):** Roger Alessandro Zavaleta Marcelo · **Asesora (USAT):** Mg. Reyes Burgos, Karla · **Coordinador piloto (IESTP RFA):** Téc. Xavier Benites Marín *(coordina acceso + pertinencia pedagógica, NO asesor tesis)*.

**Inicio desarrollo:** 23 mar 2026 · **Hito Pre Informe:** 24 abr 2026 (Sprint 3) · **Sustentación final:** 10 jul 2026.

**Piloto:** 10–15 estudiantes IESTP RFA · **Presupuesto:** S/. 3,170.00.

Estudiantes: estudian 5 módulos, consultan tutor IA privado (RAG), autoevalúan, ven progreso gamificado.

> Detalle histórico Fases 1-7.5 + Sprint 4 + matriz validación V1-V13 movido a `docs/CLAUDE-archive.md`.

**Reglas absolutas:**
- LLM 100% privado vía Ollama. Nunca APIs pagas (OpenAI/Anthropic/Gemini).
- Sin fine-tuning: "entrenar el modelo" = construir pipeline RAG sobre corpus del sílabo.
- Conocimiento dominio solo vía RAG.
- UI **español peruano**; código en **inglés** (variables/funciones/comentarios técnicos); docs + mensajes usuario en español.
- Evaluación: **RAGAS** (instrumento: librería ragas oficial, juez independiente `llama3.1:8b`) recuperación (Context Precision ≥0.70, Context Recall ≥0.75) + generación (Faithfulness ≥0.65, Answer Relevancy ≥0.65, Answer Correctness ≥0.55, umbrales para LLM 7B local) **[OE2]** · **ISO/IEC 25010:2023 + 25023:2016** (completitud funcional ≥0.95, corrección funcional ≥0.90, pertinencia funcional ≥0.90 por ≥2 jueces) **[OE5]** · **rendimiento académico** pretest/postest con **t de Student para muestras relacionadas (p<0.05)** **[OE4]**. *(SUS retirado: no figura en el mapeo oficial.)*
- Stack cerrado: **sin** Pub/Sub, Cloud SQL, Memorystore, Cloud Scheduler, Cloud Run. 1 VM Compute Engine + Firebase Hosting.
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- Verificación externa antes de citar precios/versiones/comandos Ollama: advertir usuario verifique fuente oficial.

---

## 🎯 OBJETIVOS ESPECÍFICOS (5 OE — versión oficial)

> Fuente única de verdad: documento oficial de objetivos y mapeo (V.2.1). Los enunciados quedan limpios; los umbrales viven en los indicadores.

**Objetivo general:** Desarrollar un tutor con IA generativa aplicado a la asignatura de aplicaciones móviles para mejorar el rendimiento académico de estudiantes del IESTP "RFA".

| OE | Enunciado | Resultado esperado | Indicadores objetivamente verificables |
|----|-----------|--------------------|-----------------------------------------|
| OE1 | Seleccionar el LLM de código abierto y el modelo de embeddings para generación y recuperación de respuestas en español del dominio de Aplicaciones Móviles | R1.1 LLM seleccionado · R1.2 embeddings seleccionado | LLM: Likert media ≥4.0, Accuracy ≥0.70 (≥30 preguntas). Embeddings: nDCG@10 ≥0.55, Recall@5 ≥0.70, MRR@10 ≥0.65. |
| OE2 | Validar la precisión de recuperación y la fidelidad de generación del pipeline RAG mediante RAGAS sobre un golden set representativo | R2.1 recuperación y generación del RAG validadas | Recuperación: Context Precision ≥0.70, Context Recall ≥0.75. Generación (umbrales LLM 7B local): Faithfulness ≥0.65, Answer Relevancy ≥0.65, Answer Correctness ≥0.55. Instrumento: librería ragas oficial + juez independiente. Golden set 50 ítems M1-M5 |
| OE3 | Desplegar el sistema tutor sobre Google Compute Engine en contenedores Docker, garantizando rendimiento, disponibilidad y trazabilidad | R3.1 sistema desplegado e integrado en GCE | Rendimiento: TTFT P95 ≤2.5s, ITL P95 ≤250ms, e2e P95 ≤8s, throughput ≥8 tok/s (conc. 3). Disponibilidad: uptime ≥99%, 5xx ≤2%, MTBF ≥48h, health checks ≥99%. Cobertura RF ≥0.95, citación ≥0.90, exactitud de citación ≥0.85 |
| OE4 | Contrastar la mejora del rendimiento académico mediante diseño pre-experimental con pretest y postest aplicado al grupo piloto | R4.1 mejora del rendimiento evidenciada estadísticamente | Prueba **t de Student para muestras relacionadas (pareada) con p < 0.05** sobre instrumento pretest/postest |
| OE5 | Validar la adecuación funcional del sistema conforme a ISO/IEC 25010:2023 | R5.1 adecuación funcional validada | ISO/IEC 25023:2016: completitud funcional ≥0.95, corrección funcional ≥0.90, pertinencia funcional ≥0.90 (por ≥2 jueces expertos) |

**ERS:** 52 RF en 8 módulos; **33 priorizados** alineados ISO/IEC 25010.

**Nota de alcance:** los cuatro modelos del STI y la estructuración del contenido instruccional + ejercicios siguen siendo trabajo real del sistema, pero **ya no son OE independientes**: pasan a ser insumos de OE3 (desarrollo/despliegue) y del instrumento de OE4.

---

## 📅 CRONOGRAMA — 8 SPRINTS × 2 SEMANAS (SCRUM + CRISP-DM)

| # | Período | CRISP-DM | Estado | Foco |
|---|---------|----------|--------|------|
| 1 | 23 mar – 05 abr 2026 | — | ✅ | ERS + modelado de diseño (dominio/pedagógico, insumo) + arquitectura + docker-compose |
| 2 | 06 abr – 19 abr 2026 | BU + DU | ✅ | Evaluación LLM/embeddings + backend core + frontend base |
| 3 | 20 abr – 03 may 2026 | DP + Modeling | ✅ | Pipeline RAG + personalización (Fases 5–7.5). **Hito 24/04 Pre Informe.** |
| 4 | 04 may – 17 may 2026 | Evaluation | ✅ | **RAGAS [OE2]** validado (may 2026): juez independiente llama3.1 + rerank cross-encoder + librería ragas oficial. Recuperación context_precision 0.876, context_recall 0.812; generación faithfulness 0.706, answer_relevancy 0.707, answer_correctness 0.609 → 5/5 cumplen. Ver `docs/reporte-RAGAS.md` |
| 5 | 18 may – 31 may 2026 | Deployment | 🔄 | VM e2-standard-4 + Docker Compose + Caddy+LE + Firebase Hosting + backup + Redis cache + APScheduler |
| 6 | 01 jun – 14 jun 2026 | — | ⏳ | 15 lecciones + 30 ejercicios + motor adaptativo + editor Monaco |
| 7 | 15 jun – 28 jun 2026 | — | ⏳ | **ISO/IEC 25010:2023 [OE5]**: matriz trazabilidad + casos de prueba + completitud ≥0.95, corrección ≥0.90, pertinencia ≥0.90 (≥2 jueces) + reporte |
| 8 | 29 jun – 10 jul 2026 | — | ⏳ | **Pretest/postest [OE4]** grupo piloto 10-15 estudiantes + **t de Student pareada (p<0.05)** + consolidación + Informe Final + sustentación |

Metodología: **SCRUM** global; **CRISP-DM** solo sprints pipeline LLM/RAG (2-5).

---

## 🛠 STACK (decisiones cerradas — no cambiar sin justificación cuantitativa)

### Frontend
React 18 SPA + **TypeScript estricto**, Vite 5, Tailwind 3, shadcn/ui, Zustand, TanStack Query, React Router v6, react-hot-toast, Lucide. ESLint + Prettier. Componentes funcionales con hooks. Deploy: **Firebase Hosting** (NO Cloud Run, NO Cloud Storage directo).

### Backend
FastAPI + Python 3.12, SQLAlchemy 2.0 async + asyncpg + Alembic, Pydantic v2, LangChain + langchain-ollama, slowapi, loguru (JSON estructurado), APScheduler (reindexación + limpieza sesiones), python-jose + passlib[bcrypt], httpx, pypdf, python-docx. **FastAPI BackgroundTasks** en vez de Pub/Sub. PEP 8 + type hints obligatorios + `async/await` + pytest + ruff.

### IA — LLM + Embeddings + RAG
- Servidor: **Ollama** auto-hospedado
- LLM: `qwen2.5:7b-instruct-q4_K_M` (seleccionado tras benchmark Sprint 2 — ver archive)
- Embeddings: `mxbai-embed-large` (1024 dim)
- Chunking: **semántico 15% overlap** (objetivo v4.0) · impl. actual `RecursiveCharacterTextSplitter(500/50)`
- Retrieval: coseno, top-k=5, **threshold=0.65** (v3 RAGAS) · `.env` aún 0.70 — ajustar
- Framework validación: **RAGAS [OE2]** (librería oficial + juez independiente `llama3.1:8b`) — recuperación (context_precision ≥0.70, context_recall ≥0.75) + generación (faithfulness ≥0.65, answer_relevancy ≥0.65, answer_correctness ≥0.55, umbrales LLM 7B local)

### Base de datos y caché
- **PostgreSQL 16 + pgvector** auto-hospedado (NO Cloud SQL)
- **Redis 7** auto-hospedado (NO Memorystore)
- Corpus: filesystem VM bajo `/data/corpus/` (módulos 1-3 indexados Sprint 2)

### Infraestructura
- 1 VM **Google Compute Engine e2-standard-4 (16 GB RAM)**
- Orquestación: Docker Compose
- TLS: **Caddy + Let's Encrypt**

### Seguridad
JWT 60 min access / 7 días refresh (rotación en `/refresh`), bcrypt, CORS restrictivo a `BACKEND_CORS_ORIGINS`, brute-force lockout 3 intentos × 5 min (frontend localStorage + countdown), rate limit chat 20/h (Redis) + API 100/min (slowapi global), Secret Manager, HTTPS Caddy.

### Pipeline RAG

**Ingesta:** Archivo (PDF/DOCX/TXT/MD) → BackgroundTask FastAPI → parser (pypdf/python-docx/UTF-8) → chunker (semántico 15% o Recursive 500/50) → mxbai-embed-large → vector[1024] → pgvector `document_chunks`.

**Consulta:** Pregunta → embedding → pgvector cosine (top_k=5, threshold 0.65–0.70) → chunks + historial (5 rondas) → prompt aumentado (system pedagógico + contexto + historial + pregunta) → qwen2.5 temperature=0.3 num_ctx=4096 → caché Redis `rag:{hash(q)}` TTL 3600s → respuesta con **citas trazables** (similarity ≥0.75).

---

## 📁 ESTRUCTURA

```
tutor-ia-rfa/
├── CLAUDE.md, README.md, .env.example, .env, .gitignore
├── docker-compose.yml              # stack completo dev
├── docker-compose.vm.yml           # Ollama+Redis en VM prod
├── backend/
│   ├── Dockerfile, requirements.txt, alembic.ini, pyproject.toml
│   ├── alembic/versions/           # 001_initial → 004_ai_coding_flags
│   ├── notebooks/                  # ragas_validation.ipynb (S4) · pretest_postest_analysis.ipynb (S8)
│   ├── tests/
│   │   ├── fixtures/golden_set.json    # S4 · 30 preguntas ground truth
│   │   ├── unit/
│   │   └── integration/test_iso25010.py  # S7
│   ├── scripts/                    # seed_db.py · seed_assessment_bank.py · ingest_course_docs.py · run_ragas_eval.py
│   └── app/
│       ├── main.py · config.py · database.py · dependencies.py
│       ├── models/                 # user · module · topic · quiz · progress · achievement · chat · document · coding · user_level · entry_assessment · assessment_bank
│       ├── schemas/
│       ├── routers/                # auth · users · modules · topics · quiz · progress · achievements · chat · dashboard · admin · coding · assessment
│       ├── services/               # auth · progress · achievement · rag · llm · embed · ingest · code_eval · topic_completion · entry_assessment · leveling · challenge_generator · coding_generator
│       └── utils/                  # security (JWT+bcrypt) · chunking · logger
├── frontend/
│   ├── Dockerfile · .firebaserc · firebase.json · package.json · vite/tsconfig/tailwind/postcss/components.json
│   └── src/
│       ├── main.tsx · App.tsx · vite-env.d.ts
│       ├── api/ · store/ · components/{ui,layout,auth,brand,modules,topics,quiz,chat,assessment,achievements}
│       ├── pages/                  # Login · Dashboard · Modules · ModuleDetail · Topic · Chat · Progress · Admin · Quiz · Achievements · CodingChallenge · EntryAssessment
│       ├── hooks/ · types/ · lib/utils.ts
├── ollama/modelfile-qwen2.5
├── corpus/                         # módulo-1/2/3 + sílabo (VM: /data/corpus/)
├── scripts/                        # seed_db.py · setup_ollama.sh · ingest_course_docs.py
├── infra/
│   ├── caddy/Caddyfile             # S5
│   └── scripts/{provision-vm.sh, deploy.sh, backup-postgres.sh}
├── benchmarks/                     # S2 · 3 LLMs × 50 prompts + 2 embeddings × 20 queries · ver archive
└── docs/                           # entregables .docx (mapeados a OE) + CLAUDE-archive.md
```

---

## 🗄 ESQUEMA BD

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

-- CODING (Fases 5.5 + 7.5)
coding_challenges(id, topic_id FK, title, description, difficulty, hints, reference_solution, is_ai_generated, generated_for_user_id FK, student_level, ...)
coding_submissions(id, user_id FK, challenge_id FK, code, score, feedback, strengths, improvements, submitted_at)

-- PERSONALIZACIÓN (Fase 6)
user_levels(user_id UUID PK FK, level VARCHAR(20), entry_score FLOAT, assessed_at, last_reassessed_at, history JSONB)
entry_assessment_sessions(id UUID PK, user_id FK, questions JSONB, answers JSONB, score FLOAT, computed_level, created_at)
entry_assessment_bank(id SERIAL PK, module_id FK, question_text, options JSONB, correct_index, difficulty 'easy'|'medium'|'hard', created_by FK, is_active)

-- ÍNDICES
CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
-- ⚠ Crear DESPUÉS de ingestar datos. lists ≈ sqrt(n_chunks)
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

### `/tutor` (acompañamiento proactivo — Fases 1-4)
- `GET /nudges?context=&topic_id=&module_id=&score=` → `{nudges:[{id,tone,icon,title,message,cta_label,cta_route}]}`. Motor determinista (reglas + plantillas, sin LLM). `context ∈ {dashboard,topic,module,quiz_result,coding_result,assessment_result}`. Caché Redis TTL 30s salvo contextos `*_result`. Los contextos `*_result` reciben `score` y no consultan BD (refuerzo inmediato post-respuesta).
- `GET /companion` → `{needs_assessment, position{module_id,module_title,progress_pct,topics_done,topics_total,course_completed}, greeting, diagnostic{weak[],practice[],next_action}, resources[≤3]}`. Posición del estudiante + diagnóstico determinista del módulo actual (Fase 5). Caché Redis TTL 60s, invalidada al completar tema/quiz/coding. Sin LLM.

### `/resources` (recursos de aprendizaje — Fase 3)
- `GET /resources?module_id=&topic_id=` → `LearningResource[]` activos (estudiante). Recursos curados (videos/libros/artículos). El LLM nunca los genera.
- Admin CRUD: `GET/POST/PUT/DELETE /admin/resources` (role=admin).

### `/modules`
- `GET /` → lista con `progress_pct, is_locked, total_topics, completed_topics`
- `GET /{id}` → Module + temas con `status: not_started|in_progress|completed`

### `/topics`
- `GET /{id}` → contenido + progreso + `has_coding_challenge`
- `POST /{id}/visit`, `POST /{id}/complete`, `POST /{id}/time` body `{seconds}`

### `/quiz` (IA genera preguntas, fallback BD estática)
- `GET /topic/{topic_id}` → `{session_id, questions}` (LLM con `student_level`, Redis TTL 30min)
- `POST /topic/{topic_id}/submit` body `{session_id, answers}` → `{score, is_passed, feedback, attempt_id}` · 410=expirada, 503=caído
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
- Niveles: `GET /user-levels`, `POST /user-levels/{id}/override`
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
3. pgvector cosine: `1 - (embedding <=> :query_vec::vector) AS similarity`, threshold 0.65–0.70, top 5
4. Sin chunks → mensaje educativo rechazo
5. Build context (chunks con fuente) + history (últimas 5 rondas)
6. `OllamaLLM(qwen2.5:7b-instruct-q4_K_M, temperature=0.3, num_ctx=4096).ainvoke(prompt)`
7. Sources con similarity≥0.75 → `{content_preview, document_name, similarity}`
8. Cachear TTL 3600s

**System prompt:** tutor español peruano, responde desde CONTEXTO, rechaza off-topic, ejemplos Kotlin en ```kotlin, admite incertidumbre, no inventa.

### `services/ingest_service.py`

`IngestService.process_document(doc_id, file_path, db)` (BackgroundTask):
1. status='processing' → parse (pypdf/python-docx/UTF-8) → clean (normaliza espacios, max 2 `\n`)
2. `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, separators=["\n\n","\n",". "," ",""])`
3. `OllamaEmbeddings.aembed_documents(chunks)` → guardar chunks+vectores → status='active' / 'error'

### `services/llm_service.py` (Quiz IA)
ChatOllama `format="json"`, `temperature=0.7`. Acepta `student_level`. ⚠ **Wrapper `{"questions":[...]}`** no array desnudo (incompatible con format=json). Parser maneja ambos. Trunca contenido 3500 chars.

### `services/code_eval_service.py`
LLM evalúa código. Criterios: corrección 40%, buenas prácticas 25%, eficiencia 20%, legibilidad 15%. Score 0-100 + feedback Markdown + strengths + improvements. `format="json"`. Acepta `student_level`. Solución referencia como guía.

### `services/entry_assessment_service.py` + `leveling_service.py` (Fase 6)
Genera evaluación entrada vía LLM (fallback banco docente). Score ponderado: pesos módulo M1=1.0…M5=1.5, dificultad easy=1.0/medium=1.5/hard=2.0. Umbrales: `<40` beginner · `40–75` intermediate · `>75` advanced. `check_reassessment` evalúa últimos 3 quizzes → propuesta up/down.

---

## 📊 EVALUACIÓN Y VALIDACIÓN

### OE1 — Selección LLM + embeddings — ✅ VALIDADO
- Reportes: `docs/reporte-LLM.docx` (Sprint 2: comparativa 3 LLM + 2 embeddings, Likert/latencia/VRAM) + `docs/reporte-OE1-metricas-oficiales.docx` (indicadores oficiales sobre golden set 50 + pipeline producción). Harness: `backend/scripts/oe1_{generation,retrieval}.py`.
- **Generación:** Accuracy 0.72 ✅ (≥0.70) · Likert media 4.325 ✅ (≥4.0), juez independiente `llama3.1:8b`.
- **Recuperación:** Recall@5 0.72 ✅ (≥0.70) · MRR@10 0.684 ✅ (≥0.65) · nDCG@10 0.686 ✅ (≥0.55), con rerank cross-encoder.
- **Criterio OE1 = Accuracy+Likert (generación) + Recall@5/MRR@10/nDCG@10 (recuperación), todos ✅ → OE1 validado.** Consistente con OE2/RAGAS (context_recall 0.812). Anotación multi-evaluador humano = trabajo futuro.

### RAGAS [OE2] — ✅ VALIDADO
- Golden set 50 ítems (M1-M5) → `backend/tests/fixtures/golden_set.json`. Juez **independiente** `llama3.1:8b` (≠ generador qwen2.5 → elimina sesgo de auto-preferencia).
- Instrumento: librería `ragas==0.2.6` vía `backend/scripts/run_ragas_lib_eval.py` (parche compat ollama: mueve `temperature`→`options`).
- **Criterio = 5 métricas:** recuperación → context_precision ≥0.70, context_recall ≥0.75 (canónicos). Generación → faithfulness ≥0.65, answer_relevancy ≥0.65, answer_correctness ≥0.55 (umbrales para la clase de modelo 7B open-source self-hosted sin fine-tuning).
- **Estado (ragas-lib oficial, rerank cross-encoder on):** context_precision 0.876 ✅ · context_recall 0.812 ✅ · faithfulness 0.706 ✅ · answer_relevancy 0.707 ✅ · answer_correctness 0.609 ✅ → **5/5 cumplen → OE2 validado**.
- Recuperación validada con métricas canónicas; generación dentro del rango esperable para un 7B local sin fine-tuning (mejora vía modelo mayor/fine-tuning = trabajo futuro). Reporte: `docs/reporte-RAGAS.md`.

### ISO/IEC 25010:2023 + 25023:2016 [OE5] (Sprint 7)
- Matriz trazabilidad caso de prueba ↔ RF ↔ subcaracterística ISO → `docs/matriz-trazabilidad-ISO25010.md` (exportar .docx pre-sustentación).
- Métricas oficiales (ISO/IEC 25023:2016): **completitud funcional X=A/B ≥0.95** · **corrección funcional X=1−A/B ≥0.90** · **pertinencia funcional X=A/B ≥0.90** (evaluada por ≥2 jueces expertos sobre la matriz).
- Guardian `backend/tests/integration/test_iso25010.py` (5 tests): cada RF con ≥1 test real + archivos existen + numeración secuencial.
- Estado interno: 33/33 RF implementados · 396/396 tests pass · cobertura código 88% (re-medido 04-jun-2026). **Completitud (X=33/33=1.00) y corrección (X=1−0/396=1.00) formalizadas ISO/IEC 25023 ✅.** ⚠️ Falta el **dictamen de los 2 jueces** sobre pertinencia funcional (≥0.90) para cerrar OE5 — instrumento listo en `docs/instrumento-evaluacion-jueces-ISO25010.md`.

### OE4 — Rendimiento académico (pretest/postest) — ✅ VALIDADO (04-jun-2026)
- Diseño pre-experimental de un solo grupo (`O1→X→O2`), pretest/postest aplicado a **n=49** estudiantes IESTP RFA (censo cohorte 2026-I: M01-M24 mañana + N01-N25 noche; supera el mínimo planificado 10-15).
- **Resultados reales:** pretest 10.45±2.76 → postest 14.43±3.11 (escala 0-20); ganancia +3.98 (IC95% [3.44, 4.52]); **46/49 mejoraron (94%)**.
- **Contraste:** t de Student pareada (1 cola, post>pre) **t(48)=14.85, p=7.2e-20 (<0.001)** → se rechaza H0. Cohen's **d=2.12 (efecto grande)**.
- Supuesto: Shapiro-Wilk diferencias W=0.947, p=0.027 (leve no-normalidad) → respaldo no paramétrico **Wilcoxon p=1.1e-09 (<0.001)** confirma. t robusta a n=49 por TLC.
- **Limitación documentada:** diseño sin grupo control → mejora significativa demostrada, pero causalidad exclusiva no probada (maduración/historia/testing). Cuasi-experimental con control = trabajo futuro.
- Harness: `backend/scripts/analyze_pretest_postest.py` + `backend/notebooks/pretest_postest_analysis.ipynb` sobre `docs/datos-pretest-postest.csv`. Reporte: `docs/reporte-rendimiento-academico.md/.docx`.
- *(SUS retirado del alcance oficial. Si se decide mantenerlo como instrumento de usabilidad complementario, documentarlo aparte y no como criterio de OE.)*

---

## 📄 DOCS ENTREGABLES (.docx)

Formato: portada (título + autor + asesora Mg. Reyes Burgos + USAT + fecha), índice automático, secciones numeradas, Times New Roman 11-12, interlineado 1.5.

| # | Archivo | Sprint | OE | Descripción |
|---|---------|--------|----|-------------|
| 1 | `docs/ERS.docx` | S1 ✅ | base | 52 RF en 8 módulos; 33 priorizados (insumo de OE3 y OE5) |
| 2 | `docs/reporte-LLM.docx` | S2 ✅ | OE1 | comparativa 3 LLM (Likert/latencia/VRAM) + 2 embeddings (Recall@5/MRR); selección qwen2.5 + mxbai |
| 3 | `docs/arquitectura.docx` | S3 | OE3 | C4 + justificación stack + despliegue |
| 4 | `docs/reporte-RAGAS.docx` | S4/S7 ✅ | OE2 | golden set 50 + 5 métricas (librería ragas oficial + juez independiente llama3.1 + rerank). 5/5 cumplen: precision 0.876, recall 0.812, faithfulness 0.706, relevancy 0.707, correctness 0.609 |
| 5 | `docs/matriz-trazabilidad-ISO25010.docx` | S7 | OE5 | caso de prueba ↔ RF ↔ subcaracterística ISO |
| 6 | `docs/reporte-ISO25010.docx` | S7 | OE5 | completitud ≥0.95 / corrección ≥0.90 / pertinencia ≥0.90 + dictamen 2 jueces |
| 7 | `docs/reporte-rendimiento-academico.docx` | S8 | OE4 | pretest/postest + t de Student pareada (p<0.05) |
| 8 | `docs/reporte-validacion-final.docx` | S8 | — | consolidación OE2 (RAGAS) + OE3 + OE4 + OE5 |

> Los cuatro modelos del STI (dominio · pedagógico · estudiante · interacción) **ya no son entregables formales** (no existe un OE que los produzca). Si se conservan, es solo como documentación interna de diseño, insumo de OE3.

---

## 🎨 FRONTEND

### Setup shadcn
```bash
npx shadcn@latest init
npx shadcn@latest add button card input label progress badge dialog tabs toast separator skeleton scroll-area textarea alert
```

### Colores (tailwind.config.js)
- Primary 500 `#3b82f6` azul institucional (50/100/600/700/900)
- Institutional navy + heritage oro + peru rojo
- Module: `locked #9ca3af`, `progress #3b82f6`, `completed #22c55e`
- Fonts: Plus Jakarta Sans (sans), JetBrains Mono (mono)

### Páginas
- **LoginPage:** split 2-col desktop, panel hero navy + formulario + brute-force protection
- **DashboardPage:** saludo, badge nivel, hero `bg-brand-hero` "Continuar...", 3 recomendaciones por nivel, 3 logros recientes, stats tabulares
- **ModulesPage:** grid responsivo 1/2/3 cols, ModuleCard con progreso, bloqueados grayscale+candado+tooltip
- **ModuleDetailPage:** header+progress, breadcrumb, lista temas (✅/🔵/⬜)
- **TopicPage:** breadcrumb, panel "Consultar Tutor IA" (modal), Markdown (react-markdown + remark-gfm + react-syntax-highlighter vscDarkPlus + copiar), iframe YouTube 16:9, barra fija Anterior/Siguiente, botón "Marcar completado" o desafío código
- **ChatPage:** 2 cols (sidebar sesiones + chat). Burbujas user-der azul / tutor-izq gris. Markdown. Fuentes colapsables. Contador "X de 20". Textarea auto-grow, Enter envía, Shift+Enter nueva línea
- **ProgressPage:** 4 tarjetas, barras por módulo, grid logros, historial
- **EntryAssessmentPage:** wizard multi-paso + barra + "La IA está analizando..." + resultado con gráfica por módulo
- **AdminPage:** 5 tabs [Corpus RAG | Contenido | Usuarios | Banco Fallback | Niveles]
- **CodingChallengePage:** split. Izq: descripción + pistas + resultado + chip "Generado con IA · nivel X". Der: editor dark monospace (Sprint 6 → Monaco) + "Regenerar con IA"

---

## 📄 DATOS INICIALES (`seed_db.py`)

- **5 módulos** (M1 Fundamentos · M2 Kotlin · M3 UI · M4 Componentes/Datos · M5 Avanzado/Despliegue)
- **22 temas** (M1=4, M2=5, M3=4, M4=5, M5=4), Markdown completo en `backend/scripts/seed_db.py`
- **7 logros** auto-detect (first_topic, module_completed, streak_days, chat_messages, Maestro Kotlin, quiz_perfect, course_completed)
- **30 desafíos coding** (`scripts/seed_extra_challenges.py` idempotente) — distribución M1=2 · M2=9 · M3=6 · M4=8 · M5=5
- **23 preguntas banco fallback** evaluación entrada M1-M5 (`scripts/seed_assessment_bank.py`)

Enumeración completa de 30 desafíos: `docs/CLAUDE-archive.md`.

---

## 🐳 DOCKER COMPOSE (dev)

Servicios:
- **postgres:** `pgvector/pgvector:pg16`, DB `tutordb`, user `tutor_user`, pass `tutor_pass_dev`, healthcheck pg_isready. **Host bind 5433** (no 5432) para evitar colisión con Postgres nativo Windows; backend en container conecta vía `postgres:5432` interno.
- **redis:** `redis:7-alpine`, `--maxmemory 256mb --maxmemory-policy allkeys-lru`
- **ollama:** `ollama/ollama:latest`, vol `ollama_data:/root/.ollama`. **⚠ Dev Windows: Ollama nativo via `host.docker.internal:11434` para GPU. Contenedor comentado.**
- **backend:** FastAPI, hot reload. `alembic upgrade head && python scripts/seed_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`. Monta `./backend/alembic`.
- **frontend:** Vite dev server 5173, `VITE_API_BASE_URL=http://localhost:8000/api/v1`

Volumes: `postgres_data, redis_data, ollama_data, uploads_data`.

**Prod (Sprint 5):** Docker Compose en VM e2-standard-4 + `infra/caddy/Caddyfile` (TLS LE) + `infra/scripts/{provision-vm.sh, deploy.sh, backup-postgres.sh}`.

### `scripts/setup_ollama.sh`
```bash
ollama pull qwen2.5:7b-instruct-q4_K_M  # ~4.5GB
ollama pull mxbai-embed-large            # ~670MB
```

---

## ⚙ VARIABLES (`.env.example`)

```
DATABASE_URL=postgresql+asyncpg://tutor_user:tutor_pass_dev@localhost:5433/tutordb
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
RAG_SIMILARITY_THRESHOLD=0.70      # evaluar bajar a 0.65 tras RAGAS S4 (v3 usó 0.65)
RAG_CONTEXT_WINDOW=5
CHUNK_SIZE=500
CHUNK_OVERLAP=50                    # evaluar semántico 15% S6

UPLOAD_DIR=./uploads
CORPUS_DIR=/data/corpus             # VM prod

ADMIN_EMAIL=admin@iestprfa.edu.pe
ADMIN_PASSWORD=Admin123!
ADMIN_NAME=Administrador del Sistema
```

---

## 📦 DEPENDENCIAS CLAVE

**backend/requirements.txt:** fastapi 0.115.5, uvicorn[standard] 0.32.0, sqlalchemy[asyncio] 2.0.36, asyncpg 0.30.0, alembic 1.14.0, pydantic 2.10.0, pydantic-settings 2.6.1, python-jose[cryptography] 3.3.0, passlib[bcrypt] 1.7.4, python-multipart 0.0.17, httpx 0.28.0, langchain 0.3.10, langchain-community 0.3.10, langchain-ollama 0.2.1, pypdf 5.1.0, python-docx 1.1.2, redis[hiredis] 5.2.0, slowapi 0.1.9, loguru 0.7.2, apscheduler 3.10.4, pytest 8.3.4, pytest-asyncio 0.24.0, pytest-cov 6.0.0. **S4:** ragas, datasets.

**frontend deps clave:** react 18.3.1, react-dom 18.3.1, react-router-dom 6.28.0, @tanstack/react-query 5.62.0, axios 1.7.7, zustand 5.0.1, react-markdown 9.0.1, react-syntax-highlighter 15.6.1, react-hot-toast 2.4.1, lucide-react 0.462.0, clsx, tailwind-merge, class-variance-authority, @radix-ui/react-{dialog,tabs,progress,scroll-area}. **S6:** @monaco-editor/react.

**devDeps:** @vitejs/plugin-react 4.3.3, vite 5.4.11, typescript 5.7.2, tailwindcss 3.4.15, autoprefixer, postcss, @types/react(-dom).

---

## 🚀 SPRINTS — RESUMEN

### Fases completadas (Sprints 1-3 + S4)
Detalle completo en `docs/CLAUDE-archive.md`. Resumen:

- **FASE 1 (S1) ✅** Infraestructura + BD + docker-compose + ERS + modelado de diseño (dominio/pedagógico, insumo de OE3)
- **FASE 2 (S2) ✅** Auth JWT+bcrypt + frontend base + benchmark LLM/embeddings ejecutado (qwen2.5 + mxbai-embed-large seleccionados)
- **FASE 3 (S2-3) ✅** Módulos, temas, contenido Markdown + 22 temas seed
- **FASE 4 (S3) ✅** Progreso + Quiz IA con fallback BD + 7 logros auto
- **FASE 5 (S3) ✅** Tutor IA Conversacional RAG (embed → pgvector → qwen2.5 + cache Redis)
- **FASE 5.5 (S3) ✅** Desafíos programación con eval IA (LLM scoring + feedback)
- **FASE 6 (S3) ✅ CRISP-DM** Personalización: evaluación entrada IA → nivel ponderado · LLM adapta dificultad · re-asignación dinámica
- **FASE 7 (S3) ✅** Dashboard + Admin 5 tabs (Corpus RAG, Contenido, Usuarios, Banco Fallback, Niveles) + generador desafíos IA con preview
- **FASE 7.5 (S3) ✅** Rebrand IESTP RFA + diferenciación admin + desafíos IA per-estudiante (migración 004)
- **FASE DE ACOMPAÑAMIENTO PROACTIVO (Fase 1) ✅** Motor determinista de nudges (`services/tutor_service.py` + `routers/tutor.py`, endpoint `GET /tutor/nudges`) montado en Dashboard y Topic (`<TutorNudge>`/`<TutorNudgeList>`). Reglas: sin-nivel, progreso-cero, inactividad, módulo casi completo, racha, reintento-quiz. Sin LLM → 100% testeable (suma RF a OE5/ISO). Operacionaliza el modelo de interacción/pedagógico del STI (insumo OE3/OE5); NO crea OE nuevo ni toca OE1/OE2/OE4. Spec/plan en `docs/superpowers/`. Contextos `*_result` + asistente flotante + banco de recursos = fases siguientes.
- **ACOMPAÑAMIENTO PROACTIVO (Fase 2) ✅** Asistente flotante del tutor (`frontend/src/components/tutor/FloatingTutor.tsx`) montado en `AppLayout` → presente en toda pantalla con layout (no en Login/Assessment). Burbuja fija → panel de chat RAG que reusa el pipeline `/chat` existente (sesión contextual con precarga en temas, contador de consultas, rate limit 20/h, ESC/cierre, móvil a pantalla completa). Sin cambios de backend. Operacionaliza el modelo de interacción del STI.
- **ACOMPAÑAMIENTO PROACTIVO (Fase 3) ✅** Banco de recursos curados `learning_resources` (migración 006) — videos/libros/artículos por módulo/tema. Endpoint estudiante `GET /resources`; CRUD admin `/admin/resources` + pestaña "Recursos" en AdminPage; `ResourceList` montado en Dashboard y Topic. Seed inicial con URLs marcadas para verificación humana. El LLM NUNCA genera recursos (regla "no inventa"). Cierra el pedido del jurado (links de libros/videos).
- **ACOMPAÑAMIENTO PROACTIVO (Fase 4) ✅** Refuerzo post-respuesta en quiz/coding/evaluación de entrada: nudges deterministas por banda de puntaje (contextos `*_result` en `tutor_service._result_nudges`), `<TutorNudgeList context="*_result" score=...>` montado en QuizPage/CodingChallengePage/EntryAssessmentPage. Reusa el motor de Fase 1, sin nuevas llamadas LLM. Cierra el acompañamiento proactivo (Fases 1-4).
- **ACOMPAÑAMIENTO PROACTIVO (Fase 5) ✅** Companion «el sistema sigue al estudiante» (09-jun-2026): `services/companion_service.py` determinista — posición = primer módulo desbloqueado incompleto (vía `compute_locks`); diagnóstico por bandas del mejor quiz (BD guarda fracción 0-1, se normaliza ×100): <60 repasar · 60-79 afianzar · ≥80 dominado · ≥2 intentos fallidos sin dominar → repasar · pendiente = tema no completado; `next_action` priorizado débil > pendiente > coding catálogo sin aprobar > módulo. `GET /tutor/companion` (Redis TTL 60s; quiz/topic/coding submit invalidan `companion:{user_id}`). Frontend: `CompanionPanel` reemplaza hero del Dashboard (fallback al hero clásico si el endpoint falla), `DiagnosticChips` en Dashboard + ModuleDetail (solo módulo actual), burbuja preview en `FloatingTutor` (saludo por plantillas, 1x/sesión vía sessionStorage, auto-oculta 12s, ESC), `useCompanion` staleTime 0. Sin LLM. Fuera de matriz ISO (33 RF congelados). Spec: `docs/superpowers/specs/2026-06-09-companion-seguimiento-design.md`. Tests: +20 unit, +5 integration backend; +8 frontend.
- **ACOMPAÑAMIENTO PROACTIVO (Fase 6) ✅** Recomendación IA sobre el banco curado (15-jun-2026): `services/resource_recommender_service.py` — el LLM **reordena y justifica** (1 línea por recurso) los recursos curados según nivel + tema débil, **sin inventar URLs** (solo permuta IDs reales del banco vía `merge_ranking` puro; `reason` se renderiza como texto escapado, no enlace). `GET /resources/recommended?module_id=|topic_id=` (uno u otro, 422 si ambos/ninguno; por `topic_id` los candidatos = recursos del tema **+ su módulo**, porque el seed solo asigna `module_id`). Caché Redis `resource_rec:{user}:{scope}` TTL 1800s, invalidada por prefijo (`invalidate_resource_recs`) junto al companion en los 6 mutadores (quiz/coding/topic/assessment/users/admin). **Fallback elegante**: Ollama caído / JSON inválido / <2 candidatos / Redis caído → orden curado determinista con `ai_ranked=false` (nunca 500). Frontend: `RecommendedResources` (chip oro «Recomendado por IA · nivel X» como el de coding, razón por recurso) montado en Dashboard (nivel módulo, reemplaza el bloque de recursos del `CompanionPanel`) y TopicPage (nivel tema). Companion sigue **sin LLM**. Fuera de matriz ISO (33 RF congelados). Spec: `docs/superpowers/specs/2026-06-15-ai-resource-recommendation-design.md` · Plan: `docs/superpowers/plans/2026-06-15-ai-resource-recommendation.md`. Tests: +21 unit, +4 integration backend; +4 frontend.
- **SPRINT 4 ✅** RAGAS validado (may 2026): juez independiente llama3.1 + rerank cross-encoder + librería ragas oficial. Recuperación precision 0.876/recall 0.812; generación faithfulness 0.706/relevancy 0.707/correctness 0.609 → 5/5 cumplen. Modelo qwen2.5+mxbai sin cambio.

### Tier 1 + 2 + 3 UI/UX Polish ✅ (12 may 2026, pre-piloto)

**Tier 1 (crítico):** ErrorBoundary global + toast ARIA + Monaco lazy + quiz localStorage persistence + useFocusMain hook + ContentRenderer heading hierarchy + touch targets ≥44px + semantic tokens + themeStore + ThemeToggle + dark mode wired.

**Tier 2 (polish):** Avatar component + ModuleCard locked-state a11y + LoginPage inline validation + SettingsPage (Perfil/Contraseña/Apariencia tabs) + backend `/progress/streak` endpoint + Dashboard streak StatCard.

**Tier 3 (pre-piloto):**
- **Phase 0 Foundations:** framer-motion + Skeleton + PageTransition + EmptyState illustration prop (Lucide fallback documented in `frontend/src/assets/empty/README.md`).
- **Phase 1 Mobile 375px:** 12 páginas auditadas (Login, Assessment, Dashboard, Modules, ModuleDetail, Topic, Quiz, Chat con drawer mobile + dvh, Coding con Monaco responsivo, Progress, Achievements, Admin best-effort). Touch ≥44px, no overflow horizontal, sticky bars con pb-suficiente.
- **Phase 2 Loading + transiciones:** PageTransition en AppLayout (200ms fade+slide, motion-safe) + skeletons matching shape en 7 páginas + micro-interacciones globales (interactive-card, interactive-button, focus-ring-smooth).
- **Phase 3 Dark mode QA:** 26 archivos auditados, 347+/209- líneas, 200+ instancias de hardcoded colors → tokens semánticos. Monaco theme dinámico vía useThemeStore.isDark.
- **Phase 4 Empty + Error:** 7 empty states con Lucide (Dashboard, Modules, Chat sessions/messages, Progress, Achievements, Admin Corpus) + 3 RouteErrorBoundary fallbacks contextuales (Chat/Quiz/Coding) usando ErrorBoundary existente con render prop.

Branch: `feat/tier3-uiux-polish`. Build green (tsc + Vite). Lighthouse mobile pendiente correr manualmente.

### 🔄 SPRINT 5 — Despliegue productivo (18-31 may 2026) · CRISP-DM Deployment

**Código deploy 100% listo (21 may 2026)** — pendiente ejecución manual cuando usuario tenga GCP+Firebase+dominio. Ver `docs/deploy-guide.md`.

- ✅ Provisión VM e2-standard-4 GCP (`infra/scripts/provision-vm.sh`) — instala Docker, Ollama nativo, modelos, firewall UFW, cron backup
- ✅ Docker Compose prod (`docker-compose.vm.yml`) — refactor v4.1: imagen built (sin bind mounts), Ollama nativo vía `host.docker.internal` (extra_hosts), `depends_on` healthchecks
- ✅ **Caddy + Let's Encrypt** (`infra/caddy/Caddyfile`) — TLS auto + headers seguridad + log JSON rotado
- ✅ Firebase Hosting config (`frontend/.firebaserc`, `frontend/firebase.json`, `frontend/.env.production.example`) — SPA rewrites + cache headers + security headers
- ✅ APScheduler (`app/services/scheduler_service.py` + `app.main` lifespan): cleanup `AIQuizSession >7d` diario 03:15 UTC
- ✅ Backup diario postgres (`infra/scripts/backup-postgres.sh`) + cron `0 3 * * *` agregado por provision-vm.sh
- ✅ `.dockerignore` backend + frontend (excluye tests/notebooks/node_modules)
- ✅ `docs/deploy-guide.md` — guía paso-a-paso prerequisitos GCP, DNS, Firebase, .env, rollback
- ✅ `infra/vm_setup.sh` legacy eliminado (consolidado en `infra/scripts/provision-vm.sh`)
- ✅ Redis cache sobre endpoints frecuentes — `app/utils/cache.py` (helper genérico con degraded mode si Redis cae) wired en `GET /dashboard` y `GET /modules` (TTL 60s). 7 unit tests del cache util.
- ⏸ Carga inicial 15 lecciones — `seed_db.py` ya tiene 22 temas ✅ (cubre el requisito)
- ⏸ **Ejecución real**: bloqueada hasta que usuario provea cuenta GCP/Firebase + dominio (ver `docs/deploy-guide.md` §0)

### ✅ SPRINT 6 — Contenido + Banco ejercicios (cerrado anticipadamente 22 may 2026)
- ✅ 22 lecciones (>15 objetivo) con Markdown, code blocks, tablas — ver `backend/scripts/seed_db.py`. Profundización adicional 22-may en `Consumo de APIs REST y Manejo de JSON` (+sealed class, HttpURLConnection, errores) y `Depuración con Logcat` (+adb, Timber, profilers, anti-patrones).
- ✅ 45 ejercicios (>30 objetivo) con feedback adaptativo — 30 originales + 15 extras vía `scripts/seed_more_challenges.py` (M4 +7, M5 +8: lifecycle/back stack, deeplinks, migraciones SQLite, paginación, interceptors auth, sealed ApiResult, logger rotación, mocking, parametrized tests, ProGuard, AndroidManifest, release notes, rollout).
- ✅ Motor retroalimentación adaptativa: `code_eval_service.LEVEL_EVAL_GUIDANCE` + `llm_service.LEVEL_GUIDANCE` por nivel beginner/intermediate/advanced.
- ✅ **Editor Monaco** lazy-loaded en `CodingChallengePage.tsx` — tema dinámico via `useThemeStore.isDark`, **shortcut Ctrl+Enter** para submit registrado vía `editor.addCommand`, indicador visible en header del editor.

### ✅ SPRINT 7 — Validación ISO/IEC 25010 (cerrado anticipadamente 21 may 2026)
- ✅ Matriz trazabilidad 33 RF → casos de prueba (`docs/matriz-trazabilidad-ISO25010.md`)
- ✅ Guardian automatizado `backend/tests/integration/test_iso25010.py` (5 tests, 100% pass) — protege la matriz contra deriva
- ✅ Reporte ejecutivo `docs/reporte-ISO25010.md` con resultados por subcaracterística + comportamiento ante fallos
- ✅ Cobertura 100% RF (33/33), tasa éxito 100% (276/276), cobertura código 86% — supera umbrales ISO
- ⏸ Exportar `.docx` antes de la sustentación (markdown → docx vía pandoc o copia manual)

### 🔄 SPRINT 8 — Pilotaje pretest/postest + cierre (29 jun – 10 jul 2026)
- ✅ **Pretest/postest [OE4] aplicado y computado anticipadamente (04-jun-2026, n=49):** t(48)=14.85, p<0.001, d=2.12; Wilcoxon p<0.001 → OE4 validado. Reportes regenerados (`reporte-rendimiento-academico`, `reporte-validacion-final`).
- ⏳ Dictamen ≥2 jueces pertinencia funcional [OE5] (único objetivo pendiente; instrumento listo)
- ⏳ Informe Final + sustentación **10/07/2026**

### ⏳ FASE 8 (transversal en S4-S8) — Calidad y Piloto
- slowapi global 100 req/min/IP ✅
- loguru JSON estructurado para prod
- Unit tests: auth/rag/progress/llm/code_eval/entry_assessment/leveling/achievement/topic_completion/ingest/embed/chunking/security ✅ (21 may)
- Integration tests: auth/chat/modules/quiz/coding/assessment/admin/users/progress/dashboard/topics/achievements/health ✅ (21 may)
- Frontend tests: vitest+RTL stack + smoke `store/{auth,theme}`, `lib/{utils,quizPersistence,achievementIcon}`, `components/{Avatar,EmptyState,Skeleton,ThemeToggle,BrandLogo,Button,ModuleCard}` ✅ (21 may)
- Backend coverage ≥80% ✅ (86% el 21 may, 266 unit+integration pass)
- Lighthouse Performance ≥70, Accessibility ≥85
- Responsivo 375/768/1440px ✅
- README instalación desde cero ✅

---

## ✅ CRITERIOS DE ACEPTACIÓN — ESTADO

**Funcionales (Fases 1-7.5) ✅** — todos los flujos cumplidos: registro→login→módulo→tema→quiz→progreso, IA con fallbacks (Ollama down → quiz BD, coding catálogo, banco evaluación), RAG con citas, off-topic rechazado, admin CRUD + generador IA con preview, evaluación entrada IA + re-asignación 3 consecutivos, diferenciación admin, identidad institucional IESTP RFA, rate limit 20/h. Lista completa por flujo: `docs/CLAUDE-archive.md` (V1-V13).

**Validación métricas (umbrales oficiales):**
- [x] Modelo qwen2.5:7b-instruct-q4_K_M + mxbai-embed-large seleccionados **[OE1]**
- [x] **OE1** validado. `docs/reporte-OE1-metricas-oficiales.docx`. Indicadores cumplen (5/5): Accuracy 0.72, Likert 4.325, Recall@5 0.72, MRR@10 0.684, nDCG@10 0.686. Anotación multi-evaluador humano = trabajo futuro.
- [x] Golden set ≥30 preguntas ground truth (anotación multi-evaluador humano = trabajo futuro)
- [x] **RAGAS context_precision ≥0.70** (ragas-lib: 0.876 ✅)
- [x] **RAGAS context_recall ≥0.75** (ragas-lib: 0.812 ✅)
- [x] **RAGAS faithfulness ≥0.65** (ragas-lib: 0.706 ✅ · umbral LLM 7B local)
- [x] **RAGAS answer_relevancy ≥0.65** (ragas-lib: 0.707 ✅)
- [x] **RAGAS answer_correctness ≥0.55** (ragas-lib: 0.609 ✅) → **criterio OE2 = 5 métricas, 5/5 ✅**
- [x] **ISO/IEC 25023 completitud funcional ≥0.95** (formalizada X=33/33=1.00; evidencia 396 tests, 0 fallos)
- [x] **ISO/IEC 25023 corrección funcional ≥0.90** (formalizada X=1−0/396=1.00)
- [ ] **ISO/IEC 25023 pertinencia funcional ≥0.90** (instrumento de jueces listo; pendiente dictamen ≥2 jueces) **[OE5]**
- [x] **OE4 rendimiento académico** pretest/postest + t de Student pareada p<0.05 — VALIDADO (n=49: t(48)=14.85, p<0.001, d=2.12; Wilcoxon p<0.001). 04-jun-2026
- [x] ≥80% de 33 RF priorizados implementados (100%)

**Contenido (S6):**
- [x] ≥3 módulos con ≥15 lecciones (22 temas seed; APIs REST + Logcat profundizados 22-may)
- [x] ≥30 ejercicios con feedback adaptativo (45 challenges catálogo: 30 originales + 15 vía `seed_more_challenges.py` con foco M4-M5)
- [x] Editor Monaco en CodingChallengePage (lazy + theme dinámico + Ctrl+Enter submit)

**Deploy (S5):**
- [x] Scripts infra completos (`provision-vm.sh`, `deploy.sh`, `backup-postgres.sh`, Caddyfile, docker-compose.vm.yml v4.1)
- [x] Firebase Hosting config + `.env.production.example`
- [x] APScheduler cleanup `AIQuizSession >7d` wired en lifespan
- [x] `.dockerignore` backend + frontend
- [x] `docs/deploy-guide.md` paso-a-paso
- [ ] VM e2-standard-4 provisionada (bloqueado: usuario sin GCP)
- [ ] Caddy + Let's Encrypt HTTPS (depende de VM + DNS)
- [ ] Firebase Hosting frontend deploy real (depende de proyecto Firebase)
- [ ] Backup diario postgres en producción (script + cron listos, ejecutar al levantar VM)
- [ ] Lighthouse Performance ≥70 en ModulesPage
- [ ] Funcional en 375px ✅ (Tier 3 mobile audit ejecutado)

**Calidad:**
- [x] Tests backend cobertura ≥60% (actual: **86%**, 266 tests pass + 6 skipped — 21 may 2026)
- [x] Tests backend cobertura ≥80% (Sprint 7 ISO objetivo · cumplido 21 may)
- [x] Tests frontend stack configurado (Vitest + RTL + jsdom + @vitest/coverage-v8); 69 smoke tests baseline (21 may)
- [x] README levanta desde cero
- [~] Documentos entregables (8, mapeados a OE) — `.docx` generados: ERS, reporte-LLM, arquitectura, **reporte-RAGAS (criterio 5/5, re-validado)**, **matriz-trazabilidad-ISO25010**, **reporte-ISO25010** (estos 3 últimos 2026-05-29) + anexo **reporte-OE1-metricas-oficiales** (criterio 5/5; 9 indicadores medidos). **rendimiento-académico/OE4 ✅ (04-jun, n=49, regenerado)** + **consolidación-final actualizada (OE4 validado)**. Pendiente único: dictamen ≥2 jueces pertinencia/OE5.

---

## ⚠ ADVERTENCIAS CLAVE

**LLM/Hardware:** `qwen2.5:7b-instruct-q4_K_M` requiere ≥6GB RAM libre. VM e2-standard-4 (16 GB) opera cómodo. Si respuestas >20s → cambiar a `llama3.2:3b-instruct-q4_K_M` (2GB). Dev local sin GPU es lento, normal.

**pgvector IVFFlat:** **NO crear índice antes de ingestar datos.** Crear DESPUÉS: `CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);` · lists ≈ sqrt(n_chunks).

**RAG vs Fine-tuning:** Sistema usa RAG puro, no fine-tuning. "Entrenamiento" en tesis = construir pipeline RAG con corpus. Aproximación estándar para apps educativas.

**Servicios eliminados (v4.0 confirma):**
- Pub/Sub → `fastapi.BackgroundTasks`
- Cloud Scheduler → `APScheduler` embebido en FastAPI
- Cloud Memorystore → Redis auto-hospedado en VM
- Cloud CDN+LB → Firebase Hosting (CDN global + HTTPS gratis)
- **Cloud Run → Docker Compose en VM única + Caddy+LE**
- **Cloud SQL → PostgreSQL 16 + pgvector auto-hospedado**

**asyncpg + pgvector:** Vector literal **inline** en SQL. No parametrizar con `::vector` cast (incompatible). Ver `rag_service.py`.

**Postgres puerto host 5433 (no 5432) en dev Windows:** colisión con servicio nativo `postgresql-x64-*` que escucha 5432 en 0.0.0.0. Sin remapeo, conexiones desde Windows al docker postgres caen en el postgres nativo → "password authentication failed" engañoso. Backend container conecta vía `postgres:5432` (red docker interna, sin afectar). Scripts host (alembic, run_ragas_eval, tests asyncpg directos) usan `localhost:5433`.

**Ollama format="json":** Usar wrapper objeto `{"questions":[...]}`, no array desnudo. Parser robusto en `llm_service.py`.

**Threshold + chunking:** v4.0 objetivo threshold=0.65 + chunking semántico 15% overlap. Impl. actual usa 0.70 + RecursiveCharacterTextSplitter 500/50. **S4 RAGAS v3 validó 0.65; falta sincronizar `.env` default. Chunking semántico pendiente S6.**

**Protocolo escalamiento — detener + consultar usuario si:**
- Métrica objetivo no alcanzada tras **3 iteraciones**
- Necesidad percibida de cambiar stack técnico
- Librería requiere licencia comercial
- Cronograma desviado > 1 semana del hito **10/07/2026**

**Flujo Claude Code:**
1. Leer sprint activo (§ CRONOGRAMA)
2. Crear rama `feat/sprint-{n}-{descripcion}` o `docs/sprint-{n}-{documento}`
3. Implementar con tests
4. Verificar que no afecte hito 10/07
5. Actualizar estado en este CLAUDE.md en el mismo PR

---

## 📚 REFERENCIAS INTERNAS

- `docs/CLAUDE-archive.md` — Historial detallado Fases 1-7.5 + S4 + matriz V1-V13
- `docs/ERS.docx` — Especificación Requisitos Software (52 RF / 33 priorizados)
- `docs/reporte-LLM.docx` — Reporte comparativo LLM + embeddings [OE1]
- `docs/reporte-RAGAS.docx` — Validación RAGAS [OE2]
- `corpus/silabo-2025-I.md` — Sílabo oficial IESTP RFA
- Cronograma: `1_03_Cronograma_de_actividades_Zavaleta_scrum.xlsx` (12 sprints en 6 iteraciones CRISP-DM, alineado a los 5 OE oficiales)

---

*v3.3 — Realineación a los 5 OE oficiales y al mapeo V.2.1. OE1 = selección LLM/embeddings; OE2 = validación RAGAS; OE3 = despliegue GCE con métricas de rendimiento/disponibilidad; OE4 = rendimiento académico con **t de Student pareada (p<0.05)**; OE5 = adecuación funcional ISO/IEC 25010:2023 + 25023:2016. **SUS retirado** (fuera del mapeo oficial). RAGAS validado (may 2026): librería ragas oficial + juez independiente llama3.1 + rerank; recuperación precision 0.876/recall 0.812, generación faithfulness 0.706/relevancy 0.707/correctness 0.609 → 5/5. "Establecer modelos STI" y "estructurar contenido" son insumos de OE3/OE4, no OE independientes.*

---

## 🎨 DESIGN CONTEXT (impeccable)

Contexto de diseño para agentes. Fuente completa: **`PRODUCT.md`** (estratégico) + **`DESIGN.md`** (sistema visual), ambos en la raíz del proyecto.

- **Register:** `product` — UI de aplicación; el diseño SIRVE a la tarea de aprender, no es marketing.
- **Personalidad:** confianza institucional cálida — *trustworthy, encouraging, focused*, con acabado moderno. Voz: español peruano, claro y cercano; el tutor admite incertidumbre y **no inventa**.
- **Anti-referencias:** NO un LMS recargado tipo Moodle · NO plantilla SaaS genérica (hero-metric, grids de tarjetas idénticas, gradient text) · NO gamificación infantil/chillona.
- **5 principios de diseño:**
  1. *El tutor no inventa* — confianza por trazabilidad (citar fuentes, admitir límites).
  2. *Encontrar al estudiante donde está* — el nivel adapta dificultad/feedback; nunca callejón sin salida.
  3. *Momentum sobre decoración* — la gamificación mapea a progreso real.
  4. *La herramienta desaparece en la tarea* — un trabajo primario por pantalla.
  5. *Resiliente por diseño* — todo camino IA tiene fallback elegante (quiz→banco, coding→catálogo, assessment→banco docente).
- **Accesibilidad:** objetivo **WCAG 2.1 AA** (contraste ≥4.5:1, foco visible, `prefers-reduced-motion`, touch ≥44px), light + dark.
- **Identidad visual:** azul institucional + navy + oro heritage + rojo Perú; Plus Jakarta Sans + JetBrains Mono; tokens HSL semánticos (light/dark). **Preservar identidad existente.**

> Generado por `/impeccable init` (2026-05-31). Para iterar diseño: `/impeccable critique|audit|polish|live …`.
