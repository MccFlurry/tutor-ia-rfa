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
