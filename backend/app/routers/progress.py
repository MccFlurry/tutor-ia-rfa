from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.progress import ProgressResponse, StreakResponse
from app.services.progress_service import (
    get_user_progress,
    get_activity_log,
    compute_streak,
)

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=ProgressResponse)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get overall progress stats for the current user."""
    data = await get_user_progress(current_user.id, db)
    return ProgressResponse(**data)


@router.get("/activity")
async def get_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent activity log for the current user."""
    activities = await get_activity_log(current_user.id, db)
    return activities


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current and longest consecutive-day streak for the user."""
    data = await compute_streak(current_user.id, db)
    return StreakResponse(**data)
