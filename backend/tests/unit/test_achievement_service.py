"""
Unit tests para app/services/achievement_service.py.
Cubre las 6 condiciones (first_topic, module_completed, chat_messages,
quiz_perfect, course_completed, streak_days) + skip de ya-ganados.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import achievement_service as svc


def _ach(condition_type, condition_value=1, *, module_id=None, id_=1):
    return SimpleNamespace(
        id=id_,
        name=f"ach-{condition_type}",
        description="desc",
        badge_emoji="*",
        badge_color="#fff",
        condition_type=condition_type,
        condition_value=condition_value,
        condition_module_id=module_id,
    )


def _scalar_db_sequence(scalar_values: list, *, all_values=None):
    """
    Cada execute() devuelve un MagicMock cuyo .scalar() entrega el siguiente valor,
    y cuyo .scalars().all() entrega el siguiente de all_values (si se provee).
    """
    db = MagicMock()
    results = []
    for i, v in enumerate(scalar_values):
        r = MagicMock()
        r.scalar = MagicMock(return_value=v)
        # default empty scalars.all()
        scalars = MagicMock()
        all_for_this = (all_values or [[]])[i] if all_values else []
        scalars.all = MagicMock(return_value=all_for_this)
        r.scalars = MagicMock(return_value=scalars)
        results.append(r)
    db.execute = AsyncMock(side_effect=results)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


class TestCheckCondition:
    @pytest.mark.asyncio
    async def test_first_topic_met(self):
        db = _scalar_db_sequence([1])  # 1 completed topic
        ok = await svc._check_condition(uuid.uuid4(), _ach("first_topic", 1), db)
        assert ok is True

    @pytest.mark.asyncio
    async def test_first_topic_not_met(self):
        db = _scalar_db_sequence([0])
        ok = await svc._check_condition(uuid.uuid4(), _ach("first_topic", 1), db)
        assert ok is False

    @pytest.mark.asyncio
    async def test_chat_messages_threshold(self):
        db = _scalar_db_sequence([15])
        ok = await svc._check_condition(uuid.uuid4(), _ach("chat_messages", 10), db)
        assert ok is True

    @pytest.mark.asyncio
    async def test_quiz_perfect_requires_one_score_one(self):
        db = _scalar_db_sequence([1])
        ok = await svc._check_condition(uuid.uuid4(), _ach("quiz_perfect"), db)
        assert ok is True

    @pytest.mark.asyncio
    async def test_quiz_perfect_zero_blocks(self):
        db = _scalar_db_sequence([0])
        ok = await svc._check_condition(uuid.uuid4(), _ach("quiz_perfect"), db)
        assert ok is False

    @pytest.mark.asyncio
    async def test_course_completed_requires_all_topics(self):
        db = _scalar_db_sequence([10, 10])  # 10 topics total / 10 completed
        ok = await svc._check_condition(uuid.uuid4(), _ach("course_completed"), db)
        assert ok is True

    @pytest.mark.asyncio
    async def test_course_completed_partial_blocked(self):
        db = _scalar_db_sequence([10, 7])
        ok = await svc._check_condition(uuid.uuid4(), _ach("course_completed"), db)
        assert ok is False

    @pytest.mark.asyncio
    async def test_course_completed_zero_topics_blocked(self):
        db = _scalar_db_sequence([0, 0])
        ok = await svc._check_condition(uuid.uuid4(), _ach("course_completed"), db)
        assert ok is False

    @pytest.mark.asyncio
    async def test_streak_days_threshold(self):
        db = _scalar_db_sequence([7])
        ok = await svc._check_condition(uuid.uuid4(), _ach("streak_days", 7), db)
        assert ok is True

    @pytest.mark.asyncio
    async def test_module_completed_specific_module_pass(self):
        # Single module check: 3 topics total, 3 completed
        db = _scalar_db_sequence([3, 3])
        ach = _ach("module_completed", module_id=1)
        ok = await svc._check_condition(uuid.uuid4(), ach, db)
        assert ok is True

    @pytest.mark.asyncio
    async def test_module_completed_specific_module_fail(self):
        db = _scalar_db_sequence([3, 2])
        ach = _ach("module_completed", module_id=1)
        ok = await svc._check_condition(uuid.uuid4(), ach, db)
        assert ok is False

    @pytest.mark.asyncio
    async def test_unknown_condition_returns_false(self):
        db = _scalar_db_sequence([])
        ok = await svc._check_condition(uuid.uuid4(), _ach("xxx-unknown"), db)
        assert ok is False


class TestCheckAndGrantAchievements:
    @pytest.mark.asyncio
    async def test_skips_already_earned(self):
        ach = _ach("first_topic", id_=99)
        # First execute: list achievements
        all_q = MagicMock()
        all_q.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[ach])))
        # Second execute: already-earned IDs
        earned_q = MagicMock()
        earned_q.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[99])))
        db = MagicMock()
        db.execute = AsyncMock(side_effect=[all_q, earned_q])
        db.add = MagicMock()
        db.flush = AsyncMock()

        granted = await svc.check_and_grant_achievements(uuid.uuid4(), db)
        assert granted == []
        db.add.assert_not_called()
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_grants_new_achievement(self):
        ach = _ach("first_topic", id_=42, condition_value=1)
        all_q = MagicMock()
        all_q.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[ach])))
        earned_q = MagicMock()
        earned_q.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        # Third execute: _check_condition first_topic counter
        count_q = MagicMock()
        count_q.scalar = MagicMock(return_value=5)
        db = MagicMock()
        db.execute = AsyncMock(side_effect=[all_q, earned_q, count_q])
        db.add = MagicMock()
        db.flush = AsyncMock()

        granted = await svc.check_and_grant_achievements(uuid.uuid4(), db)
        assert len(granted) == 1
        assert granted[0]["id"] == 42
        db.add.assert_called_once()
        db.flush.assert_awaited_once()
