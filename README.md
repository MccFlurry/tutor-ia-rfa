# Tutor IA Generativa · Aplicaciones Móviles — IESTP "República Federal de Alemania" (Chiclayo)

Sistema Tutor Inteligente (STI) con RAG privado para el curso **Aplicaciones Móviles** (Android/Kotlin) del IESTP RFA. Tesis de pregrado USAT · Escuela de Ingeniería de Sistemas y Computación.

- **Autor:** Roger Alessandro Zavaleta Marcelo
- **Asesora (USAT):** Mg. Reyes Burgos, Karla
- **Coordinador piloto (IESTP RFA):** Téc. Xavier Benites Marín
- **Sustentación:** 10 julio 2026

Ver `CLAUDE.md` para documentación técnica completa y `CLAUDE.original.md` para el plan formal de tesis.

---

## Características

- 5 módulos didácticos con 22 temas (Markdown con código Kotlin)
- Tutor IA conversacional vía **RAG** privado (Ollama + pgvector)
- Quizzes generados por IA adaptados al nivel del estudiante
- Desafíos de código con evaluación IA (score + feedback estructurado)
- Evaluación diagnóstica de entrada → clasificador de nivel (CRISP-DM)
- Re-asignación automática de nivel tras desempeño sostenido
- Gamificación: 7 logros automáticos
- Panel admin: CRUD contenido + corpus RAG + usuarios + niveles
- 100% **sin APIs pagas**: Ollama auto-hospedado · pgvector · Redis

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind + shadcn/ui + Zustand + TanStack Query |
| Backend | FastAPI + Python 3.12 + SQLAlchemy async + Alembic + LangChain |
| LLM | Ollama + `qwen2.5:7b-instruct-q4_K_M` |
| Embeddings | Ollama + `mxbai-embed-large` (1024 dim) |
| Base de datos | PostgreSQL 16 + pgvector |
| Caché | Redis 7 |
| Contenedores | Docker + Docker Compose |
| Producción | VM Compute Engine e2-standard-4 + Caddy + Let's Encrypt · Firebase Hosting (frontend) |
| Validación | RAGAS · ISO/IEC 25010:2023 · SUS |

---

## Requisitos previos

- Docker Desktop (Windows/macOS) o Docker Engine (Linux) con Compose v2
- Node.js 20+ (solo si corres el frontend fuera de Docker)
- Python 3.12 (solo si corres el backend fuera de Docker)
- **Ollama** instalado nativamente si quieres aceleración GPU (Windows con RTX/Linux con NVIDIA)

### ¿Por qué Ollama nativo?

En Windows el contenedor Docker de Ollama **no tiene acceso directo a la GPU**. La imagen oficial usa CPU-only, resultando en respuestas de 30-60s. Corriendo Ollama nativamente (descarga en `https://ollama.com/download`), el backend dentro de Docker se conecta vía `host.docker.internal:11434` con aceleración GPU (3-5s por respuesta en RTX 4070).

---

## Setup dev

### 1. Clonar y preparar variables

```bash
git clone <repo_url> tutor-ia-rfa
cd tutor-ia-rfa
cp .env.example .env
# Edita .env: genera SECRET_KEY con python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Instalar modelos Ollama

```bash
# En tu host (no dentro de Docker)
ollama pull qwen2.5:7b-instruct-q4_K_M   # ~4.5 GB
ollama pull mxbai-embed-large            # ~670 MB
ollama serve                              # mantener abierto
```

### 3. Levantar stack

```bash
docker compose up -d postgres redis
docker compose up backend frontend
```

El backend aplica migraciones Alembic y ejecuta seed automáticamente. Primera corrida: ~2-3 min.

### 4. Sembrar banco de evaluación (una sola vez)

```bash
docker compose exec backend python scripts/seed_assessment_bank.py
```

### 5. Ingestar corpus RAG

```bash
docker compose exec backend python scripts/ingest_course_docs.py
```

Indexa los 22 temas del seed en `document_chunks` (~163 chunks).

### 6. URLs

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 7. Credenciales iniciales

| Rol | Email | Password |
|-----|-------|----------|
| Admin | `admin@iestprfa.edu.pe` | `Admin123!` |

Cambiar en `.env` (`ADMIN_EMAIL`, `ADMIN_PASSWORD`) antes del primer arranque.

---

## Comandos comunes

```bash
# Ver logs backend
docker compose logs -f backend

