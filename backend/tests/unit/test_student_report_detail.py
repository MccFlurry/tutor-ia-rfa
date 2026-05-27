"""Unit tests for get_student_detail."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.student_report_service import get_student_detail


def _user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="a@x.pe",
        full_name="Ana",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


def _level():
    return SimpleNamespace(
        level="intermediate",
        entry_score=70.0,
        history=[
            {
                "level": "beginner",
                "score": 40.0,
                "changed_at": "2026-03-01T10:00:00+00:00",
                "reason": "initial",
            }
        ],
    )


@pytest.mark.asyncio
async def test_detail_returns_level_history_and_aggregates():
    user = _user()
    lvl = _level()

    module_row = (
        SimpleNamespace(id=1, title="M1"),
        2,    # topics_completed
        4,    # topics_total
        0.8,  # avg_quiz
        None,
    )

    db = MagicMock()
    db.execute = AsyncMock(side_effect=[
        MagicMock(first=MagicMock(return_value=(user, lvl))),
        MagicMock(all=MagicMock(return_value=[module_row])),
        MagicMock(all=MagicMock(return_value=[])),  # quizzes
        MagicMock(all=MagicMock(return_value=[])),  # coding
        MagicMock(first=MagicMock(return_value=(0, None))),  # chat count + last
        MagicMock(all=MagicMock(return_value=[])),  # achievements
        MagicMock(scalar=MagicMock(return_value=0)),  # total_time
    ])

    detail = await get_student_detail(db, user.id)

    assert detail.full_name == "Ana"
    assert detail.level == "intermediate"
    assert len(detail.level_history) == 1
    assert detail.level_history[0].level == "beginner"
    assert detail.modules[0].progress_pct == 50.0


@pytest.mark.asyncio
async def test_detail_raises_404_when_user_missing():
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock(first=MagicMock(return_value=None)))
    with pytest.raises(LookupError):
        await get_student_detail(db, uuid.uuid4())
