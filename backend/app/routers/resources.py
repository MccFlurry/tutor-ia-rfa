"""routers/resources.py — Recursos de aprendizaje (lectura para estudiantes)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.models.user import User
from app.models.learning_resource import LearningResource
from app.schemas.learning_resource import LearningResourceResponse, RecommendationResponse
from app.services.resource_recommender_service import (
    gather_recommendations, resource_rec_cache_key,
)
from app.utils.cache import cached_json

router = APIRouter(prefix="/resources", tags=["resources"])

RECOMMEND_CACHE_TTL = 1800


@router.get("", response_model=list[LearningResourceResponse])
async def list_resources(
    module_id: int | None = Query(None),
    topic_id: int | None = Query(None),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Recursos activos filtrados por módulo y/o tema, ordenados."""
    query = select(LearningResource).where(LearningResource.is_active == True)  # noqa: E712
    if topic_id is not None:
        query = query.where(LearningResource.topic_id == topic_id)
    if module_id is not None:
        query = query.where(LearningResource.module_id == module_id)
    query = query.order_by(LearningResource.order_index, LearningResource.id)
    result = await db.execute(query)
    return [LearningResourceResponse.model_validate(r) for r in result.scalars().all()]


async def _recommendations_payload(user, db, module_id, topic_id) -> dict:
    resp = await gather_recommendations(user, db, module_id, topic_id)
    return resp.model_dump(mode="json")


@router.get("/recommended", response_model=RecommendationResponse)
async def recommended_resources(
    module_id: int | None = Query(None),
    topic_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """Recursos curados reordenados y justificados por IA (fallback al orden
    curado). Exactamente uno de module_id | topic_id."""
    if (module_id is None) == (topic_id is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Especifica exactamente uno: module_id o topic_id.",
        )
    scope = f"m{module_id}" if module_id is not None else f"t{topic_id}"
    return await cached_json(
        redis_client,
        resource_rec_cache_key(user.id, scope),
        ttl=RECOMMEND_CACHE_TTL,
        loader=lambda: _recommendations_payload(user, db, module_id, topic_id),
    )
