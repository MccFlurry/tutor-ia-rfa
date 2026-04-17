# CLAUDE.md — Tutor IA Generativa · Aplicaciones Móviles IESTP RFA

Tesis pregrado USAT. STI con RAG privado para curso Apps Móviles (Android/Kotlin) del IESTP "República Federal de Alemania", Chiclayo.

Estudiantes: estudian 5 módulos, consultan tutor IA privado (RAG), autoevalúan, ven progreso gamificado.

**Reglas absolutas:**
- LLM 100% privado vía Ollama. Nunca APIs pagas (OpenAI/Anthropic/Gemini).
- Conocimiento dominio solo vía RAG.
- UI **español peruano**.
- Evaluación: ISO/IEC 25010 + SUS ≥68, 10-15 estudiantes piloto.

---

## 🏗️ STACK

**Frontend:** React 18 + Vite + TypeScript, Tailwind 3, shadcn/ui, Zustand, TanStack Query, React Router v6, react-hot-toast, Lucide. Deploy: Firebase Hosting.

**Backend:** FastAPI + Python 3.12, SQLAlchemy 2.0 async, asyncpg, Alembic, Pydantic v2, LangChain, slowapi, loguru, APScheduler, python-jose, passlib[bcrypt], httpx, pypdf. Deploy: Cloud Run.

**Compute Engine e2-standard-2 SPOT (~$5-15/mes):** Ollama (qwen2.5:7b-instruct-q4_K_M + mxbai-embed-large, puerto 11434) + Redis 7 (puerto 6379). Ubuntu 22.04 + Docker Compose.

**DB:** Cloud SQL PostgreSQL 16 + pgvector, instancia db-f1-micro (~S/.26/mes).

**Seguridad:** VPC privada Cloud Run↔VM, VPC Connector, IAM min-priv, Secret Manager, HTTPS Firebase.

### Pipeline RAG

**Ingesta:** Archivo (PDF/DOCX/TXT) → BackgroundTask FastAPI → parser (pypdf/python-docx) → TextSplitter (chunk 500, overlap 50) → mxbai-embed-large → vector[1024] → pgvector `document_chunks`.

**Consulta:** Pregunta → embedding → pgvector cosine search (top_k=5, threshold≥0.70) → chunks + historial (últimas 5 rondas) → prompt aumentado → qwen2.5 → caché Redis (TTL 3600s) → respuesta + fuentes citadas.

---

## 📁 ESTRUCTURA

```
tutor-ia-rfa/
├── CLAUDE.md, .env.example, .env, .gitignore
├── docker-compose.yml              # stack completo dev
├── docker-compose.vm.yml            # Ollama+Redis en VM prod
├── backend/
│   ├── Dockerfile, requirements.txt, alembic.ini
│   ├── alembic/versions/            # 001_initial, 002_add_coding_challenges
│   └── app/
│       ├── main.py, config.py, database.py, dependencies.py
│       ├── models/                  # user, module, topic, quiz, progress, achievement, chat, document, coding
│       ├── schemas/                 # mismo split + auth
│       ├── routers/                 # auth, users, modules, topics, quiz, progress, achievements, chat, dashboard, admin, coding
│       ├── services/                # auth, progress, achievement, rag, llm, embed, ingest, code_eval, topic_completion
│       └── utils/                   # security (JWT+bcrypt), chunking, logger
├── frontend/
│   ├── Dockerfile, .firebaserc, firebase.json, package.json, vite/tsconfig/tailwind/postcss/components.json
│   └── src/
│       ├── main.tsx, App.tsx, vite-env.d.ts
│       ├── api/                     # client (axios+JWT), auth, modules, topics, quiz, progress, achievements, chat, coding, dashboard, admin
│       ├── store/                   # authStore, progressStore, uiStore
│       ├── components/
│       │   ├── ui/                  # shadcn: button, card, input, progress, badge, dialog, tabs, toast, etc.
│       │   ├── layout/              # Navbar, Sidebar, AppLayout
│       │   ├── auth/AuthGuard.tsx
│       │   ├── modules/             # ModuleCard, TopicListItem
│       │   ├── topics/              # ContentRenderer, CodeBlock
│       │   ├── quiz/                # QuizQuestion, QuizResults
│       │   ├── chat/                # ChatMessage, ChatSources, TypingIndicator
│       │   └── achievements/AchievementCard
│       ├── pages/                   # Login, Dashboard, Modules, ModuleDetail, Topic, Chat, Progress, Admin, Quiz, Achievements, CodingChallenge
│       ├── hooks/                   # useAuth, useProgress, useChat
│       ├── types/                   # mirror schemas
│       └── lib/utils.ts             # cn()
├── scripts/                         # seed_db.py, setup_ollama.sh, ingest_course_docs.py
└── infra/                           # vm_setup.sh, gcp_commands.sh
```

