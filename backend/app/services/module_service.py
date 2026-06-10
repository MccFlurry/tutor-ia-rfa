"""
services/module_service.py — Single source of truth for the sequential
module-unlock rule.

The course is a guided path: a module stays **locked** until the immediately
previous module has *all* its topics completed. This invariant must hold
identically everywhere it is consulted — the module list, the dashboard
recommendations, and the access gates on module/topic detail. Centralising it
here prevents the surfaces from drifting apart (which is exactly how a locked
module ended up being recommended and enterable).
"""
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.module import Module
from app.models.topic import Topic
from app.models.progress import UserTopicProgress

LOCKED_DETAIL = (
    "Este contenido pertenece a un módulo bloqueado. "
    "Completa el módulo anterior para desbloquearlo."
)


def compute_locks(progress_pairs: list[tuple[int, int]]) -> list[bool]:
    """Apply the sequential-unlock rule over modules in ``order_index`` order.

    Args:
        progress_pairs: ``(total_topics, completed_topics)`` per module, ordered.

    Returns:
        ``is_locked`` per module, same order. The first module is always
        unlocked; every other module is locked until the previous one has all
        its topics completed. A module with zero topics never counts as
        complete, so it keeps the next module locked.
    """
    locks: list[bool] = []
    prev_completed = True  # the first module depends on nothing
    for total, completed in progress_pairs:
        locks.append(not prev_completed)
        prev_completed = total > 0 and completed >= total
    return locks


async def get_module_progress(
    user_id, db: AsyncSession
) -> tuple[list[Module], list[tuple[int, int]]]:
    """Módulos activos ordenados + (total, completados) por módulo.

    Base compartida del invariante de desbloqueo y de la posición del
    companion — un solo lugar emite estas consultas.
    """
    mods_res = await db.execute(
        select(Module).where(Module.is_active == True).order_by(Module.order_index)
    )
    modules = list(mods_res.scalars().all())

    totals_rows = (
        await db.execute(
            select(Topic.module_id, func.count(Topic.id))
            .where(Topic.is_active == True)
            .group_by(Topic.module_id)
        )
    ).all()
    totals = {module_id: count for module_id, count in totals_rows}

    done_rows = (
        await db.execute(
            select(Topic.module_id, func.count(UserTopicProgress.id))
            .join(UserTopicProgress, UserTopicProgress.topic_id == Topic.id)
            .where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.is_completed == True,
                Topic.is_active == True,
            )
            .group_by(Topic.module_id)
        )
    ).all()
    done = {module_id: count for module_id, count in done_rows}

    pairs = [(totals.get(m.id, 0), done.get(m.id, 0)) for m in modules]
    return modules, pairs


async def get_module_locks(user_id, db: AsyncSession) -> dict[int, bool]:
    """Return ``{module_id: is_locked}`` for all active modules."""
    modules, pairs = await get_module_progress(user_id, db)
    locks = compute_locks(pairs)
    return {m.id: is_locked for m, is_locked in zip(modules, locks)}


async def assert_module_unlocked(module_id: int, user_id, db: AsyncSession) -> None:
    """Raise 403 if the given module is still locked for this user."""
    locks = await get_module_locks(user_id, db)
    if locks.get(module_id, False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=LOCKED_DETAIL,
        )


async def assert_topic_unlocked(topic_id: int, user_id, db: AsyncSession) -> None:
    """Raise 403 if the topic's module is still locked for this user.

    Resolves the topic's module first. A missing topic is left for the caller's
    own 404 handling (the gate is a no-op so the real error surfaces).
    """
    row = await db.execute(select(Topic.module_id).where(Topic.id == topic_id))
    module_id = row.scalar_one_or_none()
    if module_id is not None:
        await assert_module_unlocked(module_id, user_id, db)
