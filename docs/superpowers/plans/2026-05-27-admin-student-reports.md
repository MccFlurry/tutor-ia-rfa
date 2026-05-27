# Admin Student Reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an admin-only "Reportes" screen with a table of enrolled students, drill-down per-student detail page, AI-generated narrative reports (summary + risk + interventions) and AI cohort comparison, exportable to PDF via browser print.

**Architecture:** New FastAPI router `admin_reports.py` with a dedicated `student_report_service.py` that aggregates pedagogical metrics from existing tables (no migrations) and calls Ollama (`qwen2.5:7b-instruct-q4_K_M`) with `format="json"` for the narrative. Cache reports in Redis (1h TTL, key includes a `_detail_hash` so cache auto-invalidates on student progress). Frontend adds a new admin tab, a dedicated `/admin/students/:userId` route and a CSS `@media print` block.

**Tech Stack:** FastAPI · SQLAlchemy async · Pydantic v2 · langchain-ollama · redis.asyncio · React 18 · TanStack Query · Vitest + RTL · react-router-dom v6.

**Spec:** `docs/superpowers/specs/2026-05-27-admin-student-reports-design.md`

---

## File Structure

**Backend — create:**
- `backend/app/schemas/admin_reports.py` — Pydantic schemas (rows, detail, AI report).
- `backend/app/services/student_report_service.py` — aggregation + AI generation.
- `backend/app/routers/admin_reports.py` — 4 endpoints under `/admin/students`.
- `backend/tests/unit/test_student_report_service.py`
- `backend/tests/integration/test_router_admin_reports.py`

**Backend — modify:**
- `backend/app/services/llm_service.py` — add `generate_student_report_text` (reuses existing ChatOllama pattern).
- `backend/app/main.py` — `app.include_router(admin_reports.router, prefix="/api/v1")`.
- `docs/matriz-trazabilidad-ISO25010.md` — append 4 new RF rows.

**Frontend — create:**
- `frontend/src/types/adminReports.ts`
- `frontend/src/api/adminReports.ts`
- `frontend/src/components/admin/StudentsReportTab.tsx`
- `frontend/src/components/admin/StudentsReportTab.test.tsx`
- `frontend/src/components/admin/CohortReportModal.tsx`
- `frontend/src/components/admin/CohortReportModal.test.tsx`
- `frontend/src/pages/AdminStudentReportPage.tsx`
- `frontend/src/pages/AdminStudentReportPage.test.tsx`

**Frontend — modify:**
- `frontend/src/pages/AdminPage.tsx` — add "Reportes" tab.
- `frontend/src/App.tsx` (or router file) — register `/admin/students/:userId`.
- `frontend/src/index.css` — add `@media print` block.

---

## Branch

Create one branch for the whole feature: `feat/admin-student-reports`.

```bash
git checkout -b feat/admin-student-reports
```

---

## Task 1: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/admin_reports.py`
- Test: `backend/tests/unit/test_admin_reports_schemas.py`

- [ ] **Step 1.1: Write the failing test**

Create `backend/tests/unit/test_admin_reports_schemas.py`:

```python
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
```

- [ ] **Step 1.2: Verify the test fails**

Run from `backend/`:

```bash
pytest tests/unit/test_admin_reports_schemas.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.schemas.admin_reports'`.

- [ ] **Step 1.3: Implement the schemas**

Create `backend/app/schemas/admin_reports.py`:

```python
"""Pydantic schemas for /admin/students endpoints (student reports + cohort)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StudentRow(BaseModel):
    """One row in the admin reports table."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    full_name: str
    email: str
    level: str | None = None
    entry_score: float | None = None
    overall_progress_pct: float
    avg_quiz_score: float | None = None
    avg_coding_score: float | None = None
    last_activity_at: datetime | None = None
    last_location: str | None = None
    is_active: bool


class ModuleProgress(BaseModel):
    module_id: int
    module_title: str
    topics_total: int
    topics_completed: int
    progress_pct: float
    avg_quiz_score: float | None = None
    avg_coding_score: float | None = None


class QuizAttemptRow(BaseModel):
    attempt_id: int
    topic_id: int
    topic_title: str
    score: float
    is_passed: bool
    attempted_at: datetime


class CodingSubmissionRow(BaseModel):
    submission_id: int
    challenge_id: int
    challenge_title: str
    score: float
    submitted_at: datetime


class AchievementRow(BaseModel):
    achievement_id: int
    name: str
    badge_emoji: str
    earned_at: datetime


class LevelHistoryEntry(BaseModel):
    level: str
    score: float
    changed_at: datetime
    reason: str | None = None


class StudentDetail(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    created_at: datetime
    is_active: bool
    level: str | None = None
    entry_score: float | None = None
    level_history: list[LevelHistoryEntry] = Field(default_factory=list)
    overall_progress_pct: float
    modules: list[ModuleProgress] = Field(default_factory=list)
    recent_quizzes: list[QuizAttemptRow] = Field(default_factory=list, max_length=10)
    recent_coding: list[CodingSubmissionRow] = Field(default_factory=list, max_length=10)
    chat_messages_count: int
    chat_last_at: datetime | None = None
    achievements_earned: list[AchievementRow] = Field(default_factory=list)
    total_time_seconds: int
    last_activity_at: datetime | None = None
    last_location: str | None = None


class AIReport(BaseModel):
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    risk_level: str  # bajo | medio | alto
    risk_reason: str
    interventions: list[str]
    generated_at: datetime
    cached: bool


class CohortReportRequest(BaseModel):
    user_ids: list[UUID] = Field(min_length=2, max_length=15)


class CohortAIReport(BaseModel):
    narrative: str
    top_performers: list[str]
    needs_support: list[str]
    common_gaps: list[str]
    recommendations: list[str]
    generated_at: datetime
    cached: bool
```

- [ ] **Step 1.4: Verify tests pass**

```bash
pytest tests/unit/test_admin_reports_schemas.py -v
```

Expected: 4 passed.

- [ ] **Step 1.5: Commit**

```bash
git add backend/app/schemas/admin_reports.py backend/tests/unit/test_admin_reports_schemas.py
git commit -m "feat(admin-reports): add Pydantic schemas for student reports"
```

---

## Task 2: Service Helpers (exceptions, hash, redis wrappers)

**Files:**
- Create: `backend/app/services/student_report_service.py` (stub with helpers only)
- Test: `backend/tests/unit/test_student_report_helpers.py`

- [ ] **Step 2.1: Write the failing tests**

Create `backend/tests/unit/test_student_report_helpers.py`:

```python
"""Tests for helper functions in student_report_service: hash, activity gate, redis wrappers."""

import asyncio
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
```

- [ ] **Step 2.2: Verify the tests fail**

```bash
pytest tests/unit/test_student_report_helpers.py -v
```

