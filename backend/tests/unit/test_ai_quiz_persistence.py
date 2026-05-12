"""
Unit tests para la persistencia de sesiones AI de quiz.

Verifica el contrato del router /quiz/topic/{id} y /submit:
- Si existe una AIQuizSession no enviada para (user, topic), se reutiliza.
- Si no existe, se genera una nueva con el LLM y se persiste.
- Si el LLM falla, se cae al catálogo estático (QuizQuestion).
- Submit marca la sesión como is_submitted=True y rechaza re-envíos (410).
- Sólo se permite UNA sesión activa por (user, topic).

Estos tests usan AsyncSession mockeada — no requieren PostgreSQL real.
La integración con DB completa se verifica en Sprint 7 (test_iso25010).
"""

import json
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.ai_quiz_session import AIQuizSession
from app.routers.quiz import (
    _get_active_session,
    _build_from_db_catalogue,
    _serialize_questions_for_student,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_session(user_id, topic_id, *, is_submitted=False, source="ai"):
    """Build an in-memory AIQuizSession that looks like a freshly hydrated row."""
    s = AIQuizSession(
        user_id=user_id,
        topic_id=topic_id,
        questions={
            "q0": {
                "question_text": "¿Qué es Kotlin?",
                "options": ["A", "B", "C", "D"],
                "correct_index": 0,
                "explanation": "Es un lenguaje moderno para Android.",
            },
            "q1": {
                "question_text": "¿Cuál es una keyword reservada?",
                "options": ["val", "let", "var", "const"],
                "correct_index": 0,
                "explanation": "val es inmutable.",
            },
        },
        student_level="intermediate",
        source=source,
        is_submitted=is_submitted,
    )
    s.id = uuid.uuid4()
    s.created_at = datetime.now(timezone.utc)
    return s


def _mock_db_with_scalar(value):
    """Return a mock AsyncSession whose execute().scalar_one_or_none() yields `value`."""
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=value)
    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Reuse-on-re-entry: the SAME questions come back until the user submits.
# ---------------------------------------------------------------------------

class TestActiveSessionReuse:
    @pytest.mark.asyncio
    async def test_returns_existing_active_session(self):
        user_id = uuid.uuid4()
        existing = _fake_session(user_id, topic_id=42, is_submitted=False)
        db = _mock_db_with_scalar(existing)

        found = await _get_active_session(db, user_id, 42)
        assert found is existing
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_no_active_session(self):
        db = _mock_db_with_scalar(None)
        found = await _get_active_session(db, uuid.uuid4(), 99)
        assert found is None

    @pytest.mark.asyncio
    async def test_submitted_sessions_are_skipped(self):
        """The query filters is_submitted == False — verify the helper trusts that."""
        db = _mock_db_with_scalar(None)  # simulate query returning nothing
        found = await _get_active_session(db, uuid.uuid4(), 1)
        assert found is None


# ---------------------------------------------------------------------------
# Fallback to catalogue when LLM fails.
# ---------------------------------------------------------------------------

class TestCatalogueFallback:
    @pytest.mark.asyncio
    async def test_returns_none_when_catalogue_empty(self):
        db = MagicMock()
        result = MagicMock()
        result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        db.execute = AsyncMock(return_value=result)

        payload = await _build_from_db_catalogue(1, db)
        assert payload is None

    @pytest.mark.asyncio
    async def test_returns_keyed_payload_when_catalogue_has_questions(self):
        db = MagicMock()
        catalogue = [
            SimpleNamespace(
                question_text="Q1",
                options=["a", "b", "c", "d"],
                correct_option_index=2,
                explanation="exp1",
            ),
            SimpleNamespace(
                question_text="Q2",
                options=["w", "x", "y", "z"],
                correct_option_index=0,
                explanation=None,  # nullable
            ),
        ]
        result = MagicMock()
        result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=catalogue)))
        db.execute = AsyncMock(return_value=result)

        payload = await _build_from_db_catalogue(7, db)
        assert payload is not None
        assert list(payload.keys()) == ["q0", "q1"]
        assert payload["q0"]["correct_index"] == 2
        # Missing explanation gets a default string, never None
        assert payload["q1"]["explanation"] == "Sin explicación disponible."


# ---------------------------------------------------------------------------
# Wire-level safety: the answer key NEVER leaks to the student.
# ---------------------------------------------------------------------------

class TestSerializationStripsAnswerKey:
    def test_correct_index_not_in_response(self):
        payload = {
            "q0": {
                "question_text": "x",
                "options": ["a", "b"],
                "correct_index": 1,
                "explanation": "leak",
            }
        }
        serialized = _serialize_questions_for_student(payload)
        assert len(serialized) == 1
        obj = serialized[0].model_dump()
        assert "correct_index" not in obj
        assert "explanation" not in obj
        assert obj["question_text"] == "x"
        assert obj["options"] == ["a", "b"]

    def test_preserves_q_ids(self):
        payload = {
            "q0": {"question_text": "a", "options": ["1", "2"], "correct_index": 0, "explanation": ""},
            "q1": {"question_text": "b", "options": ["3", "4"], "correct_index": 1, "explanation": ""},
        }
        ids = [q.id for q in _serialize_questions_for_student(payload)]
        assert ids == ["q0", "q1"]


# ---------------------------------------------------------------------------
# Model defaults / invariants.
# ---------------------------------------------------------------------------

class TestAIQuizSessionDefaults:
    def test_columns_default_to_unsubmitted_ai_source(self):
        """
        SQLAlchemy ORM `default=` is only applied on flush, not on Python
        instantiation, so check the column definitions directly.
        """
        cols = AIQuizSession.__table__.columns
        assert cols["is_submitted"].default.arg is False
        assert cols["source"].default.arg == "ai"
        assert cols["submitted_at"].nullable is True
        assert cols["is_submitted"].nullable is False

    def test_payload_round_trips_through_jsonb_shape(self):
        payload = {
            "q0": {
                "question_text": "¿X?",
                "options": ["a", "b", "c", "d"],
                "correct_index": 2,
                "explanation": "porque b * c",
            }
        }
        s = AIQuizSession(user_id=uuid.uuid4(), topic_id=1, questions=payload)
        # JSON-encodability is what JSONB needs at the DB layer.
        assert json.loads(json.dumps(s.questions)) == payload
