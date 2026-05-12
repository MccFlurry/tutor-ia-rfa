import uuid
from datetime import date, timedelta, datetime, timezone
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


async def compute_streak(user_id: uuid.UUID, db: AsyncSession) -> dict:
    """Compute current + longest consecutive-day streak.

    Activity = any topic visit (last_accessed_at). We bucket by UTC date,
    sort descending, and count consecutive days. The current streak is anchored
    to today; if last activity was yesterday, today still counts as 0 (streak
    survives until the next UTC midnight).
    """
    rows = await db.execute(
        select(UserTopicProgress.last_accessed_at)
        .where(
            UserTopicProgress.user_id == user_id,
            UserTopicProgress.last_accessed_at.is_not(None),
        )
        .order_by(UserTopicProgress.last_accessed_at.desc())
    )
    timestamps = [r[0] for r in rows.all() if r[0] is not None]

    if not timestamps:
        return {"current_streak": 0, "longest_streak": 0, "last_active_date": None}

    # Distinct UTC dates, sorted descending
    distinct_dates = sorted({ts.date() for ts in timestamps}, reverse=True)

    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)

    # Current streak: anchored to today OR yesterday
    current = 0
    if distinct_dates[0] in (today, yesterday):
        expected = distinct_dates[0]
        for d in distinct_dates:
            if d == expected:
                current += 1
                expected = expected - timedelta(days=1)
            else:
                break

    # Longest streak: scan all
    longest = 1
    run = 1
    for i in range(1, len(distinct_dates)):
        if distinct_dates[i] == distinct_dates[i - 1] - timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    return {
        "current_streak": current,
        "longest_streak": longest,
        "last_active_date": distinct_dates[0].isoformat(),
    }
