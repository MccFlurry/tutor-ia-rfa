"""Unit tests for get_students_overview aggregator.

The query is mocked at result level — we assert that the function transforms
joined rows into StudentRow correctly. Real PostgreSQL is exercised by the
integration tests in Task 8.
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.student_report_service import get_students_overview


def _user(role="student", full_name="A", is_active=True):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email=f"{full_name.lower()}@x.pe",
        full_name=full_name,
        role=role,
        is_active=is_active,
    )


def _level(level="beginner", entry_score=50.0):
    return SimpleNamespace(level=level, entry_score=entry_score)


def _row(user, level, *, progress=0.0, avg_quiz=None, avg_coding=None,
         last_at=None, last_topic_title=None):
    total = 10
    completed = int(round(progress / 100.0 * total))
    lp = last_at if last_topic_title else None
    return (user, level, completed, total, avg_quiz, avg_coding, lp, None, None, None)


@pytest.mark.asyncio
async def test_overview_maps_joined_rows_to_student_rows():
    u1 = _user(full_name="Ana")
    u2 = _user(full_name="Bruno")
    last_at = datetime.now(timezone.utc)
    rows = [
        _row(u1, _level(), progress=50.0, avg_quiz=0.8, last_at=last_at, last_topic_title="M1 - Intro"),
        _row(u2, None, progress=0.0),
    ]

    db = MagicMock()
    db.execute = AsyncMock(side_effect=[
        MagicMock(all=MagicMock(return_value=rows)),
        MagicMock(all=MagicMock(return_value=[(u1.id, "M1", "Intro")])),
    ])

    result = await get_students_overview(db)

    assert len(result) == 2
    assert result[0].full_name == "Ana"
    assert result[0].level == "beginner"
    assert result[0].overall_progress_pct == 50.0
    assert result[0].last_location == "M1 - Intro"
    assert result[1].avg_quiz_score is None


@pytest.mark.asyncio
async def test_overview_excludes_non_students():
    student = _user(full_name="Ana")
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[
        MagicMock(all=MagicMock(return_value=[_row(student, None)])),
        MagicMock(all=MagicMock(return_value=[])),
    ])
    result = await get_students_overview(db)
    assert len(result) == 1
    assert result[0].full_name == "Ana"