---

## 🗄️ ESQUEMA BD

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

-- CODING CHALLENGES (Fase 5.5)
coding_challenges(id, topic_id FK, title, description, difficulty, hints, reference_solution, ...)
coding_submissions(id, user_id FK, challenge_id FK, code, score, feedback, strengths, improvements, submitted_at)

-- ÍNDICES
CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
-- ⚠️ Crear DESPUÉS de ingestar datos. lists ≈ sqrt(n_chunks)
CREATE INDEX idx_user_progress_user/topic, idx_quiz_attempts_user, idx_chat_messages_session, idx_document_chunks_document;
```

---

## 🔌 API REST

Base dev: `http://localhost:8000/api/v1` · Prod: `https://[CLOUD_RUN_URL]/api/v1`
Auth: `Authorization: Bearer <access_token>` (excepto `/auth/login`, `/auth/register`).

### `/auth`
- `POST /register` body `{email, full_name, password}` → `{user, access_token, refresh_token}`
- `POST /login` body `{email, password}` → ídem
- `POST /refresh` body `{refresh_token}` → `{access_token}`
- `POST /logout` body `{refresh_token}` → `{message}`

### `/users`
- `GET /me`, `PUT /me` body `{full_name?, avatar_url?}`, `PUT /me/password` body `{current_password, new_password}`

### `/dashboard`
- `GET /` → `{user_name, overall_progress_pct, total_topics_completed, last_accessed_topic, recommended_modules, recent_achievements}`

### `/modules`
- `GET /` → lista con `progress_pct, is_locked, total_topics, completed_topics`
- `GET /{id}` → Module + temas con `status: not_started|in_progress|completed`

### `/topics`
- `GET /{id}` → contenido + progreso
- `POST /{id}/visit`, `POST /{id}/complete`, `POST /{id}/time` body `{seconds}`

### `/quiz` (IA genera preguntas, fallback BD estática)
- `GET /topic/{topic_id}` → `{session_id, questions}` (LLM genera, respuestas Redis TTL 30min)
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

### `/coding` (Fase 5.5)
- `GET /topic/{topic_id}/challenges`, `GET /challenge/{id}`
- `POST /challenge/{id}/submit` body `{code}` → score + feedback LLM
- `GET /challenge/{id}/history`, `GET /challenge/{id}/best`
- `GET /topic/{topic_id}/completion-status`

### `/admin` (solo role=admin)
- Usuarios: `GET /users` paginado, `PUT /users/{id}` body `{role?, is_active?}`
- Corpus RAG: `GET/POST/DELETE /documents`, `POST /documents/{id}/reprocess`
- Contenido: CRUD módulos, temas, preguntas quiz, desafíos coding

---

## 🤖 RAG — INTERFAZ

### `services/rag_service.py`

`RAGService.query(question, session_history, db, redis)` → `{content, sources}`:
1. Chequear caché Redis `rag:{hash(question)}`
2. `OllamaEmbeddings(mxbai-embed-large).aembed_query(question)` → vec[1024]
3. pgvector cosine search: `1 - (embedding <=> :query_vec::vector) AS similarity`, threshold 0.70, top 5
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
4. `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, separators=["\n\n","\n",". "," ",""])`
5. `OllamaEmbeddings.aembed_documents(chunks)` (batch)
6. Guardar chunks + vectores
7. status='active', chunk_count=N · o 'error' con mensaje

