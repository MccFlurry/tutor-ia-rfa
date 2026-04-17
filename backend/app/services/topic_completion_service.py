"""
topic_completion_service.py — Lógica centralizada para determinar si un tema está completo.

Un tema se completa cuando:
- Si tiene quiz: el estudiante aprobó (≥60%)
- Si tiene desafíos de código: el estudiante obtuvo ≥60 en al menos uno por desafío
- Si tiene ambos: AMBOS deben cumplirse
- Si no tiene ninguno: se marca manualmente
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.quiz import QuizAttempt
from app.models.coding import CodingChallenge, CodingSubmission
from app.models.progress import UserTopicProgress
from app.models.topic import Topic
from app.services.achievement_service import check_and_grant_achievements
from app.utils.logger import logger

CODING_PASS_SCORE = 60.0  # Minimum score to pass a coding challenge


async def check_and_complete_topic(
    user_id: uuid.UUID,
    topic_id: int,
    db: AsyncSession,
) -> bool:
    """
    Check if the user has met all completion requirements for a topic.
    If so, mark it as completed. Returns True if topic is now completed.
    """
    # Get topic info
    topic_result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = topic_result.scalar_one_or_none()
    if not topic:
        return False

    # Check quiz requirement
    quiz_ok = True
    if topic.has_quiz:
        quiz_ok = await _has_passed_quiz(user_id, topic_id, db)

    # Check coding challenge requirement
    coding_ok = True
    coding_required = await _topic_has_coding(topic_id, db)
    if coding_required:
        coding_ok = await _has_passed_any_coding(user_id, topic_id, db)

    # Both must be satisfied
    is_complete = quiz_ok and coding_ok

    if is_complete:
        await _mark_completed(user_id, topic_id, db)
        await check_and_grant_achievements(user_id, db)
        logger.info(f"Tema {topic_id} completado por usuario {user_id} (quiz={quiz_ok}, coding={coding_ok})")

    return is_complete


async def get_topic_completion_status(
    user_id: uuid.UUID,
    topic_id: int,
    db: AsyncSession,
) -> dict:
    """
    Return detailed completion status for a topic.
    Useful for the frontend to show what's still needed.
    """
    topic_result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = topic_result.scalar_one_or_none()
    if not topic:
        return {"quiz_required": False, "quiz_passed": False, "coding_required": False, "coding_passed": False}

    quiz_passed = await _has_passed_quiz(user_id, topic_id, db) if topic.has_quiz else False
    coding_required = await _topic_has_coding(topic_id, db)
    coding_passed = (
        await _has_passed_any_coding(user_id, topic_id, db) if coding_required else False
    )

    return {
        "quiz_required": topic.has_quiz,
        "quiz_passed": quiz_passed,
        "coding_required": coding_required,
        "coding_passed": coding_passed,
    }


async def _has_passed_quiz(user_id: uuid.UUID, topic_id: int, db: AsyncSession) -> bool:
    """Check if user has at least one passing quiz attempt."""
    result = await db.execute(
        select(func.count(QuizAttempt.id)).where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.topic_id == topic_id,
            QuizAttempt.is_passed == True,
        )
    )
    return (result.scalar() or 0) > 0


async def _topic_has_coding(topic_id: int, db: AsyncSession) -> bool:
    """
    A topic "requires coding" when it has at least one challenge in the
    catalogue (static, not per-student AI copies).
    """
    result = await db.execute(
        select(func.count(CodingChallenge.id)).where(
            CodingChallenge.topic_id == topic_id,
            CodingChallenge.is_ai_generated == False,
        )
    )
    return (result.scalar() or 0) > 0


async def _has_passed_any_coding(
    user_id: uuid.UUID,
    topic_id: int,
    db: AsyncSession,
) -> bool:
    """
    Topic's coding requirement is met when the user has at least one
    submission with score >= 60 on any challenge tied to this topic
    (either a static catalogue challenge or an AI challenge generated for them).
    """
    result = await db.execute(
        select(func.count(CodingSubmission.id))
        .join(CodingChallenge, CodingChallenge.id == CodingSubmission.challenge_id)
        .where(
            CodingSubmission.user_id == user_id,
            CodingChallenge.topic_id == topic_id,
            CodingSubmission.score >= CODING_PASS_SCORE,
        )
    )
    return (result.scalar() or 0) > 0


async def _mark_completed(user_id: uuid.UUID, topic_id: int, db: AsyncSession) -> None:
    """Mark a topic as completed for the user."""
    result = await db.execute(
        select(UserTopicProgress).where(
            UserTopicProgress.user_id == user_id,
            UserTopicProgress.topic_id == topic_id,
        )
    )
    progress = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if not progress:
        progress = UserTopicProgress(
            user_id=user_id,
            topic_id=topic_id,
            is_completed=True,
            completed_at=now,
            first_visited_at=now,
            last_accessed_at=now,
        )
        db.add(progress)
    elif not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = now
        progress.last_accessed_at = now
