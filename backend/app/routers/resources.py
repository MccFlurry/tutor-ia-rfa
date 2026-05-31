"""routers/resources.py — Recursos de aprendizaje (lectura para estudiantes)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.learning_resource import LearningResource
from app.schemas.learning_resource import LearningResourceResponse

router = APIRouter(prefix="/resources", tags=["resources"])


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
