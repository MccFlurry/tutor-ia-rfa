from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.models.user import User
from app.models.module import Module
from app.models.topic import Topic
from app.models.progress import UserTopicProgress
from app.models.coding import CodingChallenge
from app.schemas.module import ModuleResponse, ModuleDetailResponse, TopicBrief
from app.services.module_service import compute_locks, get_module_locks
from app.utils.cache import cached_json

router = APIRouter(prefix="/modules", tags=["modules"])

MODULES_LIST_CACHE_TTL = 60  # seconds — short TTL para mantener frescura


@router.get("", response_model=list[ModuleResponse])
async def list_modules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """List all active modules with progress for the current user."""
    cache_key = f"modules:list:{current_user.id}"

    async def _build() -> list[dict]:
        items = await _compute_modules_list(current_user, db)
        return [m.model_dump(mode="json") for m in items]

    cached = await cached_json(
        redis_client, cache_key, ttl=MODULES_LIST_CACHE_TTL, loader=_build
    )
    return [ModuleResponse.model_validate(m) for m in cached]


async def _compute_modules_list(
    current_user: User, db: AsyncSession
) -> list[ModuleResponse]:
    # Get all active modules ordered
    result = await db.execute(
        select(Module).where(Module.is_active == True).order_by(Module.order_index)
    )
    modules = list(result.scalars().all())

    # Gather per-module progress in order, then apply the shared unlock rule.
    stats: list[tuple[Module, int, int]] = []  # (module, total, completed)
    pairs: list[tuple[int, int]] = []
    for module in modules:
        total_q = await db.execute(
            select(func.count(Topic.id))
            .where(Topic.module_id == module.id, Topic.is_active == True)
        )
        total_topics = total_q.scalar() or 0

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
        stats.append((module, total_topics, completed_topics))
        pairs.append((total_topics, completed_topics))

    locks = compute_locks(pairs)

    response = []
    for (module, total_topics, completed_topics), is_locked in zip(stats, locks):
        progress_pct = (completed_topics / total_topics * 100) if total_topics > 0 else 0.0
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

    # Sequential-unlock gate: a locked module exposes its metadata but withholds
    # its topics, so the student can't enter content before earning access.
    locks = await get_module_locks(current_user.id, db)
    if locks.get(module_id, False):
        return ModuleDetailResponse(
            id=module.id,
            title=module.title,
            description=module.description,
            order_index=module.order_index,
            icon_name=module.icon_name,
            color_hex=module.color_hex,
            total_topics=0,
            completed_topics=0,
            progress_pct=0.0,
            is_locked=True,
            topics=[],
        )

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

    # Coding challenge presence per topic (catalogue only, exclude per-student AI copies)
    coding_result = await db.execute(
        select(CodingChallenge.topic_id, func.count(CodingChallenge.id))
        .where(
            CodingChallenge.topic_id.in_([t.id for t in topics]) if topics else False,
            CodingChallenge.is_ai_generated == False,
        )
        .group_by(CodingChallenge.topic_id)
    )
    coding_map = {row[0]: row[1] for row in coding_result.all()} if topics else {}

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
            has_coding_challenge=coding_map.get(topic.id, 0) > 0,
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
        is_locked=False,
        topics=topic_briefs,
    )
