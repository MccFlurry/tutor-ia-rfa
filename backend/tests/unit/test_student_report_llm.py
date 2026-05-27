"""Tests for prompt builder + parser. LLM client itself is monkeypatched."""

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.schemas.admin_reports import (
    StudentDetail, ModuleProgress, QuizAttemptRow,
)
from app.services.student_report_service import (
    _build_report_prompt,
    _parse_report,
    LLMReportError,
)


def _detail() -> StudentDetail:
    return StudentDetail(
        user_id=uuid4(),
        full_name="Ana",
        email="a@x",
        created_at=datetime.now(timezone.utc),
        is_active=True,
        level="beginner",
        entry_score=45.0,
        level_history=[],
        overall_progress_pct=25.0,
        modules=[ModuleProgress(
            module_id=1, module_title="M1", topics_total=4,
            topics_completed=1, progress_pct=25.0, avg_quiz_score=0.6,
            avg_coding_score=None,
        )],
        recent_quizzes=[QuizAttemptRow(
            attempt_id=1, topic_id=1, topic_title="t",
            score=0.6, is_passed=True,
            attempted_at=datetime.now(timezone.utc),
        )],
        recent_coding=[],
        chat_messages_count=3,
        chat_last_at=None,
        achievements_earned=[],
        total_time_seconds=600,
        last_activity_at=datetime.now(timezone.utc),
    )


def test_prompt_contains_student_name_and_truncates():
    prompt = _build_report_prompt(_detail())
    assert "Ana" in prompt
    assert "beginner" in prompt
    assert len(prompt) <= 4000


def test_parse_report_accepts_wrapper_object():
    payload = {
        "report": {
            "summary": "resumen",
            "strengths": ["a"],
            "weaknesses": ["b"],
            "risk_level": "bajo",
            "risk_reason": "x",
            "interventions": ["c"],
        }
    }
    parsed = _parse_report(json.dumps(payload))
    assert parsed["summary"] == "resumen"
    assert parsed["risk_level"] == "bajo"


def test_parse_report_accepts_bare_object():
    payload = {
        "summary": "ok",
        "strengths": [],
        "weaknesses": [],
        "risk_level": "medio",
        "risk_reason": "ok",
        "interventions": [],
    }
    parsed = _parse_report(json.dumps(payload))
    assert parsed["risk_level"] == "medio"


def test_parse_report_normalizes_risk_level_casing():
    parsed = _parse_report(json.dumps({
        "summary": "x", "strengths": [], "weaknesses": [],
        "risk_level": "ALTO", "risk_reason": "x", "interventions": [],
    }))
    assert parsed["risk_level"] == "alto"


def test_parse_report_rejects_invalid_risk_level():
    with pytest.raises(LLMReportError):
        _parse_report(json.dumps({
            "summary": "x", "strengths": [], "weaknesses": [],
            "risk_level": "extreme", "risk_reason": "x", "interventions": [],
        }))


def test_parse_report_rejects_missing_field():
    with pytest.raises(LLMReportError):
        _parse_report(json.dumps({"summary": "x"}))


def test_parse_report_strips_markdown_fences():
    raw = "```json\n{\"summary\":\"x\",\"strengths\":[],\"weaknesses\":[],\"risk_level\":\"bajo\",\"risk_reason\":\"x\",\"interventions\":[]}\n```"
    parsed = _parse_report(raw)
    assert parsed["summary"] == "x"