Expected: ImportError (module doesn't exist).

- [ ] **Step 2.3: Implement helpers**

Create `backend/app/services/student_report_service.py`:

```python
"""student_report_service — aggregations + AI narrative for the admin reports screen.

This file only contains helpers in Task 2; aggregation and AI calls are added in
Tasks 3-7.
"""

import hashlib
import json

from app.schemas.admin_reports import StudentDetail
from app.utils.logger import logger


class InsufficientActivityError(Exception):
    """Raised when a student has no quiz/coding activity yet."""
    pass


class LLMReportError(Exception):
    """Raised when the LLM cannot produce a valid report after retry."""
    pass


def _has_minimum_activity(detail: StudentDetail) -> bool:
    """A student qualifies for an AI report once they've completed at least one
    quiz attempt or one coding submission. Pure progress without graded work is
    not enough signal for the LLM."""
    return bool(detail.recent_quizzes) or bool(detail.recent_coding)


def _detail_hash(detail: StudentDetail) -> str:
    """Stable sha256 over volatile fields. Changes whenever the student advances
    so the Redis cache key auto-invalidates."""
    payload = {
        "progress_pct": round(detail.overall_progress_pct, 2),
        "quiz_count": len(detail.recent_quizzes),
        "last_quiz_score": detail.recent_quizzes[0].score if detail.recent_quizzes else None,
        "coding_count": len(detail.recent_coding),
        "last_coding_score": detail.recent_coding[0].score if detail.recent_coding else None,
        "chat_count": detail.chat_messages_count,
        "last_activity": detail.last_activity_at.isoformat() if detail.last_activity_at else None,
        "level": detail.level,
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


async def _safe_redis_get(redis_client, key: str) -> str | None:
    """Redis GET with degraded mode — swallows exceptions and returns None."""
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.warning(f"[student_report] Redis GET falló para {key}: {e}")
        return None


async def _safe_redis_setex(redis_client, key: str, ttl: int, value: str) -> None:
    """Redis SETEX with degraded mode — swallows exceptions."""
    try:
        await redis_client.setex(key, ttl, value)
    except Exception as e:
        logger.warning(f"[student_report] Redis SETEX falló para {key}: {e}")
```

- [ ] **Step 2.4: Verify tests pass**

```bash
pytest tests/unit/test_student_report_helpers.py -v
```

Expected: 7 passed.

- [ ] **Step 2.5: Commit**

```bash
git add backend/app/services/student_report_service.py backend/tests/unit/test_student_report_helpers.py
git commit -m "feat(admin-reports): add service helpers (hash, activity gate, redis wrappers)"
```

---

## Task 3: `get_students_overview`

**Files:**
- Modify: `backend/app/services/student_report_service.py`
- Test: `backend/tests/unit/test_student_report_overview.py`

- [ ] **Step 3.1: Write the failing test**

Create `backend/tests/unit/test_student_report_overview.py`:

```python
"""Unit tests for get_students_overview aggregator.

The query is mocked at result level — we assert that the function transforms
joined rows into StudentRow correctly. Real PostgreSQL is exercised by the
integration tests in Task 8.
"""

import uuid
from datetime import datetime, timedelta, timezone
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


def _agg(progress=0.0, avg_quiz=None, avg_coding=None, last_at=None, last_topic_title=None):
    return SimpleNamespace(
        overall_progress_pct=progress,
        avg_quiz_score=avg_quiz,
        avg_coding_score=avg_coding,
        last_activity_at=last_at,
        last_location=last_topic_title,
    )


@pytest.mark.asyncio
async def test_overview_maps_joined_rows_to_student_rows():
    u1 = _user(full_name="Ana")
    u2 = _user(full_name="Bruno")
    rows = [
        (u1, _level(), _agg(progress=50.0, avg_quiz=0.8, last_topic_title="M1 - Intro")),
        (u2, None, _agg(progress=0.0)),
    ]

    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=rows)))

    result = await get_students_overview(db)

    assert len(result) == 2
    assert result[0].full_name == "Ana"
    assert result[0].level == "beginner"
    assert result[0].overall_progress_pct == 50.0
    assert result[0].last_location == "M1 - Intro"
    assert result[1].level is None
    assert result[1].avg_quiz_score is None


@pytest.mark.asyncio
async def test_overview_excludes_non_students():
    """Admin users must never appear in the report table."""
    admin = _user(role="admin", full_name="Root")
    student = _user(full_name="Ana")
    # The function builds the WHERE clause; with role filter applied the mock
    # only returns the student row.
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock(
        all=MagicMock(return_value=[(student, None, _agg())])
    ))
    result = await get_students_overview(db)
    assert len(result) == 1
    assert result[0].full_name == "Ana"
```

- [ ] **Step 3.2: Verify the test fails**

```bash
pytest tests/unit/test_student_report_overview.py -v
```

Expected: `ImportError: cannot import name 'get_students_overview'`.

- [ ] **Step 3.3: Implement `get_students_overview`**

Append to `backend/app/services/student_report_service.py`:

```python
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_level import UserLevel
from app.models.module import Module
from app.models.topic import Topic
from app.models.progress import UserTopicProgress
from app.models.quiz import QuizAttempt
from app.models.coding import CodingSubmission
from app.models.chat import ChatMessage
from app.schemas.admin_reports import StudentRow


async def get_students_overview(db: AsyncSession) -> list[StudentRow]:
    """Build the admin reports table in a single query with subqueries.

    Aggregations:
      - overall_progress_pct = completed topics / total topics * 100
      - avg_quiz_score       = AVG(quiz_attempts.score) across user
      - avg_coding_score     = AVG(coding_submissions.score)
      - last_activity_at     = MAX over (progress, quiz, coding, chat) timestamps
      - last_location        = title of the topic touched in last_activity_at,
                               or "Chat IA" when chat is the most recent event.
    """

    # 1. Aggregations subquery — one row per student.
    topics_total_sq = select(func.count(Topic.id)).where(Topic.is_active.is_(True)).scalar_subquery()

    completed_sq = (
        select(func.count(UserTopicProgress.topic_id))
        .where(
            UserTopicProgress.user_id == User.id,
            UserTopicProgress.is_completed.is_(True),
        )
        .correlate(User)
        .scalar_subquery()
    )

    avg_quiz_sq = (
        select(func.avg(QuizAttempt.score))
        .where(QuizAttempt.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    avg_coding_sq = (
        select(func.avg(CodingSubmission.score))
        .where(CodingSubmission.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    last_progress_sq = (
        select(func.max(UserTopicProgress.last_accessed_at))
        .where(UserTopicProgress.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    last_quiz_sq = (
        select(func.max(QuizAttempt.attempted_at))
        .where(QuizAttempt.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    last_coding_sq = (
        select(func.max(CodingSubmission.submitted_at))
        .where(CodingSubmission.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    last_chat_sq = (
        select(func.max(ChatMessage.created_at))
        .where(ChatMessage.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    # Build the rows. last_location resolution is done in a second pass over the
    # results to keep the SQL readable; piloto = 10-15 estudiantes, so N+1 risk
    # is bounded and outweighed by clarity.
    overall_progress_expr = (
        func.coalesce(completed_sq, 0).cast_to(func.Float())  # noqa
        # Compose progress_pct as 100.0 * completed / NULLIF(total, 0) to avoid
        # division-by-zero when no topics exist yet.
    )

    query = (
        select(
            User,
            UserLevel,
            completed_sq.label("completed"),
            topics_total_sq.label("topics_total"),
            avg_quiz_sq.label("avg_quiz"),
            avg_coding_sq.label("avg_coding"),
            last_progress_sq.label("last_progress"),
            last_quiz_sq.label("last_quiz"),
            last_coding_sq.label("last_coding"),
            last_chat_sq.label("last_chat"),
        )
        .outerjoin(UserLevel, UserLevel.user_id == User.id)
        .where(User.role == "student")
        .order_by(User.full_name)
    )

    result = await db.execute(query)
    rows = result.all()

    # Batch-resolve last_location by fetching the topic title for each user's
    # most-recent topic_id. One extra query, total.
    user_ids = [r[0].id for r in rows]
    topic_title_by_user: dict = {}
    if user_ids:
        topic_q = (
            select(UserTopicProgress.user_id, Module.title, Topic.title)
            .join(Topic, Topic.id == UserTopicProgress.topic_id)
            .join(Module, Module.id == Topic.module_id)
            .where(UserTopicProgress.user_id.in_(user_ids))
            .order_by(UserTopicProgress.last_accessed_at.desc())
        )
        topic_rows = (await db.execute(topic_q)).all()
        for uid, module_title, topic_title in topic_rows:
            topic_title_by_user.setdefault(uid, f"{module_title} - {topic_title}")

    out: list[StudentRow] = []
    for user, lvl, completed, total, avg_quiz, avg_coding, lp, lq, lc, lch in rows:
        # Determine last activity timestamp + label.
        candidates = [
            (lp, topic_title_by_user.get(user.id)),
            (lq, "Quiz"),
            (lc, "Desafío de código"),
            (lch, "Chat IA"),
        ]
        candidates = [(t, label) for t, label in candidates if t is not None]
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            last_at, last_label = candidates[0]
        else:
            last_at, last_label = None, None

        progress_pct = 0.0
        if total and total > 0 and completed is not None:
            progress_pct = round((completed / total) * 100.0, 2)

        out.append(StudentRow(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            level=lvl.level if lvl else None,
            entry_score=lvl.entry_score if lvl else None,
            overall_progress_pct=progress_pct,
            avg_quiz_score=float(avg_quiz) if avg_quiz is not None else None,
            avg_coding_score=float(avg_coding) if avg_coding is not None else None,
            last_activity_at=last_at,
            last_location=last_label,
            is_active=user.is_active,
        ))
    return out
```

> **Note:** The first call's `result.all()` returns 10 columns; the mock in the test simplifies to a 3-tuple `(user, level, agg)` for readability. If the test breaks because of the column count mismatch, adapt the mock to return tuples of `(user, level, completed, total, avg_quiz, avg_coding, lp, lq, lc, lch)` — see Step 3.4.

- [ ] **Step 3.4: Adjust test to match real tuple shape**

Replace `_agg` and the row builders in `test_student_report_overview.py` so each row is a 10-tuple:

```python
def _row(user, level, *, progress=0.0, avg_quiz=None, avg_coding=None,
         last_at=None, last_topic_title=None):
    # completed/total computed to give the asked-for progress_pct
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
    # First execute → main query; second execute → batch topic_title query.
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
```

- [ ] **Step 3.5: Verify tests pass**

```bash
pytest tests/unit/test_student_report_overview.py -v
```

Expected: 2 passed.

- [ ] **Step 3.6: Commit**

```bash
git add backend/app/services/student_report_service.py backend/tests/unit/test_student_report_overview.py
git commit -m "feat(admin-reports): aggregate students overview for table view"
```

---

## Task 4: `get_student_detail`

**Files:**
- Modify: `backend/app/services/student_report_service.py`
- Test: `backend/tests/unit/test_student_report_detail.py`

- [ ] **Step 4.1: Write the failing test**

Create `backend/tests/unit/test_student_report_detail.py`:

```python
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
    # 1) user+level
    # 2) modules + per-module progress (returns list of named tuples)
    # 3) recent quizzes
    # 4) recent coding
    # 5) chat counts
    # 6) achievements
    # 7) total time

    module_row = (
        SimpleNamespace(id=1, title="M1"),
        2,   # topics_completed
        4,   # topics_total
        0.8, # avg_quiz
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
```

- [ ] **Step 4.2: Verify the test fails**

```bash
pytest tests/unit/test_student_report_detail.py -v
```

Expected: ImportError or AttributeError (function missing).

- [ ] **Step 4.3: Implement `get_student_detail`**

Append to `backend/app/services/student_report_service.py`:

```python
from uuid import UUID

from app.models.achievement import Achievement, UserAchievement
from app.schemas.admin_reports import (
    StudentDetail,
    ModuleProgress,
    QuizAttemptRow,
    CodingSubmissionRow,
    AchievementRow,
    LevelHistoryEntry,
)


async def get_student_detail(db: AsyncSession, user_id: UUID) -> StudentDetail:
    """Return everything we know about a student for the detail page.

    Raises LookupError if the user does not exist or is not a student. The
    router maps this to 404.
    """

    # 1) user + level
    row = (
        await db.execute(
            select(User, UserLevel)
            .outerjoin(UserLevel, UserLevel.user_id == User.id)
            .where(User.id == user_id, User.role == "student")
        )
    ).first()
    if row is None:
        raise LookupError("student_not_found")
    user, lvl = row

    # 2) modules + per-module progress
    module_q = (
        select(
            Module,
            func.count(UserTopicProgress.topic_id).filter(
                UserTopicProgress.is_completed.is_(True),
                UserTopicProgress.user_id == user_id,
            ).label("completed"),
            func.count(Topic.id).label("topics_total"),
            func.avg(QuizAttempt.score).filter(QuizAttempt.user_id == user_id).label("avg_quiz"),
            func.avg(CodingSubmission.score).filter(CodingSubmission.user_id == user_id).label("avg_coding"),
        )
        .join(Topic, Topic.module_id == Module.id)
        .outerjoin(UserTopicProgress, and_(
            UserTopicProgress.topic_id == Topic.id,
            UserTopicProgress.user_id == user_id,
        ))
        .outerjoin(QuizAttempt, and_(
            QuizAttempt.topic_id == Topic.id,
            QuizAttempt.user_id == user_id,
        ))
        .group_by(Module.id)
        .order_by(Module.order_index)
    )
    module_rows = (await db.execute(module_q)).all()

    modules: list[ModuleProgress] = []
    for mod, completed, total, avg_q, avg_c in module_rows:
        pct = round((completed / total) * 100.0, 2) if total else 0.0
        modules.append(ModuleProgress(
            module_id=mod.id,
            module_title=mod.title,
            topics_total=total or 0,
            topics_completed=completed or 0,
            progress_pct=pct,
            avg_quiz_score=float(avg_q) if avg_q is not None else None,
            avg_coding_score=float(avg_c) if avg_c is not None else None,
        ))

    # 3) recent quizzes (last 10)
    quiz_q = (
        select(QuizAttempt, Topic.title)
        .join(Topic, Topic.id == QuizAttempt.topic_id)
        .where(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(10)
    )
    quizzes = [
        QuizAttemptRow(
            attempt_id=q.id,
            topic_id=q.topic_id,
            topic_title=t_title,
            score=q.score,
            is_passed=q.is_passed,
            attempted_at=q.attempted_at,
        )
        for q, t_title in (await db.execute(quiz_q)).all()
    ]

    # 4) recent coding (last 10)
    from app.models.coding import CodingChallenge

    coding_q = (
        select(CodingSubmission, CodingChallenge.title)
        .join(CodingChallenge, CodingChallenge.id == CodingSubmission.challenge_id)
        .where(CodingSubmission.user_id == user_id)
        .order_by(CodingSubmission.submitted_at.desc())
        .limit(10)
    )
    coding = [
        CodingSubmissionRow(
            submission_id=s.id,
            challenge_id=s.challenge_id,
            challenge_title=c_title,
            score=s.score,
            submitted_at=s.submitted_at,
        )
        for s, c_title in (await db.execute(coding_q)).all()
    ]

    # 5) chat counts
    chat_count, chat_last = (
        await db.execute(
            select(func.count(ChatMessage.id), func.max(ChatMessage.created_at))
            .where(ChatMessage.user_id == user_id, ChatMessage.role == "user")
        )
    ).first() or (0, None)

    # 6) achievements
    ach_q = (
        select(Achievement, UserAchievement.earned_at)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .where(UserAchievement.user_id == user_id)
        .order_by(UserAchievement.earned_at.desc())
    )
    achievements = [
        AchievementRow(
            achievement_id=a.id,
            name=a.name,
            badge_emoji=a.badge_emoji,
            earned_at=earned,
        )
        for a, earned in (await db.execute(ach_q)).all()
    ]

    # 7) total time
    total_time = (
        await db.execute(
            select(func.coalesce(func.sum(UserTopicProgress.time_spent_seconds), 0))
            .where(UserTopicProgress.user_id == user_id)
        )
    ).scalar() or 0

    # Reuse the same last-activity selection logic as the overview.
    last_at = max(
        (x for x in [
            chat_last,
            quizzes[0].attempted_at if quizzes else None,
            coding[0].submitted_at if coding else None,
        ] if x is not None),
        default=None,
    )

    # Build level history from JSONB
    history: list[LevelHistoryEntry] = []
    if lvl and lvl.history:
        for entry in lvl.history:
            try:
                history.append(LevelHistoryEntry(**entry))
            except Exception:
                # Ignore malformed historical entries — they're informational.
                continue

    overall_pct = (
        round(sum(m.progress_pct * m.topics_total for m in modules)
              / sum(m.topics_total for m in modules), 2)
        if modules and sum(m.topics_total for m in modules) > 0
        else 0.0
    )

    return StudentDetail(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        created_at=user.created_at,
        is_active=user.is_active,
        level=lvl.level if lvl else None,
        entry_score=lvl.entry_score if lvl else None,
        level_history=history,
        overall_progress_pct=overall_pct,
        modules=modules,
        recent_quizzes=quizzes,
        recent_coding=coding,
        chat_messages_count=chat_count or 0,
        chat_last_at=chat_last,
        achievements_earned=achievements,
        total_time_seconds=int(total_time),
        last_activity_at=last_at,
        last_location=None,  # detail page surfaces this from the table query if needed
    )
```

- [ ] **Step 4.4: Verify tests pass**

```bash
pytest tests/unit/test_student_report_detail.py -v
```

Expected: 2 passed.

- [ ] **Step 4.5: Commit**

```bash
git add backend/app/services/student_report_service.py backend/tests/unit/test_student_report_detail.py
git commit -m "feat(admin-reports): aggregate per-student detail for drill-down page"
```

---

## Task 5: LLM Bridge + Prompt + Parser

**Files:**
- Modify: `backend/app/services/llm_service.py` (add `generate_student_report_text`)
- Modify: `backend/app/services/student_report_service.py` (add `_build_report_prompt`, `_parse_report`)
- Test: `backend/tests/unit/test_student_report_llm.py`

- [ ] **Step 5.1: Write the failing test**

Create `backend/tests/unit/test_student_report_llm.py`:

```python
"""Tests for prompt builder + parser. LLM client itself is monkeypatched."""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
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
    assert len(prompt) <= 4000  # leaves headroom under context window


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
```

- [ ] **Step 5.2: Verify the test fails**

```bash
pytest tests/unit/test_student_report_llm.py -v
```

Expected: ImportError on `_build_report_prompt`.

- [ ] **Step 5.3: Add LLM bridge function**

Append to `backend/app/services/llm_service.py`:

```python
async def generate_student_report_text(
    system_prompt: str, user_prompt: str, *, temperature: float = 0.3,
) -> str:
    """Single-shot ChatOllama call returning raw JSON text. Used by
    student_report_service for individual and cohort narrative reports."""

    try:
        llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=temperature,
            num_ctx=8192,
            num_predict=1500,
            format="json",
            timeout=settings.OLLAMA_TIMEOUT,
        )
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        return response.content
    except Exception as e:
        logger.error(f"Error en LLM (student report): {e}")
        raise
```

- [ ] **Step 5.4: Add prompt + parser to student_report_service**

Append to `backend/app/services/student_report_service.py`:

```python
import re
from datetime import datetime, timezone


REPORT_SYSTEM_PROMPT = """Eres un tutor pedagógico evaluador del curso de Aplicaciones Móviles \
(Android/Kotlin) del IESTP República Federal de Alemania (RFA), Chiclayo. Tu rol es analizar \
el desempeño de un estudiante y entregar un reporte breve y accionable.

REGLAS ESTRICTAS:
1. Responde ÚNICAMENTE con un objeto JSON válido (sin texto extra, sin markdown fences).
2. Estructura EXACTA del objeto:
{
  "report": {
    "summary": "Resumen narrativo de 3 a 4 párrafos en español peruano.",
    "strengths": ["máximo 4 ítems"],
    "weaknesses": ["máximo 4 ítems"],
    "risk_level": "bajo" | "medio" | "alto",
    "risk_reason": "Una oración explicando el riesgo.",
    "interventions": ["máximo 5 acciones concretas para el docente"]
  }
}
3. Basa toda inferencia en los datos provistos. No inventes eventos ni números.
4. Si la evidencia es insuficiente para concluir, indícalo en risk_reason.
5. risk_level "alto" requiere: progreso <30% Y promedio quiz <0.5, o más de 14 días sin actividad."""


def _build_report_prompt(detail: StudentDetail) -> str:
    """Compact serialization of the student detail (kept under 3 500 chars)."""

    modules_lines = "\n".join(
        f"  - {m.module_title}: {m.progress_pct}% completado, "
        f"quiz={m.avg_quiz_score if m.avg_quiz_score is not None else 'n/a'}, "
        f"coding={m.avg_coding_score if m.avg_coding_score is not None else 'n/a'}"
        for m in detail.modules
    )
    last_quizzes = "\n".join(
        f"  - {q.topic_title}: {q.score:.2f} ({'aprobado' if q.is_passed else 'no aprobado'})"
        for q in detail.recent_quizzes[:5]
    )
    last_coding = "\n".join(
        f"  - {c.challenge_title}: {c.score:.0f}/100"
        for c in detail.recent_coding[:5]
    )
    last_activity = (
        detail.last_activity_at.astimezone(timezone.utc).isoformat()
        if detail.last_activity_at else "sin registros"
    )

    user_block = f"""DATOS DEL ESTUDIANTE
- Nombre: {detail.full_name}
- Nivel actual: {detail.level or 'sin asignar'}
- Puntaje de entrada: {detail.entry_score if detail.entry_score is not None else 'n/a'}
- Progreso global: {detail.overall_progress_pct}%
- Tiempo total invertido: {detail.total_time_seconds // 60} minutos
- Logros desbloqueados: {len(detail.achievements_earned)}
- Mensajes de chat al tutor IA: {detail.chat_messages_count}
- Última actividad: {last_activity}

PROGRESO POR MÓDULO
{modules_lines or '  (sin módulos)'}

ÚLTIMOS QUIZZES
{last_quizzes or '  (sin intentos)'}

ÚLTIMOS DESAFÍOS DE CÓDIGO
{last_coding or '  (sin entregas)'}

INSTRUCCIONES
Analiza estos datos y devuelve el reporte JSON solicitado."""

    if len(user_block) > 3500:
        user_block = user_block[:3500] + "\n[...truncado]"
    return user_block


_VALID_RISKS = {"bajo", "medio", "alto"}
_REQUIRED_KEYS = {"summary", "strengths", "weaknesses", "risk_level", "risk_reason", "interventions"}


def _parse_report(raw: str) -> dict:
    """Strict parser for the LLM JSON object. Tolerates `{"report": {...}}`
    wrapper and markdown code fences."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMReportError(f"JSON inválido del LLM: {e}")

    if isinstance(data, dict) and "report" in data and isinstance(data["report"], dict):
        data = data["report"]
    if not isinstance(data, dict):
        raise LLMReportError("La respuesta del LLM no es un objeto")

    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        raise LLMReportError(f"Faltan campos en el reporte LLM: {sorted(missing)}")

    risk = str(data["risk_level"]).strip().lower()
    if risk not in _VALID_RISKS:
        raise LLMReportError(f"risk_level inválido: {data['risk_level']!r}")
    data["risk_level"] = risk

    # Defensive coercions
    for key in ("strengths", "weaknesses", "interventions"):
        if not isinstance(data[key], list):
            raise LLMReportError(f"{key} debe ser lista")
        data[key] = [str(x).strip() for x in data[key] if str(x).strip()]

    data["summary"] = str(data["summary"]).strip()
    data["risk_reason"] = str(data["risk_reason"]).strip()
    return data
```

- [ ] **Step 5.5: Verify tests pass**

```bash
pytest tests/unit/test_student_report_llm.py -v
```

Expected: 7 passed.

- [ ] **Step 5.6: Commit**

```bash
git add backend/app/services/llm_service.py backend/app/services/student_report_service.py backend/tests/unit/test_student_report_llm.py
git commit -m "feat(admin-reports): add LLM bridge + prompt + JSON parser"
```

---

## Task 6: `generate_ai_report` (cache + retry + activity gate)

**Files:**
- Modify: `backend/app/services/student_report_service.py`
- Test: `backend/tests/unit/test_student_report_generate.py`

- [ ] **Step 6.1: Write the failing tests**

Create `backend/tests/unit/test_student_report_generate.py`:

```python
"""End-to-end unit test for generate_ai_report.

`get_student_detail` and `llm_service.generate_student_report_text` are
monkeypatched.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
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
    # SETEX TTL must be 3600
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
```

- [ ] **Step 6.2: Verify the tests fail**

```bash
pytest tests/unit/test_student_report_generate.py -v
```

Expected: ImportError on `generate_ai_report`.

- [ ] **Step 6.3: Implement `generate_ai_report`**

Append to `backend/app/services/student_report_service.py`:

```python
from app.services import llm_service  # at module top — move if already imported


async def generate_ai_report(db: AsyncSession, redis_client, user_id: UUID):
    """Generate (or fetch cached) AI narrative report for a single student."""
    from app.schemas.admin_reports import AIReport  # local to avoid circular

    detail = await get_student_detail(db, user_id)
    if not _has_minimum_activity(detail):
        raise InsufficientActivityError(
            "Sin actividad suficiente. Esperar primer quiz."
        )

    key = f"student_report:{user_id}:{_detail_hash(detail)}"

    cached_raw = await _safe_redis_get(redis_client, key)
    if cached_raw:
        try:
            payload = json.loads(cached_raw)
            return AIReport(**payload, cached=True)
        except Exception as e:
            logger.warning(f"[student_report] cache corrupto para {key}: {e}")

    system_prompt = REPORT_SYSTEM_PROMPT
    user_prompt = _build_report_prompt(detail)

    try:
        raw = await llm_service.generate_student_report_text(
            system_prompt, user_prompt, temperature=0.3,
        )
        parsed = _parse_report(raw)
    except (LLMReportError, json.JSONDecodeError):
        # Single retry with lower temperature for determinism.
        try:
            raw = await llm_service.generate_student_report_text(
                system_prompt, user_prompt, temperature=0.1,
            )
            parsed = _parse_report(raw)
        except (LLMReportError, json.JSONDecodeError) as e:
            logger.error(f"LLM falló tras reintento para {user_id}: {e}")
            raise LLMReportError("LLM no produjo JSON válido tras reintento") from e
    except Exception as e:
        logger.error(f"Error de Ollama generando reporte para {user_id}: {e}")
        raise LLMReportError(f"Ollama indisponible: {e}") from e

    parsed["generated_at"] = datetime.now(timezone.utc).isoformat()
    await _safe_redis_setex(redis_client, key, 3600, json.dumps(parsed))
    return AIReport(**parsed, cached=False)
```

- [ ] **Step 6.4: Verify tests pass**

```bash
pytest tests/unit/test_student_report_generate.py -v
```

Expected: 5 passed.

- [ ] **Step 6.5: Commit**

```bash
git add backend/app/services/student_report_service.py backend/tests/unit/test_student_report_generate.py
git commit -m "feat(admin-reports): generate AI report with cache + retry + activity gate"
```

---

## Task 7: `generate_cohort_report`

**Files:**
- Modify: `backend/app/services/student_report_service.py`
- Test: `backend/tests/unit/test_student_report_cohort.py`

- [ ] **Step 7.1: Write the failing tests**

Create `backend/tests/unit/test_student_report_cohort.py`:

```python
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

    # Ask for two valid IDs + one unknown — unknown is silently dropped.
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
```

- [ ] **Step 7.2: Verify the tests fail**

```bash
pytest tests/unit/test_student_report_cohort.py -v
```

Expected: ImportError on `generate_cohort_report`.

- [ ] **Step 7.3: Implement `generate_cohort_report`**

Append to `backend/app/services/student_report_service.py`:

```python
COHORT_SYSTEM_PROMPT = """Eres un tutor pedagógico evaluador del curso de Aplicaciones Móviles \
del IESTP RFA. Te entrego datos resumidos de varios estudiantes y debes producir un reporte \
COMPARATIVO de la cohorte.

REGLAS ESTRICTAS:
1. Responde ÚNICAMENTE con JSON con esta estructura exacta:
{
  "narrative": "Análisis comparativo del grupo (2-3 párrafos).",
  "top_performers": ["nombres completos de los que destacan"],
  "needs_support": ["nombres completos de los que requieren apoyo"],
  "common_gaps": ["patrones comunes detectados"],
  "recommendations": ["acciones grupales para el docente"]
}
2. Basa todo en los datos. No inventes nombres ni números.
3. Español peruano, tono profesional."""


_COHORT_REQUIRED = {"narrative", "top_performers", "needs_support", "common_gaps", "recommendations"}


def _parse_cohort(raw: str) -> dict:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMReportError(f"JSON inválido del LLM (cohort): {e}")
    if not isinstance(data, dict):
        raise LLMReportError("Respuesta cohort no es objeto")
    missing = _COHORT_REQUIRED - set(data.keys())
    if missing:
        raise LLMReportError(f"Faltan campos cohort: {sorted(missing)}")
    for k in ("top_performers", "needs_support", "common_gaps", "recommendations"):
        if not isinstance(data[k], list):
            raise LLMReportError(f"{k} debe ser lista")
        data[k] = [str(x).strip() for x in data[k] if str(x).strip()]
    data["narrative"] = str(data["narrative"]).strip()
    return data


def _cohort_cache_key(ids: list[UUID]) -> str:
    sorted_ids = sorted(str(i) for i in ids)
    raw = json.dumps(sorted_ids).encode("utf-8")
    return "cohort_report:" + hashlib.sha256(raw).hexdigest()[:16]


def _build_cohort_prompt(rows: list[StudentRow]) -> str:
    lines = []
    for r in rows:
        lines.append(
            f"- {r.full_name} (nivel {r.level or 'sin asignar'}): "
            f"progreso {r.overall_progress_pct}%, "
            f"quiz {r.avg_quiz_score if r.avg_quiz_score is not None else 'n/a'}, "
            f"coding {r.avg_coding_score if r.avg_coding_score is not None else 'n/a'}"
        )
    block = "DATOS DE LA COHORTE\n" + "\n".join(lines) + "\n\nGenera el reporte comparativo."
    return block[:3500]


async def generate_cohort_report(db: AsyncSession, redis_client, user_ids: list[UUID]):
    from app.schemas.admin_reports import CohortAIReport

    if len(user_ids) < 2 or len(user_ids) > 15:
        raise ValueError("Selecciona entre 2 y 15 estudiantes")

    overview = await get_students_overview(db)
    by_id = {r.user_id: r for r in overview}
    rows = [by_id[uid] for uid in user_ids if uid in by_id]
    if len(rows) < 2:
        raise ValueError("Se necesitan al menos 2 estudiantes válidos en la lista")

    key = _cohort_cache_key([r.user_id for r in rows])
    cached_raw = await _safe_redis_get(redis_client, key)
    if cached_raw:
        try:
            payload = json.loads(cached_raw)
            return CohortAIReport(**payload, cached=True)
        except Exception as e:
            logger.warning(f"[student_report] cohort cache corrupto: {e}")

    prompt = _build_cohort_prompt(rows)
    try:
        raw = await llm_service.generate_student_report_text(
            COHORT_SYSTEM_PROMPT, prompt, temperature=0.3,
        )
        parsed = _parse_cohort(raw)
    except (LLMReportError, json.JSONDecodeError):
        try:
            raw = await llm_service.generate_student_report_text(
                COHORT_SYSTEM_PROMPT, prompt, temperature=0.1,
            )
            parsed = _parse_cohort(raw)
        except (LLMReportError, json.JSONDecodeError) as e:
            raise LLMReportError("LLM no produjo cohort JSON válido") from e
    except Exception as e:
        raise LLMReportError(f"Ollama indisponible: {e}") from e

    parsed["generated_at"] = datetime.now(timezone.utc).isoformat()
    await _safe_redis_setex(redis_client, key, 3600, json.dumps(parsed))
    return CohortAIReport(**parsed, cached=False)
```

- [ ] **Step 7.4: Verify tests pass**

```bash
pytest tests/unit/test_student_report_cohort.py -v
```

Expected: 3 passed.

- [ ] **Step 7.5: Commit**

```bash
git add backend/app/services/student_report_service.py backend/tests/unit/test_student_report_cohort.py
git commit -m "feat(admin-reports): cohort AI comparative report with cache"
```

---

## Task 8: Router + Integration Tests

**Files:**
- Create: `backend/app/routers/admin_reports.py`
- Create: `backend/tests/integration/test_router_admin_reports.py`
- Modify: `backend/app/main.py`

- [ ] **Step 8.1: Write the failing integration tests**

Create `backend/tests/integration/test_router_admin_reports.py`:

```python
"""Integration tests for /api/v1/admin/students/* — covers auth, happy path,
error mapping, and that the service is correctly wired into the router."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.admin_reports import (
    StudentRow, StudentDetail, AIReport, CohortAIReport,
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
    assert r.status_code == 422  # Pydantic validation < 2 elements


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
```

- [ ] **Step 8.2: Verify tests fail**

```bash
pytest tests/integration/test_router_admin_reports.py -v
```

Expected: 404s or import errors (router not registered yet).

- [ ] **Step 8.3: Implement the router**

Create `backend/app/routers/admin_reports.py`:

```python
"""routers/admin_reports.py — /admin/students/* endpoints for pedagogical reports."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin, get_redis
from app.models.user import User
from app.schemas.admin_reports import (
    StudentRow, StudentDetail, AIReport,
    CohortReportRequest, CohortAIReport,
)
from app.services import student_report_service
from app.services.student_report_service import (
    InsufficientActivityError, LLMReportError,
)
from app.utils.logger import logger


router = APIRouter(prefix="/admin/students", tags=["admin-reports"])


@router.get("", response_model=list[StudentRow])
async def list_students(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await student_report_service.get_students_overview(db)


@router.get("/{user_id}", response_model=StudentDetail)
async def get_detail(
    user_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await student_report_service.get_student_detail(db, user_id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudiante no encontrado",
        )


@router.post("/{user_id}/ai-report", response_model=AIReport)
async def generate_report(
    user_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    try:
        return await student_report_service.generate_ai_report(db, redis_client, user_id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudiante no encontrado",
        )
    except InsufficientActivityError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except LLMReportError as e:
        logger.error(f"AI report fallo: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio IA no disponible. Reintenta en unos minutos.",
        )


@router.post("/cohort/ai-report", response_model=CohortAIReport)
async def generate_cohort(
    body: CohortReportRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    try:
        return await student_report_service.generate_cohort_report(
            db, redis_client, body.user_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMReportError as e:
        logger.error(f"Cohort AI report falló: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio IA no disponible. Reintenta en unos minutos.",
        )
```

- [ ] **Step 8.4: Register router**

Edit `backend/app/main.py`. Find the block where other routers are included and add:

```python
from app.routers import admin_reports
# ... existing imports ...

app.include_router(admin_reports.router, prefix="/api/v1")
```

Place the `include_router` call near the other admin includes (search for `admin.router`).

- [ ] **Step 8.5: Verify tests pass**

```bash
pytest tests/integration/test_router_admin_reports.py -v
```

Expected: 8 passed.

- [ ] **Step 8.6: Run full backend suite**

```bash
pytest -q
```

Expected: all pre-existing tests still pass + new tests. Coverage ≥80%.

- [ ] **Step 8.7: Commit**

```bash
git add backend/app/routers/admin_reports.py backend/app/main.py backend/tests/integration/test_router_admin_reports.py
git commit -m "feat(admin-reports): wire admin_reports router under /api/v1/admin/students"
```

---

## Task 9: Update ISO/IEC 25010 Trazabilidad Matrix

**Files:**
- Modify: `docs/matriz-trazabilidad-ISO25010.md`

- [ ] **Step 9.1: Read the current matrix end**

```bash
tail -30 docs/matriz-trazabilidad-ISO25010.md
```

Identify the next free RF number; locate the table column conventions.

- [ ] **Step 9.2: Append four new rows**

At the end of the relevant table append (adapt column count/format to the current matrix style if it differs — keep the test names exactly as below):

```markdown
| RF-NEW-RPT-01 | Reporte individual del estudiante en panel admin | Completitud + Pertinencia | `tests/integration/test_router_admin_reports.py::test_students_list_returns_rows`, `::test_student_detail_404_when_missing` | ✅ |
| RF-NEW-RPT-02 | Generación de reporte narrativo IA por estudiante | Pertinencia + Corrección | `tests/unit/test_student_report_generate.py`, `tests/integration/test_router_admin_reports.py::test_ai_report_success` | ✅ |
| RF-NEW-RPT-03 | Reporte comparativo de cohorte (2-15 estudiantes) | Pertinencia | `tests/unit/test_student_report_cohort.py`, `tests/integration/test_router_admin_reports.py::test_cohort_report_success` | ✅ |
| RF-NEW-RPT-04 | Exportación de reporte IA a PDF (vía print del navegador) | Operabilidad | `frontend/src/pages/AdminStudentReportPage.test.tsx::test_print_button_invokes_window_print` | ✅ |
```

- [ ] **Step 9.3: Run the ISO guardian**

```bash
cd backend
pytest tests/integration/test_iso25010.py -v
```

Expected: all 5 guardian tests pass (file/test references exist).

- [ ] **Step 9.4: Commit**

```bash
git add docs/matriz-trazabilidad-ISO25010.md
git commit -m "docs(iso25010): add RF-NEW-RPT-01..04 for admin student reports"
```

---

## Task 10: Frontend Types

**Files:**
- Create: `frontend/src/types/adminReports.ts`

- [ ] **Step 10.1: Write the file**

Create `frontend/src/types/adminReports.ts`:

```ts
import type { StudentLevel } from './assessment'

export interface StudentRow {
  user_id: string
  full_name: string
  email: string
  level: StudentLevel | null
  entry_score: number | null
  overall_progress_pct: number
  avg_quiz_score: number | null
  avg_coding_score: number | null
  last_activity_at: string | null
  last_location: string | null
  is_active: boolean
}

export interface ModuleProgress {
  module_id: number
  module_title: string
  topics_total: number
  topics_completed: number
  progress_pct: number
  avg_quiz_score: number | null
  avg_coding_score: number | null
}

export interface QuizAttemptRow {
  attempt_id: number
  topic_id: number
  topic_title: string
  score: number
  is_passed: boolean
  attempted_at: string
}

export interface CodingSubmissionRow {
  submission_id: number
  challenge_id: number
  challenge_title: string
  score: number
  submitted_at: string
}

export interface AchievementRow {
  achievement_id: number
  name: string
  badge_emoji: string
  earned_at: string
}

export interface LevelHistoryEntry {
  level: StudentLevel
  score: number
  changed_at: string
  reason: string | null
}

export interface StudentDetail {
  user_id: string
  full_name: string
  email: string
  created_at: string
  is_active: boolean
  level: StudentLevel | null
  entry_score: number | null
  level_history: LevelHistoryEntry[]
  overall_progress_pct: number
  modules: ModuleProgress[]
  recent_quizzes: QuizAttemptRow[]
  recent_coding: CodingSubmissionRow[]
  chat_messages_count: number
  chat_last_at: string | null
  achievements_earned: AchievementRow[]
  total_time_seconds: number
  last_activity_at: string | null
  last_location: string | null
}

export type RiskLevel = 'bajo' | 'medio' | 'alto'

export interface AIReport {
  summary: string
  strengths: string[]
  weaknesses: string[]
  risk_level: RiskLevel
  risk_reason: string
  interventions: string[]
  generated_at: string
  cached: boolean
}

export interface CohortAIReport {
  narrative: string
  top_performers: string[]
  needs_support: string[]
  common_gaps: string[]
  recommendations: string[]
  generated_at: string
  cached: boolean
}
```

- [ ] **Step 10.2: Run tsc**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 10.3: Commit**

```bash
git add frontend/src/types/adminReports.ts
git commit -m "feat(admin-reports): TypeScript types"
```

---

## Task 11: Frontend API Client

**Files:**
- Create: `frontend/src/api/adminReports.ts`

- [ ] **Step 11.1: Write the file**

Create `frontend/src/api/adminReports.ts`:

```ts
import apiClient from './client'
import type {
  StudentRow,
  StudentDetail,
  AIReport,
  CohortAIReport,
} from '@/types/adminReports'

export const adminReportsApi = {
  listStudents: () => apiClient.get<StudentRow[]>('/admin/students'),

  getDetail: (userId: string) =>
    apiClient.get<StudentDetail>(`/admin/students/${userId}`),

  generateReport: (userId: string) =>
    apiClient.post<AIReport>(`/admin/students/${userId}/ai-report`),

  generateCohortReport: (userIds: string[]) =>
    apiClient.post<CohortAIReport>('/admin/students/cohort/ai-report', {
      user_ids: userIds,
    }),
}
```

- [ ] **Step 11.2: Run tsc**

```bash
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 11.3: Commit**

```bash
git add frontend/src/api/adminReports.ts
git commit -m "feat(admin-reports): frontend API client"
```

---

## Task 12: Register Route + Skeleton AdminStudentReportPage

**Files:**
- Create: `frontend/src/pages/AdminStudentReportPage.tsx` (skeleton)
- Modify: `frontend/src/App.tsx` (or wherever routes are registered — search for `Routes` element)

- [ ] **Step 12.1: Locate the router file**

```bash
cd frontend
grep -rn "<Routes" src --include="*.tsx" | head
```

Expected: hits in `App.tsx` or `routes.tsx`. Use that file in Step 12.3.

- [ ] **Step 12.2: Create skeleton page**

Create `frontend/src/pages/AdminStudentReportPage.tsx`:

```tsx
import { useParams } from 'react-router-dom'

export default function AdminStudentReportPage() {
  const { userId } = useParams<{ userId: string }>()

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
      <header className="mb-6">
        <h1 className="text-2xl font-extrabold text-foreground">
          Reporte de Estudiante
        </h1>
        <p className="text-sm text-muted-foreground">ID: {userId}</p>
      </header>
      <div className="p-12 text-center text-muted-foreground border border-dashed border-border rounded-xl">
        Contenido en construcción — ver Task 15.
      </div>
    </div>
  )
}
```

- [ ] **Step 12.3: Register the route**

In the router file (from Step 12.1), add an import and a new `<Route>` inside the admin-protected section. Follow the existing pattern used for `/admin`:

```tsx
import AdminStudentReportPage from '@/pages/AdminStudentReportPage'
// inside <Routes> protected by the admin wrapper:
<Route path="admin/students/:userId" element={<AdminStudentReportPage />} />
```

- [ ] **Step 12.4: Verify build**

```bash
npx tsc --noEmit && npx vite build
```

Expected: build succeeds.

- [ ] **Step 12.5: Commit**

```bash
git add frontend/src/pages/AdminStudentReportPage.tsx frontend/src/App.tsx
git commit -m "feat(admin-reports): register /admin/students/:userId route with skeleton page"
```

---

## Task 13: StudentsReportTab (Table + Filters + Tab wiring)

**Files:**
- Create: `frontend/src/components/admin/StudentsReportTab.tsx`
- Create: `frontend/src/components/admin/StudentsReportTab.test.tsx`
- Modify: `frontend/src/pages/AdminPage.tsx`

- [ ] **Step 13.1: Write the failing test**

Create `frontend/src/components/admin/StudentsReportTab.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, useNavigate } from 'react-router-dom'
import StudentsReportTab from './StudentsReportTab'
import { adminReportsApi } from '@/api/adminReports'

