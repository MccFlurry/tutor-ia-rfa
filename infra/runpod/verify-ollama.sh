#!/usr/bin/env bash
# verify-ollama.sh — Comprueba que el endpoint Ollama responde y mide tokens/s.
# Ejecutar desde la VM GCE (o donde quieras probar el endpoint).
# Uso:  OLLAMA_URL=http://host.docker.internal:11434 ./verify-ollama.sh
#       OLLAMA_URL=http://100.x.y.z:11434             ./verify-ollama.sh   (tailscale)
set -euo pipefail
URL="${OLLAMA_URL:-http://localhost:11434}"

echo "==> Endpoint: $URL"
echo "==> Modelos disponibles:"
curl -fsS "$URL/api/tags" \
  | python3 -c "import sys,json;[print('  -',m['name']) for m in json.load(sys.stdin)['models']]"

echo "==> Generación cronometrada (qwen2.5):"
curl -fsS "$URL/api/generate" -d '{
  "model":"qwen2.5:7b-instruct-q4_K_M",
  "prompt":"Explica en una sola frase qué es una Activity en Android.",
  "stream":false,
  "options":{"temperature":0.3}
}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('  respuesta:', d['response'][:160])
tps = d['eval_count']/(d['eval_duration']/1e9)
print(f'  velocidad: {tps:.1f} tok/s  (CPU actual ~3-8 tok/s)')
"
echo "==> Si ves >40 tok/s, la GPU está activa. Conecta el backend."
