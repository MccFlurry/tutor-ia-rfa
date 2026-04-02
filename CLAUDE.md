# CLAUDE.md — Tutor con IA Generativa para Aplicaciones Móviles
## Prompt Maestro para Claude Code — Versión 2.0 (Stack Revisado)

---

## 🎯 CONTEXTO DEL PROYECTO

Eres el desarrollador principal de un **Sistema de Tutoría Inteligente (STI) con IA Generativa** para la asignatura de Aplicaciones Móviles del IESTP "República Federal de Alemania" (RFA), Chiclayo, Perú. Este sistema es el producto tecnológico de una tesis de pregrado de Ingeniería de Sistemas de la USAT.

El sistema permite a los estudiantes:
1. Estudiar el contenido del curso de Aplicaciones Móviles a través de 5 módulos interactivos
2. Consultar a un tutor IA conversacional privado basado en arquitectura RAG
3. Realizar autoevaluaciones con retroalimentación inmediata
4. Hacer seguimiento gamificado de su progreso académico

**REGLA ABSOLUTA:** El LLM debe ejecutarse de forma **completamente privada** en infraestructura propia (Ollama). No se usa ninguna API externa de pago (OpenAI, Anthropic, Gemini, etc.). El conocimiento del dominio se provee exclusivamente mediante RAG.

El sistema se evaluará con **ISO/IEC 25010** y **SUS (mínimo 68 puntos)** con 10-15 estudiantes del IESTP RFA.

**Idioma de la interfaz:** Todo en **español peruano**.

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Stack Tecnológico Definitivo

```
┌──────────────────────────────────────────────────────────────┐
│           FRONTEND (React 18 + Vite + TypeScript)            │
│      Tailwind CSS 3 | shadcn/ui | Zustand | TanStack Query  │
│         React Router v6 | react-hot-toast | Lucide Icons     │
│               🚀 Deploy: Firebase Hosting (GRATIS)           │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTPS / REST (JSON)
┌──────────────────────▼───────────────────────────────────────┐
│              BACKEND (FastAPI + Python 3.12)                  │
│  SQLAlchemy 2.0 (async) | asyncpg | Alembic | Pydantic v2   │
│  LangChain | slowapi | loguru | APScheduler | python-jose    │
│  passlib[bcrypt] | httpx | python-multipart | pypdf          │
│          🚀 Deploy: Google Cloud Run (casi GRATIS)            │
└──────┬──────────────────────────────────────┬────────────────┘
       │ TCP (VPC privada)                     │ TCP (VPC privada)
┌──────▼──────────────────────────────────────▼────────────────┐
│         COMPUTE ENGINE — e2-standard-2 SPOT (~$5-15/mes)     │
│                                                              │
│  ┌─────────────────────────┐    ┌────────────────────────┐  │
│  │  Ollama (LLM privado)   │    │   Redis 7 (caché)      │  │
│  │  qwen2.5:7b-q4_K_M      │    │   docker container     │  │
│  │  mxbai-embed-large      │    │                        │  │
│  │  Puerto: 11434 (local)  │    │   Puerto: 6379 (local) │  │
│  └─────────────────────────┘    └────────────────────────┘  │
│                                                              │
│  OS: Ubuntu 22.04 LTS | Docker + Docker Compose             │
└──────────────────────────────────────────────────────────────┘
       │ Cloud SQL Auth Proxy
┌──────▼──────────────────┐
│  Cloud SQL PostgreSQL 16 │
│  + extensión pgvector    │
│  Instancia: db-f1-micro  │
│  (~S/. 26/mes)           │
└──────────────────────────┘

Seguridad transversal:
- VPC privada: Cloud Run y Compute Engine se comunican sin exponerse a Internet
- VPC Connector: Cloud Run → recursos privados (PostgreSQL, VM)
- IAM mínimo privilegio: cada servicio solo accede a lo que necesita
- Secret Manager: todas las credenciales y claves
- SSL/HTTPS: Firebase Hosting provee certificado SSL gratuito
```

### Arquitectura del Pipeline RAG

```
INGESTA (Admin sube documento):
  Archivo (PDF/DOCX/TXT)
       ↓
  [BackgroundTask FastAPI]
       ↓
  Parser (pypdf / python-docx)
       ↓
  TextSplitter (LangChain, chunk_size=500, overlap=50)
       ↓
  Ollama mxbai-embed-large → vector[1024]
       ↓
  pgvector (tabla document_chunks)

CONSULTA (Estudiante pregunta al tutor):
  Pregunta del usuario
       ↓
  Ollama mxbai-embed-large → query_vector[1024]
       ↓
  pgvector similarity search (cosine, top_k=5, threshold≥0.70)
       ↓
  Chunks recuperados + historial de conversación (últimas 5 rondas)
       ↓
  Prompt aumentado [system_prompt + context + history + question]
       ↓
  Ollama qwen2.5:7b-q4_K_M → respuesta en español
       ↓
  Caché Redis (TTL: 3600s para respuestas frecuentes)
       ↓
  Respuesta al frontend + fuentes citadas
```

---

## 📁 ESTRUCTURA DEL REPOSITORIO

