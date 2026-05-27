"""Schema sanity tests for admin_reports — ensures field names and bounds match spec."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.admin_reports import (
    StudentRow,
    ModuleProgress,
    QuizAttemptRow,
    CodingSubmissionRow,
    AchievementRow,
    LevelHistoryEntry,
    StudentDetail,
    AIReport,
    CohortReportRequest,
    CohortAIReport,
)


def test_student_row_minimal_fields():
    row = StudentRow(
        user_id=uuid4(),
        full_name="Juan Pérez",
        email="juan@x.pe",
        level=None,
        entry_score=None,
        overall_progress_pct=0.0,
        avg_quiz_score=None,
        avg_coding_score=None,
        last_activity_at=None,
        last_location=None,
        is_active=True,
    )
    assert row.overall_progress_pct == 0.0


def test_ai_report_requires_risk_level_string():
    rep = AIReport(
        summary="ok",
        strengths=["a"],
        weaknesses=["b"],
        risk_level="medio",
        risk_reason="x",
        interventions=["c"],
        generated_at=datetime.now(timezone.utc),
        cached=False,
    )
    assert rep.risk_level == "medio"


def test_cohort_request_min_two_max_fifteen():
    ids = [uuid4() for _ in range(2)]
    CohortReportRequest(user_ids=ids)
    with pytest.raises(ValidationError):
        CohortReportRequest(user_ids=[uuid4()])
    with pytest.raises(ValidationError):
        CohortReportRequest(user_ids=[uuid4() for _ in range(16)])


def test_student_detail_caps_recent_lists_at_ten():
    detail = StudentDetail(
        user_id=uuid4(),
        full_name="n",
        email="e@x",
        created_at=datetime.now(timezone.utc),
        is_active=True,
        level=None,
        entry_score=None,
        level_history=[],
        overall_progress_pct=0.0,
        modules=[],
        chat_messages_count=0,
        chat_last_at=None,
        achievements_earned=[],
        total_time_seconds=0,
        last_activity_at=None,
        last_location=None,
    )
    assert detail.recent_quizzes == []
    assert detail.recent_coding == []