vi.mock('@/api/adminReports', () => ({
  adminReportsApi: {
    listStudents: vi.fn(),
    generateCohortReport: vi.fn(),
  },
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: vi.fn() }
})

function wrap(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

const rows = [
  {
    user_id: 'u1', full_name: 'Ana', email: 'a@x', level: 'beginner',
    entry_score: 50, overall_progress_pct: 60, avg_quiz_score: 0.8,
    avg_coding_score: 70, last_activity_at: null, last_location: null,
    is_active: true,
  },
  {
    user_id: 'u2', full_name: 'Bruno', email: 'b@x', level: 'intermediate',
    entry_score: 70, overall_progress_pct: 20, avg_quiz_score: 0.4,
    avg_coding_score: 50, last_activity_at: null, last_location: null,
    is_active: true,
  },
]

describe('StudentsReportTab', () => {
  it('renders rows from the API', async () => {
    ;(adminReportsApi.listStudents as any).mockResolvedValue({ data: rows })
    render(wrap(<StudentsReportTab />))
    expect(await screen.findByText('Ana')).toBeInTheDocument()
    expect(screen.getByText('Bruno')).toBeInTheDocument()
  })

  it('navigates to detail on row click', async () => {
    const navigate = vi.fn()
    ;(useNavigate as any).mockReturnValue(navigate)
    ;(adminReportsApi.listStudents as any).mockResolvedValue({ data: rows })

    render(wrap(<StudentsReportTab />))
    const row = await screen.findByText('Ana')
    fireEvent.click(row.closest('tr')!)
    expect(navigate).toHaveBeenCalledWith('/admin/students/u1')
  })

  it('filters by level', async () => {
    ;(adminReportsApi.listStudents as any).mockResolvedValue({ data: rows })
    render(wrap(<StudentsReportTab />))
    await screen.findByText('Ana')
    fireEvent.change(screen.getByLabelText(/Filtrar por nivel/i), {
      target: { value: 'intermediate' },
    })
    expect(screen.queryByText('Ana')).not.toBeInTheDocument()
    expect(screen.getByText('Bruno')).toBeInTheDocument()
  })

  it('sorts by progress descending on column click', async () => {
    ;(adminReportsApi.listStudents as any).mockResolvedValue({ data: rows })
    render(wrap(<StudentsReportTab />))
    await screen.findByText('Ana')
    const progressHeader = screen.getByRole('button', { name: /Progreso/i })
    fireEvent.click(progressHeader)
    // First click → desc → Ana (60) before Bruno (20)
    const cells = screen.getAllByRole('row').slice(1).map(r => r.textContent || '')
    expect(cells[0].startsWith('Ana')).toBe(true)
  })
})
```

- [ ] **Step 13.2: Verify the test fails**

```bash
npx vitest run src/components/admin/StudentsReportTab.test.tsx
```

Expected: module not found / file missing.

- [ ] **Step 13.3: Implement the tab component**

Create `frontend/src/components/admin/StudentsReportTab.tsx`:

```tsx
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Users2 } from 'lucide-react'

