"""Integration tests para /api/v1/quiz."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.integration.conftest import (
    result_scalar_one_or_none,
    result_scalars_all,
)


def _topic(has_quiz=True):
    return SimpleNamespace(
        id=1, title="x", module_id=1, order_index=1,
        estimated_minutes=30, has_quiz=has_quiz, is_active=True,
        content="contenido extenso del tema sobre Kotlin " * 10,
        video_url=None,
    )


def _ai_session(submitted=False):
    s = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        topic_id=1,
        questions={
            "q0": {
                "question_text": "¿X?",
                "options": ["a", "b", "c", "d"],
                "correct_index": 0,
                "explanation": "porque a",
            }
        },
        student_level="intermediate",
        source="ai",
        is_submitted=submitted,
        submitted_at=None,
        created_at=datetime.now(timezone.utc),
    )
    return s


@pytest.mark.asyncio
async def test_get_quiz_topic_404(client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await client.get("/api/v1/quiz/topic/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_quiz_returns_no_quiz_topic(client, mock_db):
    t = _topic(has_quiz=False)
    mock_db.execute.return_value = result_scalar_one_or_none(t)
    r = await client.get("/api/v1/quiz/topic/1")
    assert r.status_code == 404
    assert "autoevaluación" in r.json()["detail"]


@pytest.mark.asyncio
async def test_get_quiz_reuses_active_session(client, mock_db):
    t = _topic()
    existing = _ai_session()
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(t),         # topic lookup
        result_scalar_one_or_none(existing),  # _get_active_session
    ]
    r = await client.get("/api/v1/quiz/topic/1")
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == str(existing.id)
    assert len(body["questions"]) == 1
    # Answer key never leaks
    assert "correct_index" not in body["questions"][0]


@pytest.mark.asyncio
async def test_get_quiz_falls_back_to_catalogue_when_llm_fails(client, mock_db, fake_user):
    t = _topic()
    catalogue = [
        SimpleNamespace(
            question_text="Q1",
            options=["a", "b", "c", "d"],
            correct_option_index=0,
            explanation="exp",
        )
    ]
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(t),    # topic
        result_scalar_one_or_none(None), # no active session
        result_scalars_all(catalogue),   # catalogue rows
    ]
    from app.services.llm_service import QuizGenerationError
    with patch("app.routers.quiz.get_user_level", new=AsyncMock(return_value="beginner")), \
         patch("app.routers.quiz.generate_quiz_questions",
               new=AsyncMock(side_effect=QuizGenerationError("ollama down"))):
        r = await client.get("/api/v1/quiz/topic/1")
    assert r.status_code == 200
    assert r.json()["session_id"]
    mock_db.add.assert_called_once()


@pytest.mark.asyncio
async def test_get_quiz_503_when_no_llm_and_no_catalogue(client, mock_db):
    t = _topic()
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(t),
        result_scalar_one_or_none(None),
        result_scalars_all([]),  # empty catalogue
    ]
    from app.services.llm_service import QuizGenerationError
    with patch("app.routers.quiz.get_user_level", new=AsyncMock(return_value="beginner")), \
         patch("app.routers.quiz.generate_quiz_questions",
               new=AsyncMock(side_effect=QuizGenerationError("down"))):
        r = await client.get("/api/v1/quiz/topic/1")
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_submit_quiz_grades_correctly(client, mock_db, fake_user):
    session = _ai_session()
    session.user_id = fake_user.id

    mock_db.execute.side_effect = [
        result_scalar_one_or_none(session),  # session lookup
    ]
    # Router instantiates QuizAttempt; populate its id on add() so the
    # response schema (which requires int) validates.
    def _attach_id(s):
        if not hasattr(s, "id") or s.id is None:
            s.id = 777

    mock_db.add.side_effect = _attach_id

    with patch("app.routers.quiz.check_and_complete_topic", new=AsyncMock(return_value=True)), \
         patch("app.routers.quiz.check_reassessment", new=AsyncMock(return_value={"should_reassess": False})):
        r = await client.post(
            f"/api/v1/quiz/topic/1/submit",
            json={"session_id": str(session.id), "answers": {"q0": 0}},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["score"] == 100.0
    assert body["is_passed"] is True
    assert session.is_submitted is True


@pytest.mark.asyncio
async def test_submit_quiz_410_when_already_submitted(client, mock_db, fake_user):
    session = _ai_session(submitted=True)
    session.user_id = fake_user.id
    mock_db.execute.return_value = result_scalar_one_or_none(session)
    r = await client.post(
        f"/api/v1/quiz/topic/1/submit",
        json={"session_id": str(session.id), "answers": {"q0": 0}},
    )
    assert r.status_code == 410


@pytest.mark.asyncio
async def test_submit_quiz_bad_session_id(client, mock_db):
    r = await client.post(
        "/api/v1/quiz/topic/1/submit",
        json={"session_id": "not-a-uuid", "answers": {}},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_submit_quiz_404_unknown_session(client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await client.post(
        f"/api/v1/quiz/topic/1/submit",
        json={"session_id": str(uuid.uuid4()), "answers": {}},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_quiz_history(client, mock_db):
    attempts = [
        SimpleNamespace(
            attempted_at=datetime.now(timezone.utc),
            score=0.8,
            is_passed=True,
        )
    ]
    mock_db.execute.return_value = result_scalars_all(attempts)
    r = await client.get("/api/v1/quiz/topic/1/history")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["score"] == 80.0