```
tutor-ia-rfa/
├── CLAUDE.md                        ← Este archivo (referencia siempre antes de codificar)
├── .env.example                     ← Variables de entorno de ejemplo
├── .env                             ← Variables reales (NO commitear)
├── .gitignore
├── docker-compose.yml               ← Entorno de desarrollo local (TODOS los servicios)
├── docker-compose.vm.yml            ← Para el VM de Compute Engine (Ollama + Redis)
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   └── app/
│       ├── main.py                  ← Entry point FastAPI
│       ├── config.py                ← Settings con Pydantic BaseSettings
│       ├── database.py              ← Engine async SQLAlchemy + get_db
│       ├── dependencies.py          ← Dependencias inyectables (auth, db, redis)
│       │
│       ├── models/                  ← Modelos SQLAlchemy (tablas)
│       │   ├── __init__.py          ← Exporta todos los modelos (para Alembic)
│       │   ├── user.py
│       │   ├── module.py
│       │   ├── topic.py
│       │   ├── quiz.py
│       │   ├── progress.py
│       │   ├── achievement.py
│       │   ├── chat.py
│       │   └── document.py
│       │
│       ├── schemas/                 ← Esquemas Pydantic (request + response DTOs)
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── user.py
│       │   ├── module.py
│       │   ├── topic.py
│       │   ├── quiz.py
│       │   ├── progress.py
│       │   ├── achievement.py
│       │   ├── chat.py
│       │   └── document.py
│       │
│       ├── routers/                 ← Endpoints FastAPI organizados por dominio
│       │   ├── __init__.py
│       │   ├── auth.py              ← /auth/*
│       │   ├── users.py             ← /users/*
│       │   ├── modules.py           ← /modules/*
│       │   ├── topics.py            ← /topics/*
│       │   ├── quiz.py              ← /quiz/*
│       │   ├── progress.py          ← /progress/*
│       │   ├── achievements.py      ← /achievements/*
│       │   ├── chat.py              ← /chat/*
│       │   ├── dashboard.py         ← /dashboard
│       │   └── admin.py             ← /admin/* (solo rol admin)
│       │
│       ├── services/                ← Lógica de negocio (sin acceso directo a HTTP)
│       │   ├── __init__.py
│       │   ├── auth_service.py      ← Login, registro, tokens JWT
│       │   ├── progress_service.py  ← Cálculo de progreso y estadísticas
│       │   ├── achievement_service.py ← Detección y otorgamiento de logros
│       │   ├── rag_service.py       ← Pipeline RAG principal (búsqueda + generación)
│       │   ├── llm_service.py       ← Cliente Ollama (generación de texto)
│       │   ├── embed_service.py     ← Cliente Ollama (generación de embeddings)
│       │   └── ingest_service.py    ← Procesamiento de documentos para el corpus
│       │
│       └── utils/
│           ├── __init__.py
│           ├── security.py          ← JWT encode/decode, bcrypt hash/verify
│           ├── chunking.py          ← Text splitting con LangChain
│           └── logger.py            ← Configuración de loguru
│
├── frontend/
│   ├── Dockerfile
│   ├── .firebaserc                  ← Configuración Firebase
│   ├── firebase.json                ← Reglas de hosting Firebase
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── components.json              ← Configuración shadcn/ui
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                  ← Router principal + QueryClient
│       ├── vite-env.d.ts
│       │
│       ├── api/                     ← Clientes HTTP con Axios
│       │   ├── client.ts            ← Instancia Axios + interceptors JWT
│       │   ├── auth.ts
│       │   ├── modules.ts
│       │   ├── topics.ts
│       │   ├── quiz.ts
│       │   ├── progress.ts
│       │   ├── achievements.ts
│       │   ├── chat.ts
│       │   ├── dashboard.ts
│       │   └── admin.ts
│       │
│       ├── store/                   ← Estado global con Zustand
│       │   ├── authStore.ts         ← Usuario autenticado, token
│       │   ├── progressStore.ts     ← Cache local del progreso
│       │   └── uiStore.ts           ← Estado de UI (sidebar open, etc.)
│       │
│       ├── components/
│       │   ├── ui/                  ← Componentes shadcn/ui instalados
│       │   │   ├── button.tsx
│       │   │   ├── card.tsx
│       │   │   ├── input.tsx
│       │   │   ├── progress.tsx
│       │   │   ├── badge.tsx
│       │   │   ├── dialog.tsx
│       │   │   ├── tabs.tsx
│       │   │   ├── toast.tsx
│       │   │   └── ...
│       │   │
│       │   ├── layout/
│       │   │   ├── Navbar.tsx       ← Barra superior con nombre de usuario y logout
│       │   │   ├── Sidebar.tsx      ← Navegación lateral con íconos
│       │   │   └── AppLayout.tsx    ← Layout base con Navbar + Sidebar + main
│       │   │
│       │   ├── auth/
│       │   │   └── AuthGuard.tsx    ← Redirect a /login si no hay token
│       │   │
│       │   ├── modules/
│       │   │   ├── ModuleCard.tsx   ← Tarjeta de módulo con progreso
│       │   │   └── TopicListItem.tsx ← Ítem de tema con estado
│       │   │
│       │   ├── topics/
│       │   │   ├── ContentRenderer.tsx ← Renderiza Markdown con código
│       │   │   └── CodeBlock.tsx    ← Bloque de código con syntax highlight
│       │   │
│       │   ├── quiz/
│       │   │   ├── QuizQuestion.tsx ← Pregunta individual con opciones
│       │   │   └── QuizResults.tsx  ← Resultado final con feedback
│       │   │
│       │   ├── chat/
│       │   │   ├── ChatMessage.tsx  ← Burbuja de mensaje (user/assistant)
│       │   │   ├── ChatSources.tsx  ← Fuentes RAG colapsables
│       │   │   └── TypingIndicator.tsx ← Animación "tutor escribiendo..."
│       │   │
│       │   └── achievements/
│       │       └── AchievementCard.tsx ← Tarjeta de logro (obtenido/bloqueado)
│       │
│       ├── pages/
│       │   ├── LoginPage.tsx
│       │   ├── DashboardPage.tsx
│       │   ├── ModulesPage.tsx
│       │   ├── ModuleDetailPage.tsx
│       │   ├── TopicPage.tsx
│       │   ├── ChatPage.tsx
│       │   ├── ProgressPage.tsx
│       │   └── AdminPage.tsx
│       │
│       ├── hooks/
│       │   ├── useAuth.ts           ← Login, logout, estado de autenticación
│       │   ├── useProgress.ts       ← Consulta y actualización de progreso
│       │   └── useChat.ts           ← Envío de mensajes, historial
│       │
│       ├── types/                   ← Interfaces TypeScript (espejo de los schemas)
│       │   ├── auth.ts
│       │   ├── module.ts
│       │   ├── topic.ts
│       │   ├── quiz.ts
│       │   ├── progress.ts
│       │   ├── achievement.ts
│       │   └── chat.ts
│       │
│       └── lib/
│           └── utils.ts             ← Función cn() de shadcn + utilidades
│
├── scripts/
│   ├── seed_db.py                   ← Popula BD con módulos, temas y logros del sílabo RFA
│   ├── setup_ollama.sh              ← Script para descargar modelos en Ollama
│   └── ingest_course_docs.py        ← Ingestar documentos del curso al RAG
│
└── infra/
    ├── vm_setup.sh                  ← Script de configuración del VM de Compute Engine
    └── gcp_commands.sh              ← Comandos gcloud para desplegar en producción
```

---

## 🗄️ ESQUEMA DE BASE DE DATOS

Implementar con SQLAlchemy 2.0 declarativo async. Ejecutar con Alembic.

**IMPORTANTE:** pgvector debe estar habilitado antes de la primera migración:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

```sql
-- USUARIOS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',     -- 'student' | 'admin'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    avatar_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- MÓDULOS DEL CURSO (5 módulos del sílabo IESTP RFA)
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL UNIQUE,             -- 1 a 5
    icon_name VARCHAR(100),                          -- nombre del ícono Lucide
    color_hex VARCHAR(7) DEFAULT '#3b82f6',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TEMAS DENTRO DE MÓDULOS
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,                           -- Markdown completo del tema
    video_url VARCHAR(500),                          -- URL YouTube (opcional)
    order_index INTEGER NOT NULL,
    estimated_minutes INTEGER DEFAULT 10,
    has_quiz BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(module_id, order_index)
);

-- PREGUNTAS DE AUTOEVALUACIÓN
CREATE TABLE quiz_questions (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    options JSONB NOT NULL,                          -- ["A: ...", "B: ...", "C: ...", "D: ..."]
    correct_option_index INTEGER NOT NULL,           -- 0, 1, 2 o 3
    explanation TEXT,                                -- Explicación de la respuesta correcta
    order_index INTEGER NOT NULL DEFAULT 0
);

-- PROGRESO POR TEMA
CREATE TABLE user_topic_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    time_spent_seconds INTEGER NOT NULL DEFAULT 0,
    first_visited_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, topic_id)
);

-- INTENTOS EN AUTOEVALUACIONES
CREATE TABLE quiz_attempts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    score FLOAT NOT NULL,                            -- 0.0 a 1.0 (porcentaje de aciertos)
    answers JSONB NOT NULL,                          -- {question_id: selected_index}
    is_passed BOOLEAN NOT NULL,                      -- score >= 0.60
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- LOGROS DEL SISTEMA
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    badge_emoji VARCHAR(10) NOT NULL,
    badge_color VARCHAR(7) DEFAULT '#3b82f6',
    condition_type VARCHAR(50) NOT NULL,
    -- Tipos: 'first_topic', 'module_completed', 'streak_days',
    --        'chat_messages', 'course_completed', 'quiz_perfect'
    condition_value INTEGER NOT NULL,
    condition_module_id INTEGER REFERENCES modules(id)
);

-- LOGROS OBTENIDOS POR USUARIO
CREATE TABLE user_achievements (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id INTEGER NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    earned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

-- SESIONES DE CHAT
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'Nueva conversación',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- MENSAJES DE CHAT
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,                       -- 'user' | 'assistant'
    content TEXT NOT NULL,
    sources JSONB,                                   -- [{content, document_name, similarity}]
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- DOCUMENTOS DEL CORPUS RAG
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_filename VARCHAR(500) NOT NULL,
    stored_filename VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',   -- 'pending'|'processing'|'active'|'error'
    error_message TEXT,
    chunk_count INTEGER DEFAULT 0,
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- CHUNKS VECTORIALES (NÚCLEO DEL RAG)
-- IMPORTANTE: dimensión 1024 para mxbai-embed-large
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1024),                          -- mxbai-embed-large genera 1024 dims
    chunk_index INTEGER NOT NULL,
    metadata JSONB,                                  -- {"source": "...", "module": "...", ...}
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice IVFFlat para búsqueda vectorial eficiente
-- Crear DESPUÉS de insertar datos significativos (no antes)
-- El parámetro 'lists' debe ser aproximadamente sqrt(número_de_chunks)
CREATE INDEX idx_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- Índices adicionales para performance
CREATE INDEX idx_user_progress_user ON user_topic_progress(user_id);
CREATE INDEX idx_user_progress_topic ON user_topic_progress(topic_id);
CREATE INDEX idx_quiz_attempts_user ON quiz_attempts(user_id);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_document_chunks_document ON document_chunks(document_id);
```

