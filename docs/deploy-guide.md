# Deploy Guide — Tutor IA RFA (Sprint 5)

> Guía de despliegue paso a paso desde cero. Asume que el código está completo
> (backend, frontend, scripts infra). Los pasos manuales antes de ejecutar
> `deploy.sh` están explícitos para evitar sorpresas.

---

## 0. Pre-requisitos externos (responsabilidad humana)

| # | Item | Cómo |
|---|------|------|
| A | Cuenta GCP con facturación activa | https://console.cloud.google.com → crear proyecto |
| B | Cuenta Firebase (con el mismo correo Google) | https://console.firebase.google.com → "Agregar proyecto" |
| C | Dominio registrado (sugerido `tutor.iestprfa.edu.pe`) | IESTP IT / registrador DNS |
| D | `gcloud` CLI instalado y autenticado | `gcloud auth login && gcloud config set project <PROJECT_ID>` |
| E | `firebase` CLI instalado y autenticado | `npm i -g firebase-tools && firebase login` |

---

## 1. Provisionar VM Compute Engine

```bash
gcloud compute instances create tutor-vm \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=80GB \
  --boot-disk-type=pd-balanced \
  --tags=http-server,https-server \
  --zone=us-central1-a
```

Habilitar reglas firewall (puertos 80/443):

```bash
gcloud compute firewall-rules create allow-http  --allow=tcp:80
gcloud compute firewall-rules create allow-https --allow=tcp:443
```

Capturar la IP pública:

```bash
gcloud compute instances describe tutor-vm --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

---

## 2. Configurar DNS

Crear un registro **A** en el panel DNS del dominio:

```
tutor.iestprfa.edu.pe.  A  <IP_VM>  TTL 300
```

Verificar propagación (puede tardar minutos):

```bash
dig +short tutor.iestprfa.edu.pe
```

Caddy obtendrá automáticamente certificado Let's Encrypt en el primer arranque
cuando el DNS resuelva a la VM.

---

## 3. Provisionar la VM

SSH a la VM:

```bash
gcloud compute ssh tutor-vm --zone=us-central1-a
```

Dentro de la VM:

```bash
# 1. Clonar repo
git clone https://github.com/<tu-org>/tutor-ia-rfa.git
cd tutor-ia-rfa

# 2. Ejecutar provisionamiento (Docker + Ollama + modelos + firewall + cron)
bash infra/scripts/provision-vm.sh

# 3. Cerrar sesión + reingresar para que el grupo `docker` se aplique
exit
gcloud compute ssh tutor-vm --zone=us-central1-a
```

`provision-vm.sh` deja:

- Docker + Compose plugin
- Ollama nativo + `qwen2.5:7b-instruct-q4_K_M` + `mxbai-embed-large` descargados
- Directorios `/data/{corpus,postgres,redis,uploads}` y `/var/log/{caddy,tutor}`
- UFW abierto en 22/80/443
- Cron diario `0 3 * * *` para `backup-postgres.sh`

---

## 4. Configurar `.env` de producción

```bash
cd ~/tutor-ia-rfa
cp .env.example .env
```

Editar `.env` con valores **reales**:

```bash
# Generar secretos fuertes
echo "SECRET_KEY=$(openssl rand -hex 32)"
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d /+= | head -c 24)"
```

Variables que SÍ deben cambiar respecto a `.env.example`:

| Variable | Valor prod |
|---|---|
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | salida de `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | salida de `openssl rand -base64 32 ...` |
| `DOMAIN` | `tutor.iestprfa.edu.pe` (mismo del DNS) |
| `FRONTEND_DOMAIN` | `tutor-rfa.web.app` (subdominio Firebase) |
| `BACKEND_CORS_ORIGINS` | `'["https://tutor.iestprfa.edu.pe","https://tutor-rfa.web.app"]'` |
| `ADMIN_PASSWORD` | password fuerte (no `Admin123!`) |
| `DATABASE_URL` | `postgresql+asyncpg://tutor_user:${POSTGRES_PASSWORD}@postgres:5432/tutordb` |

---

## 5. Desplegar el stack

```bash
bash infra/scripts/deploy.sh
```

