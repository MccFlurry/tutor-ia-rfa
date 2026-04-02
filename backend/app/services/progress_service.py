import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.module import Module
from app.models.topic import Topic
from app.models.progress import UserTopicProgress
from app.models.quiz import QuizAttempt


async def get_user_progress(user_id: uuid.UUID, db: AsyncSession) -> dict:
    """Calculate overall progress stats for a user."""
    # Get all active modules ordered
    modules_result = await db.execute(
        select(Module).where(Module.is_active == True).order_by(Module.order_index)
    )
    modules = modules_result.scalars().all()

    # Total topics across all modules
    total_topics_q = await db.execute(
        select(func.count(Topic.id)).where(Topic.is_active == True)
    )
    total_topics = total_topics_q.scalar() or 0

    # Completed topics for this user
    completed_q = await db.execute(
        select(func.count(UserTopicProgress.id))
        .join(Topic, Topic.id == UserTopicProgress.topic_id)
        .where(
            UserTopicProgress.user_id == user_id,
            UserTopicProgress.is_completed == True,
            Topic.is_active == True,
        )
    )
    topics_completed = completed_q.scalar() or 0

    # Total time
    time_q = await db.execute(
        select(func.coalesce(func.sum(UserTopicProgress.time_spent_seconds), 0))
        .where(UserTopicProgress.user_id == user_id)
    )
    total_time = time_q.scalar() or 0

    # Quiz average score
    quiz_q = await db.execute(
        select(func.avg(QuizAttempt.score))
        .where(QuizAttempt.user_id == user_id)
    )
    quiz_avg = quiz_q.scalar()
    quiz_avg_score = round(quiz_avg * 100, 1) if quiz_avg is not None else None

    # Per-module progress
    module_items = []
    for module in modules:
        mod_total_q = await db.execute(
            select(func.count(Topic.id))
            .where(Topic.module_id == module.id, Topic.is_active == True)
        )
        mod_total = mod_total_q.scalar() or 0

        mod_completed_q = await db.execute(
            select(func.count(UserTopicProgress.id))
            .join(Topic, Topic.id == UserTopicProgress.topic_id)
            .where(
                UserTopicProgress.user_id == user_id,
                Topic.module_id == module.id,
                Topic.is_active == True,
                UserTopicProgress.is_completed == True,
            )
        )
        mod_completed = mod_completed_q.scalar() or 0

        pct = round((mod_completed / mod_total * 100), 1) if mod_total > 0 else 0.0

        module_items.append({
            "id": module.id,
            "title": module.title,
            "pct": pct,
            "completed": mod_completed,
            "total": mod_total,
        })

    overall_pct = round((topics_completed / total_topics * 100), 1) if total_topics > 0 else 0.0

    return {
        "overall_pct": overall_pct,
        "total_time_seconds": total_time,
        "topics_completed": topics_completed,
        "quiz_avg_score": quiz_avg_score,
        "modules": module_items,
    }


async def get_activity_log(user_id: uuid.UUID, db: AsyncSession, limit: int = 20) -> list[dict]:
    """Get recent activity for a user."""
    activities = []

    # Recent topic completions
    topic_completions = await db.execute(
        select(UserTopicProgress, Topic.title)
        .join(Topic, Topic.id == UserTopicProgress.topic_id)
        .where(
            UserTopicProgress.user_id == user_id,
            UserTopicProgress.is_completed == True,
        )
        .order_by(UserTopicProgress.completed_at.desc())
        .limit(limit)
    )
    for progress, title in topic_completions:
        if progress.completed_at:
            activities.append({
                "type": "topic_completed",
                "description": f"Completaste el tema: {title}",
                "timestamp": progress.completed_at.isoformat(),
            })

    # Recent quiz attempts
    quiz_results = await db.execute(
        select(QuizAttempt, Topic.title)
        .join(Topic, Topic.id == QuizAttempt.topic_id)
        .where(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(limit)
    )
    for attempt, title in quiz_results:
        score_pct = round(attempt.score * 100)
        status = "aprobaste" if attempt.is_passed else "no aprobaste"
        activities.append({
            "type": "quiz_passed" if attempt.is_passed else "quiz_failed",
            "description": f"Quiz: {title} — {status} ({score_pct}%)",
            "timestamp": attempt.attempted_at.isoformat(),
        })

    # Sort by timestamp descending and limit
    activities.sort(key=lambda a: a["timestamp"], reverse=True)
    return activities[:limit]
