"""
Unit tests para app/services/progress_service.py.
Cubre cómputo de progreso global, log de actividad y streak.
"""

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import progress_service as svc


def _q_scalars_all(values):
    r = MagicMock()
    r.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=values)))
    return r


def _q_scalar(value):
    r = MagicMock()
    r.scalar = MagicMock(return_value=value)
    return r


def _q_rows(rows):
    """For tuple-style result iteration: result.__iter__ → rows; result.all() → rows."""
    r = MagicMock()
    r.__iter__ = MagicMock(return_value=iter(rows))
    r.all = MagicMock(return_value=rows)
    return r


class TestGetUserProgress:
    @pytest.mark.asyncio
    async def test_no_topics_returns_zero(self):
        db = MagicMock()
        db.execute = AsyncMock(side_effect=[
            _q_scalars_all([]),  # modules
            _q_scalar(0),        # total topics
            _q_scalar(0),        # completed
            _q_scalar(0),        # time
            _q_scalar(None),     # quiz avg
        ])
        out = await svc.get_user_progress(uuid.uuid4(), db)
        assert out["overall_pct"] == 0.0
        assert out["topics_completed"] == 0
        assert out["modules"] == []
        assert out["quiz_avg_score"] is None

    @pytest.mark.asyncio
    async def test_overall_pct_rounded(self):
        m1 = SimpleNamespace(id=1, title="M1", order_index=1)
        db = MagicMock()
        # Sequence: modules, total, completed, time, quiz_avg, mod_total, mod_completed
        db.execute = AsyncMock(side_effect=[
            _q_scalars_all([m1]),
            _q_scalar(10),
            _q_scalar(3),
            _q_scalar(120),
            _q_scalar(0.85),
            _q_scalar(10),
            _q_scalar(3),
        ])
        out = await svc.get_user_progress(uuid.uuid4(), db)
        assert out["overall_pct"] == 30.0
        assert out["topics_completed"] == 3
        assert out["total_time_seconds"] == 120
        assert out["quiz_avg_score"] == 85.0
        assert out["modules"][0]["pct"] == 30.0


class TestGetActivityLog:
    @pytest.mark.asyncio
    async def test_merges_and_sorts_descending(self):
        now = datetime.now(timezone.utc)
        older = now - timedelta(hours=2)
        progress = SimpleNamespace(completed_at=older)
        attempt = SimpleNamespace(
            score=0.8, is_passed=True, attempted_at=now
        )
        db = MagicMock()
        db.execute = AsyncMock(side_effect=[
            _q_rows([(progress, "Tema antiguo")]),
            _q_rows([(attempt, "Quiz reciente")]),
        ])
        log = await svc.get_activity_log(uuid.uuid4(), db, limit=10)
        # Quiz reciente (now) debe estar antes del tema (older)
        assert log[0]["type"] == "quiz_passed"
        assert log[1]["type"] == "topic_completed"
        # Score 80% formateado
        assert "80%" in log[0]["description"]

    @pytest.mark.asyncio
    async def test_failed_quiz_marked(self):
        attempt = SimpleNamespace(
            score=0.3, is_passed=False, attempted_at=datetime.now(timezone.utc)
        )
        db = MagicMock()
        db.execute = AsyncMock(side_effect=[
            _q_rows([]),
            _q_rows([(attempt, "Quiz")]),
        ])
        log = await svc.get_activity_log(uuid.uuid4(), db)
        assert log[0]["type"] == "quiz_failed"
        assert "no aprobaste" in log[0]["description"]


class TestComputeStreak:
    @pytest.mark.asyncio
    async def test_no_activity_returns_zero(self):
        db = MagicMock()
        db.execute = AsyncMock(return_value=_q_rows([]))
        out = await svc.compute_streak(uuid.uuid4(), db)
        assert out == {
            "current_streak": 0,
            "longest_streak": 0,
            "last_active_date": None,
        }

    @pytest.mark.asyncio
    async def test_today_only_streak_one(self):
        today = datetime.now(timezone.utc)
        db = MagicMock()
        db.execute = AsyncMock(return_value=_q_rows([(today,)]))
        out = await svc.compute_streak(uuid.uuid4(), db)
        assert out["current_streak"] == 1
        assert out["longest_streak"] == 1

    @pytest.mark.asyncio
    async def test_three_consecutive_days(self):
        today = datetime.now(timezone.utc)
        d1 = today
        d2 = today - timedelta(days=1)
        d3 = today - timedelta(days=2)
        db = MagicMock()
        db.execute = AsyncMock(return_value=_q_rows([(d1,), (d2,), (d3,)]))
        out = await svc.compute_streak(uuid.uuid4(), db)
        assert out["current_streak"] == 3
        assert out["longest_streak"] == 3

    @pytest.mark.asyncio
    async def test_gap_breaks_current_keeps_longest(self):
        today = datetime.now(timezone.utc)
        d1 = today
        d2 = today - timedelta(days=1)
        # Gap (day 3 missing), then 3 days
        d4 = today - timedelta(days=4)
        d5 = today - timedelta(days=5)
        d6 = today - timedelta(days=6)
        db = MagicMock()
        db.execute = AsyncMock(return_value=_q_rows([
            (d1,), (d2,), (d4,), (d5,), (d6,)
        ]))
        out = await svc.compute_streak(uuid.uuid4(), db)
        assert out["current_streak"] == 2
        assert out["longest_streak"] == 3

    @pytest.mark.asyncio
    async def test_streak_anchored_to_yesterday_still_counts(self):
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        db = MagicMock()
        db.execute = AsyncMock(return_value=_q_rows([(yesterday,)]))
        out = await svc.compute_streak(uuid.uuid4(), db)
        assert out["current_streak"] == 1

    @pytest.mark.asyncio
    async def test_stale_streak_is_zero_current(self):
        old = datetime.now(timezone.utc) - timedelta(days=5)
        db = MagicMock()
        db.execute = AsyncMock(return_value=_q_rows([(old,)]))
        out = await svc.compute_streak(uuid.uuid4(), db)
        assert out["current_streak"] == 0
        assert out["longest_streak"] == 1