### `services/llm_service.py` (Quiz IA)
ChatOllama con `format="json"`, `temperature=0.7`. Prompt español genera N preguntas. ⚠️ **Usar wrapper `{"questions":[...]}`** no array desnudo (incompatible con format=json). Parser maneja ambos. Trunca contenido 3500 chars.

### `services/code_eval_service.py`
LLM evalúa código. Criterios: corrección 40%, buenas prácticas 25%, eficiencia 20%, legibilidad 15%. Score 0-100 + feedback Markdown + strengths + improvements. `format="json"`. Solución referencia como guía, no única válida.

---

## 🎨 FRONTEND

### Setup shadcn
```bash
npx shadcn@latest init
npx shadcn@latest add button card input label progress badge dialog tabs toast separator skeleton scroll-area textarea alert
```

### Colores (tailwind.config.js)
- Primary 500 `#3b82f6` azul institucional (50/100/600/700/900)
- Module: `locked #9ca3af`, `progress #3b82f6`, `completed #22c55e`
- Fonts: Plus Jakarta Sans (sans), JetBrains Mono (mono)

### Páginas

- **LoginPage:** fondo azul degradado, tarjeta centrada, email+password con toggle, "Recordar sesión", validación on-blur
- **DashboardPage:** saludo, hero "Continuar donde lo dejaste", círculo animado progreso, 3 recomendaciones, 3 logros recientes
- **ModulesPage:** grid responsivo 1/2/3 cols, ModuleCard con progreso, bloqueados grayscale+candado+tooltip
- **ModuleDetailPage:** header+progress, breadcrumb, lista temas (✅ verde completado / 🔵 azul pulsante en progreso / ⬜ gris pendiente)
- **TopicPage:** breadcrumb, panel lateral "Consultar Tutor IA" (modal), área Markdown (react-markdown + remark-gfm + react-syntax-highlighter vscDarkPlus + botón copiar), iframe YouTube 16:9, barra fija "← Anterior | X de Y | Siguiente →", botón "Ir a Autoevaluación" o "Marcar completado", botones desafíos código
- **ChatPage:** 2 columnas (sidebar sesiones + chat). Burbujas user-der azul / tutor-izq gris. Markdown renderizado. Fuentes colapsables. "✦ escribiendo...". Contador "X de 20 consultas/hora". Textarea auto-grow, Enter envía, Shift+Enter nueva línea
- **ProgressPage:** 3 tarjetas métricas, barras por módulo, grid logros, historial
- **AdminPage:** tabs [Corpus RAG | Contenido | Usuarios]. RAG: tabla docs, drag&drop upload, estado procesando. Contenido: árbol colapsable Módulo→Temas→Preguntas+Coding con CRUD
- **CodingChallengePage:** split. Izq: descripción Markdown + pistas colapsables + resultado (score, feedback, strengths, improvements). Der: editor dark theme monospace + botón "La IA está evaluando..."

---

## 📄 DATOS INICIALES (`seed_db.py`)

**5 módulos:**
1. Fundamentos y Preparación del Entorno (index 1, `smartphone`, `#6366f1`)
2. Lógica de Programación en Kotlin (2, `code-2`, `#0ea5e9`)
3. Elaboración de Interfaces de Usuario UI (3, `layout-panel-top`, `#22c55e`)
4. Componentes Android y Gestión de Datos (4, `database`, `#f59e0b`)
5. Funcionalidades Avanzadas y Despliegue (5, `rocket`, `#ef4444`)

**22 temas totales** distribuidos: M1=4, M2=5, M3=4, M4=5, M5=4. Cada uno: title, estimated_minutes (10-35), has_quiz (true/false). Ver `backend/scripts/seed_db.py` para contenido Markdown completo con código Kotlin.

**7 logros:** Primer Paso 🚀 (first_topic=1), Finalizador Módulo 🏆 (module_completed=1), Racha 7 Días 🔥 (streak_days=7), Explorador Tutor IA 🤖 (chat_messages=10), Maestro Kotlin ⚡ (module_completed=2 mod_id=2), Quiz Perfecto 💯 (quiz_perfect=100), Desarrollador Completo 🎓 (course_completed=100).

