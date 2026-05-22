"""Integration tests para /api/v1/users."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from tests.integration.conftest import result_scalar_one_or_none
from app.utils.security import hash_password


@pytest.mark.asyncio
async def test_get_me_returns_current_user(client, fake_user):
    r = await client.get("/api/v1/users/me")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == fake_user.email
    assert body["full_name"] == fake_user.full_name


@pytest.mark.asyncio
async def test_update_me_changes_fields(client, fake_user, mock_db):
    r = await client.put("/api/v1/users/me", json={"full_name": "Nuevo Nombre"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "Nuevo Nombre"
    assert fake_user.full_name == "Nuevo Nombre"
    mock_db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_password_wrong_current(client, fake_user):
    fake_user.hashed_password = hash_password("CurrentPass1")
    r = await client.put(
        "/api/v1/users/me/password",
        json={"current_password": "WrongPass", "new_password": "NewPass1234"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_change_password_succeeds(client, fake_user, mock_db):
    fake_user.hashed_password = hash_password("CurrentPass1")
    r = await client.put(
        "/api/v1/users/me/password",
        json={"current_password": "CurrentPass1", "new_password": "NewPass1234"},
    )
    assert r.status_code == 200
    mock_db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_my_level_returns_empty_when_unassessed(client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await client.get("/api/v1/users/me/level")
    assert r.status_code == 200
    body = r.json()
    assert body["level"] is None
    assert body["history"] == []


@pytest.mark.asyncio
async def test_get_reassessment_proposal_smoke(client):
    with patch(
        "app.routers.users.check_reassessment",
        new=AsyncMock(return_value={"should_reassess": False}),
    ):
        r = await client.get("/api/v1/users/me/reassessment")
    assert r.status_code == 200
    assert r.json()["should_reassess"] is False


@pytest.mark.asyncio
async def test_accept_reassessment_409_when_no_proposal(client):
    with patch(
        "app.routers.users.check_reassessment",
        new=AsyncMock(return_value={"should_reassess": False}),
    ):
        r = await client.post(
            "/api/v1/users/me/reassess", json={"accept": True}
        )
    assert r.status_code == 409
