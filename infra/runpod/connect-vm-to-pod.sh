#!/usr/bin/env bash
# connect-vm-to-pod.sh — Ejecutar EN la VM GCE el día de la demo.
# Apaga el Ollama nativo (lento, CPU) y enruta host.docker.internal:11434
# hacia el pod GPU de RunPod por túnel SSH. Cero cambios de código/compose.
#
#   POD_IP=1.2.3.4 POD_PORT=40125 bash connect-vm-to-pod.sh
#
# ⚠️ POD_IP y POD_PORT CAMBIAN cada vez que reinicias el pod. Tómalos de
#    RunPod > tu pod > Connect > "SSH over exposed TCP"  (ej. root@IP -p PUERTO).
set -euo pipefail
: "${POD_IP:?define POD_IP (RunPod Direct TCP IP)}"
: "${POD_PORT:?define POD_PORT (RunPod Direct TCP port)}"
KEY="${KEY:-$HOME/.ssh/runpod_key}"
REPO="${REPO:-/opt/tutor-ia-rfa}"          # ajusta si el repo está en otra ruta
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.vm.yml"

[ -f "$KEY" ] || { echo "Falta la llave $KEY — cópiala desde el laptop con gcloud compute scp"; exit 1; }
chmod 600 "$KEY"

echo "==> Liberando :11434 (apagando Ollama nativo CPU)"
sudo systemctl stop ollama 2>/dev/null || true

echo "==> Matando túneles previos"
pkill -f "11434:localhost:11434" 2>/dev/null || true
sleep 1

command -v autossh >/dev/null || { echo "==> Instalando autossh"; sudo apt-get update -qq && sudo apt-get install -y autossh; }

echo "==> Túnel VM:11434 -> pod $POD_IP:$POD_PORT"
# -g: bind 0.0.0.0 para que el contenedor llegue vía host-gateway.
#     UFW debe seguir bloqueando 11434 desde internet (solo 22/80/443 abiertos).
autossh -M 0 -f -N -g \
  -L 11434:localhost:11434 \
  -p "$POD_PORT" "root@$POD_IP" -i "$KEY" \
  -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes

sleep 3
echo "==> Test host:"
curl -fsS localhost:11434/api/tags >/dev/null && echo "  OK :11434 responde en la VM" || { echo "  FALLO: el túnel no levantó"; exit 1; }

echo "==> Reiniciando backend"
cd "$REPO"
$COMPOSE restart backend
sleep 5
echo "==> Test contenedor:"
$COMPOSE exec -T backend sh -c 'curl -fsS http://host.docker.internal:11434/api/tags >/dev/null' \
  && echo "  OK: backend alcanza la GPU" \
  || echo "  El contenedor no alcanza :11434 — revisa UFW / bind del túnel"

echo "==> Listo. Inferencia en GPU (~135 tok/s). Prueba un chat real en la app."