**7 desafíos coding** (M2 y M4): Calculadora Promedio (fácil), Clasificador Triángulos (medio), Filtro con Lambda (medio), Sistema Inventario OOP (medio), Figuras Polimorfismo (difícil), Logger Ciclo Vida (fácil), Modelo Datos API (medio).

---

## 🐳 DOCKER COMPOSE (dev)

Servicios clave:
- **postgres:** `pgvector/pgvector:pg16`, DB `tutordb`, user `tutor_user`, pass `tutor_pass_dev`, healthcheck pg_isready
- **redis:** `redis:7-alpine`, `--maxmemory 256mb --maxmemory-policy allkeys-lru`
- **ollama:** `ollama/ollama:latest`, vol `ollama_data:/root/.ollama`. **⚠️ Dev Windows: Ollama nativo via `host.docker.internal:11434` para GPU. Contenedor comentado.**
- **backend:** FastAPI, hot reload. Command: `alembic upgrade head && python scripts/seed_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- **frontend:** React Vite dev server puerto 5173, `VITE_API_BASE_URL=http://localhost:8000/api/v1`

Volumes: `postgres_data, redis_data, ollama_data, uploads_data`.

### `scripts/setup_ollama.sh`
```bash
ollama pull qwen2.5:7b-instruct-q4_K_M  # ~4.5GB
ollama pull mxbai-embed-large            # ~670MB
```

---

## ⚙️ VARIABLES (`.env.example`)

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
RAG_SIMILARITY_THRESHOLD=0.70
RAG_CONTEXT_WINDOW=5
CHUNK_SIZE=500
CHUNK_OVERLAP=50

UPLOAD_DIR=./uploads