---

## 🔌 API REST — ENDPOINTS COMPLETOS

Base URL en desarrollo: `http://localhost:8000/api/v1`
Base URL en producción: `https://[CLOUD_RUN_URL]/api/v1`

Todos los endpoints (excepto `/auth/login` y `/auth/register`) requieren header:
```
Authorization: Bearer <access_token>
```

### `/auth` — Autenticación
```
POST /auth/register          Body: {email, full_name, password}
                             Returns: {user, access_token, refresh_token}

POST /auth/login             Body: {email, password}
                             Returns: {user, access_token, refresh_token}

POST /auth/refresh           Body: {refresh_token}
                             Returns: {access_token}

POST /auth/logout            Body: {refresh_token}
                             Returns: {message}
```

### `/users` — Perfil de Usuario
```
GET  /users/me               Returns: UserSchema
PUT  /users/me               Body: {full_name?, avatar_url?}
PUT  /users/me/password      Body: {current_password, new_password}
```

### `/dashboard` — Panel Principal
```
GET  /dashboard              Returns: {
                               user_name,
                               overall_progress_pct,
                               total_topics_completed,
                               last_accessed_topic: {id, title, module_title},
                               recommended_modules: [{id, title, progress_pct}],
                               recent_achievements: [AchievementSchema]
                             }
```

### `/modules` — Módulos del Curso
```
GET  /modules                Returns: [{
                               id, title, description, order_index,
                               icon_name, color_hex,
                               total_topics, completed_topics,
                               progress_pct, is_locked
                             }]

GET  /modules/{id}           Returns: ModuleSchema + [{
                               id, title, order_index,
                               estimated_minutes, has_quiz,
                               status: 'not_started'|'in_progress'|'completed'
                             }]
```

### `/topics` — Temas
```
GET  /topics/{id}            Returns: {id, title, content_markdown,
                               video_url, estimated_minutes, has_quiz,
                               module: {id, title}, progress_info}

POST /topics/{id}/visit      Body: {} → Registra visita, crea/actualiza progress
POST /topics/{id}/complete   Body: {} → Marca como completado manualmente
POST /topics/{id}/time       Body: {seconds: int} → Acumula tiempo de estudio
```

### `/quiz` — Autoevaluaciones (Generadas por IA)

**Arquitectura:** Las preguntas son generadas dinámicamente por el LLM (Ollama qwen2.5)
cada vez que el estudiante solicita un quiz. Cada intento genera preguntas únicas y
personalizadas basadas en el contenido del tema. Si Ollama no está disponible, se usan
las preguntas estáticas de la tabla `quiz_questions` como fallback.

**Flujo:**
1. Frontend solicita quiz → Backend envía contenido del tema al LLM
2. LLM genera N preguntas en JSON → respuestas correctas se guardan en Redis (TTL 30min)
3. Frontend recibe preguntas SIN respuestas + session_id
4. Estudiante responde → Backend compara contra Redis → devuelve feedback
5. Si aprueba (≥60%) → marca tema completado → verifica logros

```
GET  /quiz/topic/{topic_id}        Returns: {
                                     session_id,
                                     questions: [{id, question_text, options}]
                                   }
                                   (Genera preguntas via LLM, almacena respuestas en Redis)
                                   (Fallback: preguntas estáticas de BD si LLM falla)

POST /quiz/topic/{topic_id}/submit Body: {session_id, answers: {question_id: selected_index}}
                                   Returns: {
                                     score, is_passed,
                                     feedback: [{
                                       question_id, question_text,
                                       selected_index, correct_index,
                                       is_correct, explanation
                                     }],
                                     attempt_id
                                   }
                                   Errores: 410 si sesión expirada, 503 si servicio no disponible

GET  /quiz/topic/{topic_id}/history Returns: [{
                                     attempted_at, score, is_passed
                                   }]
```

### `/progress` — Seguimiento de Progreso
```
GET  /progress               Returns: {
                               overall_pct, total_time_seconds,
                               topics_completed, quiz_avg_score,
                               modules: [{id, title, pct, completed, total}]
                             }

GET  /progress/activity      Returns: [{
                               type: 'topic_completed'|'quiz_passed'|'achievement',
                               description, timestamp
                             }] (últimas 20 actividades)
```

### `/achievements` — Logros
```
GET  /achievements           Returns: [{
                               id, name, description, badge_emoji,
                               badge_color, is_earned, earned_at?
                             }]
```

### `/chat` — Tutor IA
```
GET  /chat/sessions          Returns: [{id, title, last_message_at}]
POST /chat/sessions          Body: {} → Returns: {id, title, created_at}

GET  /chat/sessions/{id}/messages  Returns: [{
                                     id, role, content, sources?, created_at
                                   }]

POST /chat/sessions/{id}/message   Body: {content: string}
                                   Returns: {
                                     message_id,
                                     role: 'assistant',
                                     content: string,
                                     sources: [{content_preview, document_name, similarity}],
                                     created_at
                                   }
                                   Errores: 429 si supera rate limit

DELETE /chat/sessions/{id}         Returns: {message}
```

### `/admin` — Panel de Administración (Solo rol 'admin')
```
-- Usuarios
GET  /admin/users                  Returns: [UserSchema] (paginado)
PUT  /admin/users/{id}             Body: {role?, is_active?}

-- Documentos del corpus RAG
GET  /admin/documents              Returns: [DocumentSchema]
POST /admin/documents              Body: multipart/form-data (file)
                                   Returns: {id, status: 'processing'}
DELETE /admin/documents/{id}       Elimina documento y todos sus chunks
POST /admin/documents/{id}/reprocess  Reprocesa un documento con error

-- Módulos y contenido
GET  /admin/modules                Returns: módulos con conteo de temas
POST /admin/modules                Body: {title, description, order_index, icon_name}
PUT  /admin/modules/{id}           Body: campos parciales del módulo
DELETE /admin/modules/{id}

GET  /admin/modules/{id}/topics    Returns: temas del módulo
POST /admin/modules/{id}/topics    Body: {title, content, video_url?, estimated_minutes, has_quiz}
PUT  /admin/topics/{id}
DELETE /admin/topics/{id}

GET  /admin/topics/{id}/questions  Returns: preguntas del quiz
POST /admin/topics/{id}/questions  Body: {question_text, options[4], correct_option_index, explanation}
PUT  /admin/questions/{id}
DELETE /admin/questions/{id}
```

