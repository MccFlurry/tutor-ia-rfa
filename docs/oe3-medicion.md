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

---

## 5. Resultados de medición — 02-jun-2026 (VM CPU `e2-standard-4`)

**Despliegue (cualitativo) — cumple:** sistema operativo en producción · 4 contenedores (postgres+pgvector, redis, backend FastAPI, Caddy) · TLS Let's Encrypt en `api.tutoriesrfa.lat` · frontend en Firebase (`tutor-ia-rfa.web.app`) · 3388 chunks indexados (IVFFlat) · logs JSON + respuestas RAG con citas.

### 5.1 Rendimiento (harness `oe3_perf.py`, 15 reqs, concurrencia 3, `num_predict=128`)

| Indicador | Umbral | Medido | ¿Cumple? |
|-----------|--------|--------|----------|
| TTFT P95 | ≤ 2.5 s | **99.40 s** | ❌ |
| ITL P95 | ≤ 250 ms | **362.6 ms** | ❌ |
| throughput (conc 3) | ≥ 8 tok/s | **2.69 tok/s** | ❌ |
| e2e P95 | ≤ 8 s | no medido (`--e2e` omitido) | — |

**Lectura honesta.** Los umbrales fueron calibrados para aceleración **GPU**; la VM del piloto es **CPU-only**. A concurrencia 3, un único modelo 7B sobre CPU **no paraleliza**: las peticiones se encolan, por lo que el TTFT P95 (99 s) refleja la **saturación por encolamiento**, no la latencia de una sola consulta. La condición real del piloto (10–15 estudiantes con uso esporádico) se aproxima a **1 usuario concurrente**, sustancialmente más rápida (sin cola). La medición formal a concurrencia 3 evidencia, por tanto, la **necesidad de una instancia con GPU** para alcanzar los umbrales.

> Re-encuadre consistente con OE1/OE2 (aprobado por la asesora): se reportan los valores reales y se documenta "sub-2.5 s / ≥8 tok/s requiere GPU" como **recomendación de infraestructura / trabajo futuro**. La **calidad** del RAG ya está validada offline por RAGAS (OE2, 5/5); el rendimiento es un asunto de hardware, no del pipeline.

### 5.2 Disponibilidad — pendiente ventana de observación

Requiere ≥ **48 h** de `tutor-health-poller` corriendo (para MTBF ≥ 48 h). Arrancar el poller al inicio del piloto y medir con `oe3_availability.py` sobre los logs de Caddy + poller. No medido en esta corrida.

### 5.3 Trazabilidad — cumple

- Cobertura RF = **1.0** (33/33, matriz ISO/OE5).
- Exactitud de citación apoyada en RAGAS `context_precision` = **0.876** (OE2).

### 5.4 Conclusión OE3

Despliegue, arquitectura de disponibilidad (healthchecks, `restart: unless-stopped`, backup, poller) y trazabilidad **logrados**. La latencia de generación queda por debajo de los umbrales sobre **CPU**; alcanzarlos exige **GPU** (recomendación de infraestructura documentada). Medición de disponibilidad sobre ventana ≥48 h y, opcionalmente, latencia a concurrencia 1, quedan como mediciones complementarias.

