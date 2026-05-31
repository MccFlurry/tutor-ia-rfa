"""Integration tests para /api/v1/tutor/nudges."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from tests.integration.conftest import (
    result_scalar,
    result_scalar_one_or_none,
    result_rows,
)


@pytest.mark.asyncio
async def test_nudges_no_level(client, mock_db):
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(None),  # user level → has_level False, corta aquí
    ]
    r = await client.get("/api/v1/tutor/nudges?context=dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["nudges"][0]["id"] == "no_level"


@pytest.mark.asyncio
async def test_nudges_dashboard_zero_progress(client, mock_db):
    level = SimpleNamespace(level="beginner")

    # compute_streak se parchea para aislar los db.execute de gather_snapshot.
    # Sin el parche, compute_streak consumiría un 7.º side_effect (query de
    # last_accessed_at para fechas de racha), haciendo la lista frágil.
    fixed_streak = {"current_streak": 0, "longest_streak": 0, "last_active_date": None}

    mock_db.execute.side_effect = [
        result_scalar_one_or_none(level),  # 1. UserLevel → level="beginner"
        result_scalar(10),                  # 2. count(Topic) total activos
        result_scalar(0),                   # 3. count(UserTopicProgress) completados
        result_rows([]),                    # 4. último QuizAttempt join Topic → ninguno
        result_rows([]),                    # 5. last_accessed_at para inactividad → ninguno
        result_rows([]),                    # 6. módulos progress (group_by) → ninguno
    ]

    with patch(
        "app.services.tutor_service.compute_streak",
        new=AsyncMock(return_value=fixed_streak),
    ):
        r = await client.get("/api/v1/tutor/nudges?context=dashboard")

    assert r.status_code == 200
    ids = [n["id"] for n in r.json()["nudges"]]
    assert "welcome_start" in ids


@pytest.mark.asyncio
async def test_nudges_requires_context(client):
    r = await client.get("/api/v1/tutor/nudges")
    assert r.status_code == 422  # context es requerido
