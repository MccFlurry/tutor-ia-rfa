# PROD-STATE — Estado de producción (Sprint 5)

> Estado del despliegue productivo en Google Compute Engine. Actualizar este
> archivo cuando cambie algo de infra/prod. Desplegado el **2026-06-02**.

## URLs

| Qué | URL |
|---|---|
| Frontend (estudiantes) | https://tutor-ia-rfa.web.app |
| Backend API | https://api.tutoriesrfa.lat |
| Health | https://api.tutoriesrfa.lat/api/v1/health |
| Firebase console | https://console.firebase.google.com/project/tutor-ia-rfa |
| Admin login | `admin@iestprfa.edu.pe` (password en `.env` de la VM) |

Dominio custom `tutoriesrfa.lat` (Porkbun): **solo `api.` apunta a la VM**. El
frontend quedó en `.web.app` (apuntar la raíz a Firebase es opcional, no hecho).

## Infraestructura

- **GCP project:** `tutor-ia-rfa` (cuenta paga `meencantas7u7@gmail.com`).
- **VM:** `tutor-vm` · `e2-standard-4` (4 vCPU, 16GB RAM, **CPU, sin GPU**) · zona `us-central1-a` · Ubuntu 22.04 · disco 80GB.
- **IP estática:** `35.254.147.254` (recurso `tutor-ip`, región us-central1).
- **Firewall:** GCP `allow-http`(80) + `allow-https`(443) + SSH(22). UFW idem + `172.18.0.0/16 → 11434` (bridge Docker → Ollama).
- **Stack:** `docker compose -f docker-compose.yml -f docker-compose.vm.yml` → contenedores `tutor_postgres`, `tutor_redis`, `tutor_backend`, `tutor_caddy`. **Ollama nativo** (systemd) en la VM, alcanzado vía `host.docker.internal`.
- **TLS:** Caddy + Let's Encrypt (auto).
- **Modelos Ollama:** `qwen2.5:7b-instruct-q4_K_M` + `mxbai-embed-large`.

## Datos en prod

- Seed: 5 módulos, 22 temas, 25 quizzes, 7 desafíos, 7 logros, 23 banco evaluación, 1 admin.
- **Corpus RAG:** 153 documentos / **3388 chunks** (M1=181, M2=706, M3=596, M4=1065, M5=833) + índice IVFFlat `idx_chunks_embedding` (lists=58). El corpus NO está en git (vive local en `corpus/semana-XX/`); se sube por scp + `docker exec tutor_backend python scripts/ingest_corpus.py`.

## Operación (desde la PC)

gcloud está en `C:\Users\meenc\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd`.

```powershell
$g = "C:\Users\meenc\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
# SSH
& $g compute ssh tutor-vm --zone=us-central1-a --quiet
# Apagar para ahorrar (la IP estática persiste, el dominio no se rompe)
& $g compute instances stop  tutor-vm --zone=us-central1-a
& $g compute instances start tutor-vm --zone=us-central1-a
```

> ⚠️ En comandos remotos vía `--command='...'`: **nunca comillas dobles ni
> simples adentro** (rompen el parsing de gcloud.cmd). Para SQL/JSON: subir un
> archivo por scp y pasarlo por stdin (`cat file | docker exec -i ...`).

Dentro de la VM (repo en `~/tutor-ia-rfa`):
```bash
docker compose -f docker-compose.yml -f docker-compose.vm.yml ps
docker logs tutor_backend --tail 50
docker compose -f docker-compose.yml -f docker-compose.vm.yml restart backend
```

## Costo
e2-standard-4 ≈ USD 100-120/mes si corre 24/7. **Apagar fuera de sesiones.**

## Fixes aplicados en la VM que faltan en el repo
1. **Ollama listen** — escuchaba solo `127.0.0.1` → el contenedor no lo alcanzaba (ingesta/RAG fallaban). Corregido con `/etc/systemd/system/ollama.service.d/override.conf` → `OLLAMA_HOST=0.0.0.0:11434` + regla UFW. **Pendiente: agregarlo a `infra/scripts/provision-vm.sh`.**

## Bugs conocidos
- **`deploy.sh`** corre `alembic upgrade` + seeds vía `exec` que duplican el comando de arranque del contenedor → carrera de migraciones → `duplicate key pg_type` → `rc=1` **cosmético** (el sistema queda OK). Fix: quitar pasos 4-5 redundantes. *(El auto-deploy de abajo NO usa deploy.sh, así que evita este bug.)*

## OE3 (rendimiento) — realidad CPU
Smoke test (conc 3): **TTFT P95 122s · ITL 404ms · throughput 1.85 tok/s** → NO
cumple umbrales (≤2.5s / ≤250ms / ≥8 tok/s). Esperado en CPU. Re-encuadre:
"sub-8s requiere GPU = recomendación de infra" (mismo criterio aprobado por la
asesora en OE1/OE2). Harness: `backend/scripts/oe3_perf.py`,
`oe3_availability.py`; guía `docs/oe3-medicion.md`.

## Pendientes
1. **Modelo del piloto** — 7b es lento en CPU. Opciones: bajar `num_ctx` 8192→4096 en `rag_service.py` (barato, no toca OE1/OE2) · cambiar a `llama3.2:3b` (re-validar OE1/OE2) · esperar GPU T4 (cuota se desbloquea ~1 sem tras generar historial de gasto, iniciado 2026-06-02).
2. **Medición OE3 formal** — arrancar poller (servicio `tutor-health-poller`) 48h + `oe3_perf.py --e2e` + `oe3_availability.py` → `docs/reporte-OE3-despliegue.docx`.
3. Fix `provision-vm.sh` (Ollama 0.0.0.0) + `deploy.sh` (carrera migraciones).
4. (Opcional) dominio custom `tutoriesrfa.lat` → frontend en Firebase.

## Auto-deploy a prod (commit → pull)
Hook local `.git/hooks/post-commit`: en cada commit de **`main`** hace
`git push origin main` y luego en la VM `git fetch && git reset --hard
origin/main && docker compose restart backend`. Reinicia el backend en cada
commit de main; aplica cambios de código (bind-mount). **Cambios de
dependencias (`requirements.txt`) necesitan rebuild manual** (`deploy.sh` o
`docker compose build backend`). Desactivar: borrar el archivo del hook.
