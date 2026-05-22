"""Integration tests para /api/v1/admin.

Cubre el guardian require_admin + happy path de cada grupo (assessment-bank,
user-levels, modules/topics/quiz-questions/coding-challenges CRUD, docs,
users CRUD, AI challenge generator).
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.integration.conftest import (
    result_scalar_one_or_none,
    result_scalars_all,
    result_rows,
)


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_blocked_from_admin(client):
    r = await client.get("/api/v1/admin/modules")
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Assessment bank CRUD
# ---------------------------------------------------------------------------

def _bank_item(id_=1, module_id=1, difficulty="easy"):
    return SimpleNamespace(
        id=id_,
        module_id=module_id,
        question_text="x",
        options=["a", "b", "c", "d"],
        correct_index=0,
        difficulty=difficulty,
        created_by=uuid.uuid4(),
        is_active=True,
    )


@pytest.mark.asyncio
async def test_admin_list_bank_empty(admin_client, mock_db):
    mock_db.execute.return_value = result_scalars_all([])
    r = await admin_client.get("/api/v1/admin/assessment-bank")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_admin_create_bank_item(admin_client, mock_db):
    def _attach(s):
        s.id = 42
        s.created_at = datetime.now(timezone.utc)
        s.is_active = True
    mock_db.add.side_effect = _attach
    r = await admin_client.post(
        "/api/v1/admin/assessment-bank",
        json={
            "module_id": 1,
            "question_text": "Pregunta válida con suficiente longitud?",
            "options": ["a", "b", "c", "d"],
            "correct_index": 0,
            "difficulty": "easy",
        },
    )
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_admin_update_bank_item_404(admin_client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await admin_client.put(
        "/api/v1/admin/assessment-bank/999", json={"difficulty": "hard"}
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_bank_item_validates_4_options(admin_client, mock_db):
    item = _bank_item()
    mock_db.execute.return_value = result_scalar_one_or_none(item)
    r = await admin_client.put(
        "/api/v1/admin/assessment-bank/1", json={"options": ["a", "b"]}
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_admin_delete_bank_item(admin_client, mock_db):
    item = _bank_item()
    mock_db.execute.return_value = result_scalar_one_or_none(item)
    r = await admin_client.delete("/api/v1/admin/assessment-bank/1")
    assert r.status_code == 204
    mock_db.delete.assert_awaited_once_with(item)


# ---------------------------------------------------------------------------
# User levels
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_list_user_levels(admin_client, mock_db):
    now = datetime.now(timezone.utc)
    user = SimpleNamespace(
        id=uuid.uuid4(), email="s@x.pe", full_name="Stu",
    )
    lvl = SimpleNamespace(
        level="beginner", entry_score=30.0, assessed_at=now, last_reassessed_at=None
    )
    mock_db.execute.return_value = result_rows([(user, lvl)])
    r = await admin_client.get("/api/v1/admin/user-levels")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["level"] == "beginner"


@pytest.mark.asyncio
async def test_admin_override_user_level_404(admin_client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await admin_client.put(
        f"/api/v1/admin/user-levels/{uuid.uuid4()}",
        json={"level": "advanced", "reason": "fast learner"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_override_user_level_succeeds(admin_client, mock_db):
    now = datetime.now(timezone.utc)
    target = SimpleNamespace(id=uuid.uuid4())
    existing_lvl = SimpleNamespace(entry_score=42.0)
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(target),
        result_scalar_one_or_none(existing_lvl),
    ]
    new_lvl = SimpleNamespace(
        level="advanced", entry_score=42.0, assessed_at=now,
        last_reassessed_at=now, history=[],
    )
    with patch(
        "app.routers.admin.upsert_user_level", new=AsyncMock(return_value=new_lvl)
    ):
        r = await admin_client.put(
            f"/api/v1/admin/user-levels/{target.id}",
            json={"level": "advanced", "reason": "consistency"},
        )
    assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# Modules / Topics / Quiz-Questions / Coding-Challenges CRUD smoke
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_modules_list_empty(admin_client, mock_db):
    mock_db.execute.return_value = result_scalars_all([])
    r = await admin_client.get("/api/v1/admin/modules")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_admin_module_update_404(admin_client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await admin_client.put(
        "/api/v1/admin/modules/999", json={"title": "Otro"}
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_topic_delete_404(admin_client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await admin_client.delete("/api/v1/admin/topics/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_quiz_question_update_validates_options(admin_client, mock_db):
    q = SimpleNamespace(
        id=1, topic_id=1, question_text="x",
        options=["a", "b", "c", "d"], correct_option_index=0,
        explanation=None, order_index=0,
    )
    mock_db.execute.return_value = result_scalar_one_or_none(q)
    # Update schema accepts any list; router rejects len != 4 with 400.
    r = await admin_client.put(
        "/api/v1/admin/quiz-questions/1",
        json={"options": ["only", "two"]},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_admin_coding_challenge_delete(admin_client, mock_db):
    ch = SimpleNamespace(id=1)
    mock_db.execute.return_value = result_scalar_one_or_none(ch)
    r = await admin_client.delete("/api/v1/admin/coding-challenges/1")
    assert r.status_code == 204


# ---------------------------------------------------------------------------
# AI challenge generator
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_generate_challenge_404_topic(admin_client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await admin_client.post(
        "/api/v1/admin/coding-challenges/generate",
        json={"topic_id": 999, "difficulty": "easy", "target_level": "beginner"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_generate_challenge_400_short_topic(admin_client, mock_db):
    topic = SimpleNamespace(id=1, content="too short")
    mock_db.execute.return_value = result_scalar_one_or_none(topic)
    r = await admin_client.post(
        "/api/v1/admin/coding-challenges/generate",
        json={"topic_id": 1, "difficulty": "easy", "target_level": "beginner"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_admin_generate_challenge_success(admin_client, mock_db):
    topic = SimpleNamespace(id=1, content="x" * 500)
    mock_db.execute.return_value = result_scalar_one_or_none(topic)
    generated = SimpleNamespace(
        title="Reto", description="desc",
        hints="pista", solution_code="fun x(){}",
        difficulty="medium", language="kotlin",
    )
    with patch(
        "app.routers.admin.generate_challenge", new=AsyncMock(return_value=generated)
    ):
        r = await admin_client.post(
            "/api/v1/admin/coding-challenges/generate",
            json={"topic_id": 1, "difficulty": "medium", "target_level": "intermediate"},
        )
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_admin_generate_challenge_503_on_failure(admin_client, mock_db):
    from app.services.challenge_generator_service import ChallengeGenerationError
    topic = SimpleNamespace(id=1, content="x" * 500)
    mock_db.execute.return_value = result_scalar_one_or_none(topic)
    with patch(
        "app.routers.admin.generate_challenge",
        new=AsyncMock(side_effect=ChallengeGenerationError("down")),
    ):
        r = await admin_client.post(
            "/api/v1/admin/coding-challenges/generate",
            json={"topic_id": 1, "difficulty": "medium", "target_level": "intermediate"},
        )
    assert r.status_code == 503


# ---------------------------------------------------------------------------
# Documents (RAG corpus)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_list_documents_empty(admin_client, mock_db):
    mock_db.execute.return_value = result_scalars_all([])
    r = await admin_client.get("/api/v1/admin/documents")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_admin_upload_rejects_bad_mime(admin_client):
    r = await admin_client.post(
        "/api/v1/admin/documents",
        files={"file": ("malo.exe", b"abc", "application/x-msdownload")},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_admin_reprocess_404_when_missing(admin_client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await admin_client.post(
        f"/api/v1/admin/documents/{uuid.uuid4()}/reprocess"
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_document_404(admin_client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await admin_client.delete(f"/api/v1/admin/documents/{uuid.uuid4()}")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Users CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_list_users(admin_client, mock_db):
    now = datetime.now(timezone.utc)
    user = SimpleNamespace(
        id=uuid.uuid4(), email="s@x.pe", full_name="Stu",
        role="student", is_active=True, created_at=now,
    )
    lvl = SimpleNamespace(level="beginner")
    mock_db.execute.return_value = result_rows([(user, lvl)])
    r = await admin_client.get("/api/v1/admin/users")
    assert r.status_code == 200
    body = r.json()
    assert body[0]["level"] == "beginner"


@pytest.mark.asyncio
async def test_admin_update_user_404(admin_client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await admin_client.put(
        f"/api/v1/admin/users/{uuid.uuid4()}", json={"is_active": False}
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_cannot_deactivate_self(admin_client, fake_admin):
    r = await admin_client.put(
        f"/api/v1/admin/users/{fake_admin.id}",
        json={"is_active": False},
    )
    assert r.status_code == 400
