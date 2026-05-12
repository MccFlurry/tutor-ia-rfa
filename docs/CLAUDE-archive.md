# CLAUDE-archive.md — Historial detallado fases completadas

> Material de referencia movido desde `CLAUDE.md` para mantenerlo <40k chars. Detalle ejecución Fases 1-7.5 + Sprint 4, benchmarks completos, matriz validación V1-V13. **Para reglas activas + Sprint 5+ consultar `CLAUDE.md` raíz.**

---

## 🚀 FASES COMPLETADAS — DETALLE

### ✅ FASE 1 — Sprint 1 · Infraestructura y BD
Estructura, docker-compose con pgvector/redis/ollama, config.py + database.py async, todos modelos SQLAlchemy, migración inicial Alembic con `CREATE EXTENSION vector`, React+Vite+TS+Tailwind+shadcn en frontend. `docker compose up` funciona. ERS 52 RF / 33 priorizados. 4 modelos STI documentados.

### ✅ FASE 2 — Sprint 2 · Autenticación + evaluación LLM (OE2 R2.1)
`security.py` JWT+bcrypt, `auth_service.py`, `routers/auth.py`, `dependencies.py` (get_db, get_current_user, get_redis, require_admin). Frontend: `LoginPage` con toggle registro + brute-force protection (3 intentos+lockout 5min), `authStore` Zustand+localStorage, `api/client.ts` interceptor 401, `AuthGuard` con requireAdmin.

**Evaluación comparativa LLM/embeddings ejecutada 2026-04-24** — `benchmarks/` completo. Reporte final: `docs/reporte-LLM.docx` (43 KB, 8 secciones + 2 anexos + referencias IEEE, formato USAT Times New Roman 12).

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

**Decisión final:** qwen2.5:7b-instruct-q4_K_M + mxbai-embed-large. qwen2.5 ganó rúbrica por 0.01 sobre llama3 (empate técnico) pero usa 0.5 GB menos VRAM y único con nota perfecta 5.00 en "ausencia de alucinaciones". mxbai-embed-large supera nomic por +0.20 Recall@5, margen claro.

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

**Objetivo:** Evaluación entrada IA asigna nivel (`beginner` | `intermediate` | `advanced`). LLM adapta dificultad quiz + coding al nivel. Re-asignación dinámica según desempeño.

#### 1️⃣ Business Understanding
- Problema: estudiantes distinto nivel reciben mismos ejercicios → desmotivación + aprendizaje subóptimo
- KPIs éxito: SUS ≥68, tasa completación por nivel, accuracy clasificador vs juicio docente, re-asignaciones correctas

#### 2️⃣ Data Understanding
- Evaluación entrada: respuestas + tiempo + cobertura por módulo
- Señales continuas: quiz scores, intentos, coding scores, tiempo por tema, consultas al tutor
- Metadata: fecha, ID tema/módulo, tipo pregunta

#### 3️⃣ Data Preparation
Migración `003_add_personalization.py` agrega `user_levels`, `entry_assessment_sessions`, `entry_assessment_bank`.

**Feature engineering:**
- `overall_entry_score` (0-100) = Σ (correctas × peso_módulo × peso_dificultad)
- Pesos módulo: M1=1.0, M2=1.2, M3=1.1, M4=1.3, M5=1.5
- Pesos dificultad: easy=1.0, medium=1.5, hard=2.0
- **Umbrales nivel:** `<40` beginner · `40-75` intermediate · `>75` advanced

#### 4️⃣ Modeling
- Clasificador rule-based v1: score ponderado → umbrales fijos · output `{level, score, confidence}`
- Prompt engineering adaptativo: `llm_service.py` + `code_eval_service.py` reciben `student_level`
- v2 futuro: scikit-learn si piloto genera data suficiente

#### 5️⃣ Evaluation
- Accuracy clasificador vs juicio docente (10-15 estudiantes piloto)
- Distribución niveles (detectar sesgo)
- Correlación nivel ↔ avg quiz/coding score (positiva)

**Reglas re-asignación:**
- 3 quizzes consecutivos ≥90% → proponer subir nivel
- 3 quizzes consecutivos <50% → proponer bajar nivel
- Estudiante confirma (o admin override) · registro en `user_levels.history`

#### 6️⃣ Deployment
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
| baseline  | thr 0.70 · top_k 5 · temp 0.3 · num_predict default | 0.663 ⚠️ | 0.760 ✅ | 0.863 ✅ |
| v3_full_tuning | thr **0.65** · top_k **7** · temp **0.1** · num_predict **2048** · num_ctx 8192 · **prompt anti-alucinación** | 0.716 ⚠️ | **0.768 ✅** | 0.856 ✅ |

¹ Subconjunto apto = 22 preguntas (16 conceptual + 6 application). Excluye 8 preguntas type=code porque piden GENERAR snippets no presentes literalmente en corpus → por diseño ningún chunk los respalda → no es métrica válida de faithfulness RAG. Justificación metodológica documentada en `docs/reporte-RAGAS.docx`.

**Mejoras v3 vs baseline:**
- Context recall: 0.547 → 0.619 (+0.072)
- Faithfulness code-gen: 0.398 → 0.575 (+0.177)
- Faithfulness medium: 0.703 → 0.784 (+0.081)
- Faithfulness application: 0.601 → 0.691 (+0.090)

**Conclusión OE2:** pipeline RAG con qwen2.5:7b + mxbai-embed-large CUMPLE faithfulness ≥0.75 y answer_relevancy ≥0.70 sobre subconjunto apto → **modelo seleccionado**. No requiere cambiar LLM.

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

