"""
routers/dashboard.py — Aggregated dashboard endpoint for the student home screen.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.module import Module
from app.models.topic import Topic
from app.models.progress import UserTopicProgress
from app.models.achievement import Achievement, UserAchievement
from app.models.user_level import UserLevel
from app.schemas.dashboard import (
    DashboardResponse,
    LastAccessedTopic,
    RecommendedModule,
    RecentAchievement,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# Level-specific encouragement for module recommendations
LEVEL_REASON = {
    "beginner": "Continúa a tu ritmo",
    "intermediate": "Siguiente desafío recomendado",
    "advanced": "Perfecciona tus habilidades",
}


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate dashboard data: progress, last topic, recommendations, achievements, level."""
    # 1. User level
    level_result = await db.execute(
        select(UserLevel).where(UserLevel.user_id == current_user.id)
    )
    user_level = level_result.scalar_one_or_none()
    level_str = user_level.level if user_level else None

    # 2. Total topics + completed
    total_q = await db.execute(
        select(func.count(Topic.id)).where(Topic.is_active == True)
    )
    total_topics = total_q.scalar() or 0

    completed_q = await db.execute(
        select(func.count(UserTopicProgress.id))
        .join(Topic, Topic.id == UserTopicProgress.topic_id)
        .where(
            UserTopicProgress.user_id == current_user.id,
            UserTopicProgress.is_completed == True,
            Topic.is_active == True,
        )
    )
    completed = completed_q.scalar() or 0

    overall_pct = round((completed / total_topics * 100), 1) if total_topics > 0 else 0.0

    # 3. Last accessed topic
    last_q = await db.execute(
        select(UserTopicProgress, Topic, Module)
        .join(Topic, Topic.id == UserTopicProgress.topic_id)
        .join(Module, Module.id == Topic.module_id)
        .where(UserTopicProgress.user_id == current_user.id)
        .order_by(desc(UserTopicProgress.last_accessed_at))
        .limit(1)
    )
    last_row = last_q.first()
    last_accessed = None
    if last_row:
        prog, topic, module = last_row
        last_accessed = LastAccessedTopic(
            topic_id=topic.id,
            topic_title=topic.title,
            module_id=module.id,
            module_title=module.title,
            last_accessed_at=prog.last_accessed_at,
            is_completed=prog.is_completed,
        )

    # 4. Recommended modules — next 3 in progress / not started, ordered
    mods_q = await db.execute(
        select(Module).where(Module.is_active == True).order_by(Module.order_index)
    )
    modules = list(mods_q.scalars().all())

    recommended: list[RecommendedModule] = []
    reason_text = LEVEL_REASON.get(level_str or "beginner", "Sigue avanzando")

    for module in modules:
        if len(recommended) >= 3:
            break
        total_mod_q = await db.execute(
            select(func.count(Topic.id)).where(
                Topic.module_id == module.id, Topic.is_active == True
            )
        )
        total_mod = total_mod_q.scalar() or 0
        if total_mod == 0:
            continue

        done_mod_q = await db.execute(
            select(func.count(UserTopicProgress.id))
            .join(Topic, Topic.id == UserTopicProgress.topic_id)
            .where(
                UserTopicProgress.user_id == current_user.id,
                UserTopicProgress.is_completed == True,
                Topic.module_id == module.id,
                Topic.is_active == True,
            )
        )
        done_mod = done_mod_q.scalar() or 0
        pct = round(done_mod / total_mod * 100, 1) if total_mod > 0 else 0.0

        # Recommend only if not 100% completed
        if pct >= 100:
            continue

        recommended.append(RecommendedModule(
            id=module.id,
            title=module.title,
            description=module.description,
            icon_name=module.icon_name,
            color_hex=module.color_hex,
            progress_pct=pct,
            reason=reason_text if pct == 0 else "Continúa donde lo dejaste",
        ))

    # 5. Recent achievements (last 3)
    ach_q = await db.execute(
        select(UserAchievement, Achievement)
        .join(Achievement, Achievement.id == UserAchievement.achievement_id)
        .where(UserAchievement.user_id == current_user.id)
        .order_by(desc(UserAchievement.earned_at))
        .limit(3)
    )
    recent_achievements = [
        RecentAchievement(
            id=a.id,
            name=a.name,
            badge_emoji=a.badge_emoji,
            badge_color=a.badge_color,
            earned_at=ua.earned_at,
        )
        for ua, a in ach_q.all()
    ]

    return DashboardResponse(
        user_name=current_user.full_name,
        user_level=level_str,
        overall_progress_pct=overall_pct,
        total_topics_completed=completed,
        total_topics=total_topics,
        last_accessed_topic=last_accessed,
        recommended_modules=recommended,
        recent_achievements=recent_achievements,
    )
