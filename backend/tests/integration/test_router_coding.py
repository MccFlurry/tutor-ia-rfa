"""Integration tests para /api/v1/coding."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.integration.conftest import (
    result_scalar,
    result_scalar_one_or_none,
    result_scalars_all,
)


def _challenge(id_=1, title="Reto Kotlin", language="kotlin"):
    return SimpleNamespace(
        id=id_,
        topic_id=1,
        title=title,
        description="Implementa X",
        initial_code="fun main() {}",
        solution_code="fun main() { println(0) }",
        language=language,
        difficulty="easy",
        hints="Considera Y",
        order_index=1,
        is_ai_generated=True,
        student_level="intermediate",
    )


def _topic(content="contenido"):
    return SimpleNamespace(
        id=1, title="T", module_id=1, order_index=1,
        estimated_minutes=30, has_quiz=True, is_active=True,
        content=content, video_url=None,
    )


@pytest.mark.asyncio
async def test_get_topic_404(client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await client.get("/api/v1/coding/topic/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_topic_returns_or_generates(client, mock_db):
    t = _topic()
    ch = _challenge()
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(t),  # topic
        result_scalar(1),              # has_fallback
    ]
    with patch("app.routers.coding.get_user_level", new=AsyncMock(return_value="intermediate")), \
         patch("app.routers.coding.get_or_generate_for_student",
               new=AsyncMock(return_value=ch)):
        r = await client.get("/api/v1/coding/topic/1")
    assert r.status_code == 200
    body = r.json()
    assert body["challenge"]["id"] == 1
    assert body["student_level"] == "intermediate"


@pytest.mark.asyncio
async def test_get_topic_503_when_generator_runtime_error(client, mock_db):
    t = _topic()
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(t),
        result_scalar(1),
    ]
    with patch("app.routers.coding.get_user_level", new=AsyncMock(return_value="intermediate")), \
         patch("app.routers.coding.get_or_generate_for_student",
               new=AsyncMock(side_effect=RuntimeError("ollama down"))):
        r = await client.get("/api/v1/coding/topic/1")
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_get_topic_404_when_no_content_no_fallback(client, mock_db):
    t = _topic(content=None)
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(t),
        result_scalar(0),  # no fallback
    ]
    r = await client.get("/api/v1/coding/topic/1")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_regenerate_smoke(client, mock_db):
    t = _topic()
    ch = _challenge(id_=99, title="Nuevo reto")
    mock_db.execute.return_value = result_scalar_one_or_none(t)
    with patch("app.routers.coding.get_user_level", new=AsyncMock(return_value="advanced")), \
         patch("app.routers.coding.regenerate_for_student", new=AsyncMock(return_value=ch)):
        r = await client.post("/api/v1/coding/topic/1/regenerate")
    assert r.status_code == 200
    assert r.json()["challenge"]["id"] == 99


@pytest.mark.asyncio
async def test_get_challenge_by_id(client, mock_db):
    ch = _challenge()
    mock_db.execute.return_value = result_scalar_one_or_none(ch)
    r = await client.get("/api/v1/coding/challenge/1")
    assert r.status_code == 200
    assert r.json()["id"] == 1


@pytest.mark.asyncio
async def test_submit_code_grades_and_caches(client, mock_db):
    ch = _challenge()
    mock_db.execute.return_value = result_scalar_one_or_none(ch)
    evaluation = {
        "score": 82.5,
        "feedback": "Bien",
        "strengths": ["claridad"],
        "improvements": ["edge cases"],
    }

    # The router builds a CodingSubmission and reads .id after flush.
    # We patch flush to populate the id.
    def _set_id(s):
        s.id = 123

    mock_db.add.side_effect = _set_id

    with patch("app.routers.coding.get_user_level", new=AsyncMock(return_value="intermediate")), \
         patch("app.routers.coding.evaluate_code", new=AsyncMock(return_value=evaluation)), \
         patch("app.routers.coding.check_and_complete_topic",
               new=AsyncMock(return_value=True)), \
         patch("app.routers.coding.auto_apply_reassessment",
               new=AsyncMock(return_value=None)):
        r = await client.post(
            "/api/v1/coding/challenge/1/submit",
            json={"code": "fun main() { println(\"ok\") }"},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["score"] == 82.5
    assert body["feedback"] == "Bien"
    assert body["level_change"] is None


@pytest.mark.asyncio
async def test_submit_code_returns_level_change(client, mock_db):
    """Coding submit propagates level_change payload when auto-apply fires."""
    ch = _challenge()
    mock_db.execute.return_value = result_scalar_one_or_none(ch)
    evaluation = {
        "score": 92.0,
        "feedback": "Excelente",
        "strengths": [],
        "improvements": [],
    }
    change = {
        "direction": "up",
        "previous_level": "intermediate",
        "new_level": "advanced",
        "reason": "3 quizzes consecutivos ≥90%",
    }

    def _set_id(s):
        s.id = 124
    mock_db.add.side_effect = _set_id

    with patch("app.routers.coding.get_user_level", new=AsyncMock(return_value="intermediate")), \
         patch("app.routers.coding.evaluate_code", new=AsyncMock(return_value=evaluation)), \
         patch("app.routers.coding.check_and_complete_topic", new=AsyncMock(return_value=True)), \
         patch("app.routers.coding.auto_apply_reassessment", new=AsyncMock(return_value=change)):
        r = await client.post(
            "/api/v1/coding/challenge/1/submit",
            json={"code": "fun main() {}"},
        )
    assert r.status_code == 200, r.text
    assert r.json()["level_change"] == change


@pytest.mark.asyncio
async def test_submit_code_503_on_llm_failure(client, mock_db):
    ch = _challenge()
    mock_db.execute.return_value = result_scalar_one_or_none(ch)
    with patch("app.routers.coding.get_user_level", new=AsyncMock(return_value="beginner")), \
         patch("app.routers.coding.evaluate_code", new=AsyncMock(side_effect=RuntimeError("boom"))):
        r = await client.post(
            "/api/v1/coding/challenge/1/submit",
            json={"code": "fun x(){}"},
        )
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_completion_status_endpoint(client):
    with patch("app.routers.coding.get_topic_completion_status",
               new=AsyncMock(return_value={
                   "quiz_required": True, "quiz_passed": False,
                   "coding_required": True, "coding_passed": False,
               })):
        r = await client.get("/api/v1/coding/topic/1/completion-status")
    assert r.status_code == 200
    assert r.json()["quiz_required"] is True


@pytest.mark.asyncio
async def test_get_best_returns_null_when_no_submissions(client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await client.get("/api/v1/coding/challenge/1/best")
    assert r.status_code == 200
    assert r.json() is None
