"""
Unit tests for check_reassessment + auto_apply_reassessment.

Validates:
- Boundary filter (last_reassessed_at) prevents re-triggering on the same streak.
- Coding submissions (0-100) and quiz attempts (0-1) merge into the same streak
  after normalization.
- auto_apply_reassessment writes the new level and returns a change payload.
"""

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.leveling_service import (
    check_reassessment,
    auto_apply_reassessment,
)


def _user_level(level: str, last_reassessed_at=None, assessed_at=None) -> SimpleNamespace:
    return SimpleNamespace(
        user_id=uuid.uuid4(),
        level=level,
        entry_score=50.0,
        assessed_at=assessed_at or datetime(2026, 1, 1, tzinfo=timezone.utc),
        last_reassessed_at=last_reassessed_at,
        history=[],
    )


def _result_one_or_none(value):
    r = MagicMock()
    r.scalar_one_or_none = MagicMock(return_value=value)
    return r


def _result_rows(rows):
    r = MagicMock()
    r.all = MagicMock(return_value=rows)
    return r


def _mock_db_for_check(level_row, quiz_rows, coding_rows):
    """Wire mock_db.execute for the 3 queries inside check_reassessment."""
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[
        _result_one_or_none(level_row),
        _result_rows(quiz_rows),
        _result_rows(coding_rows),
    ])
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_check_returns_false_when_no_userlevel():
    db = MagicMock()
    db.execute = AsyncMock(return_value=_result_one_or_none(None))
    result = await check_reassessment(db, uuid.uuid4())
    assert result == {"should_reassess": False}


@pytest.mark.asyncio
async def test_check_returns_false_when_fewer_than_three_events():
    lvl = _user_level("beginner")
    db = _mock_db_for_check(lvl, quiz_rows=[(0.95, datetime.now(timezone.utc))], coding_rows=[])
    result = await check_reassessment(db, lvl.user_id)
    assert result["should_reassess"] is False
    assert result["current_level"] == "beginner"


@pytest.mark.asyncio
async def test_check_triggers_up_on_three_high_quizzes():
    lvl = _user_level("beginner")
    now = datetime.now(timezone.utc)
    quizzes = [(0.95, now - timedelta(minutes=i)) for i in range(3)]
    db = _mock_db_for_check(lvl, quizzes, [])

    result = await check_reassessment(db, lvl.user_id)
    assert result["should_reassess"] is True
    assert result["direction"] == "up"
    assert result["current_level"] == "beginner"
    assert result["proposed_level"] == "intermediate"


@pytest.mark.asyncio
async def test_check_triggers_down_on_three_low_events():
    lvl = _user_level("advanced")
    now = datetime.now(timezone.utc)
    quizzes = [(0.30, now - timedelta(minutes=i)) for i in range(3)]
    db = _mock_db_for_check(lvl, quizzes, [])

    result = await check_reassessment(db, lvl.user_id)
    assert result["should_reassess"] is True
    assert result["direction"] == "down"
    assert result["proposed_level"] == "intermediate"


@pytest.mark.asyncio
async def test_coding_submissions_count_after_normalization():
    """3 coding submissions (score 90+/100) → up trigger via normalization."""
    lvl = _user_level("beginner")
    now = datetime.now(timezone.utc)
    coding = [(95.0, now - timedelta(minutes=i)) for i in range(3)]
    db = _mock_db_for_check(lvl, [], coding)

    result = await check_reassessment(db, lvl.user_id)
    assert result["should_reassess"] is True
    assert result["direction"] == "up"


@pytest.mark.asyncio
async def test_quiz_and_coding_events_merge_into_streak():
    """Streak = top 3 most recent across BOTH event sources."""
    lvl = _user_level("beginner")
    now = datetime.now(timezone.utc)
    quizzes = [(0.95, now - timedelta(minutes=5))]
    coding = [(92.0, now - timedelta(minutes=1)), (91.0, now - timedelta(minutes=3))]
    db = _mock_db_for_check(lvl, quizzes, coding)

    result = await check_reassessment(db, lvl.user_id)
    assert result["should_reassess"] is True
    assert result["direction"] == "up"


@pytest.mark.asyncio
async def test_boundary_filter_excludes_old_attempts():
    """Quizzes attempted BEFORE last_reassessed_at must not be queried at all.

    We simulate the boundary filter by returning an empty quiz row set — what
    the SQL would do given the WHERE clause. The point of the assertion is
    that the service treats fewer-than-three events as 'no reassessment'.
    """
    boundary = datetime.now(timezone.utc) - timedelta(hours=1)
    lvl = _user_level("intermediate", last_reassessed_at=boundary)
    db = _mock_db_for_check(lvl, [], [])

    result = await check_reassessment(db, lvl.user_id)
    assert result["should_reassess"] is False


@pytest.mark.asyncio
async def test_check_does_not_propose_up_when_already_advanced():
    lvl = _user_level("advanced")
    now = datetime.now(timezone.utc)
    quizzes = [(0.99, now - timedelta(minutes=i)) for i in range(3)]
    db = _mock_db_for_check(lvl, quizzes, [])

    result = await check_reassessment(db, lvl.user_id)
    assert result["should_reassess"] is False


@pytest.mark.asyncio
async def test_check_does_not_propose_down_when_already_beginner():
    lvl = _user_level("beginner")
    now = datetime.now(timezone.utc)
    quizzes = [(0.10, now - timedelta(minutes=i)) for i in range(3)]
    db = _mock_db_for_check(lvl, quizzes, [])

    result = await check_reassessment(db, lvl.user_id)
    assert result["should_reassess"] is False


@pytest.mark.asyncio
async def test_auto_apply_returns_none_when_no_proposal():
    db = MagicMock()
    db.execute = AsyncMock(return_value=_result_one_or_none(None))
    result = await auto_apply_reassessment(db, uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_auto_apply_writes_and_returns_change_payload():
    """When check fires, auto_apply persists the new level and returns the dict."""
    lvl = _user_level("beginner")
    now = datetime.now(timezone.utc)
    quizzes = [(0.95, now - timedelta(minutes=i)) for i in range(3)]

    db = MagicMock()
    db.execute = AsyncMock(side_effect=[
        # check_reassessment
        _result_one_or_none(lvl),
        _result_rows(quizzes),
        _result_rows([]),
        # apply_reassessment
        _result_one_or_none(lvl),
        # upsert_user_level
        _result_one_or_none(lvl),
    ])
    db.add = MagicMock()
    db.flush = AsyncMock()

    change = await auto_apply_reassessment(db, lvl.user_id)
    assert change == {
        "direction": "up",
        "previous_level": "beginner",
        "new_level": "intermediate",
        "reason": "3 quizzes consecutivos ≥90%",
    }
    # UserLevel.level was mutated to the proposed level by upsert
    assert lvl.level == "intermediate"
