"""Integration tests para /api/v1/dashboard."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.integration.conftest import (
    result_scalar,
    result_scalar_one_or_none,
    result_scalars_all,
    result_rows,
)


def _module(id_=1, order=1):
    return SimpleNamespace(
        id=id_, title=f"M{id_}", description="desc",
        icon_name="book", color_hex="#3b82f6", order_index=order, is_active=True,
    )


@pytest.mark.asyncio
async def test_dashboard_empty_state(client, mock_db, fake_user):
    # No level, no topics, no progress, no modules, no achievements
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(None),  # user level
        result_scalar(0),                 # total topics
        result_scalar(0),                 # completed
        result_rows([]),                  # last accessed
        result_scalars_all([]),           # modules
        result_rows([]),                  # achievements
    ]
    r = await client.get("/api/v1/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["user_name"] == fake_user.full_name
    assert body["overall_progress_pct"] == 0.0
    assert body["total_topics_completed"] == 0
    assert body["last_accessed_topic"] is None
    assert body["recommended_modules"] == []
    assert body["recent_achievements"] == []


@pytest.mark.asyncio
async def test_dashboard_with_progress(client, mock_db, fake_user):
    level = SimpleNamespace(level="intermediate")
    m1 = _module(1, 1)
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(level),  # user level
        result_scalar(10),                 # total topics
        result_scalar(3),                  # completed
        result_rows([]),                   # last accessed (empty)
        result_scalars_all([m1]),          # modules
        result_scalar(4),                  # m1 total topics
        result_scalar(2),                  # m1 done topics → 50% → recommended
        result_rows([]),                   # achievements
    ]
    r = await client.get("/api/v1/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["user_level"] == "intermediate"
    assert body["overall_progress_pct"] == 30.0
    assert len(body["recommended_modules"]) == 1
    assert body["recommended_modules"][0]["progress_pct"] == 50.0


@pytest.mark.asyncio
async def test_dashboard_excludes_locked_modules(client, mock_db, fake_user):
    """Las recomendaciones nunca incluyen módulos bloqueados.

    M1 100% (completo → no se recomienda), M2 desbloqueado al 0% (se recomienda),
    M3 bloqueado porque M2 no está completo (no se recomienda).
    """
    level = SimpleNamespace(level="beginner")
    m1, m2, m3 = _module(1, 1), _module(2, 2), _module(3, 3)
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(level),   # user level
        result_scalar(12),                  # total topics
        result_scalar(4),                   # completed
        result_rows([]),                    # last accessed
        result_scalars_all([m1, m2, m3]),   # modules
        result_scalar(4), result_scalar(4),  # M1 total/done → 100% (skip, complete)
        result_scalar(4), result_scalar(0),  # M2 total/done → 0% (unlocked, recommend)
        result_scalar(4), result_scalar(0),  # M3 total/done → 0% (locked, skip)
        result_rows([]),                    # achievements
    ]
    r = await client.get("/api/v1/dashboard")
    assert r.status_code == 200
    body = r.json()
    ids = [m["id"] for m in body["recommended_modules"]]
    assert ids == [2]  # solo M2: M1 completo, M3 bloqueado
