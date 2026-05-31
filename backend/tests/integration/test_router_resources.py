"""Integration tests para /api/v1/resources (estudiante)."""
from types import SimpleNamespace

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
