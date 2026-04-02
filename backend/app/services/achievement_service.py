import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.achievement import Achievement, UserAchievement
from app.models.progress import UserTopicProgress
from app.models.topic import Topic
from app.models.module import Module
from app.models.quiz import QuizAttempt
from app.models.chat import ChatMessage


async def check_and_grant_achievements(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """
    Check all achievement conditions for a user and grant any newly earned ones.
    Returns list of newly granted achievements.
    """
    # Get all achievements
    result = await db.execute(select(Achievement))
    all_achievements = result.scalars().all()

    # Get already earned achievement IDs
    earned_result = await db.execute(
        select(UserAchievement.achievement_id)
        .where(UserAchievement.user_id == user_id)
    )
    earned_ids = {row for row in earned_result.scalars().all()}

    newly_granted = []

    for achievement in all_achievements:
        if achievement.id in earned_ids:
            continue

        earned = await _check_condition(user_id, achievement, db)
        if earned:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
            )
            db.add(user_achievement)
            newly_granted.append({
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "badge_emoji": achievement.badge_emoji,
                "badge_color": achievement.badge_color,
            })

    if newly_granted:
        await db.flush()

    return newly_granted


async def _check_condition(
    user_id: uuid.UUID,
    achievement: Achievement,
    db: AsyncSession,
) -> bool:
    """Check if a user meets the condition for a specific achievement."""
    ct = achievement.condition_type

    if ct == "first_topic":
        # Completed at least 1 topic
        q = await db.execute(
            select(func.count(UserTopicProgress.id))
            .where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.is_completed == True,
            )
        )
        count = q.scalar() or 0
        return count >= achievement.condition_value

    elif ct == "module_completed":
        if achievement.condition_module_id:
            # Specific module must be completed
            return await _is_module_completed(user_id, achievement.condition_module_id, db)
        else:
            # Any module completed
            modules_result = await db.execute(
                select(Module.id).where(Module.is_active == True)
            )
            module_ids = modules_result.scalars().all()
            completed_count = 0
            for mid in module_ids:
                if await _is_module_completed(user_id, mid, db):
                    completed_count += 1
            return completed_count >= achievement.condition_value

    elif ct == "chat_messages":
        q = await db.execute(
            select(func.count(ChatMessage.id))
            .where(
                ChatMessage.user_id == user_id,
                ChatMessage.role == "user",
            )
        )
        count = q.scalar() or 0
        return count >= achievement.condition_value

    elif ct == "quiz_perfect":
        q = await db.execute(
            select(func.count(QuizAttempt.id))
            .where(
                QuizAttempt.user_id == user_id,
                QuizAttempt.score == 1.0,
            )
        )
        count = q.scalar() or 0
        return count >= 1

    elif ct == "course_completed":
        # All active topics must be completed
        total_q = await db.execute(
            select(func.count(Topic.id)).where(Topic.is_active == True)
        )
        total = total_q.scalar() or 0

        completed_q = await db.execute(
            select(func.count(UserTopicProgress.id))
            .join(Topic, Topic.id == UserTopicProgress.topic_id)
            .where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.is_completed == True,
                Topic.is_active == True,
            )
        )
        completed = completed_q.scalar() or 0
        return total > 0 and completed >= total

    elif ct == "streak_days":
        # Simplified: check distinct days with activity
        q = await db.execute(
            select(
                func.count(
                    func.distinct(func.date(UserTopicProgress.last_accessed_at))
                )
            ).where(UserTopicProgress.user_id == user_id)
        )
        days = q.scalar() or 0
        return days >= achievement.condition_value

    return False


async def _is_module_completed(
    user_id: uuid.UUID, module_id: int, db: AsyncSession
) -> bool:
    """Check if all active topics in a module are completed by a user."""
    total_q = await db.execute(
        select(func.count(Topic.id))
        .where(Topic.module_id == module_id, Topic.is_active == True)
    )
    total = total_q.scalar() or 0
    if total == 0:
        return False

    completed_q = await db.execute(
        select(func.count(UserTopicProgress.id))
        .join(Topic, Topic.id == UserTopicProgress.topic_id)
        .where(
            UserTopicProgress.user_id == user_id,
            Topic.module_id == module_id,
            Topic.is_active == True,
            UserTopicProgress.is_completed == True,
        )
    )
    completed = completed_q.scalar() or 0
    return completed >= total
