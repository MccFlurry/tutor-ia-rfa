"""routers/tutor.py — Nudges proactivos del tutor (deterministas)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.models.user import User
from app.schemas.companion import CompanionResponse
from app.schemas.tutor import NudgeResponse
from app.services.companion_service import gather_companion
from app.services.tutor_service import get_nudges
from app.utils.cache import cached_json

router = APIRouter(prefix="/tutor", tags=["tutor"])

_NO_CACHE = {"quiz_result", "coding_result", "assessment_result"}
NUDGE_CACHE_TTL = 30  # seconds
# Hasta 60s de desfase tras mutaciones; los endpoints de quiz/topic/coding
# invalidan companion:{user_id} al mutar, así el panel se refresca al volver.
# Race cache-aside posible (GET concurrente re-escribe dato pre-commit tras
# la invalidación); el TTL de 60s lo auto-corrige — aceptado.
COMPANION_CACHE_TTL = 60  # seconds


@router.get("/nudges", response_model=NudgeResponse)
async def get_tutor_nudges(
    context: str = Query(..., description="dashboard|topic|module|*_result"),
    topic_id: int | None = None,
    module_id: int | None = None,
    score: float | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    async def _build() -> dict:
        nudges = await get_nudges(
            current_user, db, context,
            topic_id=topic_id, module_id=module_id, score=score,
        )
        return NudgeResponse(nudges=nudges).model_dump(mode="json")

    if context in _NO_CACHE:
        payload = await _build()
    else:
        key = f"nudges:{current_user.id}:{context}:{topic_id}:{module_id}"
        payload = await cached_json(
            redis_client, key, ttl=NUDGE_CACHE_TTL, loader=_build
        )
    return NudgeResponse.model_validate(payload)


@router.get("/companion", response_model=CompanionResponse)
async def get_tutor_companion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """Posición del estudiante + diagnóstico del módulo actual (Fase 5, sin LLM)."""

    async def _build() -> dict:
        payload = await gather_companion(current_user, db)
        return payload.model_dump(mode="json")

    data = await cached_json(
        redis_client,
        f"companion:{current_user.id}",
        ttl=COMPANION_CACHE_TTL,
        loader=_build,
    )
    return CompanionResponse.model_validate(data)
