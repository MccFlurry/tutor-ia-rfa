"""
logger.py — Configuración Loguru.
- development: colores + DEBUG a stderr
- production: JSON estructurado a stderr + archivo rotado (captura request_id, path, method via contextualize)
"""

import os
import sys
from pathlib import Path

from loguru import logger

from app.config import settings

logger.remove()

if settings.ENVIRONMENT == "development":
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        backtrace=True,
        diagnose=True,
    )
else:
    # Producción · JSON a stderr (capturado por Docker / systemd)
    logger.add(
        sys.stderr,
        level="INFO",
        serialize=True,
        backtrace=False,
        diagnose=False,
    )
    # Archivo rotado en la VM, si existe /var/log/tutor
    log_dir = Path(os.getenv("LOG_DIR", "/var/log/tutor"))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_dir / "app.log",
            level="INFO",
            serialize=True,
            rotation="50 MB",
            retention="14 days",
            compression="gz",
            enqueue=True,
        )
    except (PermissionError, OSError):
        # Sin permiso de escritura en /var/log: queda solo stderr.
        pass
