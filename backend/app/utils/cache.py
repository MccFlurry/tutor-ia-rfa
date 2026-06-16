"""
cache.py — Helper genérico de caché Redis para endpoints frecuentes.

Patrón: clave determinista derivada del scope + user_id (cuando aplique),
TTL corto (60s default) para mantener frescura aceptable mientras se
mitiga la latencia. JSON-encoded para portabilidad.

Uso típico en un router:

    from app.utils.cache import cached_json
    payload = await cached_json(
        redis, f"dash:{user.id}",
        ttl=60,
        loader=lambda: _expensive_query(...),
    )
"""

import json
from typing import Any, Awaitable, Callable

from app.utils.logger import logger


async def cached_json(
    redis_client,
    key: str,
    *,
    ttl: int,
    loader: Callable[[], Awaitable[Any]],
) -> Any:
    """Return cached value or compute via loader and persist.

    `loader` is awaited only on cache miss. The result must be JSON-serializable.
    If Redis is unavailable, falls through to loader without raising (degraded
    mode keeps the endpoint serving even with a flaky cache).
    """
    try:
        raw = await redis_client.get(key)
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(f"[cache] Redis get falló para {key}: {e}; cae a loader")

    value = await loader()

    try:
        await redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"[cache] Redis setex falló para {key}: {e}")

    return value


async def invalidate(redis_client, *keys: str) -> None:
    """Delete cache keys (e.g. after a mutation). Errors are swallowed."""
    try:
        for k in keys:
            await redis_client.delete(k)
    except Exception as e:
        logger.warning(f"[cache] Redis delete falló: {e}")


async def invalidate_prefix(redis_client, prefix: str) -> None:
    """Delete every key starting with `prefix` (SCAN-based). Errors swallowed
    (degraded mode): a flaky cache must never break the mutation that triggers it."""
    try:
        async for key in redis_client.scan_iter(match=f"{prefix}*"):
            await redis_client.delete(key)
    except Exception as e:
        logger.warning(f"[cache] Redis invalidate_prefix falló para {prefix}: {e}")
