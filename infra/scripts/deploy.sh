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

echo "==> 4. Aplicar migraciones Alembic"
docker compose exec -T backend alembic upgrade head

echo "==> 5. Seed idempotente"
docker compose exec -T backend python scripts/seed_db.py || true
docker compose exec -T backend python scripts/seed_assessment_bank.py || true

echo "==> 6. Healthcheck"
sleep 5
if curl -fsS http://localhost:8000/health >/dev/null; then
    echo "✓ Backend OK"
else
    echo "✗ Backend no responde" >&2
    docker compose logs --tail=50 backend
    exit 1
fi

echo ""
echo "=============================================="
echo "✓ Despliegue completado."
echo "Logs:    docker compose logs -f backend"
echo "Status:  docker compose ps"
echo "=============================================="
