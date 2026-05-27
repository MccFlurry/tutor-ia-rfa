import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

import pytest

from app.schemas.admin_reports import StudentRow
from app.services import student_report_service
from app.services.student_report_service import (
    generate_cohort_report,
    LLMReportError,
)


def _row(name: str) -> StudentRow:
    return StudentRow(
        user_id=uuid4(),
        full_name=name,
        email=f"{name}@x",
        level="beginner",
        entry_score=50.0,
        overall_progress_pct=30.0,
        avg_quiz_score=0.5,
        avg_coding_score=70.0,
        last_activity_at=datetime.now(timezone.utc),
        last_location="M1",
        is_active=True,
    )


def _valid_cohort_payload() -> str:
    return json.dumps({
        "narrative": "El grupo avanza desigual.",
        "top_performers": ["Ana"],
        "needs_support": ["Bruno"],
        "common_gaps": ["coding M3"],
        "recommendations": ["tutoría focal"],
    })


@pytest.mark.asyncio
async def test_cohort_filters_non_existent_users(monkeypatch):
    rows = [_row("Ana"), _row("Bruno")]
    monkeypatch.setattr(
        student_report_service, "get_students_overview",
        AsyncMock(return_value=rows),
    )
    monkeypatch.setattr(
        student_report_service.llm_service, "generate_student_report_text",
        AsyncMock(return_value=_valid_cohort_payload()),
    )

    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()

    ids = [rows[0].user_id, rows[1].user_id, uuid4()]
    out = await generate_cohort_report(MagicMock(), redis, ids)
    assert "Ana" in out.top_performers
    assert out.cached is False


@pytest.mark.asyncio
async def test_cohort_raises_when_less_than_two_match(monkeypatch):
    monkeypatch.setattr(
        student_report_service, "get_students_overview",
        AsyncMock(return_value=[_row("Ana")]),
    )
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)

    with pytest.raises(ValueError):
        await generate_cohort_report(MagicMock(), redis, [uuid4(), uuid4()])


@pytest.mark.asyncio
async def test_cohort_cache_key_stable_across_order(monkeypatch):
    rows = [_row("Ana"), _row("Bruno")]
    monkeypatch.setattr(
        student_report_service, "get_students_overview",
        AsyncMock(return_value=rows),
    )
    monkeypatch.setattr(
        student_report_service.llm_service, "generate_student_report_text",
        AsyncMock(return_value=_valid_cohort_payload()),
    )
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    setex = AsyncMock()
    redis.setex = setex

    ids_a = [rows[0].user_id, rows[1].user_id]
    ids_b = [rows[1].user_id, rows[0].user_id]
    await generate_cohort_report(MagicMock(), redis, ids_a)
    await generate_cohort_report(MagicMock(), redis, ids_b)
    keys = [c.args[0] for c in setex.call_args_list]
    assert keys[0] == keys[1]