ADMIN_EMAIL=admin@iestprfa.edu.pe
ADMIN_PASSWORD=Admin123!
ADMIN_NAME=Administrador del Sistema
```

---

## 📦 DEPENDENCIAS CLAVE

**backend/requirements.txt:** fastapi 0.115.5, uvicorn[standard] 0.32.0, sqlalchemy[asyncio] 2.0.36, asyncpg 0.30.0, alembic 1.14.0, pydantic 2.10.0, pydantic-settings 2.6.1, python-jose[cryptography] 3.3.0, passlib[bcrypt] 1.7.4, python-multipart 0.0.17, httpx 0.28.0, langchain 0.3.10, langchain-community 0.3.10, langchain-ollama 0.2.1, pypdf 5.1.0, python-docx 1.1.2, redis[hiredis] 5.2.0, slowapi 0.1.9, loguru 0.7.2, apscheduler 3.10.4, pytest 8.3.4, pytest-asyncio 0.24.0, pytest-cov 6.0.0.

**frontend deps clave:** react 18.3.1, react-dom 18.3.1, react-router-dom 6.28.0, @tanstack/react-query 5.62.0, axios 1.7.7, zustand 5.0.1, react-markdown 9.0.1, react-syntax-highlighter 15.6.1, react-hot-toast 2.4.1, lucide-react 0.462.0, clsx, tailwind-merge, class-variance-authority, @radix-ui/react-{dialog,tabs,progress,scroll-area}.

**devDeps:** @vitejs/plugin-react 4.3.3, vite 5.4.11, typescript 5.7.2, tailwindcss 3.4.15, autoprefixer, postcss, @types/react(-dom).

---

## 🚀 FASES

### ✅ FASE 1 — Infraestructura y BD
Estructura, docker-compose con pgvector/redis/ollama, config.py + database.py async, todos modelos SQLAlchemy, migración inicial Alembic con `CREATE EXTENSION vector`, React+Vite+TS+Tailwind+shadcn en frontend. `docker compose up` funciona.

### ✅ FASE 2 — Autenticación
`security.py` JWT+bcrypt, `auth_service.py`, `routers/auth.py`, `dependencies.py` (get_db, get_current_user, get_redis, require_admin). Frontend: `LoginPage` con toggle registro + brute-force protection (3 intentos+lockout 5min), `authStore` Zustand+localStorage, `api/client.ts` interceptor 401, `AuthGuard` con requireAdmin.

### ✅ FASE 3 — Módulos, Temas, Contenido
`setup_ollama.sh`, `seed_db.py` (5 módulos + 22 temas Markdown completo + 25+ preguntas + 7 logros + admin). `routers/modules.py` + `topics.py`. Frontend: `ModulesPage`, `ModuleDetailPage`, `TopicPage`, `ContentRenderer` (react-markdown + remark-gfm), `CodeBlock` (syntax+copy), layout (AppLayout/Sidebar/Navbar), shadcn components.

### ✅ FASE 4 — Progreso, Quiz IA, Logros
`progress_service.py`, `achievement_service.py` (7 tipos auto-detect), `llm_service.py` (Ollama quizzes JSON), `routers/quiz.py` (GET genera vía LLM→Redis TTL 30min, POST evalúa, fallback BD estática si Ollama caído, sesiones single-use), `progress.py`, `achievements.py`. Frontend: `QuizPage` ("IA está preparando...", retry genera NUEVAS, 410→auto-regenera), `QuizQuestion`, `QuizResults`, `ProgressPage` (4 cards + barras + logros + actividad), `AchievementsPage`.

### ✅ FASE 5 — Tutor IA Conversacional RAG
`embed_service.py` singleton mxbai, `ingest_service.py` (parse→clean→chunk→embed→pgvector), `rag_service.py` (embed→pgvector cosine top5 ≥0.70→prompt aumentado con historial→qwen2.5→cache Redis TTL 1h). `routers/chat.py`: CRUD sesiones, POST mensaje con RAG, rate limit Redis 20/h→429, fuentes ≥0.75, `GET /remaining`, título auto desde primer msg, integra achievement. Frontend: `ChatPage` + `ChatMessage` (Markdown+syntax), `ChatSources` (colapsable %relevancia), `TypingIndicator`, sidebar sesiones, input Enter/Shift+Enter, contador, optimistic updates.

`ingest_course_docs.py` → 22 temas = 163 chunks. Ollama nativo Windows GPU (RTX 4070 16GB) → respuestas 3-5s.

**Fixes críticos:**
- `llm_service.py`: wrapper `{"questions":[...]}` para `format="json"`, parser ambos formatos
- `rag_service.py`: vector literal **inline** en SQL (asyncpg no soporta `::vector` parametrizado)
- `docker-compose.yml`: Ollama nativo via `host.docker.internal:11434`

### ✅ FASE 5.5 — Desafíos Programación con IA
`models/coding.py` (CodingChallenge + CodingSubmission), migración `002_add_coding_challenges.py`, `code_eval_service.py` (LLM scoring 0-100 + Markdown feedback + strengths + improvements, criterios 40/25/20/15, `format="json"`), `schemas/coding.py` + `routers/coding.py` (CRUD, submit con LLM, history, best, completion-status).

Frontend: `CodingChallengePage` split (izq: problem Markdown + hints + resultado / der: editor dark monospace + "IA evaluando..."), `types/coding.ts`, `api/coding.ts`, ruta `/coding/:challengeId`.

7 desafíos seeded. `topic_completion_service.py`: tema con quiz+coding → AMBOS deben aprobarse (quiz ≥60%, coding ≥60pts). Quiz submit y coding submit ambos llaman `check_and_complete_topic()`. `TopicListItem` muestra ícono "Desafío de Código". `has_coding_challenge` en TopicBrief schema con query agrupada.

### ✅ FASE 6 — Personalización vía CRISP-DM (completada 2026-04-17)

**Objetivo:** Evaluación de entrada generada por IA asigna nivel (`beginner` | `intermediate` | `advanced`). LLM adapta dificultad de quizzes + coding challenges al nivel del estudiante. Re-asignación dinámica según desempeño.

#### 1️⃣ Business Understanding
- Problema: estudiantes con distinto nivel reciben mismos ejercicios → desmotivación + aprendizaje subóptimo
- Meta: diferenciar dificultad por nivel, medir progreso adaptativo
- Niveles: `beginner` | `intermediate` | `advanced`
- KPIs éxito: SUS ≥68, tasa completación por nivel, accuracy clasificador vs juicio docente, re-asignaciones correctas

#### 2️⃣ Data Understanding
Datos a capturar:
- **Evaluación entrada:** respuestas + tiempo por pregunta + cobertura por módulo (M1-M5)
- **Señales continuas:** quiz scores, intentos por quiz, coding scores, tiempo por tema, consultas al tutor
- **Metadata:** fecha, ID tema/módulo, tipo pregunta (conceptual | código | aplicación)

#### 3️⃣ Data Preparation
**Nuevas tablas** (migración `003_add_personalization.py`):
```sql
user_levels(user_id UUID PK FK, level VARCHAR(20), entry_score FLOAT, assessed_at, last_reassessed_at, history JSONB)

