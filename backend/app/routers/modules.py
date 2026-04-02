from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.module import Module
from app.models.topic import Topic
from app.models.progress import UserTopicProgress
from app.schemas.module import ModuleResponse, ModuleDetailResponse, TopicBrief

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=list[ModuleResponse])
async def list_modules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active modules with progress for the current user."""
    # Get all active modules ordered
    result = await db.execute(
        select(Module).where(Module.is_active == True).order_by(Module.order_index)
    )
    modules = result.scalars().all()

    response = []
    prev_completed = True  # First module is always unlocked

    for module in modules:
        # Count total topics
        total_q = await db.execute(
            select(func.count(Topic.id))
            .where(Topic.module_id == module.id, Topic.is_active == True)
        )
        total_topics = total_q.scalar() or 0

        # Count completed topics for this user
        completed_q = await db.execute(
            select(func.count(UserTopicProgress.id))
            .join(Topic, Topic.id == UserTopicProgress.topic_id)
            .where(
                UserTopicProgress.user_id == current_user.id,
                Topic.module_id == module.id,
                Topic.is_active == True,
                UserTopicProgress.is_completed == True,
            )
        )
        completed_topics = completed_q.scalar() or 0

        progress_pct = (completed_topics / total_topics * 100) if total_topics > 0 else 0.0
        is_locked = not prev_completed

        response.append(ModuleResponse(
            id=module.id,
            title=module.title,
            description=module.description,
            order_index=module.order_index,
            icon_name=module.icon_name,
            color_hex=module.color_hex,
            total_topics=total_topics,
            completed_topics=completed_topics,
            progress_pct=round(progress_pct, 1),
            is_locked=is_locked,
        ))

        # A module is "completed" for unlock purposes if all topics are done
        if total_topics > 0 and completed_topics >= total_topics:
            prev_completed = True
        else:
            prev_completed = False

    return response


@router.get("/{module_id}", response_model=ModuleDetailResponse)
async def get_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get module detail with its topics and progress status."""
    result = await db.execute(
        select(Module).where(Module.id == module_id, Module.is_active == True)
    )
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")

    # Get topics
    topics_result = await db.execute(
        select(Topic)
        .where(Topic.module_id == module_id, Topic.is_active == True)
        .order_by(Topic.order_index)
    )
    topics = topics_result.scalars().all()

    # Get progress for all topics in this module
    progress_result = await db.execute(
        select(UserTopicProgress)
        .where(
            UserTopicProgress.user_id == current_user.id,
            UserTopicProgress.topic_id.in_([t.id for t in topics]) if topics else False,
        )
    )
    progress_map = {p.topic_id: p for p in progress_result.scalars().all()} if topics else {}

    topic_briefs = []
    completed_count = 0
    for topic in topics:
        prog = progress_map.get(topic.id)
        if prog and prog.is_completed:
            topic_status = "completed"
            completed_count += 1
        elif prog and prog.first_visited_at:
            topic_status = "in_progress"
        else:
            topic_status = "not_started"

        topic_briefs.append(TopicBrief(
            id=topic.id,
            title=topic.title,
            order_index=topic.order_index,
            estimated_minutes=topic.estimated_minutes,
            has_quiz=topic.has_quiz,
            status=topic_status,
        ))

    total_topics = len(topics)
    progress_pct = (completed_count / total_topics * 100) if total_topics > 0 else 0.0

    return ModuleDetailResponse(
        id=module.id,
        title=module.title,
        description=module.description,
        order_index=module.order_index,
        icon_name=module.icon_name,
        color_hex=module.color_hex,
        total_topics=total_topics,
        completed_topics=completed_count,
        progress_pct=round(progress_pct, 1),
        topics=topic_briefs,
    )
