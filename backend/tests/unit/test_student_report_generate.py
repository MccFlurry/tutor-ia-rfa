"""End-to-end unit test for generate_ai_report.

`get_student_detail` and `llm_service.generate_student_report_text` are
monkeypatched.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.admin_reports import (
    StudentDetail, QuizAttemptRow,
)
from app.services import student_report_service
from app.services.student_report_service import (
    generate_ai_report,
    InsufficientActivityError,
    LLMReportError,
)


def _detail_with_quiz() -> StudentDetail:
    return StudentDetail(
        user_id=uuid4(),
        full_name="Ana",
        email="a@x",
        created_at=datetime.now(timezone.utc),
        is_active=True,
        overall_progress_pct=20.0,
        chat_messages_count=0,
        total_time_seconds=0,
        recent_quizzes=[QuizAttemptRow(
            attempt_id=1, topic_id=1, topic_title="t",
            score=0.7, is_passed=True,
            attempted_at=datetime.now(timezone.utc),
        )],
    )


def _detail_empty() -> StudentDetail:
    return StudentDetail(
        user_id=uuid4(), full_name="Bruno", email="b@x",
        created_at=datetime.now(timezone.utc), is_active=True,
        overall_progress_pct=0.0, chat_messages_count=0, total_time_seconds=0,
    )


def _valid_llm_payload() -> str:
    return json.dumps({
        "report": {
            "summary": "Estudiante activo.",
            "strengths": ["consistencia"],
            "weaknesses": ["coding"],
            "risk_level": "bajo",
            "risk_reason": "ninguna alarma",
            "interventions": ["asignar reto extra"],
        }
    })


@pytest.mark.asyncio
async def test_generate_raises_when_no_activity(monkeypatch):
    db = MagicMock()
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()

    monkeypatch.setattr(
        student_report_service, "get_student_detail",
        AsyncMock(return_value=_detail_empty()),
    )
    with pytest.raises(InsufficientActivityError):
        await generate_ai_report(db, redis, uuid4())


@pytest.mark.asyncio
async def test_generate_calls_llm_and_caches(monkeypatch):
    db = MagicMock()
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()

    detail = _detail_with_quiz()
    monkeypatch.setattr(
        student_report_service, "get_student_detail", AsyncMock(return_value=detail)
    )
    llm = AsyncMock(return_value=_valid_llm_payload())
    monkeypatch.setattr(student_report_service.llm_service,
                        "generate_student_report_text", llm)

    out = await generate_ai_report(db, redis, detail.user_id)

    assert out.cached is False
    assert out.risk_level == "bajo"
    llm.assert_called_once()
    redis.setex.assert_called_once()
    assert redis.setex.call_args.args[1] == 3600


@pytest.mark.asyncio
async def test_generate_returns_cached_payload(monkeypatch):
    db = MagicMock()
    redis = MagicMock()
    cached_payload = json.dumps({
        "summary": "x", "strengths": [], "weaknesses": [],
        "risk_level": "bajo", "risk_reason": "x", "interventions": [],
        "generated_at": "2026-05-27T10:00:00+00:00",
    })
    redis.get = AsyncMock(return_value=cached_payload)
    redis.setex = AsyncMock()

    detail = _detail_with_quiz()
    monkeypatch.setattr(
        student_report_service, "get_student_detail", AsyncMock(return_value=detail)
    )
    llm = AsyncMock()
    monkeypatch.setattr(student_report_service.llm_service,
                        "generate_student_report_text", llm)

    out = await generate_ai_report(db, redis, detail.user_id)
    assert out.cached is True
    llm.assert_not_called()


@pytest.mark.asyncio
async def test_generate_retries_then_succeeds(monkeypatch):
    db = MagicMock()
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()

    detail = _detail_with_quiz()
    monkeypatch.setattr(
        student_report_service, "get_student_detail", AsyncMock(return_value=detail)
    )
    llm = AsyncMock(side_effect=["not-json-at-all", _valid_llm_payload()])
    monkeypatch.setattr(student_report_service.llm_service,
                        "generate_student_report_text", llm)

    out = await generate_ai_report(db, redis, detail.user_id)
    assert llm.call_count == 2
    assert out.cached is False


@pytest.mark.asyncio
async def test_generate_raises_after_two_failures(monkeypatch):
    db = MagicMock()
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()

    detail = _detail_with_quiz()
    monkeypatch.setattr(
        student_report_service, "get_student_detail", AsyncMock(return_value=detail)
    )
    llm = AsyncMock(side_effect=["garbage", "still-garbage"])
    monkeypatch.setattr(student_report_service.llm_service,
                        "generate_student_report_text", llm)

    with pytest.raises(LLMReportError):
        await generate_ai_report(db, redis, detail.user_id)