---

## 🤖 IMPLEMENTACIÓN DEL PIPELINE RAG

### `app/services/rag_service.py` — Estructura de referencia

```python
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.utils.logger import logger
import json

SYSTEM_PROMPT = """Eres un tutor académico experto en el curso de Aplicaciones Móviles \
del IESTP República Federal de Alemania (RFA) en Chiclayo, Perú.

Tu especialidad es guiar a los estudiantes en el aprendizaje de desarrollo de \
aplicaciones Android usando Kotlin. Enseñas con paciencia, claridad y con ejemplos \
prácticos adaptados al nivel técnico del IESTP.

REGLAS:
1. Responde SIEMPRE en español peruano claro y académico.
2. Basa tus respuestas en el CONTEXTO DEL CURSO que se te provee.
3. Si la pregunta no está relacionada con el curso, indícalo amablemente y redirige.
4. Incluye ejemplos de código Kotlin cuando sea útil (dentro de bloques ```kotlin).
5. Si el contexto no tiene información suficiente, admítelo honestamente.
6. NUNCA inventes información técnica ni cites fuentes que no estén en el contexto.
7. Sé motivador y reconoce el esfuerzo del estudiante.

CONTEXTO DEL CURSO (material recuperado):
{context}

HISTORIAL DE LA CONVERSACIÓN:
{history}
"""

class RAGService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            model=settings.OLLAMA_EMBED_MODEL,   # "mxbai-embed-large"
            base_url=settings.OLLAMA_BASE_URL
        )
        self.llm = OllamaLLM(
            model=settings.OLLAMA_MODEL,          # "qwen2.5:7b-instruct-q4_K_M"
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3,                      # Bajo: respuestas más precisas y menos creativas
            num_ctx=4096,                         # Ventana de contexto
            timeout=settings.OLLAMA_TIMEOUT
        )

    async def query(
        self,
        question: str,
        session_history: list[dict],
        db: AsyncSession,
        redis_client
    ) -> dict:
        """
        Ejecuta el pipeline RAG completo.
        Retorna: {"content": str, "sources": list}
        """
        # 1. Verificar caché Redis
        cache_key = f"rag:{hash(question)}"
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"RAG cache hit para query: {question[:50]}")
            return json.loads(cached)

        # 2. Generar embedding de la pregunta
        query_embedding = await self.embeddings.aembed_query(question)

        # 3. Búsqueda semántica en pgvector
        chunks = await self._semantic_search(query_embedding, db, top_k=5)

        if not chunks:
            return {
                "content": "No encontré información específica sobre eso en el material del curso. "
                          "¿Podrías reformular tu pregunta o consultarme sobre un tema "
                          "específico del curso de Aplicaciones Móviles?",
                "sources": []
            }

        # 4. Construir contexto desde los chunks recuperados
        context = self._build_context(chunks)

        # 5. Construir historial de conversación (últimas 5 rondas)
        history_text = self._build_history(session_history[-10:])  # 5 rondas = 10 mensajes

        # 6. Construir prompt aumentado
        full_prompt = SYSTEM_PROMPT.format(context=context, history=history_text)

        # 7. Llamar al LLM
        response = await self.llm.ainvoke(
            f"{full_prompt}\n\nPREGUNTA DEL ESTUDIANTE: {question}\n\nRESPUESTA:"
        )

        # 8. Preparar fuentes para citar
        sources = [
            {
                "content_preview": chunk["content"][:150] + "...",
                "document_name": chunk["metadata"].get("source", "Material del curso"),
                "similarity": round(chunk["similarity"], 3)
            }
            for chunk in chunks if chunk["similarity"] >= 0.75
        ]

        result = {"content": response, "sources": sources}

        # 9. Cachear respuesta (TTL: 1 hora)
        await redis_client.setex(cache_key, 3600, json.dumps(result))

        return result

    async def _semantic_search(
        self, query_embedding: list, db: AsyncSession, top_k: int = 5
    ) -> list[dict]:
        """Búsqueda de similitud coseno en pgvector."""
        from sqlalchemy import text
        query = text("""
            SELECT
                content,
                metadata,
                1 - (embedding <=> :query_vec::vector) AS similarity
            FROM document_chunks
            WHERE 1 - (embedding <=> :query_vec::vector) >= :threshold
            ORDER BY embedding <=> :query_vec::vector
            LIMIT :top_k
        """)
        result = await db.execute(query, {
            "query_vec": str(query_embedding),
            "threshold": 0.70,
            "top_k": top_k
        })
        rows = result.fetchall()
        return [{"content": r.content, "metadata": r.metadata or {}, "similarity": r.similarity}
                for r in rows]

    def _build_context(self, chunks: list[dict]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source", "Material del curso")
            parts.append(f"[Fragmento {i} — Fuente: {source}]\n{chunk['content']}")
        return "\n\n---\n\n".join(parts)

    def _build_history(self, messages: list[dict]) -> str:
        if not messages:
            return "Sin historial previo."
        parts = []
        for msg in messages:
            role = "Estudiante" if msg["role"] == "user" else "Tutor"
            parts.append(f"{role}: {msg['content'][:300]}")
        return "\n".join(parts)
```

### `app/services/ingest_service.py` — Ingesta de documentos

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
import pypdf
import docx

class IngestService:
    CHUNK_SIZE = 500       # caracteres por chunk
    CHUNK_OVERLAP = 50     # solapamiento entre chunks

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    async def process_document(self, document_id: str, file_path: str, db: AsyncSession):
        """
        Pipeline completo: parsear → limpiar → dividir → embeddings → guardar.
        Se ejecuta como BackgroundTask en FastAPI.
        """
        try:
            # 1. Actualizar estado a 'processing'
            await self._update_status(document_id, 'processing', db)

            # 2. Parsear el documento
            raw_text = await self._parse(file_path)

            # 3. Limpiar texto
            clean_text = self._clean(raw_text)

            # 4. Dividir en chunks
            chunks = self.splitter.split_text(clean_text)

            # 5. Generar embeddings (en batches de 10 para no saturar Ollama)
            embeddings_model = OllamaEmbeddings(
                model=settings.OLLAMA_EMBED_MODEL,
                base_url=settings.OLLAMA_BASE_URL
            )
            all_embeddings = await embeddings_model.aembed_documents(chunks)

            # 6. Guardar en BD
            await self._save_chunks(document_id, chunks, all_embeddings, file_path, db)

            # 7. Marcar como activo
            await self._update_status(document_id, 'active', db, chunk_count=len(chunks))
            logger.info(f"Documento {document_id} procesado: {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Error procesando documento {document_id}: {e}")
            await self._update_status(document_id, 'error', db, error=str(e))

    async def _parse(self, file_path: str) -> str:
        if file_path.endswith('.pdf'):
            reader = pypdf.PdfReader(file_path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        else:  # .txt
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

    def _clean(self, text: str) -> str:
        import re
        text = re.sub(r'\s+', ' ', text)        # normalizar espacios
        text = re.sub(r'\n{3,}', '\n\n', text)  # máximo 2 saltos de línea consecutivos
        return text.strip()
```

---

## 🎨 FRONTEND — DISEÑO Y COMPONENTES

### Configuración de Tailwind y shadcn/ui

```bash
# Instalar shadcn/ui y componentes necesarios
npx shadcn@latest init
npx shadcn@latest add button card input label progress badge
npx shadcn@latest add dialog tabs toast separator skeleton
npx shadcn@latest add scroll-area textarea alert
```

### Paleta de Colores del Sistema

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50:  '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',   // Azul institucional USAT/IESTP
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        // Estados de módulos
        module: {
          locked:    '#9ca3af',  // gris
          progress:  '#3b82f6',  // azul
          completed: '#22c55e',  // verde
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    }
  }
}
```

### Descripción de Páginas

**`LoginPage.tsx`**
- Centrado en pantalla con fondo azul oscuro degradado
- Tarjeta blanca centrada: logo 📱, "Sistema de Tutoría Inteligente", "Curso de Aplicaciones Móviles — IESTP RFA"
- Campos: correo electrónico, contraseña (con toggle mostrar/ocultar)
- Checkbox "Recordar mi sesión"
- Botón "Ingresar" (azul primary, full-width)
- Link "¿Olvidaste tu contraseña?"
- Validación: errores en rojo bajo cada campo al perder el foco

**`DashboardPage.tsx`**
- Saludo: "¡Hola de nuevo, [nombre]! 👋"
- Banner hero: "Continuar donde lo dejaste" → último tema con barra de progreso del módulo + botón "Continuar"
- Sección "Tu progreso general": círculo animado con porcentaje grande
- Grid de recomendaciones: 3 tarjetas de módulos con progreso individual
- Sección "Logros recientes": últimas 3 insignias obtenidas

**`ModulesPage.tsx`**
- Grid responsivo (1 col mobile, 2 col tablet, 3 col desktop)
- Cada `ModuleCard`: ícono coloreado, título, descripción breve, barra de progreso horizontal, estado badge (Bloqueado/En progreso/Completado)
- Módulos bloqueados: grayscale + ícono candado + tooltip "Completa el módulo anterior"

**`ModuleDetailPage.tsx`**
- Header: ícono + título del módulo + barra de progreso del módulo
- Breadcrumb: Módulos > [Módulo N]
- Lista de temas ordenada con estado visual:
  - ✅ Verde: completado
  - 🔵 Azul pulsante: en progreso
  - ⬜ Gris: pendiente
- Cada ítem: título, tiempo estimado, botón "Ver tema"

**`TopicPage.tsx`**
- Breadcrumb: Módulos > [Módulo] > [Tema]
- Panel lateral derecho (desktop): botón flotante "Consultar al Tutor IA" que abre modal de chat
- Área de contenido principal: renderizador Markdown con `react-markdown` + `react-syntax-highlighter`
  - Tipografía legible (Plus Jakarta Sans 16px, line-height 1.8)
  - Bloques de código: tema oscuro (vscDarkPlus), con botón "Copiar código"
  - Videos: iframe YouTube responsivo (aspect ratio 16:9)
- Barra inferior fija: botón "← Tema Anterior" | indicador "X de Y" | botón "Siguiente Tema →"
- Botón "Ir a la Autoevaluación" (si el tema tiene quiz)
- Botón "Marcar como completado" (si no tiene quiz)

**`ChatPage.tsx`**
- Layout de 2 columnas: sidebar de sesiones (izq) + área de chat (der)
- Sidebar: botón "Nueva conversación" + lista de sesiones con título y fecha
- Área de chat:
  - Burbujas: usuario a la derecha (azul), tutor a la izquierda (gris claro)
  - Respuestas del tutor con Markdown renderizado (código, negritas, listas)
  - Desplegable "Fuentes del tutor" bajo cada respuesta del asistente
  - Indicador animado "✦ escribiendo..." mientras el LLM procesa
  - Contador de mensajes restantes: "X de 20 consultas disponibles esta hora"
- Input: `Textarea` que crece automáticamente + botón enviar (Enter envía, Shift+Enter nueva línea)

**`ProgressPage.tsx`**
- Métricas globales en 3 tarjetas horizontales: % completado, lecciones totales, promedio en quizzes
- Barras de progreso por módulo (etiqueta + porcentaje + barra coloreada)
- Sección "Logros e Insignias": grid de tarjetas con emoji + nombre + descripción + estado
- Historial de actividad reciente (lista cronológica)

**`AdminPage.tsx`** — Solo admins
- Tabs: "Corpus RAG" | "Contenido del Curso" | "Usuarios"
- Tab "Corpus RAG":
  - Tabla: nombre del archivo, fecha, estado (badge), N° de chunks, acciones
  - Zona de drag & drop para subir documentos (PDF, DOCX, TXT)
  - Estado "Procesando..." con spinner animado
- Tab "Contenido del Curso":
  - Árbol colapsable: Módulo → Lista de temas → Lista de preguntas
  - Botones CRUD en cada nivel
  - Editor de contenido Markdown inline para temas

---

## 📄 DATOS INICIALES — SCRIPT `seed_db.py`

Ejecutar DESPUÉS de las migraciones de Alembic:

### Módulos del Curso (5 módulos del sílabo IESTP RFA)
```python
modules = [
    {
        "title": "Fundamentos y Preparación del Entorno",
        "description": "Introduce el desarrollo móvil en Android: ecosistema, herramientas de desarrollo y configuración del entorno de programación con Android Studio.",
        "order_index": 1,
        "icon_name": "smartphone",
        "color_hex": "#6366f1"   # índigo
    },
    {
        "title": "Lógica de Programación en Kotlin",
        "description": "Domina las bases de la programación en Kotlin: variables, operadores, estructuras de control, funciones y los fundamentos de la Programación Orientada a Objetos.",
        "order_index": 2,
        "icon_name": "code-2",
        "color_hex": "#0ea5e9"   # azul cielo
    },
    {
        "title": "Elaboración de Interfaces de Usuario (UI)",
        "description": "Diseña interfaces Android profesionales con XML: layouts, componentes visuales, RecyclerView y CardView para presentar datos de forma atractiva.",
        "order_index": 3,
        "icon_name": "layout-panel-top",
        "color_hex": "#22c55e"   # verde
    },
    {
        "title": "Componentes Android y Gestión de Datos",
        "description": "Implementa la lógica de navegación entre pantallas (Activities e Intents), almacenamiento local (SQLite, SharedPreferences) y consumo de APIs REST con Retrofit.",
        "order_index": 4,
        "icon_name": "database",
        "color_hex": "#f59e0b"   # ámbar
    },
    {
        "title": "Funcionalidades Avanzadas y Despliegue",
        "description": "Domina el depurado con Logcat, las pruebas unitarias con JUnit y el proceso completo de publicación en Google Play Store.",
        "order_index": 5,
        "icon_name": "rocket",
        "color_hex": "#ef4444"   # rojo
    }
]
```

### Temas por Módulo (19 temas totales)
```python
topics_by_module = {
    1: [
        {"title": "Introducción al Desarrollo Móvil y Android", "estimated_minutes": 15, "has_quiz": True},
        {"title": "Instalación y Configuración de Android Studio", "estimated_minutes": 25, "has_quiz": False},
        {"title": "SDK de Android: Versiones y Compatibilidad", "estimated_minutes": 10, "has_quiz": True},
        {"title": "Tu Primera Aplicación Android en Kotlin", "estimated_minutes": 30, "has_quiz": True},
    ],
    2: [
        {"title": "Variables, Tipos de Datos y Operadores en Kotlin", "estimated_minutes": 20, "has_quiz": True},
        {"title": "Estructuras de Control: if/else, when y bucles", "estimated_minutes": 20, "has_quiz": True},
        {"title": "Funciones, Lambdas y Alcance en Kotlin", "estimated_minutes": 25, "has_quiz": True},
        {"title": "POO: Clases, Objetos y Constructores", "estimated_minutes": 25, "has_quiz": True},
        {"title": "POO: Herencia, Interfaces y Polimorfismo", "estimated_minutes": 30, "has_quiz": True},
    ],
    3: [
        {"title": "Fundamentos de XML para Layouts Android", "estimated_minutes": 20, "has_quiz": True},
        {"title": "Views básicos: TextView, Button, EditText e ImageView", "estimated_minutes": 20, "has_quiz": True},
        {"title": "Layouts: ConstraintLayout y RelativeLayout", "estimated_minutes": 25, "has_quiz": True},
        {"title": "RecyclerView y CardView para Listas de Datos", "estimated_minutes": 35, "has_quiz": True},
    ],
    4: [
        {"title": "Activities y el Ciclo de Vida de Android", "estimated_minutes": 25, "has_quiz": True},
        {"title": "Navegación entre Pantallas con Intents", "estimated_minutes": 20, "has_quiz": True},
        {"title": "Almacenamiento Local: SharedPreferences y SQLite", "estimated_minutes": 30, "has_quiz": True},
        {"title": "Consumo de APIs REST y Manejo de JSON", "estimated_minutes": 25, "has_quiz": True},
        {"title": "Retrofit para Servicios Web en Android", "estimated_minutes": 30, "has_quiz": True},
    ],
    5: [
        {"title": "Depuración de Aplicaciones con Logcat", "estimated_minutes": 20, "has_quiz": False},
        {"title": "Pruebas Unitarias con JUnit en Android", "estimated_minutes": 25, "has_quiz": True},
        {"title": "Firma y Preparación de la APK para Producción", "estimated_minutes": 20, "has_quiz": False},
        {"title": "Publicación en Google Play Store", "estimated_minutes": 30, "has_quiz": True},
    ]
}
```

### Logros a sembrar
```python
achievements = [
    {"name": "Primer Paso", "description": "Completaste tu primera lección",
     "badge_emoji": "🚀", "badge_color": "#6366f1",
     "condition_type": "first_topic", "condition_value": 1},

    {"name": "Finalizador de Módulo", "description": "Completaste todos los temas de un módulo",
     "badge_emoji": "🏆", "badge_color": "#f59e0b",
     "condition_type": "module_completed", "condition_value": 1},

    {"name": "Racha de 7 Días", "description": "Accediste a la plataforma 7 días consecutivos",
     "badge_emoji": "🔥", "badge_color": "#ef4444",
     "condition_type": "streak_days", "condition_value": 7},

    {"name": "Explorador del Tutor IA", "description": "Realizaste 10 consultas al Tutor IA",
     "badge_emoji": "🤖", "badge_color": "#0ea5e9",
     "condition_type": "chat_messages", "condition_value": 10},

    {"name": "Maestro de Kotlin", "description": "Completaste el Módulo 2 — Lógica de Programación",
     "badge_emoji": "⚡", "badge_color": "#22c55e",
     "condition_type": "module_completed", "condition_value": 2,
     "condition_module_id": 2},

    {"name": "Quiz Perfecto", "description": "Obtuviste 100% en una autoevaluación",
     "badge_emoji": "💯", "badge_color": "#8b5cf6",
     "condition_type": "quiz_perfect", "condition_value": 100},

    {"name": "Desarrollador Completo", "description": "¡Completaste el 100% del curso!",
     "badge_emoji": "🎓", "badge_color": "#10b981",
     "condition_type": "course_completed", "condition_value": 100},
]
```

---

## 🐳 DOCKER COMPOSE — ENTORNO DE DESARROLLO LOCAL

```yaml
# docker-compose.yml
version: '3.9'

services:
  # ----------------------------------------------------------------
  # Base de datos PostgreSQL con pgvector
  # ----------------------------------------------------------------
  postgres:
    image: pgvector/pgvector:pg16
    container_name: tutor_postgres
    environment:
      POSTGRES_DB: tutordb
      POSTGRES_USER: tutor_user
      POSTGRES_PASSWORD: tutor_pass_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tutor_user -d tutordb"]
      interval: 5s
      timeout: 5s
      retries: 10

  # ----------------------------------------------------------------
  # Redis para caché de respuestas RAG y rate limiting
  # ----------------------------------------------------------------
  redis:
    image: redis:7-alpine
    container_name: tutor_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ----------------------------------------------------------------
  # Ollama — LLM privado (requiere que tengas descargados los modelos)
  # Ejecutar antes: ./scripts/setup_ollama.sh
  # ----------------------------------------------------------------
  ollama:
    image: ollama/ollama:latest
    container_name: tutor_ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    # Para GPU NVIDIA, descomentar:
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: [gpu]

  # ----------------------------------------------------------------
  # Backend FastAPI
  # ----------------------------------------------------------------
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: tutor_backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+asyncpg://tutor_user:tutor_pass_dev@postgres:5432/tutordb
      REDIS_URL: redis://redis:6379/0
      OLLAMA_BASE_URL: http://ollama:11434
      ENVIRONMENT: development
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend/app:/app/app          # Hot reload en desarrollo
      - uploads_data:/app/uploads
    command: >
      sh -c "alembic upgrade head &&
             python scripts/seed_db.py &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  # ----------------------------------------------------------------
  # Frontend React + Vite
  # ----------------------------------------------------------------
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    container_name: tutor_frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_BASE_URL: http://localhost:8000/api/v1
    volumes:
      - ./frontend/src:/app/src         # Hot reload en desarrollo
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
  ollama_data:
  uploads_data:
```

### `scripts/setup_ollama.sh` — Descargar modelos

```bash
#!/bin/bash
# Ejecutar UNA SOLA VEZ antes del primer docker compose up
# Requiere que el contenedor de Ollama esté corriendo

echo "Descargando modelo LLM: qwen2.5:7b-instruct-q4_K_M (~4.5GB)..."
docker exec tutor_ollama ollama pull qwen2.5:7b-instruct-q4_K_M

echo "Descargando modelo de embeddings: mxbai-embed-large (~670MB)..."
docker exec tutor_ollama ollama pull mxbai-embed-large

echo "✅ Modelos descargados. Verificando..."
docker exec tutor_ollama ollama list
```

---

## ⚙️ VARIABLES DE ENTORNO (`.env.example`)

```bash
# ─── BASE DE DATOS ───────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://tutor_user:tutor_pass_dev@localhost:5432/tutordb

# ─── REDIS (CACHÉ) ───────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ─── OLLAMA (LLM PRIVADO) ────────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M
OLLAMA_EMBED_MODEL=mxbai-embed-large
OLLAMA_TIMEOUT=120          # segundos máximos de espera al LLM
EMBEDDING_DIMENSION=1024    # dimensiones del modelo mxbai-embed-large

# ─── SEGURIDAD JWT ───────────────────────────────────────────────
# Generar con: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=REEMPLAZAR_CON_256_BITS_ALEATORIOS
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ─── APLICACIÓN ──────────────────────────────────────────────────
ENVIRONMENT=development             # development | production
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
MAX_UPLOAD_SIZE_MB=50

# ─── RATE LIMITING ───────────────────────────────────────────────
CHAT_RATE_LIMIT_PER_HOUR=20        # consultas al tutor IA por usuario por hora
API_RATE_LIMIT_PER_MINUTE=100      # peticiones generales por IP por minuto

# ─── RAG ─────────────────────────────────────────────────────────
RAG_TOP_K=5                         # chunks a recuperar por consulta
RAG_SIMILARITY_THRESHOLD=0.70       # similitud coseno mínima para incluir chunk
RAG_CONTEXT_WINDOW=5                # rondas de historial a incluir en el prompt
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# ─── UPLOADS ─────────────────────────────────────────────────────
UPLOAD_DIR=./uploads               # directorio local de archivos subidos

# ─── ADMIN INICIAL (solo para seed) ──────────────────────────────
ADMIN_EMAIL=admin@iestprfa.edu.pe
ADMIN_PASSWORD=Admin123!
ADMIN_NAME=Administrador del Sistema
```

---

## 📦 DEPENDENCIAS

### `backend/requirements.txt`
```
# Framework web
fastapi==0.115.5
uvicorn[standard]==0.32.0

# Base de datos
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0

# Validación y configuración
pydantic==2.10.0
pydantic-settings==2.6.1

# Seguridad
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# HTTP y archivos
python-multipart==0.0.17
httpx==0.28.0

# IA y RAG
langchain==0.3.10
langchain-community==0.3.10
langchain-ollama==0.2.1

# Procesamiento de documentos
pypdf==5.1.0
python-docx==1.1.2

# Caché Redis
redis[hiredis]==5.2.0

# Rate limiting
slowapi==0.1.9

# Logging
loguru==0.7.2

# Tareas programadas (reemplaza Cloud Scheduler)
apscheduler==3.10.4

# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
httpx==0.28.0
```

### `frontend/package.json` (dependencias clave)
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",
    "@tanstack/react-query": "^5.62.0",
    "axios": "^1.7.7",
    "zustand": "^5.0.1",
    "react-markdown": "^9.0.1",
    "react-syntax-highlighter": "^15.6.1",
    "@types/react-syntax-highlighter": "^15.5.13",
    "react-hot-toast": "^2.4.1",
    "lucide-react": "^0.462.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.5",
    "class-variance-authority": "^0.7.1",
    "@radix-ui/react-dialog": "^1.1.2",
    "@radix-ui/react-tabs": "^1.1.1",
    "@radix-ui/react-progress": "^1.1.0",
    "@radix-ui/react-scroll-area": "^1.2.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.3",
    "vite": "^5.4.11",
    "typescript": "^5.7.2",
    "tailwindcss": "^3.4.15",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1"
  }
}
```

---

## 🚀 ORDEN DE CONSTRUCCIÓN

### FASE 1: Infraestructura y Base de Datos — ✅ COMPLETADA
1. ✅ Crear estructura completa de carpetas del repositorio
2. ✅ Configurar `docker-compose.yml` (postgres pgvector, redis, ollama, backend, frontend)
3. ✅ Crear `backend/app/config.py` (Pydantic BaseSettings) y `backend/app/database.py` (async SQLAlchemy)
4. ✅ Crear TODOS los modelos SQLAlchemy en `backend/app/models/` (user, module, topic, quiz, progress, achievement, chat, document)
5. ✅ Generar migración inicial de Alembic con `CREATE EXTENSION IF NOT EXISTS vector;` y todas las tablas
6. ✅ Configurar React 18 + Vite + TypeScript + Tailwind + shadcn/ui en `frontend/`
7. ✅ `docker compose up` levanta todos los servicios

### FASE 2: Autenticación Completa — ✅ COMPLETADA
8. ✅ Implementar `utils/security.py` (JWT encode/decode + bcrypt hash/verify)
9. ✅ Implementar `services/auth_service.py` (register, login, refresh)
10. ✅ Implementar `routers/auth.py` (POST register, login, refresh, logout)
11. ✅ Implementar `dependencies.py` (get_db, get_current_user, get_redis, require_admin)
12. ✅ Implementar `LoginPage.tsx` con formulario, toggle registro, protección brute-force (3 intentos + lockout 5min)
13. ✅ Implementar `authStore.ts` (Zustand + localStorage) y `api/client.ts` (interceptor JWT, 401 redirect)
14. ✅ Implementar `AuthGuard.tsx` (redirect a /login, soporte requireAdmin)
15. ✅ **Verificado:** Registro → Login → Token → Rutas protegidas funcionan

### FASE 3: Módulos, Temas y Contenido — ✅ COMPLETADA
16. ✅ `scripts/setup_ollama.sh` para descargar modelos qwen2.5 y mxbai-embed-large
17. ✅ `scripts/seed_db.py` — 5 módulos, 22 temas con contenido Markdown completo (código Kotlin, tablas, tips), 25+ preguntas quiz, 7 logros, usuario admin
18. ✅ `routers/modules.py` (list con progreso + detail con status por tema) y `routers/topics.py` (get, visit, complete, time)
19. ✅ `ModulesPage.tsx` (grid responsivo), `ModuleDetailPage.tsx` (breadcrumb + lista temas), `TopicPage.tsx` (contenido + navegación prev/next)
20. ✅ `ContentRenderer.tsx` con react-markdown + remark-gfm (tablas) + `CodeBlock.tsx` (syntax highlight + copiar)
21. ✅ Layout compartido: `AppLayout.tsx` + `Sidebar.tsx` (responsivo mobile) + `Navbar.tsx`
22. ✅ Componentes shadcn/ui: button, card, progress, badge, separator, skeleton
23. ✅ **Verificado:** Login → Ver módulos → Entrar tema → Leer contenido con código y tablas

### FASE 4: Progreso, Autoevaluaciones con IA y Logros — ✅ COMPLETADA
24. ✅ `services/progress_service.py` — cálculo de progreso global, por módulo, tiempo, promedio quizzes, historial actividad
25. ✅ `services/achievement_service.py` — detección automática de 7 tipos de logros (first_topic, module_completed, streak_days, chat_messages, quiz_perfect, course_completed)
26. ✅ `services/llm_service.py` — Cliente Ollama para generación de quizzes con IA
    - Prompt en español que genera N preguntas en JSON estructurado
    - Trunca contenido a 3500 chars para ventana de contexto del modelo 7B
    - Parser robusto: limpia markdown fences, valida opciones y correct_index
    - ChatOllama con `format="json"` y `temperature=0.7`
27. ✅ `routers/quiz.py` — **Quizzes generados por IA:**
    - GET genera preguntas via Ollama → almacena respuestas en Redis (TTL 30min) → envía solo preguntas al frontend
    - POST evalúa contra Redis → grading instantáneo → marca tema completado si aprueba → verifica logros
    - Fallback automático a preguntas estáticas de BD si Ollama no está disponible
    - Sesiones single-use (se eliminan de Redis después de evaluar)
28. ✅ `routers/progress.py` (GET stats globales + GET actividad reciente)
29. ✅ `routers/achievements.py` (GET todos con estado earned/locked)
30. ✅ `QuizPage.tsx` — Loading "La IA está preparando tus preguntas..." con animación, manejo de sesión expirada (410 → auto-regenera), retry genera preguntas NUEVAS
31. ✅ `QuizQuestion.tsx` + `QuizResults.tsx` — selección, score, feedback con explicaciones
32. ✅ `ProgressPage.tsx` — 4 cards stats, barras por módulo, grid de logros, historial actividad
33. ✅ `AchievementsPage.tsx` — Logros obtenidos vs por desbloquear
34. ✅ **Verificado:** Leer tema → Quiz IA genera preguntas únicas → Responder → Score + feedback → Progreso actualizado → Logros otorgados

### FASE 5: Tutor IA Conversacional con RAG (SIGUIENTE)
35. Implementar `services/embed_service.py` (cliente mxbai-embed-large para generar embeddings)
36. Implementar `services/ingest_service.py` (parseo PDF/DOCX/TXT → chunking → embeddings → pgvector)
37. Implementar `services/rag_service.py` (pipeline completo: embed query → pgvector similarity search → prompt aumentado → Ollama → caché Redis)
38. Implementar `routers/chat.py` con:
    - CRUD de sesiones de chat
    - POST mensaje con pipeline RAG
    - Rate limiting via slowapi (20 msgs/hora)
    - Fuentes citadas en cada respuesta
39. Implementar `ChatPage.tsx` con:
    - Sidebar de sesiones (nueva conversación, historial)
    - Burbujas de chat (user/assistant) con Markdown renderizado
    - Fuentes RAG colapsables bajo cada respuesta
    - Indicador "Tutor escribiendo..." mientras el LLM procesa
    - Input con Enter envía, Shift+Enter nueva línea
40. **Prueba:** Hacer una pregunta al tutor → Recibir respuesta fundamentada en el material → Ver fuentes citadas

### FASE 6: Dashboard Completo y Panel Admin
41. Implementar `routers/dashboard.py` — endpoint dedicado con agregación de datos (último tema, recomendaciones, logros recientes)
42. Mejorar `DashboardPage.tsx` — banner "Continuar donde lo dejaste", logros recientes, recomendaciones personalizadas
43. Implementar `routers/admin.py`:
    - CRUD de módulos, temas y preguntas
    - Upload de documentos (multipart/form-data) con procesamiento asíncrono via BackgroundTasks
    - Gestión de usuarios (activar/desactivar, cambiar rol)
    - Reprocesamiento de documentos con error
44. Implementar `AdminPage.tsx` con tabs:
    - Tab "Corpus RAG": tabla de documentos, drag & drop upload, estado procesamiento
    - Tab "Contenido del Curso": árbol colapsable Módulo → Temas → Preguntas con CRUD
    - Tab "Usuarios": lista paginada con acciones de gestión
45. **Prueba:** Admin sube PDF → procesamiento automático → chunks en BD → tutor usa el contenido en respuestas

### FASE 7: Calidad y Preparación para Piloto
46. Implementar rate limiting global con `slowapi` (100 req/min por IP)
47. Configurar `loguru` con logs JSON estructurados para producción
48. Escribir pruebas unitarias para `auth_service.py`, `rag_service.py`, `progress_service.py`, `llm_service.py`
49. Escribir pruebas de integración para endpoints críticos (auth, chat, modules, quiz)
50. Ejecutar Lighthouse → Corregir hasta Performance ≥ 70 y Accessibility ≥ 85
51. Verificar diseño responsivo en 375px, 768px, 1440px
52. Configurar Firebase Hosting → primer deploy del frontend
53. Configurar Cloud Run → primer deploy del backend
54. Escribir `README.md` con instrucciones de instalación paso a paso
55. **Verificación final:** Todos los criterios de aceptación cumplidos

---

## ✅ CRITERIOS DE ACEPTACIÓN

El sistema está listo para evaluación con usuarios piloto cuando:

- [x] `docker compose up` levanta TODOS los servicios sin errores en equipo limpio
- [x] La semilla (`seed_db.py`) pobla correctamente los 5 módulos, 22 temas y 7 logros
- [x] Flujo estudiante completo: Registro → Login → Ver módulo → Leer tema → Hacer quiz → Ver progreso actualizado
- [x] Las autoevaluaciones son generadas por IA (Ollama) con preguntas únicas en cada intento
- [x] Fallback a preguntas estáticas de BD si Ollama no está disponible
- [x] Sistema de logros detecta y otorga automáticamente (7 tipos de logros)
- [ ] El tutor IA conversacional responde preguntas usando el corpus RAG
- [ ] Las respuestas del tutor citan las fuentes del corpus
- [ ] El tutor rechaza preguntas ajenas al curso con mensaje educativo
- [ ] El panel de admin permite subir un PDF y procesarlo (ver chunks generados en BD)
- [ ] Lighthouse Performance ≥ 70 en la página de módulos
- [ ] El diseño es completamente funcional en pantalla de 375px
- [x] Todos los textos visibles al usuario están en español
- [ ] Las pruebas del backend pasan con cobertura ≥ 60%
- [ ] El rate limiting del chat IA funciona (responde 429 al superar 20 mensajes/hora)
- [ ] El `README.md` permite a una persona nueva levantar el sistema desde cero

---

## ⚠️ ADVERTENCIAS Y DECISIONES IMPORTANTES

### LLM y Hardware
- **`qwen2.5:7b-instruct-q4_K_M`** requiere mínimo **6GB de RAM libre** en el servidor. En el VM de Compute Engine (`e2-standard-2`, 8GB total), esto funciona pero con poca holgura.
- Si las respuestas son demasiado lentas (> 20 segundos), cambiar a `llama3.2:3b-instruct-q4_K_M` (solo 2GB RAM, respuestas más rápidas pero menor calidad).
- En desarrollo local, el LLM puede ser lento si la máquina no tiene GPU. Esto es normal.

### pgvector y el índice IVFFlat
- **NO crear el índice IVFFlat antes de tener datos.** El índice se debe crear DESPUÉS de ingestar todos los documentos del corpus. Crear el índice en una tabla vacía no tiene sentido y degrada el rendimiento.
- Ejecutar manualmente después de ingestar documentos: `CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);`

### RAG vs Fine-tuning
- Este sistema usa **RAG puro**. No se hace fine-tuning del modelo base.
- El "entrenamiento" en los objetivos de la tesis se refiere a construir y configurar el pipeline RAG con el corpus del curso.
- Esto es técnicamente correcto y es la aproximación estándar para este tipo de aplicación educativa.

### Pub/Sub ELIMINADO
- Usar `fastapi.BackgroundTasks` para el procesamiento de documentos. Es suficiente para el volumen del proyecto.
- Cloud Scheduler ELIMINADO → Usar `APScheduler` dentro del proceso FastAPI si se necesitan tareas programadas.

### Cloud Memorystore ELIMINADO
- Redis corre en el mismo VM de Compute Engine que Ollama. Accesible desde Cloud Run vía VPC Connector.
- Esto ahorra ~S/. 75/mes sin pérdida de funcionalidad.

### Frontend hosting
- **Firebase Hosting** (parte de Google/GCP) en lugar de Cloud CDN + Load Balancer.
- Firebase Hosting provee: CDN global, HTTPS automático, deploy con 1 comando (`firebase deploy`).
- Costo: $0 dentro del free tier para el tráfico esperado del piloto.

---

*Versión 2.0 — Revisado y optimizado para presupuesto de pregrado individual.*
*Stack original de la tesis mantenido en concepto; optimizado en costos y complejidad.*
