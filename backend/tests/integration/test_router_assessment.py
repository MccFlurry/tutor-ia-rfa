"""Integration tests para /api/v1/assessment."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.integration.conftest import (
    result_scalar_one_or_none,
    result_scalars_all,
)


def _gen_q(idx=0, module_id=1, difficulty="medium"):
    return SimpleNamespace(
        question_text=f"Pregunta {idx}",
        options=["a", "b", "c", "d"],
        correct_index=0,
        module_id=module_id,
        difficulty=difficulty,
    )


@pytest.mark.asyncio
async def test_start_assessment_503_when_generator_fails(client, mock_db):
    from app.services.entry_assessment_service import AssessmentGenerationError
    with patch("app.routers.assessment.generate_assessment",
               new=AsyncMock(side_effect=AssessmentGenerationError("ollama down"))):
        r = await client.post("/api/v1/assessment/start")
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_start_assessment_persists_and_returns(client, mock_db):
    questions = [_gen_q(0), _gen_q(1, module_id=2, difficulty="hard")]
    # Router instantiates EntryAssessmentSession; we capture and emulate flush()
    def _attach_id(s):
        s.id = uuid.uuid4()
    mock_db.add.side_effect = _attach_id

    with patch("app.routers.assessment.generate_assessment",
               new=AsyncMock(return_value=(questions, "ai"))):
        r = await client.post("/api/v1/assessment/start")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source"] == "ai"
    assert len(body["questions"]) == 2
    # No correct_index leaked
    assert "correct_index" not in body["questions"][0]


@pytest.mark.asyncio
async def test_submit_assessment_404_when_no_session(client, mock_db):
    mock_db.execute.return_value = result_scalar_one_or_none(None)
    r = await client.post(
        "/api/v1/assessment/submit",
        json={"session_id": str(uuid.uuid4()), "answers": {}},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_submit_assessment_409_when_already_graded(client, mock_db, fake_user):
    session = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=fake_user.id,
        questions=[],
        answers=None,
        score=75.0,  # already graded
        computed_level="intermediate",
    )
    mock_db.execute.return_value = result_scalar_one_or_none(session)
    r = await client.post(
        "/api/v1/assessment/submit",
        json={"session_id": str(session.id), "answers": {}},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_submit_assessment_happy_path(client, mock_db, fake_user):
    qid = "q0"
    session = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=fake_user.id,
        questions=[{
            "id": qid,
            "question_text": "x",
            "options": ["a", "b"],
            "correct_index": 0,
            "module_id": 1,
            "difficulty": "easy",
        }],
        answers=None,
        score=None,
        computed_level=None,
    )
    m1 = SimpleNamespace(id=1, title="M1")
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(session),  # session lookup
        result_scalars_all([m1]),            # module titles for breakdown
    ]
    computation = SimpleNamespace(
        level="intermediate",
        score=68.0,
        confidence=0.8,
        module_breakdown={1: {"correct": 1, "total": 1, "percentage": 100.0}},
    )
    with patch("app.routers.assessment.compute_level", return_value=computation), \
         patch("app.routers.assessment.upsert_user_level", new=AsyncMock(return_value=None)):
        r = await client.post(
            "/api/v1/assessment/submit",
            json={"session_id": str(session.id), "answers": {qid: 0}},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["level"] == "intermediate"
    assert body["score"] == 68.0
    assert body["module_breakdown"][0]["module_title"] == "M1"
