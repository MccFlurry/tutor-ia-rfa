"""Integration tests para /api/v1/tutor/companion."""
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.companion import (
    CompanionPosition,
    CompanionResponse,
    ModuleDiagnostic,
    NextAction,
    TopicDiagnostic,
)
from tests.integration.conftest import result_scalar_one_or_none


def _payload() -> CompanionResponse:
    return CompanionResponse(
        needs_assessment=False,
        position=CompanionPosition(
            module_id=3, module_title="Interfaces de Usuario", icon_name=None,
            color_hex="#3b82f6", progress_pct=60.0, topics_done=3, topics_total=5,
            course_completed=False,
        ),
        greeting="Estás en «Interfaces de Usuario» — 60% completado.",
        diagnostic=ModuleDiagnostic(
            weak=[TopicDiagnostic(topic_id=12, title="Layouts", best_score=45.0, attempts=2)],
            practice=[],
            next_action=NextAction(
                kind="retry_quiz", label="Repasar «Layouts»", route="/topics/12"
            ),
        ),
        resources=[],
    )


@pytest.mark.asyncio
async def test_companion_returns_payload(client):
    with patch(
        "app.routers.tutor.gather_companion", new=AsyncMock(return_value=_payload())
    ):
        r = await client.get("/api/v1/tutor/companion")
    assert r.status_code == 200
    body = r.json()
    assert body["needs_assessment"] is False
    assert body["position"]["module_id"] == 3
    assert body["diagnostic"]["weak"][0]["title"] == "Layouts"
    assert body["diagnostic"]["next_action"]["route"] == "/topics/12"


@pytest.mark.asyncio
async def test_companion_needs_assessment_via_real_gather(client, mock_db):
    # Sin patch: gather_companion real corta en la 1.ª query (UserLevel → None).
    mock_db.execute.side_effect = [result_scalar_one_or_none(None)]
    r = await client.get("/api/v1/tutor/companion")
    assert r.status_code == 200
    body = r.json()
    assert body["needs_assessment"] is True
    assert body["position"] is None
    assert body["diagnostic"] is None
    assert "evaluación de entrada" in body["greeting"]


@pytest.mark.asyncio
async def test_companion_served_from_cache_skips_service(client, mock_redis_pipe):
    cached = _payload().model_dump(mode="json")
    mock_redis_pipe.get = AsyncMock(return_value=json.dumps(cached))
    with patch("app.routers.tutor.gather_companion", new=AsyncMock()) as svc:
        r = await client.get("/api/v1/tutor/companion")
    assert r.status_code == 200
    svc.assert_not_called()


@pytest.mark.asyncio
async def test_companion_requires_auth(anon_client):
    r = await anon_client.get("/api/v1/tutor/companion")
    assert r.status_code in (401, 403)  # dep real de auth sin token
