"""Integration tests para /api/v1/topics."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.integration.conftest import (
    result_scalar,
    result_scalar_one,
    result_scalar_one_or_none,
)


def _topic(id_=1, module_id=1):
    return SimpleNamespace(
        id=id_,
        title=f"Tema {id_}",
        module_id=module_id,
        order_index=1,
        estimated_minutes=30,
        has_quiz=True,
        is_active=True,
        content="contenido **markdown**",
        video_url="https://youtube.com/x",
    )


def _module(id_=1):
    return SimpleNamespace(
        id=id_,
        title="M1",
        description="desc",
        order_index=1,
        icon_name="book",
        color_hex="#fff",
    )


@pytest.mark.asyncio
async def test_get_topic_404(client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await client.get("/api/v1/topics/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_topic_returns_payload(client, mock_db):
    t = _topic()
    m = _module()
    progress = SimpleNamespace(
        is_completed=False,
        time_spent_seconds=120,
        first_visited_at=datetime.now(timezone.utc),
        completed_at=None,
    )
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(t),  # _get_topic_or_404
        result_scalar_one(m),          # module lookup
        result_scalar_one_or_none(progress),  # progress lookup
        result_scalar(1),              # coding count
    ]
    r = await client.get("/api/v1/topics/1")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 1
    assert body["has_coding_challenge"] is True
    assert body["module"]["id"] == 1
    assert body["progress_info"]["time_spent_seconds"] == 120


@pytest.mark.asyncio
async def test_visit_topic_creates_progress(client, mock_db):
    t = _topic()
    # _get_topic_or_404 → topic; _get_or_create_progress → None (new)
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(t),
        result_scalar_one_or_none(None),
    ]
    r = await client.post("/api/v1/topics/1/visit")
    assert r.status_code == 200
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_topic_marks_existing_progress(client, mock_db):
    t = _topic()
    progress = SimpleNamespace(
        is_completed=False,
        completed_at=None,
        first_visited_at=datetime.now(timezone.utc),
        last_accessed_at=None,
        time_spent_seconds=0,
    )
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(t),
        result_scalar_one_or_none(progress),
    ]
    r = await client.post("/api/v1/topics/1/complete")
    assert r.status_code == 200
    assert r.json()["is_completed"] is True
    assert progress.is_completed is True


@pytest.mark.asyncio
async def test_track_time_accumulates(client, mock_db):
    t = _topic()
    progress = SimpleNamespace(
        is_completed=False,
        first_visited_at=datetime.now(timezone.utc),
        last_accessed_at=None,
        time_spent_seconds=100,
        completed_at=None,
    )
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(t),
        result_scalar_one_or_none(progress),
    ]
    r = await client.post("/api/v1/topics/1/time", json={"seconds": 50})
    assert r.status_code == 200
    assert r.json()["total_seconds"] == 150
    assert progress.time_spent_seconds == 150
