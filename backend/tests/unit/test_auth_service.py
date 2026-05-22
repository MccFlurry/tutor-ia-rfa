"""
Unit tests para app/services/auth_service.py.
Mockea la AsyncSession y verifica:
- register_user rechaza emails duplicados con 409.
- login_user rechaza credenciales malas con 401 y cuenta inactiva con 403.
- refresh_access_token rechaza tokens inválidos y devuelve nuevo access token.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.schemas.auth import LoginRequest, RegisterRequest
from app.services import auth_service
from app.utils.security import (
    create_refresh_token,
    create_access_token,
    decode_access_token,
    hash_password,
)


def _mock_db(scalar_value):
    """Async DB whose execute().scalar_one_or_none() yields `scalar_value`."""
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=scalar_value)
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_creates_user_when_email_free(self):
        db = _mock_db(None)
        data = RegisterRequest(
            email="new@iestprfa.edu.pe",
            full_name="Nuevo Estudiante",
            password="Secret123",
        )
        out = await auth_service.register_user(data, db)
        assert "access_token" in out
        assert "refresh_token" in out
        assert out["user"].email == "new@iestprfa.edu.pe"
        # Access token debe decodificarse y contener el sub del nuevo user
        payload = decode_access_token(out["access_token"])
        assert payload is not None
        assert payload["sub"] == str(out["user"].id)
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rejects_duplicate_email(self):
        existing = SimpleNamespace(id=uuid.uuid4(), email="dup@x.pe")
        db = _mock_db(existing)
        data = RegisterRequest(
            email="dup@x.pe", full_name="Dup", password="Secret123"
        )
        with pytest.raises(HTTPException) as exc:
            await auth_service.register_user(data, db)
        assert exc.value.status_code == 409


class TestLoginUser:
    @pytest.mark.asyncio
    async def test_successful_login(self):
        user = SimpleNamespace(
            id=uuid.uuid4(),
            email="ok@x.pe",
            hashed_password=hash_password("Secret123"),
            is_active=True,
        )
        db = _mock_db(user)
        out = await auth_service.login_user(
            LoginRequest(email="ok@x.pe", password="Secret123"), db
        )
        assert out["user"] is user
        assert decode_access_token(out["access_token"])["sub"] == str(user.id)

    @pytest.mark.asyncio
    async def test_wrong_password_rejected(self):
        user = SimpleNamespace(
            id=uuid.uuid4(),
            email="ok@x.pe",
            hashed_password=hash_password("Secret123"),
            is_active=True,
        )
        db = _mock_db(user)
        with pytest.raises(HTTPException) as exc:
            await auth_service.login_user(
                LoginRequest(email="ok@x.pe", password="WRONG"), db
            )
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_unknown_email_rejected(self):
        db = _mock_db(None)
        with pytest.raises(HTTPException) as exc:
            await auth_service.login_user(
                LoginRequest(email="ghost@x.pe", password="anything"), db
            )
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_blocked(self):
        user = SimpleNamespace(
            id=uuid.uuid4(),
            email="dead@x.pe",
            hashed_password=hash_password("Secret123"),
            is_active=False,
        )
        db = _mock_db(user)
        with pytest.raises(HTTPException) as exc:
            await auth_service.login_user(
                LoginRequest(email="dead@x.pe", password="Secret123"), db
            )
        assert exc.value.status_code == 403


class TestRefreshAccessToken:
    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self):
        db = _mock_db(None)
        with pytest.raises(HTTPException) as exc:
            await auth_service.refresh_access_token("garbage", db)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_access_token_rejected_as_refresh(self):
        db = _mock_db(None)
        bad = create_access_token({"sub": "u"})
        with pytest.raises(HTTPException) as exc:
            await auth_service.refresh_access_token(bad, db)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_refresh_yields_new_access_token(self):
        uid = uuid.uuid4()
        user = SimpleNamespace(id=uid, is_active=True)
        db = _mock_db(user)
        refresh = create_refresh_token({"sub": str(uid)})
        access = await auth_service.refresh_access_token(refresh, db)
        payload = decode_access_token(access)
        assert payload["sub"] == str(uid)

    @pytest.mark.asyncio
    async def test_inactive_user_blocked(self):
        uid = uuid.uuid4()
        user = SimpleNamespace(id=uid, is_active=False)
        db = _mock_db(user)
        refresh = create_refresh_token({"sub": str(uid)})
        with pytest.raises(HTTPException) as exc:
            await auth_service.refresh_access_token(refresh, db)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_user_blocked(self):
        db = _mock_db(None)
        refresh = create_refresh_token({"sub": str(uuid.uuid4())})
        with pytest.raises(HTTPException) as exc:
            await auth_service.refresh_access_token(refresh, db)
        assert exc.value.status_code == 401
