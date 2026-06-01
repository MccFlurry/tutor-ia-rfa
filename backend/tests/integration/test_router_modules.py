"""Integration tests para /api/v1/modules."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.integration.conftest import (
    result_scalar,
    result_scalar_one_or_none,
    result_scalars_all,
    result_rows,
)


def _make_module(id_=1, title="Fundamentos", order=1):
    return SimpleNamespace(
        id=id_,
        title=title,
        description="desc",
        order_index=order,
        icon_name="book",
        color_hex="#3b82f6",
        is_active=True,
    )


def _make_topic(id_=10, module_id=1, order=1):
    return SimpleNamespace(
        id=id_,
        title=f"Tema {id_}",
        module_id=module_id,
        order_index=order,
        estimated_minutes=30,
        has_quiz=True,
        is_active=True,
        content="contenido",
        video_url=None,
    )


@pytest.mark.asyncio
async def test_list_modules_empty(client, mock_db):
    mock_db.execute.side_effect = [
        result_scalars_all([]),  # modules
    ]
    r = await client.get("/api/v1/modules")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_modules_locks_after_incomplete(client, mock_db):
    m1 = _make_module(1, "M1", 1)
    m2 = _make_module(2, "M2", 2)
    mock_db.execute.side_effect = [
        result_scalars_all([m1, m2]),
        result_scalar(4),  # M1 total topics
        result_scalar(2),  # M1 completed (50% — not done)
        result_scalar(4),  # M2 total
        result_scalar(0),  # M2 completed
    ]
    r = await client.get("/api/v1/modules")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert body[0]["is_locked"] is False  # M1 unlocked
    assert body[1]["is_locked"] is True   # M2 locked (M1 incomplete)
    assert body[0]["progress_pct"] == 50.0


@pytest.mark.asyncio
async def test_get_module_not_found(client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await client.get("/api/v1/modules/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_module_returns_topics(client, mock_db):
    m1 = _make_module(1)
    t1 = _make_topic(10, module_id=1, order=1)
    t2 = _make_topic(11, module_id=1, order=2)

    progress = SimpleNamespace(
        topic_id=10, is_completed=True, first_visited_at="x"
    )
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(m1),   # module fetch
        result_scalars_all([m1]),        # lock check: modules ordered
        result_rows([(1, 2)]),           # lock check: totals per module
        result_rows([(1, 1)]),           # lock check: done per module (M1 first → unlocked)
        result_scalars_all([t1, t2]),    # topics
        result_scalars_all([progress]),  # progress map
        result_rows([(10, 1)]),          # coding_map for t1
    ]
    r = await client.get("/api/v1/modules/1")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 1
    assert body["is_locked"] is False
    assert len(body["topics"]) == 2
    statuses = {t["id"]: t["status"] for t in body["topics"]}
    assert statuses[10] == "completed"
    assert statuses[11] == "not_started"


@pytest.mark.asyncio
async def test_get_module_locked_withholds_topics(client, mock_db):
    """Un módulo bloqueado no expone sus temas y se marca is_locked=True."""
    m1 = _make_module(1, "M1", 1)
    m2 = _make_module(2, "M2", 2)
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(m2),    # module fetch (M2)
        result_scalars_all([m1, m2]),     # lock check: modules ordered
        result_rows([(1, 4), (2, 4)]),    # totals: M1=4, M2=4
        result_rows([(1, 2)]),            # done: M1=2 (50%, incompleto) → M2 bloqueado
    ]
    r = await client.get("/api/v1/modules/2")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 2
    assert body["is_locked"] is True
    assert body["topics"] == []
