"""Integration tests para /api/v1/progress."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_progress_smoke(client):
    payload = {
        "overall_pct": 25.0,
        "total_time_seconds": 600,
        "topics_completed": 5,
        "quiz_avg_score": 80.0,
        "modules": [
            {"id": 1, "title": "M1", "pct": 50.0, "completed": 2, "total": 4}
        ],
    }
    with patch(
        "app.routers.progress.get_user_progress",
        new=AsyncMock(return_value=payload),
    ):
        r = await client.get("/api/v1/progress")
    assert r.status_code == 200
    assert r.json()["overall_pct"] == 25.0


@pytest.mark.asyncio
async def test_get_activity(client):
    activities = [
        {"type": "topic_completed", "description": "x", "timestamp": "2026-05-01T00:00:00+00:00"},
    ]
    with patch(
        "app.routers.progress.get_activity_log",
        new=AsyncMock(return_value=activities),
    ):
        r = await client.get("/api/v1/progress/activity")
    assert r.status_code == 200
    assert r.json() == activities


@pytest.mark.asyncio
async def test_get_streak(client):
    streak = {"current_streak": 3, "longest_streak": 5, "last_active_date": "2026-05-21"}
    with patch(
        "app.routers.progress.compute_streak",
        new=AsyncMock(return_value=streak),
    ):
        r = await client.get("/api/v1/progress/streak")
    assert r.status_code == 200
    assert r.json()["current_streak"] == 3
