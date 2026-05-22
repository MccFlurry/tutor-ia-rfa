"""
Unit tests para app/services/topic_completion_service.py.
La lógica decide cuándo marcar un tema como completado:
- has_quiz + has_coding → ambos
- solo quiz → quiz
- solo coding → coding
- ninguno → no auto-completa (queda manual)
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import topic_completion_service as svc


def _scalar_db(values: list):
    """
    Mock AsyncSession donde cada execute().scalar() devuelve el siguiente valor.
    Para flujos que también necesitan scalar_one_or_none (ej. lookup Topic / progress),
    usar _mock_db_multi.
    """
    db = MagicMock()
    results = []
    for v in values:
        r = MagicMock()
        r.scalar = MagicMock(return_value=v)
        results.append(r)
    db.execute = AsyncMock(side_effect=results)
    db.add = MagicMock()
    return db


def _mock_db_multi(responses: list):
    """
    Cada item de `responses` es un dict con keys opcionales:
    `scalar` (int) o `scalar_one_or_none` (object).
    Cada execute() consume el siguiente item.
    """
    db = MagicMock()
    results = []
    for r in responses:
        m = MagicMock()
        if "scalar" in r:
            m.scalar = MagicMock(return_value=r["scalar"])
        if "scalar_one_or_none" in r:
            m.scalar_one_or_none = MagicMock(return_value=r["scalar_one_or_none"])
        results.append(m)
    db.execute = AsyncMock(side_effect=results)
    db.add = MagicMock()
    return db


class TestCheckAndCompleteTopic:
    @pytest.mark.asyncio
    async def test_returns_false_when_topic_missing(self):
        db = _mock_db_multi([{"scalar_one_or_none": None}])
        ok = await svc.check_and_complete_topic(uuid.uuid4(), 999, db)
        assert ok is False

    @pytest.mark.asyncio
    async def test_quiz_only_topic_completes_when_quiz_passed(self):
        topic = SimpleNamespace(id=1, has_quiz=True)
        db = _mock_db_multi([
            {"scalar_one_or_none": topic},  # topic lookup
            {"scalar": 1},                  # _has_passed_quiz (>0 passed)
            {"scalar": 0},                  # _topic_has_coding (no static challenge)
            {"scalar_one_or_none": None},   # _mark_completed: progress row not found
        ])
        with patch.object(svc, "check_and_grant_achievements", new=AsyncMock(return_value=[])):
            ok = await svc.check_and_complete_topic(uuid.uuid4(), 1, db)
        assert ok is True
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_quiz_only_topic_does_not_complete_when_quiz_failed(self):
        topic = SimpleNamespace(id=1, has_quiz=True)
        db = _mock_db_multi([
            {"scalar_one_or_none": topic},
            {"scalar": 0},  # zero passing attempts
            {"scalar": 0},  # no coding challenges
        ])
        with patch.object(svc, "check_and_grant_achievements", new=AsyncMock(return_value=[])):
            ok = await svc.check_and_complete_topic(uuid.uuid4(), 1, db)
        assert ok is False

    @pytest.mark.asyncio
    async def test_coding_topic_completes_when_submission_passes(self):
        topic = SimpleNamespace(id=2, has_quiz=False)
        db = _mock_db_multi([
            {"scalar_one_or_none": topic},
            # quiz check skipped (has_quiz=False)
            {"scalar": 1},  # _topic_has_coding (has challenge)
            {"scalar": 1},  # _has_passed_any_coding (≥60)
            {"scalar_one_or_none": None},  # mark_completed: no prior progress
        ])
        with patch.object(svc, "check_and_grant_achievements", new=AsyncMock(return_value=[])):
            ok = await svc.check_and_complete_topic(uuid.uuid4(), 2, db)
        assert ok is True

    @pytest.mark.asyncio
    async def test_coding_topic_blocked_when_no_passing_submission(self):
        topic = SimpleNamespace(id=2, has_quiz=False)
        db = _mock_db_multi([
            {"scalar_one_or_none": topic},
            {"scalar": 1},  # _topic_has_coding
            {"scalar": 0},  # no passing submissions
        ])
        with patch.object(svc, "check_and_grant_achievements", new=AsyncMock(return_value=[])):
            ok = await svc.check_and_complete_topic(uuid.uuid4(), 2, db)
        assert ok is False

    @pytest.mark.asyncio
    async def test_quiz_and_coding_both_required(self):
        topic = SimpleNamespace(id=3, has_quiz=True)
        # quiz passed, coding NOT passed → blocked
        db = _mock_db_multi([
            {"scalar_one_or_none": topic},
            {"scalar": 1},  # quiz passed
            {"scalar": 1},  # coding required
            {"scalar": 0},  # no passing coding submission
        ])
        with patch.object(svc, "check_and_grant_achievements", new=AsyncMock(return_value=[])):
            ok = await svc.check_and_complete_topic(uuid.uuid4(), 3, db)
        assert ok is False

    @pytest.mark.asyncio
    async def test_marks_existing_progress_row(self):
        topic = SimpleNamespace(id=1, has_quiz=True)
        existing_progress = SimpleNamespace(
            user_id=uuid.uuid4(),
            topic_id=1,
            is_completed=False,
            completed_at=None,
            last_accessed_at=None,
        )
        db = _mock_db_multi([
            {"scalar_one_or_none": topic},
            {"scalar": 1},  # quiz passed
            {"scalar": 0},  # no coding required
            {"scalar_one_or_none": existing_progress},
        ])
        with patch.object(svc, "check_and_grant_achievements", new=AsyncMock(return_value=[])):
            ok = await svc.check_and_complete_topic(existing_progress.user_id, 1, db)
        assert ok is True
        assert existing_progress.is_completed is True
        assert existing_progress.completed_at is not None


class TestGetTopicCompletionStatus:
    @pytest.mark.asyncio
    async def test_missing_topic_returns_default(self):
        db = _mock_db_multi([{"scalar_one_or_none": None}])
        out = await svc.get_topic_completion_status(uuid.uuid4(), 999, db)
        assert out == {
            "quiz_required": False,
            "quiz_passed": False,
            "coding_required": False,
            "coding_passed": False,
        }

    @pytest.mark.asyncio
    async def test_reports_quiz_and_coding_flags(self):
        topic = SimpleNamespace(id=1, has_quiz=True)
        db = _mock_db_multi([
            {"scalar_one_or_none": topic},
            {"scalar": 1},  # quiz passed
            {"scalar": 1},  # coding required
            {"scalar": 1},  # coding passed
        ])
        out = await svc.get_topic_completion_status(uuid.uuid4(), 1, db)
        assert out["quiz_required"] is True
        assert out["quiz_passed"] is True
        assert out["coding_required"] is True
        assert out["coding_passed"] is True
