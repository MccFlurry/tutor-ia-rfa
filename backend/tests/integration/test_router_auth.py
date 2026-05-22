"""Integration tests para /api/v1/auth.

Cubre register/login/refresh/logout asegurando que el wiring del router al
servicio funcione + códigos HTTP correctos. La lógica de servicio ya está
cubierta en tests/unit/test_auth_service.py.
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.integration.conftest import result_scalar_one_or_none
from app.utils.security import create_refresh_token, hash_password


@pytest.mark.asyncio
async def test_register_succeeds(anon_client, mock_db):
    # email lookup returns None (no duplicate). Patch flush() so SQLAlchemy
    # column defaults (id, role, is_active, created_at) get populated since
    # we don't have a real DB.
    mock_db.execute.return_value = result_scalar_one_or_none(None)

    added: list = []
    mock_db.add.side_effect = lambda u: added.append(u)

    async def fake_flush():
        u = added[-1]
        if u.id is None:
            u.id = uuid.uuid4()
        if not getattr(u, "role", None):
            u.role = "student"
        if u.is_active is None:
            u.is_active = True
        if u.created_at is None:
            u.created_at = datetime.now(timezone.utc)

    mock_db.flush.side_effect = fake_flush

    r = await anon_client.post(
        "/api/v1/auth/register",
        json={
            "email": "nuevo@iestprfa.edu.pe",
            "full_name": "Nuevo Estudiante",
            "password": "Secret123",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["user"]["email"] == "nuevo@iestprfa.edu.pe"
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_register_rejects_duplicate(anon_client, mock_db):
    existing = SimpleNamespace(id=uuid.uuid4(), email="dup@x.pe")
    mock_db.execute.return_value = result_scalar_one_or_none(existing)

    r = await anon_client.post(
        "/api/v1/auth/register",
        json={"email": "dup@x.pe", "full_name": "Dup", "password": "Secret123"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_validates_short_password(anon_client):
    r = await anon_client.post(
        "/api/v1/auth/register",
        json={"email": "x@x.pe", "full_name": "x", "password": "12"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_succeeds(anon_client, mock_db):
    now = datetime.now(timezone.utc)
    user = SimpleNamespace(
        id=uuid.uuid4(),
        email="ok@x.pe",
        full_name="OK",
        hashed_password=hash_password("Secret123"),
        is_active=True,
        avatar_url=None,
        role="student",
        created_at=now,
        updated_at=now,
    )
    mock_db.execute.return_value = result_scalar_one_or_none(user)

    r = await anon_client.post(
        "/api/v1/auth/login",
        json={"email": "ok@x.pe", "password": "Secret123"},
    )
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_login_wrong_password(anon_client, mock_db):
    user = SimpleNamespace(
        id=uuid.uuid4(),
        email="ok@x.pe",
        hashed_password=hash_password("Secret123"),
        is_active=True,
    )
    mock_db.execute.return_value = result_scalar_one_or_none(user)

    r = await anon_client.post(
        "/api/v1/auth/login",
        json={"email": "ok@x.pe", "password": "WRONG"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_valid_token(anon_client, mock_db):
    uid = uuid.uuid4()
    user = SimpleNamespace(id=uid, is_active=True)
    mock_db.execute.return_value = result_scalar_one_or_none(user)

    refresh = create_refresh_token({"sub": str(uid)})
    r = await anon_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_refresh_garbage_rejected(anon_client, mock_db):
    r = await anon_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "garbage"}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_logout_always_ok(anon_client):
    # Logout is stateless on the server (refresh token rotation handled separately)
    r = await anon_client.post(
        "/api/v1/auth/logout", json={"refresh_token": "anything"}
    )
    assert r.status_code == 200
    assert "message" in r.json()