import { adminReportsApi } from '@/api/adminReports'
import type { StudentRow } from '@/types/adminReports'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import CohortReportModal from './CohortReportModal'

type SortKey =
  | 'full_name' | 'email' | 'level'
  | 'overall_progress_pct' | 'avg_quiz_score'
  | 'avg_coding_score' | 'last_activity_at'

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: 'full_name', label: 'Nombre' },
  { key: 'email', label: 'Email' },
  { key: 'level', label: 'Nivel' },
  { key: 'overall_progress_pct', label: 'Progreso' },
  { key: 'avg_quiz_score', label: 'Promedio Quiz' },
  { key: 'avg_coding_score', label: 'Promedio Coding' },
  { key: 'last_activity_at', label: 'Última actividad' },
]

function compareRows(a: StudentRow, b: StudentRow, key: SortKey, dir: 1 | -1): number {
  const av = a[key]
  const bv = b[key]
  if (av === bv) return 0
  if (av === null || av === undefined) return 1
  if (bv === null || bv === undefined) return -1
  return (av > bv ? 1 : -1) * dir
}

export default function StudentsReportTab() {
  const navigate = useNavigate()
  const [sortKey, setSortKey] = useState<SortKey>('full_name')
  const [sortDir, setSortDir] = useState<1 | -1>(1)
  const [levelFilter, setLevelFilter] = useState<string>('')
  const [search, setSearch] = useState<string>('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [cohortOpen, setCohortOpen] = useState(false)

  const { data: rows = [], isLoading } = useQuery({
    queryKey: ['admin', 'students-report'],
    queryFn: () => adminReportsApi.listStudents().then((r) => r.data),
  })

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return rows
      .filter((r) => (includeInactive ? true : r.is_active))
      .filter((r) => (levelFilter ? r.level === levelFilter : true))
      .filter((r) =>
        q ? r.full_name.toLowerCase().includes(q) || r.email.toLowerCase().includes(q) : true
      )
      .sort((a, b) => compareRows(a, b, sortKey, sortDir))
  }, [rows, levelFilter, search, includeInactive, sortKey, sortDir])

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === 1 ? -1 : 1))
    } else {
      setSortKey(key)
      setSortDir(-1)  // first click on a new column → descending (largest first)
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <input
          type="search"
          placeholder="Buscar nombre o email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-9 px-3 text-sm border border-border bg-background rounded-md min-w-[200px]"
        />
        <label className="flex items-center gap-2 text-sm">
          <span className="sr-only">Filtrar por nivel</span>
          <select
            aria-label="Filtrar por nivel"
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="h-9 px-2 text-sm border border-border bg-background rounded-md"
          >
            <option value="">Todos los niveles</option>
            <option value="beginner">Principiante</option>
            <option value="intermediate">Intermedio</option>
            <option value="advanced">Avanzado</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          />
          Incluir inactivos
        </label>
        <div className="ml-auto">
          <Button onClick={() => setCohortOpen(true)} variant="default" size="sm">
            <Users2 className="w-4 h-4 mr-1" />
            Reporte cohorte IA
          </Button>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-8 text-center text-muted-foreground">Cargando estudiantes…</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">
            No hay estudiantes que coincidan con los filtros.
          </div>
        ) : (
          <table className="w-full text-sm min-w-[860px]">
            <thead className="bg-muted text-muted-foreground text-xs uppercase">
              <tr>
                {COLUMNS.map((c) => (
                  <th key={c.key} className="px-4 py-3 text-left">
                    <button
                      type="button"
                      onClick={() => toggleSort(c.key)}
                      className="font-semibold uppercase tracking-wide hover:text-foreground"
                    >
                      {c.label}
                      {sortKey === c.key ? (sortDir === 1 ? ' ▲' : ' ▼') : ''}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr
                  key={r.user_id}
                  onClick={() => navigate(`/admin/students/${r.user_id}`)}
                  className={cn(
                    'border-t border-border cursor-pointer hover:bg-muted/50',
                    !r.is_active && 'opacity-60'
                  )}
                >
                  <td className="px-4 py-3 font-medium text-foreground">{r.full_name}</td>
                  <td className="px-4 py-3 text-muted-foreground">{r.email}</td>
                  <td className="px-4 py-3">{r.level ?? '—'}</td>
                  <td className="px-4 py-3">{r.overall_progress_pct.toFixed(0)}%</td>
                  <td className="px-4 py-3">
                    {r.avg_quiz_score !== null
                      ? (r.avg_quiz_score * 100).toFixed(0) + '%'
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {r.avg_coding_score !== null
                      ? r.avg_coding_score.toFixed(0)
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {r.last_activity_at
                      ? new Date(r.last_activity_at).toLocaleString('es-PE')
                      : 'sin actividad'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {cohortOpen && (
        <CohortReportModal
          students={filtered}
          onClose={() => setCohortOpen(false)}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 13.4: Implement placeholder CohortReportModal**

To make the import resolve (real impl in Task 14), create `frontend/src/components/admin/CohortReportModal.tsx`:

```tsx
import type { StudentRow } from '@/types/adminReports'

interface Props {
  students: StudentRow[]
  onClose: () => void
}

export default function CohortReportModal({ onClose }: Props) {
  return (
    <div
      role="dialog"
      aria-label="Reporte cohorte IA"
      className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4"
    >
      <div className="bg-card border border-border rounded-xl p-6 max-w-2xl w-full">
        <p>Modal en construcción — ver Task 14.</p>
        <button
          type="button"
          onClick={onClose}
          className="mt-4 px-3 py-1 text-sm border border-border rounded"
        >
          Cerrar
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 13.5: Wire the tab into AdminPage**

Edit `frontend/src/pages/AdminPage.tsx`:

```tsx
import { useState } from 'react'
import { Database, FileCode, Users, ClipboardList, TrendingUp, BarChart3 } from 'lucide-react'
import { cn } from '@/lib/utils'
import CorpusTab from '@/components/admin/CorpusTab'
import ContentTab from '@/components/admin/ContentTab'
import UsersTab from '@/components/admin/UsersTab'
import BankTab from '@/components/admin/BankTab'
import LevelsTab from '@/components/admin/LevelsTab'
import StudentsReportTab from '@/components/admin/StudentsReportTab'

type TabId = 'corpus' | 'content' | 'users' | 'bank' | 'levels' | 'reports'

const TABS: { id: TabId; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'reports', label: 'Reportes', icon: BarChart3 },
  { id: 'corpus', label: 'Corpus RAG', icon: Database },
  { id: 'content', label: 'Contenido', icon: FileCode },
  { id: 'users', label: 'Usuarios', icon: Users },
  { id: 'bank', label: 'Banco Fallback', icon: ClipboardList },
  { id: 'levels', label: 'Niveles', icon: TrendingUp },
]

export default function AdminPage() {
  const [tab, setTab] = useState<TabId>('reports')

  return (
    // ... existing header markup unchanged ...
    <>
      {tab === 'reports' && <StudentsReportTab />}
      {tab === 'corpus' && <CorpusTab />}
      {tab === 'content' && <ContentTab />}
      {tab === 'users' && <UsersTab />}
      {tab === 'bank' && <BankTab />}
      {tab === 'levels' && <LevelsTab />}
    </>
  )
}
```

> Keep the existing header and tab-bar JSX exactly as they are; only update the `TABS` array, `TabId` type, default state, and the conditional render block.

- [ ] **Step 13.6: Verify tests pass**

```bash
npx vitest run src/components/admin/StudentsReportTab.test.tsx
```

Expected: 4 passed.

- [ ] **Step 13.7: Commit**

```bash
git add frontend/src/components/admin/StudentsReportTab.tsx frontend/src/components/admin/StudentsReportTab.test.tsx frontend/src/components/admin/CohortReportModal.tsx frontend/src/pages/AdminPage.tsx
git commit -m "feat(admin-reports): students reports tab with sortable/filterable table"
```

---

## Task 14: CohortReportModal (Multi-select + AI narrative)

**Files:**
- Modify: `frontend/src/components/admin/CohortReportModal.tsx`
- Create: `frontend/src/components/admin/CohortReportModal.test.tsx`

- [ ] **Step 14.1: Write the failing test**

Create `frontend/src/components/admin/CohortReportModal.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CohortReportModal from './CohortReportModal'
import { adminReportsApi } from '@/api/adminReports'

vi.mock('@/api/adminReports', () => ({
  adminReportsApi: {
    generateCohortReport: vi.fn(),
  },
}))

function wrap(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{ui}</QueryClientProvider>
}

const students = [
  { user_id: 'u1', full_name: 'Ana', email: 'a@x', level: 'beginner',
    entry_score: null, overall_progress_pct: 0, avg_quiz_score: null,
    avg_coding_score: null, last_activity_at: null, last_location: null,
    is_active: true },
  { user_id: 'u2', full_name: 'Bruno', email: 'b@x', level: 'intermediate',
    entry_score: null, overall_progress_pct: 0, avg_quiz_score: null,
    avg_coding_score: null, last_activity_at: null, last_location: null,
    is_active: true },
]

describe('CohortReportModal', () => {
  it('disables generate button until at least 2 selected', () => {
    render(wrap(<CohortReportModal students={students} onClose={() => {}} />))
    expect(screen.getByRole('button', { name: /Generar reporte/i })).toBeDisabled()
    fireEvent.click(screen.getByLabelText('Ana'))
    expect(screen.getByRole('button', { name: /Generar reporte/i })).toBeDisabled()
    fireEvent.click(screen.getByLabelText('Bruno'))
    expect(screen.getByRole('button', { name: /Generar reporte/i })).toBeEnabled()
  })

  it('renders narrative after API call', async () => {
    ;(adminReportsApi.generateCohortReport as any).mockResolvedValue({
      data: {
        narrative: 'Grupo desigual.',
        top_performers: ['Ana'],
        needs_support: ['Bruno'],
        common_gaps: [],
        recommendations: ['x'],
        generated_at: '2026-05-27T10:00:00Z',
        cached: false,
      },
    })
    render(wrap(<CohortReportModal students={students} onClose={() => {}} />))
    fireEvent.click(screen.getByLabelText('Ana'))
    fireEvent.click(screen.getByLabelText('Bruno'))
    fireEvent.click(screen.getByRole('button', { name: /Generar reporte/i }))
    await waitFor(() =>
      expect(screen.getByText('Grupo desigual.')).toBeInTheDocument()
    )
  })

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn()
    render(wrap(<CohortReportModal students={students} onClose={onClose} />))
    fireEvent.click(screen.getByRole('button', { name: /Cerrar/i }))
    expect(onClose).toHaveBeenCalled()
  })
})
```

- [ ] **Step 14.2: Verify it fails**

```bash
npx vitest run src/components/admin/CohortReportModal.test.tsx
```

Expected: 3 failed (placeholder modal lacks the API, labels, list).

- [ ] **Step 14.3: Implement the modal**

Overwrite `frontend/src/components/admin/CohortReportModal.tsx`:

```tsx
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import { adminReportsApi } from '@/api/adminReports'
import type { StudentRow, CohortAIReport } from '@/types/adminReports'
import { Button } from '@/components/ui/button'

interface Props {
  students: StudentRow[]
  onClose: () => void
}

export default function CohortReportModal({ students, onClose }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [report, setReport] = useState<CohortAIReport | null>(null)

  const mutation = useMutation({
    mutationFn: () =>
      adminReportsApi
        .generateCohortReport(Array.from(selected))
        .then((r) => r.data),
    onSuccess: (data) => setReport(data),
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || 'No se pudo generar el reporte'),
  })

  function toggle(id: string) {
    setSelected((s) => {
      const next = new Set(s)
      if (next.has(id)) next.delete(id)
      else if (next.size < 15) next.add(id)
      else toast.error('Máximo 15 estudiantes para la cohorte')
      return next
    })
  }

  const canGenerate = selected.size >= 2 && selected.size <= 15 && !mutation.isPending

  return (
    <div
      role="dialog"
      aria-label="Reporte cohorte IA"
      className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4"
    >
      <div className="bg-card border border-border rounded-xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-foreground">Reporte cohorte IA</h2>
            <p className="text-sm text-muted-foreground">
              Selecciona entre 2 y 15 estudiantes.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-muted-foreground hover:text-foreground"
            aria-label="Cerrar"
          >
            Cerrar
          </button>
        </div>

        {!report && (
          <>
            <div className="border border-border rounded-md max-h-72 overflow-y-auto mb-4">
              {students.map((s) => (
                <label
                  key={s.user_id}
                  className="flex items-center gap-3 px-3 py-2 text-sm border-b border-border last:border-b-0 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selected.has(s.user_id)}
                    onChange={() => toggle(s.user_id)}
                    aria-label={s.full_name}
                  />
                  <span className="flex-1">{s.full_name}</span>
                  <span className="text-xs text-muted-foreground">{s.level ?? '—'}</span>
                </label>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={onClose} disabled={mutation.isPending}>
                Cancelar
              </Button>
              <Button
                onClick={() => mutation.mutate()}
                disabled={!canGenerate}
              >
                {mutation.isPending
                  ? 'La IA está analizando…'
                  : 'Generar reporte'}
              </Button>
            </div>
          </>
        )}

        {report && (
          <article className="prose prose-sm dark:prose-invert max-w-none">
            <h3>Narrativa</h3>
            <p>{report.narrative}</p>

            <h3>Destacan</h3>
            <ul>{report.top_performers.map((n) => <li key={n}>{n}</li>)}</ul>

            <h3>Requieren apoyo</h3>
            <ul>{report.needs_support.map((n) => <li key={n}>{n}</li>)}</ul>

            {report.common_gaps.length > 0 && (
              <>
                <h3>Brechas comunes</h3>
                <ul>{report.common_gaps.map((g) => <li key={g}>{g}</li>)}</ul>
              </>
            )}

            <h3>Recomendaciones</h3>
            <ul>{report.recommendations.map((r) => <li key={r}>{r}</li>)}</ul>

            <div className="flex justify-end mt-4 gap-2">
              <Button variant="ghost" onClick={() => setReport(null)}>
                Nueva selección
              </Button>
              <Button onClick={onClose}>Cerrar</Button>
            </div>
          </article>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 14.4: Verify tests pass**

```bash
npx vitest run src/components/admin/CohortReportModal.test.tsx
```

Expected: 3 passed.

- [ ] **Step 14.5: Commit**

```bash
git add frontend/src/components/admin/CohortReportModal.tsx frontend/src/components/admin/CohortReportModal.test.tsx
git commit -m "feat(admin-reports): cohort AI report modal with multi-select"
```

---

## Task 15: AdminStudentReportPage (Detail Sections + IA Panel + Print)

**Files:**
- Overwrite: `frontend/src/pages/AdminStudentReportPage.tsx`
- Create: `frontend/src/pages/AdminStudentReportPage.test.tsx`

- [ ] **Step 15.1: Write the failing test**

Create `frontend/src/pages/AdminStudentReportPage.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import AdminStudentReportPage from './AdminStudentReportPage'
import { adminReportsApi } from '@/api/adminReports'

vi.mock('@/api/adminReports', () => ({
  adminReportsApi: {
    getDetail: vi.fn(),
    generateReport: vi.fn(),
  },
}))

function wrap(initialPath: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/admin/students/:userId" element={<AdminStudentReportPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

const detail = {
  user_id: 'u1', full_name: 'Ana', email: 'a@x',
  created_at: '2026-01-01T00:00:00Z', is_active: true,
  level: 'beginner', entry_score: 50, level_history: [],
  overall_progress_pct: 60,
  modules: [{ module_id: 1, module_title: 'M1', topics_total: 4,
              topics_completed: 2, progress_pct: 50,
              avg_quiz_score: 0.5, avg_coding_score: null }],
  recent_quizzes: [],
  recent_coding: [],
  chat_messages_count: 3,
  chat_last_at: null,
  achievements_earned: [],
  total_time_seconds: 120,
  last_activity_at: '2026-05-20T10:00:00Z',
  last_location: 'M1 - Intro',
}

describe('AdminStudentReportPage', () => {
  it('renders detail sections when loaded', async () => {
    ;(adminReportsApi.getDetail as any).mockResolvedValue({ data: detail })
    render(wrap('/admin/students/u1'))
    expect(await screen.findByText('Ana')).toBeInTheDocument()
    expect(screen.getByText(/M1/)).toBeInTheDocument()
    expect(screen.getByText(/60%/)).toBeInTheDocument()
  })

  it('triggers AI report generation', async () => {
    ;(adminReportsApi.getDetail as any).mockResolvedValue({ data: detail })
    ;(adminReportsApi.generateReport as any).mockResolvedValue({
      data: {
        summary: 'Resumen IA.',
        strengths: ['x'], weaknesses: ['y'],
        risk_level: 'bajo', risk_reason: 'ok', interventions: ['z'],
        generated_at: '2026-05-27T10:00:00Z',
        cached: false,
      },
    })
    render(wrap('/admin/students/u1'))
    await screen.findByText('Ana')
    fireEvent.click(screen.getByRole('button', { name: /Generar reporte/i }))
    await waitFor(() =>
      expect(screen.getByText('Resumen IA.')).toBeInTheDocument()
    )
  })

  it('test_print_button_invokes_window_print', async () => {
    ;(adminReportsApi.getDetail as any).mockResolvedValue({ data: detail })
    const printSpy = vi.spyOn(window, 'print').mockImplementation(() => {})
    render(wrap('/admin/students/u1'))
    await screen.findByText('Ana')
    fireEvent.click(screen.getByRole('button', { name: /Imprimir/i }))
    expect(printSpy).toHaveBeenCalled()
    printSpy.mockRestore()
  })
})
```

- [ ] **Step 15.2: Verify it fails**

```bash
npx vitest run src/pages/AdminStudentReportPage.test.tsx
```

Expected: failures (the skeleton page doesn't fetch detail or have a Print button).

- [ ] **Step 15.3: Implement the full page**

Overwrite `frontend/src/pages/AdminStudentReportPage.tsx`:

```tsx
import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'
import { Printer, Sparkles } from 'lucide-react'

import { adminReportsApi } from '@/api/adminReports'
import type { AIReport, RiskLevel } from '@/types/adminReports'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const RISK_STYLES: Record<RiskLevel, string> = {
  bajo: 'bg-success/10 text-success border-success/30',
  medio: 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-500/15 dark:text-amber-300',
  alto: 'bg-destructive/10 text-destructive border-destructive/30',
}

export default function AdminStudentReportPage() {
  const { userId = '' } = useParams<{ userId: string }>()

  const { data: detail, isLoading } = useQuery({
    queryKey: ['admin', 'student-detail', userId],
    queryFn: () => adminReportsApi.getDetail(userId).then((r) => r.data),
    enabled: Boolean(userId),
  })

  const mutation = useMutation<AIReport>({
    mutationFn: () => adminReportsApi.generateReport(userId).then((r) => r.data),
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || 'No se pudo generar el reporte IA'),
  })

  if (isLoading || !detail) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="h-8 w-40 bg-muted animate-pulse rounded mb-4" />
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-muted animate-pulse rounded" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 printable-report">
      <header className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground">{detail.full_name}</h1>
          <p className="text-sm text-muted-foreground">{detail.email}</p>
          {detail.level && (
            <span className="inline-block mt-2 px-2 py-0.5 text-xs font-semibold rounded bg-primary-100 text-primary-700">
              Nivel: {detail.level}
            </span>
          )}
          {detail.last_location && (
            <span className="block mt-1 text-xs text-muted-foreground">
              Última ubicación: {detail.last_location}
            </span>
          )}
        </div>
        <Button
          variant="ghost"
          onClick={() => window.print()}
          className="no-print"
        >
          <Printer className="w-4 h-4 mr-1" />
          Imprimir / PDF
        </Button>
      </header>

      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <Card label="Progreso global" value={`${detail.overall_progress_pct.toFixed(0)}%`} />
        <Card label="Tiempo invertido" value={`${Math.round(detail.total_time_seconds / 60)} min`} />
        <Card label="Mensajes al tutor" value={detail.chat_messages_count.toString()} />
        <Card label="Logros" value={detail.achievements_earned.length.toString()} />
      </section>

      <section className="mb-6">
        <h2 className="text-lg font-bold mb-3">Progreso por módulo</h2>
        <div className="space-y-2">
          {detail.modules.map((m) => (
            <div key={m.module_id} className="bg-card border border-border rounded-md p-3">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{m.module_title}</span>
                <span className="text-muted-foreground">
                  {m.topics_completed}/{m.topics_total} temas
                </span>
              </div>
              <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500"
                  style={{ width: `${m.progress_pct}%` }}
                />
              </div>
              <div className="mt-1 text-xs text-muted-foreground flex gap-4">
                <span>Quiz: {m.avg_quiz_score !== null ? (m.avg_quiz_score * 100).toFixed(0) + '%' : '—'}</span>
                <span>Coding: {m.avg_coding_score !== null ? m.avg_coding_score.toFixed(0) : '—'}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid md:grid-cols-2 gap-6 mb-6">
        <RecentList
          title="Últimos quizzes"
          items={detail.recent_quizzes.map((q) => ({
            id: q.attempt_id,
            label: q.topic_title,
            score: `${(q.score * 100).toFixed(0)}%`,
            when: q.attempted_at,
          }))}
        />
        <RecentList
          title="Últimos desafíos de código"
          items={detail.recent_coding.map((c) => ({
            id: c.submission_id,
            label: c.challenge_title,
            score: `${c.score.toFixed(0)}/100`,
            when: c.submitted_at,
          }))}
        />
      </section>

      {detail.level_history.length > 0 && (
        <section className="mb-6">
          <h2 className="text-lg font-bold mb-3">Historial de nivel</h2>
          <ol className="space-y-2 text-sm">
            {detail.level_history.map((h, i) => (
              <li key={i} className="flex gap-4">
                <span className="text-muted-foreground w-32">
                  {new Date(h.changed_at).toLocaleDateString('es-PE')}
                </span>
                <span className="font-medium">{h.level}</span>
                <span className="text-muted-foreground">({h.score.toFixed(0)} pts)</span>
                {h.reason && <span className="text-xs text-muted-foreground">— {h.reason}</span>}
              </li>
            ))}
          </ol>
        </section>
      )}

      <section className="bg-card border border-border rounded-xl p-5">
        <div className="flex items-start justify-between flex-wrap gap-3 mb-3">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary-500" />
            Reporte IA
          </h2>
          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="no-print"
          >
            {mutation.isPending ? 'La IA está analizando…' : 'Generar reporte'}
          </Button>
        </div>

        {mutation.data && (
          <article className="prose prose-sm dark:prose-invert max-w-none">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={cn(
                  'px-2 py-0.5 text-xs font-semibold rounded border',
                  RISK_STYLES[mutation.data.risk_level],
                )}
              >
                Riesgo: {mutation.data.risk_level}
              </span>
              {mutation.data.cached && (
                <span className="text-xs text-muted-foreground">cacheado</span>
              )}
            </div>
            <ReactMarkdown>{mutation.data.summary}</ReactMarkdown>
            <p className="text-sm text-muted-foreground">
              <strong>Justificación:</strong> {mutation.data.risk_reason}
            </p>

            <h3>Fortalezas</h3>
            <ul>{mutation.data.strengths.map((s) => <li key={s}>{s}</li>)}</ul>

            <h3>Debilidades</h3>
            <ul>{mutation.data.weaknesses.map((s) => <li key={s}>{s}</li>)}</ul>

            <h3>Intervenciones sugeridas</h3>
            <ul>{mutation.data.interventions.map((s) => <li key={s}>{s}</li>)}</ul>
          </article>
        )}
      </section>
    </div>
  )
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-card border border-border rounded-md p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="text-xl font-bold text-foreground">{value}</div>
    </div>
  )
}

function RecentList({
  title,
  items,
}: {
  title: string
  items: { id: number; label: string; score: string; when: string }[]
}) {
  return (
    <div>
      <h2 className="text-lg font-bold mb-3">{title}</h2>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">Sin registros.</p>
      ) : (
        <ul className="text-sm space-y-2">
          {items.map((it) => (
            <li key={it.id} className="flex items-center justify-between border-b border-border pb-1">
              <span className="truncate mr-2">{it.label}</span>
              <span className="font-semibold">{it.score}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
```

- [ ] **Step 15.4: Verify tests pass**

```bash
npx vitest run src/pages/AdminStudentReportPage.test.tsx
```

Expected: 3 passed.

- [ ] **Step 15.5: Commit**

```bash
git add frontend/src/pages/AdminStudentReportPage.tsx frontend/src/pages/AdminStudentReportPage.test.tsx
git commit -m "feat(admin-reports): student detail page with AI report panel and print"
```

---

## Task 16: Print CSS + Full Frontend Pass

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 16.1: Add the print block**

Append to `frontend/src/index.css`:

```css
@media print {
  .no-print { display: none !important; }
  .printable-report { max-width: 100% !important; box-shadow: none !important; padding: 0 !important; }
  body { background: #fff !important; color: #000 !important; }
  /* Hide the global app shell while printing — adjust selectors if the layout
     uses different element types or classes. */
  aside, nav, .app-sidebar, header.app-header { display: none !important; }
  /* Ensure progress bars print legibly */
  .bg-primary-500 { background: #1d4ed8 !important; }
  a { color: #000 !important; text-decoration: none !important; }
}
```

- [ ] **Step 16.2: Run full frontend tests**

```bash
cd frontend
npx tsc --noEmit
npx vitest run
```

Expected: 0 errors, all tests pass (existing + new).

- [ ] **Step 16.3: Manual print verification**

Run locally:

```bash
cd /  # any working dir
cd C:/tutor-ia-rfa && bash scripts/start-stack.sh   # or equivalent for the dev env
```

Open `http://localhost:5173`, log in as admin, click **Reportes** → click a student → click **Imprimir / PDF** → in the print dialog choose "Save as PDF" and confirm:

- [ ] Sidebar and tab navigation are hidden in preview.
- [ ] Student name, progress bars, last quizzes/coding, and the AI panel (if generated) are visible.
- [ ] Buttons (`Generar reporte`, `Imprimir / PDF`) are NOT visible in the printout.

If any of those checks fails, adjust the selectors in Step 16.1 to match the actual layout markup (e.g. inspect the live DOM for the sidebar's outer element).

- [ ] **Step 16.4: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat(admin-reports): print stylesheet for PDF export via browser"
```

---

## Final Steps

- [ ] **F.1: Run full backend + frontend suite**

```bash
# backend
cd backend && pytest -q
# frontend
cd ../frontend && npx vitest run && npx tsc --noEmit
```

Expected: all green.

- [ ] **F.2: Run ISO/IEC 25010 guardian**

```bash
cd ../backend
pytest tests/integration/test_iso25010.py -v
```

Expected: 5 passed (matrix references valid).

- [ ] **F.3: Update CLAUDE.md note**

In `CLAUDE.md`, in the section listing post-Sprint extensions, add one line under the existing admin features bullet list:

```
- ✅ Pantalla admin "Reportes": tabla estudiantes + detalle + reporte IA narrativo + cohorte + export PDF (`docs/superpowers/specs/2026-05-27-admin-student-reports-design.md`)
```

Commit:

```bash
git add CLAUDE.md
git commit -m "docs(claude): note admin student reports screen"
```

- [ ] **F.4: Push and open PR**

```bash
git push -u origin feat/admin-student-reports
gh pr create --title "feat(admin): student reports screen with AI narratives" --body "$(cat <<'EOF'
## Summary
- Admin-only "Reportes" tab + dedicated /admin/students/:userId page
- AI narrative per student (summary, strengths/weaknesses, risk_level, interventions) via qwen2.5
- Cohort AI comparative report (2-15 students)
- PDF export via browser print + dedicated stylesheet
- 4 new ISO/IEC 25010 RFs (RF-NEW-RPT-01..04)

Spec: docs/superpowers/specs/2026-05-27-admin-student-reports-design.md

## Test plan
- [x] Backend unit tests (helpers, overview, detail, parser, generate, cohort)
- [x] Backend integration tests (router, auth gate, 404/422/503 error mapping)
- [x] Frontend tests (StudentsReportTab sort/filter/navigate, CohortReportModal selection+narrative, AdminStudentReportPage detail+IA panel+print spy)
- [x] ISO/IEC 25010 guardian still passes
- [ ] Manual: print preview hides app chrome, shows full report

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-Review (executed before publishing this plan)

1. **Spec coverage:**
   - Tabla + filtros + click navigation → Tasks 12+13.
   - Detail page → Task 15.
   - AI report individual → Tasks 5+6+8 wired + Task 15 UI.
   - Cohort report → Tasks 7+8+14.
   - PDF print → Task 16.
   - ISO matrix update → Task 9.
   - No-migration constraint → all queries reuse existing tables.
   - Cache with hit/miss flag → handled in Task 6/7 via explicit GET+SETEX wrappers (not `cached_json`).
   - Insufficient-activity gate → Task 6.

2. **Placeholder scan:** No `TBD`/`TODO`/`Similar to Task N`. The only remaining decision points are explicitly called out: Step 12.1 locates the router file before editing it; Step 16.3 inspects the live DOM if the print selectors need adjusting.

3. **Type consistency:** `StudentRow`, `StudentDetail`, `AIReport`, `CohortAIReport` types match between Pydantic (`backend/app/schemas/admin_reports.py`) and TS (`frontend/src/types/adminReports.ts`). Risk levels constrained to `bajo|medio|alto` in both sides. `_detail_hash` signature stable across Task 2 (definition), Task 6 (use), Task 7 (cohort reuse).

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-27-admin-student-reports.md`.**
