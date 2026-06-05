# Runbook — GPU externa (RunPod) para la demo

> **Infra de DEMO, no de tesis.** La arquitectura documentada sigue siendo
> "1 VM GCE + Ollama nativo" (ver `docs/arquitectura.docx` / Figura C4). Esto
> solo reubica la **inferencia** a una GPU rentada mientras el CPU de la VM es
> lento. Postgres, Redis, backend, Caddy y el frontend Firebase **no se tocan**.
> Solo cambia el destino de `OLLAMA_BASE_URL`.
>
> Se mantiene `qwen2.5:7b-instruct-q4_K_M` (NO bajar a llama3.2:3b) para no
> invalidar la validación OE1/OE2/RAGAS.
>
> **Estado (2026-06-05):** pod GPU RunPod **RTX 3090 24GB LISTO** — qwen2.5 a
> **~135 tok/s** (vs 3-8 en CPU), ambos modelos persistidos en `/workspace`.
> Pod ID `ezhivdjw3h5d2i`. Falta solo el túnel VM→pod (Fase C), que se hace el
> día de la demo porque la VM GCE está apagada. Llave en `~/.ssh/runpod_key` (laptop).

## Topología

```
Firebase Hosting (frontend)
        │ HTTPS
        ▼
  api.tutoriesrfa.lat ── Caddy+LE ── backend (Docker, GCE VM)
                                          │ OLLAMA_BASE_URL
                                          ▼
                              Ollama qwen2.5 + mxbai  ← AHORA en GPU RunPod
```

---

## Fase A — Lanzar el pod GPU (consola RunPod)

1. Cuenta en runpod.io → carga saldo (la demo cuesta centavos/hora; precio no importa).
2. **Deploy → GPU Pod**. GPU recomendada para 7B-q4:
   - **RTX 4090 24GB** (la más barata que sobra; ~70-120 tok/s) — o
   - **L40S 48GB** si quieres holgura.
3. Template: cualquiera basada en Ubuntu/CUDA (o la plantilla "Ollama" si aparece).
   Asegura que el pod permita **SSH** (RunPod lo da por defecto: IP pública + puerto TCP).
4. **Región: la más cercana a tu VM GCE** (menos RTT al TTFT).
5. Lanza el pod. Anota: **IP pública**, **puerto SSH** y la **clave SSH**.

## Fase B — Instalar Ollama + modelos en el pod

En la web-terminal del pod (o por SSH):

```bash
# sube/pega el script y ejecútalo
bash setup-ollama-pod.sh      # infra/runpod/setup-ollama-pod.sh de este repo
```

Descarga ~5.4GB de modelos y los deja sirviendo en `0.0.0.0:11434` con el modelo
caliente en VRAM. Si la plantilla ya trae Ollama, el script es idempotente.

---

## Fase C — Conectar la VM GCE al pod (elige UNA)

### Opción 1 — Túnel SSH (RECOMENDADA: privada, sin cambiar compose)

El backend ya alcanza Ollama vía `host.docker.internal:11434`. Reemplazamos el
Ollama nativo por un túnel SSH a la GPU. Ollama del pod queda solo en localhost
(no expuesto a internet); el único acceso es por clave SSH.

Ya hay un script que hace todo. **Día de la demo**, con la VM encendida:

```bash
# 1. (desde el laptop) copiar la llave privada a la VM
gcloud compute scp ~/.ssh/runpod_key tutor-vm:~/.ssh/runpod_key --zone=us-central1-a

# 2. (desde el laptop) copiar el script a la VM, o usar el del repo en la VM
gcloud compute scp infra/runpod/connect-vm-to-pod.sh tutor-vm:~/ --zone=us-central1-a

# 3. (en la VM) tomar IP+PUERTO de RunPod > Connect > "SSH over exposed TCP"
#    (CAMBIAN cada reinicio del pod) y levantar el túnel + reiniciar backend:
gcloud compute ssh tutor-vm --zone=us-central1-a
POD_IP=<IP_POD> POD_PORT=<PUERTO_POD> bash ~/connect-vm-to-pod.sh
```

El script apaga el Ollama nativo, levanta el túnel `autossh` (bind 0.0.0.0 con `-g`
para que el contenedor llegue vía `host.docker.internal`), reinicia el backend y
verifica que el contenedor alcanza la GPU. Compose **sin cambios**
(`OLLAMA_BASE_URL=http://host.docker.internal:11434`).

