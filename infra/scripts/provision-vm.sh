#!/usr/bin/env bash
# provision-vm.sh — Aprovisiona VM Compute Engine (Ubuntu 22.04) para Tutor IA RFA.
# Uso: ejecutar UNA SOLA VEZ en una VM recién creada, como usuario con sudo.

set -euo pipefail

echo "==> 1. Actualizar sistema"
sudo apt-get update
sudo apt-get upgrade -y

echo "==> 2. Instalar utilidades base"
sudo apt-get install -y \
    curl \
    git \
    ufw \
    ca-certificates \
    gnupg \
    lsb-release \
    tmux \
    htop

echo "==> 3. Instalar Docker + Docker Compose plugin"
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    sudo usermod -aG docker "$USER"
    echo "Usuario $USER añadido al grupo docker. Cerrar sesión y reingresar para aplicar."
fi

echo "==> 4. Instalar Ollama (binario oficial)"
if ! command -v ollama >/dev/null 2>&1; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

echo "==> 5. Descargar modelos LLM + embeddings"
sudo systemctl enable --now ollama
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull mxbai-embed-large

echo "==> 6. Crear directorios persistentes"
sudo mkdir -p /data/corpus /data/postgres /data/redis /data/uploads /var/log/caddy
sudo chown -R "$USER":"$USER" /data

echo "==> 7. Configurar firewall UFW"
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo "==> 8. Clonar repositorio (si aún no existe)"
cd "$HOME"
if [ ! -d "tutor-ia-rfa" ]; then
    echo "Clona manualmente: git clone <repo_url> tutor-ia-rfa"
fi

echo "==> 9. Programar backup diario PostgreSQL (cron a las 03:00)"
BACKUP_SCRIPT="$HOME/tutor-ia-rfa/infra/scripts/backup-postgres.sh"
CRON_LINE="0 3 * * * $BACKUP_SCRIPT >> /var/log/tutor/backup.log 2>&1"
if ! (crontab -l 2>/dev/null | grep -Fq "$BACKUP_SCRIPT"); then
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Cron agregado: $CRON_LINE"
else
    echo "Cron de backup ya existe, no se duplica."
fi
sudo mkdir -p /var/log/tutor
sudo chown -R "$USER":"$USER" /var/log/tutor

echo ""
echo "=============================================="
echo "✓ VM aprovisionada."
echo "Siguientes pasos:"
echo "  1. Cerrar sesión y reingresar (para grupo docker)."
echo "  2. cd ~/tutor-ia-rfa && cp .env.example .env  # ajustar secretos"
echo "  3. Configurar DNS → IP pública VM"
echo "  4. Ejecutar ./infra/scripts/deploy.sh"
echo "=============================================="
