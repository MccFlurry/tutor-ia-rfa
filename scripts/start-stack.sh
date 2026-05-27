#!/usr/bin/env bash
# start-stack.sh — Verifica precondiciones, repara y levanta el stack completo.
# Uso: bash scripts/start-stack.sh [--no-ai] [--restart] [--hard-restart]
#   --no-ai         Omite verificación Ollama (solo postgres/redis/backend/frontend).
#   --restart       Baja contenedores antes de levantar (preserva volúmenes).
#   --hard-restart  Igual a --restart + mata y reinicia Ollama nativo.
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
RESTART=false
HARD_RESTART=false
for arg in "$@"; do
  case "$arg" in
    --no-ai)        SKIP_AI=true ;;
    --restart)      RESTART=true ;;
    --hard-restart) RESTART=true; HARD_RESTART=true ;;
    -h|--help)
      sed -n '2,13p' "$0"; exit 0 ;;
  esac
done

# Detectar WSL: si dentro de WSL, Ollama Windows-host no se alcanza vía localhost
# (WSL2 NAT default). Probar host.docker.internal primero.
is_wsl() {
  grep -qi microsoft /proc/version 2>/dev/null
}

if is_wsl; then
  OLLAMA_URL="${OLLAMA_BASE_URL:-http://host.docker.internal:11434}"
else
  OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
fi

# ─── Helpers Ollama ────────────────────────────────────────────────────────
ollama_alive() {
  curl -sf -m 3 "$OLLAMA_URL/api/tags" >/dev/null 2>&1 && return 0
  # Fallback: si OLLAMA_URL usa localhost en WSL, probar host.docker.internal
  if is_wsl && echo "$OLLAMA_URL" | grep -q "localhost"; then
    curl -sf -m 3 "http://host.docker.internal:11434/api/tags" >/dev/null 2>&1 && {
      OLLAMA_URL="http://host.docker.internal:11434"
      return 0
    }
  fi
  return 1
}

ollama_bound_all_ifaces() {
  # Bajo WSL, usar netstat.exe (Windows) — netstat Linux mira la red WSL, no la del host
  if command -v netstat.exe >/dev/null 2>&1; then
    netstat.exe -an 2>/dev/null | tr -d '\r' | grep -E "^[[:space:]]*TCP[[:space:]]+(0\.0\.0\.0|\[::\]):11434[[:space:]]+.*LISTEN" >/dev/null
    return $?
  fi
  return 0   # asumir OK si no podemos chequear
}

kill_ollama() {
  # taskkill.exe via interop WSL→Windows
  if command -v taskkill.exe >/dev/null 2>&1; then
    taskkill.exe /IM ollama.exe /F >/dev/null 2>&1 || true
    taskkill.exe /IM "ollama app.exe" /F >/dev/null 2>&1 || true
  fi
  # esperar liberación puerto
  for _ in $(seq 1 10); do
    ollama_alive || return 0
    sleep 1
  done
}

ollama_cmd() {
  # Resolver binario ollama: Linux WSL primero, Windows interop después
  if command -v ollama >/dev/null 2>&1; then
    echo "ollama"
  elif command -v ollama.exe >/dev/null 2>&1; then
    echo "ollama.exe"
  else
    return 1
  fi
}

start_ollama() {
  local OLLAMA_BIN
  OLLAMA_BIN=$(ollama_cmd) || { fail "ollama no en PATH (ni Linux ni Windows interop)"; return 1; }

  export OLLAMA_HOST="${OLLAMA_HOST:-0.0.0.0:11434}"
  export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-30m}"
  log "Lanzando '$OLLAMA_BIN serve' (HOST=$OLLAMA_HOST KEEP_ALIVE=$OLLAMA_KEEP_ALIVE)..."

  if [ "$OLLAMA_BIN" = "ollama.exe" ]; then
    # Lanzar binario Windows desacoplado vía PowerShell (sobrevive cierre de bash)
    powershell.exe -NoProfile -Command "\$env:OLLAMA_HOST='$OLLAMA_HOST'; \$env:OLLAMA_KEEP_ALIVE='$OLLAMA_KEEP_ALIVE'; Start-Process -WindowStyle Hidden -FilePath 'ollama.exe' -ArgumentList 'serve'" >/dev/null 2>&1
  else
    nohup ollama serve >"$PROJECT_ROOT/.ollama.log" 2>&1 &
    disown || true
  fi

  for i in $(seq 1 30); do
    if ollama_alive; then
      ok "Ollama responde tras ${i}s"
      return 0
    fi
    sleep 1
  done
  fail "Ollama no levantó en 30s"
  return 1
}

# ─── 1. Docker disponible (auto-launch Docker Desktop) ───────────────────
log "Verificando Docker..."
if ! command -v docker >/dev/null 2>&1; then
  fail "docker no instalado en PATH"; exit 1
fi