El script:

1. Verifica `.env`
2. `git pull` de `main`
3. `docker compose build --pull`
4. `docker compose up -d` con el overlay VM
5. `alembic upgrade head` + seeds idempotentes
6. Healthcheck `GET /health`

Validar:

```bash
docker compose ps
docker compose logs -f backend
curl -k https://tutor.iestprfa.edu.pe/api/v1/health
```

---

## 6. Desplegar el frontend en Firebase Hosting

Desde tu máquina local (no la VM):

```bash
cd frontend

# 1. Asignar el project ID real en .firebaserc
# Editar manualmente o:
firebase use --add  # selecciona el proyecto en la lista

# 2. Crear .env.production
cp .env.production.example .env.production
# Editar y reemplazar VITE_API_BASE_URL=https://tutor.iestprfa.edu.pe/api/v1

# 3. Build + deploy
npm install
npm run build
firebase deploy --only hosting
```

El frontend queda en `https://<project-id>.web.app` y opcionalmente en
`https://<project-id>.firebaseapp.com`.

Para dominio custom (ej. `tutor-rfa.iestprfa.edu.pe`):
Firebase Console → Hosting → "Agregar dominio personalizado" → seguir el
asistente que te pide crear registros TXT/A en el DNS del dominio.

---

## 7. Validaciones post-deploy

| Check | Comando |
|---|---|
| Health backend | `curl https://tutor.iestprfa.edu.pe/api/v1/health` |
| Login admin | POST `/api/v1/auth/login` con credenciales del `.env` |
| Cert Let's Encrypt | `curl -vI https://tutor.iestprfa.edu.pe 2>&1 | grep -i "issuer"` |
| Frontend carga | abrir `https://<project>.web.app` en navegador |
| Backup cron activo | `crontab -l \| grep backup-postgres` |
| Scheduler activo | `docker compose logs backend \| grep APScheduler` |
| Ollama responde | `curl http://localhost:11434/api/tags` (en la VM) |

---

## 8. Operaciones diarias

| Operación | Comando |
|---|---|
| Ver logs en vivo | `docker compose logs -f backend` |
| Reiniciar backend | `docker compose restart backend` |
| Aplicar nueva versión | `bash infra/scripts/deploy.sh` |
| Backup manual | `bash infra/scripts/backup-postgres.sh` |
| Restaurar backup | `gunzip < /data/backups/postgres/tutordb_<ts>.sql.gz \| docker compose exec -T postgres psql -U tutor_user -d tutordb` |
| Cargar nuevo PDF al corpus | Admin UI `/admin → Corpus RAG → Subir documento` (background reindex) |
| Re-deploy frontend | `cd frontend && npm run build && firebase deploy --only hosting` |

---

## 9. Advertencias

- **Latencia LLM en CPU**: VM `e2-standard-4` sin GPU, `qwen2.5:7b` toma **15–30 s** por respuesta. Documentar en reporte SUS. Si necesario, migrar a `llama3.2:3b-instruct-q4_K_M` (5–10 s, calidad menor — re-ejecutar RAGAS).
- **`apt-get upgrade` durante provision** puede prompt interactivamente por restart de servicios. Pasar `DEBIAN_FRONTEND=noninteractive` si se automatiza.
- **`pgvector IVFFlat` index** debe crearse DESPUÉS de ingestar el corpus. Comando en `CLAUDE.md → ADVERTENCIAS CLAVE`.
- **Costo**: VM e2-standard-4 + disco 80GB + tráfico saliente ≈ USD 120/mes en us-central1. Verificar saldo antes del piloto SUS de 2 semanas.
- **Secretos**: `.env` NO debe commitarse. `cp .env.example .env` y editar en cada VM nueva.

---

## 10. Rollback

Si un deploy rompe producción:

```bash
cd ~/tutor-ia-rfa
git log --oneline -5            # ver último commit estable
git checkout <commit-bueno>     # detached HEAD
bash infra/scripts/deploy.sh    # re-builder + restart con código anterior
```

Para volver a `main`:

```bash
git checkout main
git pull
bash infra/scripts/deploy.sh
```
