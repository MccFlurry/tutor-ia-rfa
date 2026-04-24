#!/usr/bin/env bash
# backup-postgres.sh — Dump diario de PostgreSQL con retención de 14 días.
# Programar vía cron: 0 3 * * * /home/user/tutor-ia-rfa/infra/scripts/backup-postgres.sh

set -euo pipefail

BACKUP_DIR="/data/backups/postgres"
RETENTION_DAYS=14
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/tutordb_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "==> Dump $BACKUP_FILE"
docker compose exec -T postgres \
    pg_dump -U tutor_user -d tutordb --no-owner --no-privileges \
    | gzip -9 > "$BACKUP_FILE"

SIZE="$(du -h "$BACKUP_FILE" | cut -f1)"
echo "✓ Backup creado ($SIZE)"

echo "==> Limpieza backups > $RETENTION_DAYS días"
find "$BACKUP_DIR" -name 'tutordb_*.sql.gz' -type f -mtime +$RETENTION_DAYS -delete -print

echo "✓ Listo"
