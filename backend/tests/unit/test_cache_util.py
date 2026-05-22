"""
Unit tests para app/utils/cache.py — helper Redis genérico.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.utils import cache


class TestCachedJson:
    @pytest.mark.asyncio
    async def test_cache_miss_invokes_loader_and_persists(self):
        redis = MagicMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock()

        loader_calls = []

        async def loader():
            loader_calls.append(1)
            return {"a": 1}

        out = await cache.cached_json(redis, "k", ttl=60, loader=loader)
        assert out == {"a": 1}
        assert len(loader_calls) == 1
        redis.setex.assert_awaited_once()
        args = redis.setex.await_args.args
        assert args[0] == "k"
        assert args[1] == 60
        assert json.loads(args[2]) == {"a": 1}

    @pytest.mark.asyncio
    async def test_cache_hit_skips_loader(self):
        redis = MagicMock()
        redis.get = AsyncMock(return_value=json.dumps({"cached": True}))
        redis.setex = AsyncMock()

        async def loader():
            raise AssertionError("loader should not run on cache hit")

        out = await cache.cached_json(redis, "k", ttl=60, loader=loader)
        assert out == {"cached": True}
        redis.setex.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_redis_get_failure_falls_through_to_loader(self):
        redis = MagicMock()
        redis.get = AsyncMock(side_effect=RuntimeError("redis down"))
        redis.setex = AsyncMock()

        async def loader():
            return {"ok": True}

        out = await cache.cached_json(redis, "k", ttl=60, loader=loader)
        assert out == {"ok": True}

    @pytest.mark.asyncio
    async def test_redis_setex_failure_does_not_propagate(self):
        redis = MagicMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock(side_effect=RuntimeError("redis down"))

        async def loader():
            return [1, 2]

        out = await cache.cached_json(redis, "k", ttl=60, loader=loader)
        assert out == [1, 2]

    @pytest.mark.asyncio
    async def test_default_handles_datetime(self):
        """json.dumps usa default=str → datetime serializa sin TypeError."""
        from datetime import datetime, timezone

        redis = MagicMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock()

        async def loader():
            return {"ts": datetime(2026, 5, 21, tzinfo=timezone.utc)}

        await cache.cached_json(redis, "k", ttl=60, loader=loader)
        args = redis.setex.await_args.args
        assert "2026-05-21" in args[2]


class TestInvalidate:
    @pytest.mark.asyncio
    async def test_deletes_each_key(self):
        redis = MagicMock()
        redis.delete = AsyncMock()
        await cache.invalidate(redis, "a", "b", "c")
        assert redis.delete.await_count == 3

    @pytest.mark.asyncio
    async def test_swallows_redis_errors(self):
        redis = MagicMock()
        redis.delete = AsyncMock(side_effect=RuntimeError("down"))
        # Should not raise
        await cache.invalidate(redis, "k")