if ! docker info >/dev/null 2>&1; then
  warn "Docker daemon no responde — puede estar booteando o apagado"

  # Detectar Docker Desktop.exe corriendo (tasklist plain, sin filter MSYS-broken)
  DOCKER_RUNNING=false
  if command -v tasklist >/dev/null 2>&1; then
    if tasklist 2>/dev/null | grep -qi "Docker Desktop.exe"; then
      DOCKER_RUNNING=true
    fi
  fi

  if [ "$DOCKER_RUNNING" = true ]; then
    ok "Docker Desktop.exe ya corre — esperando daemon (WSL/Engine boot)"
  else
    log "Lanzando Docker Desktop..."
    # Validación vía PowerShell Test-Path (cmd //c rompe por MSYS path mangling)
    DOCKER_DESKTOP_WIN=""
    for win_path in \
        "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe" \
        "C:\\Program Files (x86)\\Docker\\Docker\\Docker Desktop.exe" \
        "${LOCALAPPDATA:-C:\\Users\\${USERNAME:-${USER:-default}}\\AppData\\Local}\\Docker\\Docker Desktop.exe"; do
      log "  probando: $win_path"
      result=$(powershell.exe -NoProfile -Command "if (Test-Path '$win_path') { 'YES' } else { 'NO' }" 2>/dev/null | tr -d '\r\n ')
      if [ "$result" = "YES" ]; then
        DOCKER_DESKTOP_WIN="$win_path"
        ok "  encontrado en: $win_path"
        break
      fi
    done
    if [ -z "$DOCKER_DESKTOP_WIN" ]; then
      fail "Docker Desktop.exe no encontrado en rutas conocidas"
      warn "Ábrelo manualmente y reintenta"
      exit 1
    fi
    powershell.exe -NoProfile -Command "Start-Process -FilePath '$DOCKER_DESKTOP_WIN'" >/dev/null 2>&1
  fi

  log "Esperando daemon Docker (hasta 240s, WSL cold boot puede tardar)..."
  for i in $(seq 1 120); do
    elapsed=$((i*2))
    # Usar `docker version` (más liviano y fiable que `docker info`)
    if docker version --format '{{.Server.Version}}' >/dev/null 2>&1; then
      ok "Docker daemon listo tras ${elapsed}s"
      break
    fi
    # feedback cada 20s
    if [ $((i % 10)) = 0 ]; then
      warn "  aún esperando... ${elapsed}s transcurridos (Docker Desktop GUI debe mostrar 'Engine running')"
    fi
    if [ "$i" = 120 ]; then
      fail "Docker daemon no respondió en 240s"
      warn "Diagnóstico — corre estos comandos:"
      warn "  docker version --format '{{.Server.Version}}'"
      warn "  echo \$DOCKER_HOST"
      warn "Posibles causas: login/EULA pendiente, WSL2 no listo, contexto mal apuntado"
      exit 1
    fi
    sleep 2
  done
fi
ok "Docker daemon activo ($(docker version --format '{{.Server.Version}}'))"

# ─── 2. Restart contenedores si pidieron ──────────────────────────────────
if [ "$RESTART" = true ]; then
  log "Bajando contenedores (preserva volúmenes)..."
  docker compose down --remove-orphans >/dev/null 2>&1 || true
  ok "Contenedores detenidos"
fi

# ─── 3. Ollama nativo (host) ──────────────────────────────────────────────
if [ "$SKIP_AI" = false ]; then
  log "Verificando Ollama (host)..."

  # 3a. Hard restart explícito
  if [ "$HARD_RESTART" = true ]; then
    warn "Reinicio forzado de Ollama"
    kill_ollama
    start_ollama || exit 2
  fi

  # 3b. Auto-arranque si caído
  if ! ollama_alive; then
    warn "Ollama no responde en $OLLAMA_URL — intentando auto-arranque"
    if ! ollama_cmd >/dev/null; then
      fail "ollama no instalado en PATH (ni Linux ni Windows interop)"
      warn "Instala desde https://ollama.com/download o asegúrate de ollama.exe esté en PATH Windows"
      exit 2
    fi
    start_ollama || exit 2
  else
    ok "Ollama ya responde en $OLLAMA_URL"
  fi

  # 3c. Auto-fix binding (127.0.0.1 → 0.0.0.0)
  if ! ollama_bound_all_ifaces; then
    warn "Ollama bound sólo a 127.0.0.1 — Docker no podrá alcanzarlo"
    warn "Reiniciando Ollama con OLLAMA_HOST=0.0.0.0:11434..."
    kill_ollama
    start_ollama || exit 2
    if ! ollama_bound_all_ifaces; then
      fail "Ollama sigue bound sólo a 127.0.0.1 tras restart"
      warn "Setea persistente: setx OLLAMA_HOST 0.0.0.0:11434  y reinicia terminal"
      exit 2
    fi
    ok "Ollama ahora bound a todas las interfaces"
  fi

  # 3d. Modelos requeridos presentes
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

  # 3e. Smoke test inferencia (1 token, cold load + GPU check)
  log "Smoke test inferencia (puede tardar 10-50s si modelo frío)..."
  if curl -sf -m 90 -X POST "$OLLAMA_URL/api/generate" \
      -H "Content-Type: application/json" \
      -d '{"model":"qwen2.5:7b-instruct-q4_K_M","prompt":"hola","stream":false,"options":{"num_predict":1}}' \
      >/dev/null 2>&1; then
    ok "Inferencia LLM OK (modelo warm)"
  else
    fail "Inferencia LLM falló (timeout o error)"
    exit 2
  fi
fi

# ─── 4. docker compose up con healthcheck wait ────────────────────────────
log "Levantando contenedores (compose up -d --wait)..."
if ! docker compose up -d --wait --wait-timeout 180; then
  fail "docker compose up falló o healthchecks no se completaron en 180s"
  docker compose ps
  exit 3
fi
ok "postgres + redis + backend + frontend arriba"

# ─── 5. Smoke test backend HTTP ───────────────────────────────────────────
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

# ─── 6. Smoke test frontend ───────────────────────────────────────────────
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

# ─── 7. Reporte final ─────────────────────────────────────────────────────
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
