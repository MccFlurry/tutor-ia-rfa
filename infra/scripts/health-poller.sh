#!/usr/bin/env bash
# health-poller.sh — Sonda de disponibilidad [OE3].
# Hace curl al endpoint /health cada INTERVAL segundos y registra una linea
# CSV  epoch,http_code,latency_s  en LOG. Ese log lo consume
# scripts/oe3_availability.py para calcular uptime, health% y MTBF.
#
# Variables (env, todas opcionales):
#   HEALTH_URL       endpoint a sondear (default: dominio publico vía Caddy)
#   HEALTH_LOG       archivo de salida   (default: /var/log/tutor/health.log)
#   HEALTH_INTERVAL  segundos entre sondas (default: 60)
#
# Recomendado correrlo como servicio systemd (ver tutor-health-poller.service)
# para que sobreviva reinicios. Alternativa rapida:
#   nohup HEALTH_URL=... bash infra/scripts/health-poller.sh >/dev/null 2>&1 &

set -u

URL="${HEALTH_URL:-https://api.tutoriesrfa.lat/api/v1/health}"
LOG="${HEALTH_LOG:-/var/log/tutor/health.log}"
INTERVAL="${HEALTH_INTERVAL:-60}"

mkdir -p "$(dirname "$LOG")"

while true; do
    start=$(date +%s.%N)
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$URL" 2>/dev/null || echo 000)
    end=$(date +%s.%N)
    lat=$(awk "BEGIN{printf \"%.3f\", ${end} - ${start}}")
    printf '%s,%s,%s\n' "$(date +%s)" "$code" "$lat" >> "$LOG"
    sleep "$INTERVAL"
done
