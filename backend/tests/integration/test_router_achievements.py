"""Integration tests para /api/v1/achievements."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from tests.integration.conftest import result_scalars_all


def _ach(id_=1, name="First Topic"):
    return SimpleNamespace(
        id=id_,
        name=name,
        description="desc",
        badge_emoji="🏆",
        badge_color="#fbbf24",
        condition_type="first_topic",
        condition_value=1,
        condition_module_id=None,
    )


@pytest.mark.asyncio
async def test_list_achievements_empty(client, mock_db):
    mock_db.execute.side_effect = [
        result_scalars_all([]),
        result_scalars_all([]),
    ]
    r = await client.get("/api/v1/achievements")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_achievements_marks_earned(client, fake_user, mock_db):
    a = _ach(1)
    earned = SimpleNamespace(
        achievement_id=1,
        earned_at=datetime.now(timezone.utc),
    )
    mock_db.execute.side_effect = [
        result_scalars_all([a]),
        result_scalars_all([earned]),
    ]
    r = await client.get("/api/v1/achievements")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["is_earned"] is True
    assert body[0]["earned_at"] is not None
