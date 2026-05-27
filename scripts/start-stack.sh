#!/usr/bin/env bash
# start-stack.sh — Verifica precondiciones y levanta el stack completo.
# Uso: bash scripts/start-stack.sh [--no-ai]
#   --no-ai  Omite verificación Ollama (solo postgres/redis/backend/frontend).
#
# Salida:
#   0 → stack arriba, healthchecks OK
#   1 → Docker no disponible
#   2 → Ollama inaccesible / modelos faltantes
#   3 → docker compose up falló
#   4 → healthcheck backend falló
#   5 → healthcheck frontend falló

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { printf "%b[%s]%b %s\n" "$CYAN" "$(date +%H:%M:%S)" "$NC" "$*"; }
ok()   { printf "  %b✓%b %s\n" "$GREEN" "$NC" "$*"; }
warn() { printf "  %b!%b %s\n" "$YELLOW" "$NC" "$*"; }
fail() { printf "  %b✗%b %s\n" "$RED" "$NC" "$*"; }

SKIP_AI=false
for arg in "$@"; do
  case "$arg" in
    --no-ai) SKIP_AI=true ;;
    -h|--help)
      sed -n '2,11p' "$0"; exit 0 ;;
  esac
done

# ─── 1. Docker disponible ─────────────────────────────────────────────────
log "Verificando Docker..."
if ! command -v docker >/dev/null 2>&1; then
  fail "docker no instalado en PATH"; exit 1
fi
if ! docker info >/dev/null 2>&1; then
  fail "Docker daemon no responde (Docker Desktop apagado?)"; exit 1
fi
ok "Docker daemon activo ($(docker version --format '{{.Server.Version}}'))"

# ─── 2. Ollama nativo (host) ──────────────────────────────────────────────
if [ "$SKIP_AI" = false ]; then
  log "Verificando Ollama (host)..."

  OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
  if ! curl -sf -m 5 "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
    fail "Ollama no responde en $OLLAMA_URL"
    warn "Inicia Ollama o lanza: ollama serve"
    warn "Si Docker no alcanza host.docker.internal:11434, exporta OLLAMA_HOST=0.0.0.0:11434 y reinicia Ollama"
    exit 2
  fi
  ok "Ollama responde en $OLLAMA_URL"

  # Binding scope warning: bound only to 127.0.0.1 cuts Docker access on Windows
  if command -v netstat >/dev/null 2>&1; then
    if netstat -an 2>/dev/null | grep -E "^[[:space:]]*TCP[[:space:]]+127\.0\.0\.1:11434[[:space:]]+.*LISTEN" >/dev/null; then
      if ! netstat -an 2>/dev/null | grep -E "^[[:space:]]*TCP[[:space:]]+(0\.0\.0\.0|\[::\]):11434[[:space:]]+.*LISTEN" >/dev/null; then
        warn "Ollama escucha sólo en 127.0.0.1 — Docker puede fallar al alcanzarlo"
        warn "Solución: setx OLLAMA_HOST 0.0.0.0:11434  (cerrar y reiniciar Ollama)"
      fi
    fi
  fi

  # Modelos requeridos presentes
  REQUIRED_MODELS=("qwen2.5:7b-instruct-q4_K_M" "mxbai-embed-large")
  MODELS_JSON="$(curl -sf -m 5 "$OLLAMA_URL/api/tags")"
  for m in "${REQUIRED_MODELS[@]}"; do
    if echo "$MODELS_JSON" | grep -q "\"$m"; then
      ok "Modelo presente: $m"
    else
      fail "Modelo faltante: $m"
      warn "Ejecuta: ollama pull $m"
      exit 2
    fi
  done

  # Smoke test inferencia (1 token, cold load + GPU check)
  log "Smoke test inferencia (puede tardar 10-30s si modelo frío)..."
  if curl -sf -m 60 -X POST "$OLLAMA_URL/api/generate" \
      -H "Content-Type: application/json" \
      -d '{"model":"qwen2.5:7b-instruct-q4_K_M","prompt":"hola","stream":false,"options":{"num_predict":1}}' \
      >/dev/null 2>&1; then
    ok "Inferencia LLM OK"
  else
    fail "Inferencia LLM falló (timeout o error)"
    exit 2
  fi
fi

# ─── 3. docker compose up con healthcheck wait ────────────────────────────
log "Levantando contenedores (compose up -d --wait)..."
if ! docker compose up -d --wait --wait-timeout 180; then
  fail "docker compose up falló o healthchecks no se completaron en 180s"
  docker compose ps
  exit 3
fi
ok "postgres + redis + backend + frontend arriba"

# ─── 4. Smoke test backend HTTP ───────────────────────────────────────────
log "Verificando backend /health..."
for i in $(seq 1 30); do
  if curl -sf -m 3 http://localhost:8000/health >/dev/null 2>&1; then
    ok "backend /health OK"
    break
  fi
  if [ "$i" = 30 ]; then
    fail "backend no respondió /health tras 30 intentos"
    docker compose logs --tail=50 backend
    exit 4
  fi
  sleep 2
done

# ─── 5. Smoke test frontend ───────────────────────────────────────────────
log "Verificando frontend (puerto 5173)..."
for i in $(seq 1 15); do
  if curl -sf -m 3 http://localhost:5173 >/dev/null 2>&1; then
    ok "frontend respondiendo en :5173"
    break
  fi
  if [ "$i" = 15 ]; then
    fail "frontend no respondió en :5173"
    docker compose logs --tail=30 frontend
    exit 5
  fi
  sleep 2
done

# ─── 6. Reporte final ─────────────────────────────────────────────────────
echo
log "Estado contenedores:"
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
echo
ok "Stack listo:"
echo "    Frontend  → http://localhost:5173"
echo "    Backend   → http://localhost:8000/docs"
echo "    Postgres  → localhost:5433 (tutor_user/tutor_pass_dev)"
echo "    Redis     → localhost:6379"
[ "$SKIP_AI" = false ] && echo "    Ollama    → $OLLAMA_URL"
