"""
routers/assessment.py — Evaluación de entrada diagnóstica (Fase 6 CRISP-DM).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.user_level import UserLevel
from app.models.module import Module
from app.models.entry_assessment import EntryAssessmentSession
from app.schemas.assessment import (
    AssessmentStartResponse,
    AssessmentQuestionResponse,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
    ModuleScoreBreakdown,
)
from app.services.entry_assessment_service import (
    generate_assessment,
    AssessmentGenerationError,
)
from app.services.leveling_service import compute_level, upsert_user_level
from app.utils.logger import logger

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.post("/start", response_model=AssessmentStartResponse)
async def start_assessment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new entry assessment. Generates questions via LLM (or bank fallback),
    persists session with correct answers, returns session_id + questions (no answers).
    """
    try:
        generated, source = await generate_assessment(db)
    except AssessmentGenerationError as e:
        logger.error(f"No se pudo generar evaluación de entrada: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo generar la evaluación de entrada. Intenta más tarde.",
        )

    # Persist session with full questions (including correct_index) for grading
    questions_payload = []
    response_questions = []
    for i, q in enumerate(generated):
        qid = f"q{i}"
        questions_payload.append({
            "id": qid,
            "question_text": q.question_text,
            "options": q.options,
            "correct_index": q.correct_index,
            "module_id": q.module_id,
            "difficulty": q.difficulty,
        })
        response_questions.append(AssessmentQuestionResponse(
            id=qid,
            question_text=q.question_text,
            options=q.options,
            module_id=q.module_id,
            difficulty=q.difficulty,
        ))

    session = EntryAssessmentSession(
        user_id=current_user.id,
        questions=questions_payload,
    )
    db.add(session)
    await db.flush()
    await db.commit()

    return AssessmentStartResponse(
        session_id=session.id,
        questions=response_questions,
        source=source,
    )


@router.post("/submit", response_model=AssessmentSubmitResponse)
async def submit_assessment(
    body: AssessmentSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grade entry assessment, compute level, persist UserLevel."""
    result = await db.execute(
        select(EntryAssessmentSession).where(
            EntryAssessmentSession.id == body.session_id,
            EntryAssessmentSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión de evaluación no encontrada",
        )

    if session.score is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta sesión ya fue enviada",
        )

    computation = compute_level(session.questions, body.answers)

    # Persist answers + score on session
    session.answers = body.answers
    session.score = computation.score
    session.computed_level = computation.level

    # Upsert user level
    await upsert_user_level(
        db, current_user.id, computation.level, computation.score, reason="entry"
    )

    # Resolve module titles for breakdown
    module_ids = list(computation.module_breakdown.keys())
    mods_result = await db.execute(select(Module).where(Module.id.in_(module_ids)))
    title_map = {m.id: m.title for m in mods_result.scalars().all()}

    breakdown = [
        ModuleScoreBreakdown(
            module_id=mid,
            module_title=title_map.get(mid, f"Módulo {mid}"),
            correct=stats["correct"],
            total=stats["total"],
            percentage=stats["percentage"],
        )
        for mid, stats in computation.module_breakdown.items()
    ]

    # Level-appropriate feedback message
    feedback_map = {
        "beginner": (
            "Comenzarás como Principiante. El sistema te ofrecerá explicaciones más detalladas "
            "y ejercicios con pistas explícitas. Avanza a tu ritmo — ¡puedes subir de nivel!"
        ),
        "intermediate": (
            "Tu nivel es Intermedio. Recibirás ejercicios con aplicación práctica y lógica moderada. "
            "Combina conceptos y profundiza en casos reales."
        ),
        "advanced": (
            "¡Nivel Avanzado! El sistema te desafiará con edge cases, optimización y patrones. "
            "Prepárate para problemas sin pistas."
        ),
    }

    await db.commit()

    logger.info(
        f"Usuario {current_user.id} evaluado: nivel={computation.level}, "
        f"score={computation.score}, confidence={computation.confidence}"
    )

    return AssessmentSubmitResponse(
        level=computation.level,
        score=computation.score,
        confidence=computation.confidence,
        module_breakdown=breakdown,
        feedback=feedback_map.get(computation.level, ""),
    )
