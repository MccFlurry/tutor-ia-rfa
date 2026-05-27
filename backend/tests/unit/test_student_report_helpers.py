"""Tests for helper functions in student_report_service: hash, activity gate, redis wrappers."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.admin_reports import StudentDetail, QuizAttemptRow
from app.services.student_report_service import (
    InsufficientActivityError,
    LLMReportError,
    _detail_hash,
    _has_minimum_activity,
    _safe_redis_get,
    _safe_redis_setex,
)


def _empty_detail() -> StudentDetail:
    return StudentDetail(
        user_id=uuid4(),
        full_name="x",
        email="x@x",
        created_at=datetime.now(timezone.utc),
        is_active=True,
        overall_progress_pct=0.0,
        chat_messages_count=0,
        total_time_seconds=0,
    )


def test_has_minimum_activity_false_when_no_quiz_or_coding():
    d = _empty_detail()
    assert _has_minimum_activity(d) is False


def test_has_minimum_activity_true_with_one_quiz():
    d = _empty_detail()
    d.recent_quizzes = [
        QuizAttemptRow(
            attempt_id=1,
            topic_id=1,
            topic_title="t",
            score=0.5,
            is_passed=False,
            attempted_at=datetime.now(timezone.utc),
        )
    ]
    assert _has_minimum_activity(d) is True


def test_detail_hash_changes_on_progress_change():
    d1 = _empty_detail()
    h1 = _detail_hash(d1)
    d2 = _empty_detail()
    d2.overall_progress_pct = 50.0
    h2 = _detail_hash(d2)
    assert h1 != h2


def test_detail_hash_stable_across_calls():
    d = _empty_detail()
    assert _detail_hash(d) == _detail_hash(d)


def test_exceptions_exist():
    assert issubclass(InsufficientActivityError, Exception)
    assert issubclass(LLMReportError, Exception)


@pytest.mark.asyncio
async def test_safe_redis_get_returns_value():
    client = MagicMock()
    client.get = AsyncMock(return_value='{"a":1}')
    assert await _safe_redis_get(client, "k") == '{"a":1}'


@pytest.mark.asyncio
async def test_safe_redis_get_returns_none_on_exception():
    client = MagicMock()
    client.get = AsyncMock(side_effect=RuntimeError("boom"))
    assert await _safe_redis_get(client, "k") is None


@pytest.mark.asyncio
async def test_safe_redis_setex_swallows_exception():
    client = MagicMock()
    client.setex = AsyncMock(side_effect=RuntimeError("boom"))
    # must not raise
    await _safe_redis_setex(client, "k", 60, "v")
