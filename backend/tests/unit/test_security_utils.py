"""
Unit tests para app/utils/security.py — JWT + bcrypt.
Validan que tokens access/refresh tengan tipo correcto y rechacen el contrario,
que verify_password sea constante respecto al hash, y que decode_* devuelva None
ante tokens corruptos.
"""

from datetime import timedelta

import pytest

from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        h = hash_password("Test1234!")
        assert h != "Test1234!"
        assert len(h) > 20

    def test_verify_correct_password(self):
        h = hash_password("Test1234!")
        assert verify_password("Test1234!", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("Test1234!")
        assert verify_password("Wrong", h) is False

    def test_hash_changes_each_call(self):
        # bcrypt incluye salt — dos hashes del mismo password difieren
        assert hash_password("same") != hash_password("same")


class TestAccessToken:
    def test_create_and_decode_round_trip(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_expired_token_returns_none(self):
        token = create_access_token({"sub": "x"}, expires_delta=timedelta(seconds=-10))
        assert decode_access_token(token) is None

    def test_garbage_token_returns_none(self):
        assert decode_access_token("not.a.valid.jwt") is None

    def test_refresh_token_rejected_by_access_decoder(self):
        refresh = create_refresh_token({"sub": "u"})
        assert decode_access_token(refresh) is None


class TestRefreshToken:
    def test_create_and_decode(self):
        token = create_refresh_token({"sub": "user-456"})
        payload = decode_refresh_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"

    def test_access_token_rejected_by_refresh_decoder(self):
        access = create_access_token({"sub": "u"})
        assert decode_refresh_token(access) is None

    def test_garbage_refresh_returns_none(self):
        assert decode_refresh_token("xxx") is None