> Seguridad: el `-g` expone 11434 en todas las interfaces de la VM. UFW debe
> seguir permitiendo solo 22/80/443 (provision-vm.sh ya lo hace) → 11434 no es
> alcanzable desde internet, solo por la red docker local.

### Opción 2 — Tailscale (privada, sin túnel manual)

```bash
# En la VM GCE y en el pod:
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up        # autentica ambos en el mismo tailnet
tailscale ip -4          # anota la IP 100.x del POD
```

En la VM, edita el `OLLAMA_BASE_URL` del backend en `docker-compose.vm.yml`
(o pásalo por env) a `http://<IP_TAILSCALE_POD>:11434` y reinicia el backend.
Requiere `/dev/net/tun` en el pod (los GPU pods de RunPod Secure Cloud lo traen).
Si el contenedor no alcanza la IP 100.x, usa la Opción 1.

### Opción 3 — Endpoint público RunPod (ÚLTIMO RECURSO)

Solo si 1 y 2 fallan y estás contra reloj.

> ⚠️ **Seguridad:** Ollama NO tiene autenticación. Exponer el puerto público
> deja tu GPU abierta a cualquiera que descubra la URL y permite prompt-injection
> directo al modelo. El pod NO contiene datos sensibles (corpus y datos de
> estudiantes viven en Postgres/GCE), así que el riesgo es "te gastan GPU".
> Si la usas: **destruye el pod apenas termine la demo** y no reutilices la URL.

Expón el puerto 11434 (TCP público) en RunPod, toma la URL `IP:puerto` y en la VM
pon `OLLAMA_BASE_URL=http://<IP_PUBLICA_POD>:<PUERTO>` → reinicia backend.

---

## Fase D — Verificar

```bash
# Desde la VM:
OLLAMA_URL=http://host.docker.internal:11434 bash infra/runpod/verify-ollama.sh
```

Debe listar `qwen2.5:7b-instruct-q4_K_M` + `mxbai-embed-large` y mostrar **>40 tok/s**.
Luego prueba un chat real en la app (tutor-ia-rfa.web.app) y confirma latencia baja.

## Fase E — Apagar / encender (uso recurrente)

Patrón: **se apaga la GPU cuando no se trabaja** y se reenciende para trabajar/demo.

**Para pausar (deja de cobrar la GPU $0.46/hr):**
- RunPod > pod > **Stop**. NO borres el network volume (conserva los modelos, ~$3.6/mes).
- En la VM (si estaba conectada): `pkill -f "11434:localhost:11434"; sudo systemctl start ollama`.

**Para reanudar:**
1. RunPod > **Start** (o redeploy con el mismo network volume si la 3090 fue tomada).
2. El container disk se borró al detener → re-instala Ollama (binario, ~15s) y
   re-sirve. Los modelos siguen en `/workspace` → no se descargan. Desde el laptop:
   ```bash
   tr -d '\r' < infra/runpod/setup-ollama-pod.sh | \
     ssh -i ~/.ssh/runpod_key -p <PUERTO_NUEVO> root@<IP_NUEVA> 'bash -s'
   ```
3. Toma el **nuevo IP+PUERTO** (Connect > SSH over exposed TCP — cambian cada vez).
4. Conecta la VM (Fase C): `POD_IP=... POD_PORT=... bash ~/connect-vm-to-pod.sh`.

## Fase F — Teardown definitivo (fin del proyecto)

```bash
# En la VM: matar el túnel y volver al Ollama nativo
pkill -f "11434:localhost:11434"
sudo systemctl start ollama
docker compose -f docker-compose.yml -f docker-compose.vm.yml restart backend
```

Luego en RunPod **Terminate** el pod **y borra el network volume** (deja de
facturar del todo). El sistema vuelve a su estado documentado (Ollama nativo en la VM).

---

## Checklist

- [ ] Pod GPU lanzado (RTX 4090 / L40S), región cercana a la VM
- [ ] `setup-ollama-pod.sh` corrido → modelos descargados + servidos
- [ ] Conexión elegida (SSH túnel / Tailscale) levantada y privada
- [ ] `verify-ollama.sh` muestra >40 tok/s
- [ ] Backend reiniciado, chat real rápido en la app
- [ ] (post-demo) Túnel cerrado, Ollama nativo restaurado, **pod destruido**
