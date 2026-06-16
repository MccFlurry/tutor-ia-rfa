"""Integration tests para /api/v1/resources (estudiante)."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from tests.integration.conftest import result_scalars_all


def _res(id_=1, kind="video"):
    return SimpleNamespace(
        id=id_, module_id=1, topic_id=None, kind=kind,
        title="Kotlin Basics", url="https://youtu.be/abc", author="Google",
        description=None, order_index=0, is_active=True,
    )


@pytest.mark.asyncio
async def test_list_resources_by_module(client, mock_db):
    mock_db.execute.side_effect = [result_scalars_all([_res()])]
    r = await client.get("/api/v1/resources?module_id=1")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["kind"] == "video"
    assert body[0]["url"] == "https://youtu.be/abc"


@pytest.mark.asyncio
async def test_list_resources_empty(client, mock_db):
    mock_db.execute.side_effect = [result_scalars_all([])]
    r = await client.get("/api/v1/resources?topic_id=5")
    assert r.status_code == 200
    assert r.json() == []


from app.schemas.learning_resource import RecommendationResponse, RecommendedResource


def _rec(reason):
    return RecommendedResource(
        id=1, module_id=1, topic_id=None, kind="video", title="R1",
        url="http://x/1", author=None, description=None, order_index=0,
        is_active=True, reason=reason,
    )


@pytest.mark.asyncio
async def test_recommended_ai_ranked(client):
    payload = RecommendationResponse(
        ai_ranked=True, level="beginner", recommendations=[_rec("empieza aquí")],
    )
    with patch("app.routers.resources.gather_recommendations",
               new=AsyncMock(return_value=payload)):
        r = await client.get("/api/v1/resources/recommended?module_id=1")
    assert r.status_code == 200
    body = r.json()
    assert body["ai_ranked"] is True
    assert body["recommendations"][0]["reason"] == "empieza aquí"


@pytest.mark.asyncio
async def test_recommended_fallback(client):
    payload = RecommendationResponse(
        ai_ranked=False, level="beginner", recommendations=[_rec(None)],
    )
    with patch("app.routers.resources.gather_recommendations",
               new=AsyncMock(return_value=payload)):
        r = await client.get("/api/v1/resources/recommended?topic_id=9")
    assert r.status_code == 200
    assert r.json()["ai_ranked"] is False


@pytest.mark.asyncio
async def test_recommended_requires_exactly_one_param(client):
    none = await client.get("/api/v1/resources/recommended")
    both = await client.get("/api/v1/resources/recommended?module_id=1&topic_id=2")
    assert none.status_code == 422
    assert both.status_code == 422


@pytest.mark.asyncio
async def test_recommended_served_from_cache(client, mock_redis_pipe):
    import json as _json
    mock_redis_pipe.get = AsyncMock(
        return_value=_json.dumps({"ai_ranked": True, "level": "beginner", "recommendations": []})
    )
    with patch("app.routers.resources.gather_recommendations", new=AsyncMock()) as svc:
        r = await client.get("/api/v1/resources/recommended?module_id=1")
    svc.assert_not_called()
    assert r.json()["ai_ranked"] is True
