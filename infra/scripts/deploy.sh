#!/usr/bin/env bash
# deploy.sh — Despliega Tutor IA RFA en la VM (Docker Compose prod).
# Se ejecuta desde la raíz del repo.

set -euo pipefail

cd "$(dirname "$0")/../.."

echo "==> 1. Verificar .env"
if [ ! -f .env ]; then
    echo "ERROR: falta .env. Copiar de .env.example y ajustar." >&2
    exit 1
fi

echo "==> 2. Fetch + checkout main"
git fetch --all --prune
git checkout main
git pull --ff-only

echo "==> 3. Build imágenes y levantar stack"
docker compose -f docker-compose.yml -f docker-compose.vm.yml build --pull
docker compose -f docker-compose.yml -f docker-compose.vm.yml up -d

echo "==> 4. Esperar backend saludable"
# El comando del contenedor (docker-compose.vm.yml) ya ejecuta alembic upgrade
# + seeds antes de uvicorn. Duplicarlos aquí con `exec` creaba una carrera de
# migraciones contra el arranque del contenedor (rc=1 y el script abortaba por
# set -e antes del healthcheck). Solo esperamos a que el arranque termine.
ok=0
for i in $(seq 1 45); do
    if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
        ok=1
        break
    fi
    sleep 2
done
if [ "$ok" != "1" ]; then
    echo "✗ Backend no responde tras 90s" >&2
    docker compose -f docker-compose.yml -f docker-compose.vm.yml logs --tail=50 backend
    exit 1
fi
echo "✓ Backend OK"

echo ""
echo "=============================================="
echo "✓ Despliegue completado."
echo "Logs:    docker compose logs -f backend"
echo "Status:  docker compose ps"
echo "=============================================="
