# Medición OE3 — Rendimiento, disponibilidad y trazabilidad (Sprint 5)

Procedimiento para medir los indicadores de **OE3** sobre el sistema desplegado en
la VM de Google Compute Engine. Requiere el stack levantado (`deploy.sh`) y el
corpus ingestado.

> Contexto: el despliegue actual usa **CPU** (`e2-standard-4`, sin GPU). Los
> umbrales de rendimiento de OE3 fueron definidos pensando en aceleración GPU;
> en CPU se reportan los valores reales y, si no alcanzan el umbral, se documenta
> "sub-8s / sub-2.5s requiere GPU" como recomendación de infraestructura. Misma
> lógica de re-encuadre aprobada por la asesora en OE1/OE2.

## Indicadores y umbrales

| Grupo | Indicador | Umbral | Harness |
|------|-----------|--------|---------|
| Rendimiento | TTFT P95 | ≤ 2.5 s | `oe3_perf.py` |
| Rendimiento | ITL P95 | ≤ 250 ms | `oe3_perf.py` |
| Rendimiento | throughput (conc 3) | ≥ 8 tok/s | `oe3_perf.py` |
| Rendimiento | e2e P95 | ≤ 8 s | `oe3_perf.py --e2e` |
| Disponibilidad | uptime | ≥ 99 % | `oe3_availability.py` |
| Disponibilidad | health checks | ≥ 99 % | `oe3_availability.py` |
| Disponibilidad | 5xx | ≤ 2 % | `oe3_availability.py` |
| Disponibilidad | MTBF | ≥ 48 h | `oe3_availability.py` |
| Trazabilidad | cobertura RF | ≥ 0.95 | matriz ISO (OE5) — ya = 1.0 |
| Trazabilidad | citación / exactitud | ≥ 0.90 / ≥ 0.85 | golden set + RAGAS (context_precision) |

## 1. Arrancar la sonda de disponibilidad (dejar corriendo todo el piloto)

```bash
# en la VM
sudo cp infra/scripts/tutor-health-poller.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tutor-health-poller
systemctl status tutor-health-poller   # debe quedar "active (running)"
```

Esto escribe `epoch,code,latency` cada 60 s en `/var/log/tutor/health.log`. Para
MTBF ≥ 48 h se necesita una ventana de **al menos ~48 h** de observación.

## 2. Medir rendimiento (cuando quieras, sistema vivo)

`oe3_perf.py` corre **dentro del contenedor backend** (usa httpx + app.config):

```bash
# en la VM, raiz del repo
docker compose exec backend python scripts/oe3_perf.py --iterations 30 --concurrency 3
# incluir el plano e2e contra el endpoint real /chat:
docker compose exec backend python scripts/oe3_perf.py --e2e --e2e-iterations 15
```

- TTFT / ITL / throughput se miden contra **Ollama directo** (streaming).
- e2e se mide contra `/chat` autenticado, con preguntas de nonce único (evita
  cache Redis). Limitado por `CHAT_RATE_LIMIT_PER_HOUR` (20): para una muestra
  mayor, sube ese valor en `.env` durante la medición o usa varios usuarios.
- Salida: `oe3_results/perf_<ts>.json` dentro del contenedor.

## 3. Medir disponibilidad (tras ≥48 h de poller)

`oe3_availability.py` es **stdlib puro** → corre en el **host** (lee los logs de
Caddy y del poller, que viven en el host):

```bash
# en la VM, raiz del repo
python3 backend/scripts/oe3_availability.py \
    --caddy-log /var/log/caddy/access.log \
    --health-log /var/log/tutor/health.log
```

- 5xx % y latencia proxy salen del access.log JSON de Caddy.
- uptime %, health % y MTBF salen del log del poller.
- Salida: `oe3_results/availability_<ts>.json`.

## 4. Cerrar la medición

```bash
sudo systemctl disable --now tutor-health-poller
```

Consolidar los JSON de `oe3_results/` en `docs/reporte-OE3-despliegue.docx` junto
con la evidencia de despliegue (uptime de la VM, capturas de Caddy/cert, etc.).
