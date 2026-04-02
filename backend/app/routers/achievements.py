from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.achievement import Achievement, UserAchievement
from app.schemas.achievement import AchievementResponse

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("", response_model=list[AchievementResponse])
async def list_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all achievements with earned status for the current user."""
    # Get all achievements
    result = await db.execute(select(Achievement).order_by(Achievement.id))
    achievements = result.scalars().all()

    # Get user's earned achievements
    earned_result = await db.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == current_user.id)
    )
    earned_map = {ua.achievement_id: ua for ua in earned_result.scalars().all()}

    response = []
    for a in achievements:
        ua = earned_map.get(a.id)
        response.append(AchievementResponse(
            id=a.id,
            name=a.name,
            description=a.description,
            badge_emoji=a.badge_emoji,
            badge_color=a.badge_color,
            is_earned=ua is not None,
            earned_at=ua.earned_at if ua else None,
        ))

    return response
