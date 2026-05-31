"""Integration tests para CRUD admin de /admin/resources."""
from types import SimpleNamespace

import pytest

from tests.integration.conftest import result_scalars_all, result_scalar_one_or_none


def _res(id_=1):
    return SimpleNamespace(
        id=id_, module_id=1, topic_id=None, kind="video",
        title="X", url="https://youtu.be/x", author=None,
        description=None, order_index=0, is_active=True,
    )


@pytest.mark.asyncio
async def test_admin_list_resources(admin_client, mock_db):
    mock_db.execute.side_effect = [result_scalars_all([_res()])]
    r = await admin_client.get("/api/v1/admin/resources")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_admin_create_resource(admin_client, mock_db):
    async def _fake_refresh(obj):
        obj.id = 1
    mock_db.refresh.side_effect = _fake_refresh
    r = await admin_client.post("/api/v1/admin/resources", json={
        "module_id": 1, "kind": "video", "title": "Nuevo",
        "url": "https://youtu.be/new",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Nuevo"
    assert body["kind"] == "video"


@pytest.mark.asyncio
async def test_admin_create_resource_requires_admin(client):
    r = await client.post("/api/v1/admin/resources", json={
        "kind": "video", "title": "x", "url": "https://y",
    })
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_delete_resource_404(admin_client, mock_db):
    mock_db.execute.side_effect = [result_scalar_one_or_none(None)]
    r = await admin_client.delete("/api/v1/admin/resources/999")
    assert r.status_code == 404
