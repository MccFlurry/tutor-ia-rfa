from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.topic import Topic
from app.models.module import Module
from app.models.progress import UserTopicProgress
from app.schemas.topic import (
    TopicResponse,
    TopicModuleInfo,
    TopicProgressInfo,
    TopicVisitResponse,
    TopicCompleteResponse,
    TopicTimeRequest,
    TopicTimeResponse,
)

router = APIRouter(prefix="/topics", tags=["topics"])


async def _get_topic_or_404(topic_id: int, db: AsyncSession) -> Topic:
    result = await db.execute(
        select(Topic).where(Topic.id == topic_id, Topic.is_active == True)
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema no encontrado")
    return topic


async def _get_or_create_progress(
    user_id, topic_id: int, db: AsyncSession
) -> UserTopicProgress:
    result = await db.execute(
        select(UserTopicProgress).where(
            UserTopicProgress.user_id == user_id,
            UserTopicProgress.topic_id == topic_id,
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        progress = UserTopicProgress(
            user_id=user_id,
            topic_id=topic_id,
        )
        db.add(progress)
        await db.flush()
    return progress


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full topic content with module info and user progress."""
    topic = await _get_topic_or_404(topic_id, db)

    # Get module info
    module_result = await db.execute(
        select(Module).where(Module.id == topic.module_id)
    )
    module = module_result.scalar_one()

    # Get user progress
    progress_result = await db.execute(
        select(UserTopicProgress).where(
            UserTopicProgress.user_id == current_user.id,
            UserTopicProgress.topic_id == topic_id,
        )
    )
    progress = progress_result.scalar_one_or_none()

    progress_info = None
    if progress:
        progress_info = TopicProgressInfo(
            is_completed=progress.is_completed,
            time_spent_seconds=progress.time_spent_seconds,
            first_visited_at=progress.first_visited_at,
            completed_at=progress.completed_at,
        )

    return TopicResponse(
        id=topic.id,
        title=topic.title,
        content_markdown=topic.content,
        video_url=topic.video_url,
        estimated_minutes=topic.estimated_minutes,
        has_quiz=topic.has_quiz,
        order_index=topic.order_index,
        module=TopicModuleInfo(id=module.id, title=module.title),
        progress_info=progress_info,
    )


@router.post("/{topic_id}/visit", response_model=TopicVisitResponse)
async def visit_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a visit to a topic. Creates or updates progress record."""
    await _get_topic_or_404(topic_id, db)
    now = datetime.now(timezone.utc)

    progress = await _get_or_create_progress(current_user.id, topic_id, db)
    if not progress.first_visited_at:
        progress.first_visited_at = now
    progress.last_accessed_at = now
    await db.commit()

    return TopicVisitResponse(message="Visita registrada")


@router.post("/{topic_id}/complete", response_model=TopicCompleteResponse)
async def complete_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a topic as completed manually (for topics without quiz)."""
    await _get_topic_or_404(topic_id, db)
    now = datetime.now(timezone.utc)

    progress = await _get_or_create_progress(current_user.id, topic_id, db)
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = now
    if not progress.first_visited_at:
        progress.first_visited_at = now
    progress.last_accessed_at = now
    await db.commit()

    return TopicCompleteResponse(message="Tema marcado como completado", is_completed=True)


@router.post("/{topic_id}/time", response_model=TopicTimeResponse)
async def track_time(
    topic_id: int,
    body: TopicTimeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accumulate study time for a topic."""
    await _get_topic_or_404(topic_id, db)

    progress = await _get_or_create_progress(current_user.id, topic_id, db)
    progress.time_spent_seconds += body.seconds
    progress.last_accessed_at = datetime.now(timezone.utc)
    await db.commit()

    return TopicTimeResponse(
        message="Tiempo registrado",
        total_seconds=progress.time_spent_seconds,
    )
