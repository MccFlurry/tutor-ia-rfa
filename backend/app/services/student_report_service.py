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


# ---------------------------------------------------------------------------
# Task 3: get_students_overview
# ---------------------------------------------------------------------------

from sqlalchemy import select, func
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
      - avg_quiz_score       = AVG(quiz_attempts.score)
      - avg_coding_score     = AVG(coding_submissions.score)
      - last_activity_at     = MAX over (progress, quiz, coding, chat) timestamps
      - last_location        = title of the topic touched last, or "Chat IA" /
                               "Quiz" / "Desafío de código" when one of those
                               events is the most recent.
    """
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

    rows = (await db.execute(query)).all()

    # Batch-resolve last topic location for each user (single extra query).
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
