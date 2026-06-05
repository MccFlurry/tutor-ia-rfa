#!/usr/bin/env bash
# setup-ollama-pod.sh — Prepara un pod GPU de RunPod para servir los modelos
# del tutor-ia-rfa (qwen2.5 + mxbai). Ejecutar DENTRO del pod (web terminal o SSH).
# Idempotente. Infra de DEMO — no es parte de la arquitectura GCE documentada.
set -euo pipefail

# Persistir modelos en el volumen de red (/workspace) si está montado.
# El container disk de RunPod se BORRA al detener el pod; /workspace NO.
# Así apagar/encender la GPU no re-descarga los 5.4GB de modelos.
if [ -d /workspace ]; then
  export OLLAMA_MODELS=/workspace/ollama
  mkdir -p "$OLLAMA_MODELS"
  echo "==> Modelos persistentes en $OLLAMA_MODELS (sobrevive stop/start)"
else
  echo "==> /workspace no montado; modelos irán al container disk (se borran al detener)"
fi

echo "==> 1/5 Instalando Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# El install.sh puede dejar un servicio systemd escuchando solo en 127.0.0.1.
# Lo detenemos para arrancarlo nosotros con OLLAMA_HOST explícito.
systemctl stop ollama 2>/dev/null || true
systemctl disable ollama 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true
sleep 2

echo "==> 2/5 Arrancando ollama serve (0.0.0.0:11434, keep-alive 24h)..."
# OLLAMA_HOST=0.0.0.0 → alcanzable por el túnel/tailnet.
# KEEP_ALIVE=24h → el modelo queda en VRAM entre requests (TTFT bajo en demo).
# OLLAMA_MODELS → ruta persistente si /workspace existe.
nohup env OLLAMA_HOST=0.0.0.0:11434 OLLAMA_KEEP_ALIVE=24h ${OLLAMA_MODELS:+OLLAMA_MODELS=$OLLAMA_MODELS} ollama serve \
  > /var/log/ollama.log 2>&1 &
sleep 5

echo "==> 3/5 Descargando modelos (qwen2.5 ~4.7GB + mxbai ~670MB)..."
echo "    (si ya están en /workspace de una sesión previa, es instantáneo)"
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull mxbai-embed-large

echo "==> 4/5 Calentando qwen2.5 (carga a VRAM)..."
ollama run qwen2.5:7b-instruct-q4_K_M "Responde solo con la palabra: listo" || true

echo "==> 5/5 GPU + endpoint:"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv 2>/dev/null || echo "  (nvidia-smi no disponible)"
curl -fsS localhost:11434/api/tags >/dev/null && echo "  OK: Ollama responde en :11434" || echo "  FALLO: revisa /var/log/ollama.log"

echo
echo "Listo. Ollama sirviendo en 0.0.0.0:11434 dentro del pod."
echo "Siguiente: conecta la VM GCE a este pod (ver docs/runbook-gpu-demo.md)."