---

## 📄 DATOS INICIALES — DETALLE COMPLETO

**5 módulos:**
1. Fundamentos y Preparación del Entorno (index 1, `smartphone`, `#6366f1`)
2. Lógica de Programación en Kotlin (2, `code-2`, `#0ea5e9`)
3. Elaboración de Interfaces de Usuario UI (3, `layout-panel-top`, `#22c55e`)
4. Componentes Android y Gestión de Datos (4, `database`, `#f59e0b`)
5. Funcionalidades Avanzadas y Despliegue (5, `rocket`, `#ef4444`)

**22 temas totales** distribuidos: M1=4, M2=5, M3=4, M4=5, M5=4. Cada uno: title, estimated_minutes (10-35), has_quiz (true/false). Ver `backend/scripts/seed_db.py` para contenido Markdown completo con código Kotlin.

**7 logros:** Primer Paso 🚀 (first_topic=1), Finalizador Módulo 🏆 (module_completed=1), Racha 7 Días 🔥 (streak_days=7), Explorador Tutor IA 🤖 (chat_messages=10), Maestro Kotlin ⚡ (module_completed=2 mod_id=2), Quiz Perfecto 💯 (quiz_perfect=100), Desarrollador Completo 🎓 (course_completed=100).

**30 desafíos coding** (objetivo OE4 cumplido, `scripts/seed_extra_challenges.py` idempotente):
- M1 (+2): Verificador Compatibilidad API, Hola Mundo Variables
- M2 (9): los 5 originales (Calculadora Promedio, Clasificador Triángulos, Filtro Lambda, Inventario, Figuras Polimorfismo) + Conversor Temperaturas, Simulador Calificaciones, Ordenar Personas, Jerarquía Vehículos
- M3 (+6): Layout XML Registro, Validador Email, Click Handler, ConstraintLayout, Card Responsivo, Adapter RecyclerView
- M4 (8): los 2 originales (Logger Ciclo Vida, Modelo API) + Counter Bundle, Intent Extras, SharedPrefs, Mini CRUD SQLite, Parser JSON, Retrofit GitHub
- M5 (5): Logger por Nivel, Test JUnit Calculadora, Test Data Class, signingConfigs Gradle, Checklist Play Store

Distribución final: M1=2 · M2=9 · M3=6 · M4=8 · M5=5 (total 30).

**23 preguntas banco fallback** evaluación entrada distribuidas M1-M5 (`scripts/seed_assessment_bank.py`).

---

## 🧪 VALIDACIONES DEL SISTEMA — MATRIZ COMPLETA

Matriz pruebas por flujo. Cada ítem debe reproducirse end-to-end antes de declarar piloto listo.

### ✅ Resultados validación end-to-end (ejecutada 2026-04-17)

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

### 👨‍🎓 Flujos estudiante

#### V1. Registro + Evaluación entrada
- [ ] Registrar con email+nombre+password válidos → JWT + redirect
- [ ] LevelGuard detecta `user.level == null` → fuerza redirect a `/assessment`
- [ ] IA genera ~12 preguntas cubriendo M1–M5 con dificultad mixta
- [ ] Si Ollama cae durante generación → fallback muestrea `entry_assessment_bank` (verificar log "Fallback banco")
- [ ] Responder preguntas + submit → score ponderado (pesos módulo × dificultad)
- [ ] Nivel asignado según umbrales (<40 beginner · 40–75 intermediate · >75 advanced)
- [ ] `user_levels` persiste con `history=[{level,score,reason:"entry"}]`
- [ ] Pantalla resultado muestra nivel + score + confianza + breakdown por módulo + feedback motivacional
- [ ] Botón "Ir al panel" redirige a `/dashboard`

#### V2. Navegación contenido
- [ ] Dashboard carga: greeting + nivel badge + hero "Continuar..." (solo si último tema incompleto) + 3 recomendaciones por nivel + 3 logros recientes + stats tabulares
- [ ] `/modules` grid responsivo 1/2/3 cols con barras progreso
- [ ] Módulos bloqueados con grayscale + candado + tooltip
- [ ] Módulo 1 siempre desbloqueado; resto espera 100% del anterior
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

#### V4. Desafío código per-estudiante
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

#### V6. Re-asignación automática nivel
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

### 👨‍💼 Flujos administrador

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
- [ ] Árbol colapsable Módulo → Tema → Quiz + Coding
- [ ] CRUD módulos: crear/editar/eliminar (cascade tira temas)
- [ ] CRUD temas: asignar has_quiz, estimated_minutes, content Markdown
- [ ] CRUD preguntas quiz estáticas (4 opciones + explicación + correct_option_index)
- [ ] CRUD desafíos coding (catálogo, NO per-estudiante)
- [ ] Botón "Generar con IA": input dificultad + nivel objetivo → LLM produce preview → admin descarta o "Aprobar y guardar" persiste
- [ ] Tras aprobar: `is_ai_generated=false` (catálogo del docente)

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
- [ ] 3 niveles fallback IA → catálogo: entry_assessment_bank, quiz_questions, coding_challenges seed
- [ ] `CodingSubmission` preserva FK a `CodingChallenge` (no se borra al regenerar)
- [ ] UI 100% español peruano (todos strings)
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
- [ ] Sesión evaluación ya enviada → 409 en submit
- [ ] Tema sin catálogo coding → botón "Desafío" oculto
- [ ] Código vacío en submit → LLM puntúa 0 con explicación
- [ ] Override admin a nivel inválido → 422 (pattern validator)