# Aplicar nueva migración
docker compose exec backend alembic upgrade head

# Crear migración manual
docker compose exec backend alembic revision -m "descripcion" --autogenerate

# Shell psql
docker compose exec postgres psql -U tutor_user -d tutordb

# Reset completo (¡borra datos!)
docker compose down -v
```

---

## Tests

```bash
# Suite completa
docker compose exec backend pytest

# Solo unit tests
docker compose exec backend pytest tests/unit/

# Con cobertura
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

---

## Validación RAGAS (Sprint 4)

```bash
# Instalar jupyter en el contenedor backend o abrirlo localmente
cd backend/notebooks
jupyter lab ragas_validation.ipynb
```

El golden set está en `backend/tests/fixtures/golden_set.json` (30 preguntas M1-M3).

Umbrales objetivo: faithfulness ≥ 0.75, answer_relevance ≥ 0.70.

---

## Despliegue producción (Sprint 5)

1. Crear VM **e2-standard-4** Ubuntu 22.04 en GCP Compute Engine (16 GB RAM)
2. Apuntar DNS → IP pública
3. En la VM:
   ```bash
   sudo ./infra/scripts/provision-vm.sh   # instala Docker, Ollama, firewall, directorios
   # cerrar sesión, reingresar
   cp .env.example .env                    # ajustar secretos + DOMAIN
   ./infra/scripts/deploy.sh               # build + up + migrate + seed
   ```
4. Configurar frontend Firebase:
   ```bash
   cd frontend
   firebase login
   firebase deploy --only hosting
   ```
5. Backup diario:
   ```bash
   crontab -e
   0 3 * * * /home/user/tutor-ia-rfa/infra/scripts/backup-postgres.sh
   ```

---

## Troubleshooting

### Backend reinicia por OOM

`qwen2.5:7b` necesita ~6 GB RAM. Si VM tiene solo 8 GB, cambiar `OLLAMA_MODEL=llama3.2:3b-instruct-q4_K_M` (2 GB, menor calidad).

### Ollama en Docker es lento (dev Windows)

Usa Ollama nativo. El contenedor en `docker-compose.yml` está comentado a propósito; el backend apunta a `host.docker.internal:11434`.

### Migración no aplica

```bash
docker compose exec backend alembic current   # ver versión actual
docker compose exec backend alembic upgrade head
```

Si falta el volumen `./backend/alembic`, revisar `docker-compose.yml`.

### `invalid literal for int() with base 10` en embeddings

Reiniciar Ollama + volver a `ollama pull mxbai-embed-large`.

### 429 en chat

Rate limit es 20 consultas/hora por usuario. Contador se resetea automáticamente. `GET /api/v1/chat/remaining` muestra cuántas quedan.

---

## Roadmap sprints

| Sprint | Período | Estado | Hitos |
|--------|---------|--------|-------|
| 1-3 | 23 mar – 03 may 2026 | ✅ | Fases 1-7.5 completadas |
| 4 | 04-17 may 2026 | ⏳ | **RAGAS validation** (faithfulness ≥0.75) |
| 5 | 18-31 may 2026 | ⏳ | Deploy VM + Caddy + Firebase |
| 6 | 01-14 jun 2026 | ⏳ | 15 lecciones + 30 ejercicios + Monaco |
| 7 | 15-28 jun 2026 | ⏳ | **ISO/IEC 25010:2023** (cobertura ≥80%, éxito ≥90%) |
| 8 | 29 jun – 10 jul 2026 | ⏳ | **SUS ≥68** (piloto 10-15 estudiantes) + sustentación |

---

## Contribución

Commits: **Conventional Commits** (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

Ramas: `feat/sprint-{n}-{descripcion}` o `docs/sprint-{n}-{documento}`.

Antes de push: `pytest` + `eslint` deben pasar.

---

## Licencia y privacidad

Uso exclusivo académico para sustentación de tesis USAT. **100% privado:** sin APIs pagas, sin telemetría hacia terceros, todo el LLM corre auto-hospedado.

---

*Última actualización: 2026-04-23*