entry_assessment_sessions(id UUID PK, user_id FK, questions JSONB, answers JSONB, score FLOAT, computed_level, created_at)

-- Fallback docente (solo si LLM falla)
entry_assessment_bank(id SERIAL PK, module_id FK, question_text, options JSONB, correct_index, difficulty 'easy'|'medium'|'hard', created_by FK, is_active)
```

**Feature engineering:**
- `overall_entry_score` (0-100) = Σ (correctas × peso_módulo × peso_dificultad)
- Pesos módulo: M1=1.0, M2=1.2, M3=1.1, M4=1.3, M5=1.5
- Pesos dificultad: easy=1.0, medium=1.5, hard=2.0
- **Umbrales nivel:** `<40` beginner · `40-75` intermediate · `>75` advanced

Índices: `user_id`, `computed_level`, `module_id` en bank.

#### 4️⃣ Modeling
**Clasificador de nivel (rule-based v1):**
- Input: respuestas entrada + pesos
- Output: `{level, score, confidence}`
- Algoritmo: score ponderado → umbrales fijos
- v2 futuro: scikit-learn classifier si piloto genera data suficiente

**Prompt engineering adaptativo:**
- `llm_service.py` + `code_eval_service.py` reciben parámetro `student_level`
- Diferenciación:
  - `beginner`: preguntas conceptuales, código sintaxis básica, pistas explícitas, 1 concepto por pregunta
  - `intermediate`: aplicación práctica, lógica moderada, menos pistas, combinar 2 conceptos
  - `advanced`: edge cases, optimización, sin pistas, diseño + refactor, patrones avanzados
- Coding eval: criterios más estrictos en buenas prácticas/eficiencia para nivel alto

#### 5️⃣ Evaluation
**Métricas:**
- Accuracy clasificador vs juicio docente (muestra 10-15 estudiantes piloto)
- Distribución niveles (detectar sesgo a un solo bucket)
- Correlación nivel ↔ avg quiz/coding score (debe ser positiva)

**Reglas re-asignación automática:**
- 3 quizzes consecutivos ≥90% → proponer subir nivel
- 3 quizzes consecutivos <50% → proponer bajar nivel
- Estudiante confirma (o admin override)
- Registro en `user_levels.history`

#### 6️⃣ Deployment
**Backend:**
1. `models/user_level.py`, `models/entry_assessment.py`, `models/assessment_bank.py`
2. Migración Alembic `003_add_personalization.py`
3. `services/entry_assessment_service.py`:
   - `generate_assessment()` → LLM crea 10-15 preguntas cubriendo M1-M5 con dificultad mixta, `format="json"`, wrapper `{"questions":[...]}`
   - Fallback: muestrear de `entry_assessment_bank` si Ollama falla/timeout
4. `services/leveling_service.py`:
   - `compute_level(answers, weights)` → `{level, score, confidence}`
   - `check_reassessment(user_id, db)` → evalúa últimos N quizzes, retorna propuesta
   - Integra con `achievement_service` (logro "Subiste de nivel")
5. **Endpoints nuevos:**
   - `POST /assessment/start` → `{session_id, questions}` (LLM o fallback)
   - `POST /assessment/submit` body `{session_id, answers}` → `{level, score, feedback_por_modulo}`
   - `GET /users/me/level` → nivel actual + historial
   - `POST /users/me/reassess` → dispara evaluación nueva
   - `GET/POST/PUT/DELETE /admin/assessment-bank` (CRUD fallback)
6. Modificar `llm_service.py` y `code_eval_service.py`: aceptar `student_level`, adaptar prompts
7. Modificar `routers/quiz.py` + `routers/coding.py`: leer `user_level`, pasar a servicios LLM

**Frontend:**
- `EntryAssessmentPage.tsx`: wizard multi-paso con preguntas IA, barra progreso, "La IA está analizando tu nivel..." al final, resultado con gráfica por módulo
- **Redirect forzado post-login:** si `user.level IS NULL` → `/assessment` antes de dashboard
- Badge nivel en `Navbar` (color-coded: gris/azul/morado)
- `ReassessmentModal.tsx`: propuesta subir/bajar tras N quizzes
- Panel admin:
  - Tab "Banco Fallback": CRUD preguntas por módulo/dificultad
  - Tab "Niveles Estudiantes": tabla con nivel actual, historial, botón override

**Verificación:**
- Nuevo usuario registra → forzado a evaluación → LLM genera preguntas únicas → responde → nivel asignado
- Quiz siguiente adapta dificultad según nivel (verificar prompts diferenciados en logs)
- Tras 3 quizzes ≥90% → modal propone subir nivel
- Si Ollama down durante evaluación → fallback usa banco del docente
- Admin ve tabla niveles + puede hacer override manual

### ✅ FASE 7 — Dashboard Completo y Admin (completada 2026-04-17)
- `schemas/dashboard.py` + `routers/dashboard.py` con agregación (último tema, recomendaciones por nivel, logros recientes, **nivel del estudiante**)
- `DashboardPage` rediseñado: hero `bg-brand-hero` "Continuar...", recomendaciones por nivel, 3 logros recientes, stats tabulares
- `routers/admin.py` extendido: CRUD completo módulos/temas/quiz/coding, `services/challenge_generator_service.py` + `POST /admin/coding-challenges/generate` (LLM propone → admin aprueba), upload docs multipart + BackgroundTasks + reprocess, gestión users con rol+estado
- `services/challenge_generator_service.py` para IA preview en admin
- `AdminPage` 5 tabs [Corpus RAG | Contenido | Usuarios | Banco Fallback | Niveles] con árbol colapsable + tabla + upload drag & click

### ✅ FASE 7.5 — Rebrand institucional + Desafíos IA per-estudiante (completada 2026-04-17)
- **Rebrand IESTP RFA Chiclayo:**
  - `tailwind.config.js` paleta: `primary` azul institucional, `institutional` navy, `heritage` oro (academia + Alemania), `peru` rojo. Shadows `brand-sm/md/lg`, gradientes `bg-brand-hero` + `bg-heritage-accent`, animación `fade-in-up`
  - `index.css` CSS vars HSL + focus-visible global + prefers-reduced-motion + skip-link
  - `public/favicon.svg` escudo navy + oro + monograma "RFA"
  - `components/brand/BrandLogo.tsx` (compact/full/stacked + onDark)
  - Sidebar con brand header + barra heritage + footer institucional
  - Navbar con eyebrow "IESTP RFA · Chiclayo" + avatar iniciales + rol español
  - Footer institucional en AppLayout
  - LoginPage split 2-col desktop con panel hero navy + bullets + formulario card
  - DashboardPage hero gradiente navy + logros con chips heritage
  - Skip link WCAG + focus rings consistentes + touch 44×44
- **Diferenciación admin (no evaluación):**
  - `LevelGuard` bypass para rol admin
  - `useAuth.useLogin` redirige admin → `/admin`, estudiante → `/dashboard`
  - `LevelBadge` + `ReassessmentModal` + `EntryAssessmentPage` gated por `!isAdmin`
- **Desafíos IA per-estudiante (migración 004):**
  - `coding_challenges` gana `is_ai_generated`, `generated_for_user_id`, `student_level` + índices
  - `services/coding_generator_service.py`: `get_or_generate_for_student()` genera por LLM adaptado a nivel (beginner→easy, intermediate→medium, advanced→hard); `regenerate_for_student()` fuerza uno nuevo; fallback clona catálogo seed si Ollama cae
  - `GET /coding/topic/{id}` retorna un desafío del estudiante (AI o fallback) en vez de lista
  - `POST /coding/topic/{id}/regenerate` genera nuevo
  - `topic_completion_service` actualizado: coding_required = tema tiene catálogo; coding_passed = user tiene submission ≥60 en cualquier challenge del tema
  - `routers/modules.py` + `routers/topics.py` calculan `has_coding_challenge` filtrando `is_ai_generated=false` (solo catálogo marca tema)
  - `TopicResponse.has_coding_challenge` añadido
  - Frontend: `TopicPage` botón llama `getForTopic` → toast si fallback → navega; `CodingChallengePage` chip "Generado con IA · nivel X" + botón "Regenerar con IA" con confirm

### ⏳ FASE 8 — Calidad y Piloto
- slowapi global 100 req/min/IP
- loguru JSON estructurado para prod
- Unit tests: auth/rag/progress/llm/code_eval/**entry_assessment/leveling**. Integration: auth/chat/modules/quiz/coding/**assessment**
- Lighthouse Performance ≥70, Accessibility ≥85
- Responsivo 375/768/1440px
- Firebase Hosting + Cloud Run deploy
- README instalación
- Verificación criterios aceptación

---

## ✅ CRITERIOS DE ACEPTACIÓN

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
- [ ] Lighthouse Performance ≥70 en ModulesPage
- [ ] Funcional en 375px
- [x] Textos UI en español
- [ ] Tests backend cobertura ≥60%
- [x] Rate limit chat 20/h responde 429
- [ ] README levanta desde cero

---

## ⚠️ ADVERTENCIAS CLAVE

**LLM/Hardware:** `qwen2.5:7b-instruct-q4_K_M` requiere ≥6GB RAM libre. VM e2-standard-2 (8GB total) funciona justo. Si respuestas >20s → cambiar a `llama3.2:3b-instruct-q4_K_M` (2GB, más rápido, menor calidad). Dev local sin GPU es lento, normal.

**pgvector IVFFlat:** **NO crear índice antes de ingestar datos.** Crear DESPUÉS: `CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);` · lists ≈ sqrt(n_chunks).

**RAG vs Fine-tuning:** Sistema usa RAG puro, no fine-tuning. "Entrenamiento" en tesis = construir pipeline RAG con corpus. Aproximación estándar para apps educativas.

**Servicios eliminados:**
- Pub/Sub → `fastapi.BackgroundTasks` (suficiente para volumen piloto)
- Cloud Scheduler → `APScheduler` embebido en FastAPI
- Cloud Memorystore → Redis en mismo VM via VPC Connector (ahorra ~S/.75/mes)
- Cloud CDN+LB → Firebase Hosting (CDN global + HTTPS + `firebase deploy` gratis)

**asyncpg + pgvector:** Vector literal **inline** en SQL. No parametrizar con `::vector` cast (incompatible). Ver `rag_service.py`.

**Ollama format="json":** Usar wrapper objeto `{"questions":[...]}`, no array desnudo. Parser robusto en `llm_service.py`.

---

## 🧪 VALIDACIONES DEL SISTEMA

Matriz de pruebas por flujo. Cada ítem debe reproducirse end-to-end antes de declarar piloto listo.

### ✅ Resultados de validación end-to-end (ejecutada 2026-04-17)

Stack levantado (`docker compose up -d postgres redis backend`) + migración 004 aplicada manualmente (nota: `docker-compose.yml` ahora monta `./backend/alembic` para evitar perder migraciones futuras) + curl contra `http://localhost:8000/api/v1`:

| Ítem | Estado | Evidencia |
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

### 👨‍🎓 Flujos de estudiante

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
- [ ] RAG: embed question → pgvector cosine top5 con threshold 0.70 → build prompt con historial (5 rondas) → qwen2.5 temp=0.3
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

### 👨‍💼 Flujos de administrador

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
- [ ] `process_document` pipeline: parse → clean → RecursiveCharacterTextSplitter (500/50) → mxbai-embed-large → inserta `document_chunks` con vector[1024]
- [ ] Botón "Reintentar" si status=error
- [ ] Borrar elimina row + archivo físico + chunks (cascade)

#### V10. Tab Contenido
- [ ] Árbol colapsable Módulo → Tema → Quiz + Coding
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
- [ ] pgvector threshold 0.70 filtra contexto irrelevante en RAG
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

### ⚠️ Casos que deben fallar graciosamente

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

*v2.1 — Fases 1 a 7.5 completadas. Fase 8 (quality + piloto) pendiente.*