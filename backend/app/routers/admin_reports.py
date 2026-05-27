"""routers/admin_reports.py — /admin/students/* endpoints for pedagogical reports."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin, get_redis
from app.models.user import User
from app.schemas.admin_reports import (
    StudentRow, StudentDetail, AIReport,
    CohortReportRequest, CohortAIReport,
)
from app.services import student_report_service
from app.services.student_report_service import (
    InsufficientActivityError, LLMReportError,
)
from app.utils.logger import logger


router = APIRouter(prefix="/admin/students", tags=["admin-reports"])


@router.get("", response_model=list[StudentRow])
async def list_students(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await student_report_service.get_students_overview(db)


# NOTE: register /cohort/* BEFORE /{user_id}/* — otherwise the parameterized
# route swallows the literal "cohort" path segment and FastAPI returns
# 422 (uuid_parsing) for valid cohort requests.
@router.post("/cohort/ai-report", response_model=CohortAIReport)
async def generate_cohort(
    body: CohortReportRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    try:
        return await student_report_service.generate_cohort_report(
            db, redis_client, body.user_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMReportError as e:
        logger.error(f"Cohort AI report falló: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio IA no disponible. Reintenta en unos minutos.",
        )


@router.get("/{user_id}", response_model=StudentDetail)
async def get_detail(
    user_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await student_report_service.get_student_detail(db, user_id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudiante no encontrado",
        )


@router.post("/{user_id}/ai-report", response_model=AIReport)
async def generate_report(
    user_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    try:
        return await student_report_service.generate_ai_report(db, redis_client, user_id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudiante no encontrado",
        )
    except InsufficientActivityError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except LLMReportError as e:
        logger.error(f"AI report fallo: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio IA no disponible. Reintenta en unos minutos.",
        )
