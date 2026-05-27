"""Integration tests for /api/v1/admin/students/* — covers auth, happy path,
error mapping, and that the service is correctly wired into the router."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.admin_reports import (
    StudentRow, AIReport, CohortAIReport,
)


def _row(name="Ana"):
    return StudentRow(
        user_id=uuid.uuid4(),
        full_name=name,
        email=f"{name.lower()}@x.pe",
        level="beginner",
        entry_score=50.0,
        overall_progress_pct=10.0,
        avg_quiz_score=0.5,
        avg_coding_score=70.0,
        last_activity_at=datetime.now(timezone.utc),
        last_location="M1",
        is_active=True,
    )


def _ai():
    return AIReport(
        summary="ok",
        strengths=["a"], weaknesses=["b"],
        risk_level="bajo", risk_reason="x", interventions=["c"],
        generated_at=datetime.now(timezone.utc),
        cached=False,
    )


def _cohort():
    return CohortAIReport(
        narrative="ok",
        top_performers=["Ana"], needs_support=["Bruno"],
        common_gaps=[], recommendations=["x"],
        generated_at=datetime.now(timezone.utc),
        cached=False,
    )


@pytest.mark.asyncio
async def test_students_list_requires_admin(client):
    r = await client.get("/api/v1/admin/students")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_students_list_returns_rows(admin_client):
    with patch("app.routers.admin_reports.student_report_service.get_students_overview",
               AsyncMock(return_value=[_row(), _row("Bruno")])):
        r = await admin_client.get("/api/v1/admin/students")
        assert r.status_code == 200, r.text
        data = r.json()
        assert len(data) == 2
        assert data[0]["full_name"] == "Ana"


@pytest.mark.asyncio
async def test_student_detail_404_when_missing(admin_client):
    with patch("app.routers.admin_reports.student_report_service.get_student_detail",
               AsyncMock(side_effect=LookupError())):
        r = await admin_client.get(f"/api/v1/admin/students/{uuid.uuid4()}")
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_ai_report_success(admin_client):
    with patch("app.routers.admin_reports.student_report_service.generate_ai_report",
               AsyncMock(return_value=_ai())):
        r = await admin_client.post(f"/api/v1/admin/students/{uuid.uuid4()}/ai-report")
        assert r.status_code == 200, r.text
        assert r.json()["risk_level"] == "bajo"


@pytest.mark.asyncio
async def test_ai_report_503_when_llm_fails(admin_client):
    from app.services.student_report_service import LLMReportError
    with patch("app.routers.admin_reports.student_report_service.generate_ai_report",
               AsyncMock(side_effect=LLMReportError("boom"))):
        r = await admin_client.post(f"/api/v1/admin/students/{uuid.uuid4()}/ai-report")
        assert r.status_code == 503


@pytest.mark.asyncio
async def test_ai_report_422_insufficient_activity(admin_client):
    from app.services.student_report_service import InsufficientActivityError
    with patch("app.routers.admin_reports.student_report_service.generate_ai_report",
               AsyncMock(side_effect=InsufficientActivityError("x"))):
        r = await admin_client.post(f"/api/v1/admin/students/{uuid.uuid4()}/ai-report")
        assert r.status_code == 422


@pytest.mark.asyncio
async def test_cohort_report_validates_bounds(admin_client):
    r = await admin_client.post(
        "/api/v1/admin/students/cohort/ai-report",
        json={"user_ids": [str(uuid.uuid4())]},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_cohort_report_success(admin_client):
    with patch("app.routers.admin_reports.student_report_service.generate_cohort_report",
               AsyncMock(return_value=_cohort())):
        ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        r = await admin_client.post(
            "/api/v1/admin/students/cohort/ai-report",
            json={"user_ids": ids},
        )
        assert r.status_code == 200, r.text
        assert r.json()["narrative"] == "ok"
