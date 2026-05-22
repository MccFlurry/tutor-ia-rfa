"""Integration tests para /api/v1/chat."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.integration.conftest import (
    result_scalar,
    result_scalar_one_or_none,
    result_scalars_all,
)


def _session(user_id, title="Conversación"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        title=title,
        created_at=datetime.now(timezone.utc),
        last_message_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_list_sessions_empty(client, mock_db):
    mock_db.execute.return_value = result_scalars_all([])
    r = await client.get("/api/v1/chat/sessions")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_session_smoke(client, mock_db):
    # Router does db.add + refresh — emulate refresh to populate timestamps
    def _refresh(s):
        s.created_at = datetime.now(timezone.utc)
        s.last_message_at = datetime.now(timezone.utc)

    mock_db.refresh.side_effect = _refresh
    r = await client.post("/api/v1/chat/sessions")
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Nueva conversación"


@pytest.mark.asyncio
async def test_delete_session_404_when_missing(client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await client.delete(f"/api/v1/chat/sessions/{uuid.uuid4()}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_succeeds(client, mock_db, fake_user):
    s = _session(fake_user.id)
    mock_db.execute.return_value = result_scalar_one_or_none(s)
    r = await client.delete(f"/api/v1/chat/sessions/{s.id}")
    assert r.status_code == 200
    mock_db.delete.assert_awaited_once_with(s)


@pytest.mark.asyncio
async def test_get_messages_404_when_no_session(client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await client.get(f"/api/v1/chat/sessions/{uuid.uuid4()}/messages")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_messages_returns_list(client, mock_db, fake_user):
    s = _session(fake_user.id)
    msg = SimpleNamespace(
        id=uuid.uuid4(),
        role="user",
        content="hola",
        sources=None,
        created_at=datetime.now(timezone.utc),
    )
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(s),
        result_scalars_all([msg]),
    ]
    r = await client.get(f"/api/v1/chat/sessions/{s.id}/messages")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_send_message_runs_rag_pipeline(client, mock_db, fake_user, mock_redis_pipe):
    s = _session(fake_user.id)
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(s),     # session
        result_scalars_all([]),           # history
        result_scalar(1),                 # user msg count → set title
    ]
    rag_payload = {"content": "respuesta", "sources": []}
    with patch("app.routers.chat.query_rag",
               new=AsyncMock(return_value=rag_payload)), \
         patch("app.routers.chat.check_and_grant_achievements",
               new=AsyncMock(return_value=[])):
        r = await client.post(
            f"/api/v1/chat/sessions/{s.id}/message",
            json={"content": "¿Qué es Kotlin?"},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "assistant"
    assert body["content"] == "respuesta"


@pytest.mark.asyncio
async def test_send_message_falls_back_when_rag_throws(client, mock_db, fake_user):
    s = _session(fake_user.id)
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(s),
        result_scalars_all([]),
        result_scalar(2),  # not first msg
    ]
    with patch("app.routers.chat.query_rag",
               new=AsyncMock(side_effect=RuntimeError("rag down"))), \
         patch("app.routers.chat.check_and_grant_achievements",
               new=AsyncMock(return_value=[])):
        r = await client.post(
            f"/api/v1/chat/sessions/{s.id}/message",
            json={"content": "hola"},
        )
    assert r.status_code == 200
    assert "no está disponible" in r.json()["content"]


@pytest.mark.asyncio
async def test_send_message_rate_limited(client, mock_db, fake_user, mock_redis_pipe):
    s = _session(fake_user.id)
    mock_db.execute.return_value = result_scalar_one_or_none(s)
    # Force rate limit cap
    from app.config import settings
    mock_redis_pipe.get = AsyncMock(return_value=str(settings.CHAT_RATE_LIMIT_PER_HOUR))
    r = await client.post(
        f"/api/v1/chat/sessions/{s.id}/message", json={"content": "hi"}
    )
    assert r.status_code == 429


@pytest.mark.asyncio
async def test_remaining_endpoint(client, mock_redis_pipe):
    mock_redis_pipe.get = AsyncMock(return_value="3")
    r = await client.get("/api/v1/chat/remaining")
    assert r.status_code == 200
    body = r.json()
    from app.config import settings
    assert body["limit"] == settings.CHAT_RATE_LIMIT_PER_HOUR
    assert body["remaining"] == settings.CHAT_RATE_LIMIT_PER_HOUR - 3
