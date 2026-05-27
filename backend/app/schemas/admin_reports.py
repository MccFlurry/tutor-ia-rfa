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
