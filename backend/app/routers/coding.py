"""
routers/coding.py — Desafíos de programación con evaluación por IA.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.models.user import User
from app.services.companion_service import invalidate_companion
from app.services.resource_recommender_service import invalidate_resource_recs
from app.models.coding import CodingChallenge, CodingSubmission
from app.models.topic import Topic
from app.schemas.coding import (
    CodingChallengeResponse,
    CodingSubmitRequest,
    CodingEvaluationResponse,
    CodingSubmissionHistory,
    TopicChallengesResponse,
    TopicChallengeForStudent,
)
from app.schemas.quiz import LevelChange
from app.services.code_eval_service import evaluate_code
from app.services.topic_completion_service import check_and_complete_topic, get_topic_completion_status
from app.services.leveling_service import get_user_level, auto_apply_reassessment
from app.services.coding_generator_service import (
    get_or_generate_for_student,
    regenerate_for_student,
)
from app.services.module_service import assert_module_unlocked, assert_topic_unlocked
from app.utils.logger import logger

router = APIRouter(prefix="/coding", tags=["coding"])


@router.get("/topic/{topic_id}", response_model=TopicChallengeForStudent)
async def get_or_generate_challenge_for_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a coding challenge for the current student on this topic.
    If one already exists (AI-generated for this user+topic), return it.
    Otherwise ask the LLM to build one adapted to the student's level.
    Falls back to cloning from the teacher's seeded catalogue when LLM fails.
    """
    topic_result = await db.execute(
        select(Topic).where(Topic.id == topic_id, Topic.is_active == True)
    )
    topic = topic_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema no encontrado")

    # Sequential-unlock gate: don't generate a challenge for a locked module.
    await assert_module_unlocked(topic.module_id, current_user.id, db)

    # Ensure the topic has at least a fallback catalogue OR content worth generating from
    fallback_result = await db.execute(
        select(func.count(CodingChallenge.id)).where(
            CodingChallenge.topic_id == topic_id,
            CodingChallenge.is_ai_generated == False,
        )
    )
    has_fallback = (fallback_result.scalar() or 0) > 0
    if not topic.content and not has_fallback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este tema no tiene desafíos de programación disponibles",
        )

    student_level = await get_user_level(db, current_user.id)

    try:
        challenge = await get_or_generate_for_student(db, topic, current_user, student_level)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    await db.commit()

    source = "ai" if challenge.title and not challenge.title.startswith("[Fallback]") else "fallback"
    return TopicChallengeForStudent(
        challenge=CodingChallengeResponse.model_validate(challenge),
        source=source,
        student_level=student_level,
    )


@router.post("/topic/{topic_id}/regenerate", response_model=TopicChallengeForStudent)
async def regenerate_challenge_for_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Force a fresh AI-generated coding challenge for this student+topic."""
    topic_result = await db.execute(
        select(Topic).where(Topic.id == topic_id, Topic.is_active == True)
    )
    topic = topic_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema no encontrado")

    # Sequential-unlock gate: don't regenerate a challenge for a locked module.
    await assert_module_unlocked(topic.module_id, current_user.id, db)

    student_level = await get_user_level(db, current_user.id)

    try:
        challenge = await regenerate_for_student(db, topic, current_user, student_level)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    await db.commit()

    source = "ai" if challenge.title and not challenge.title.startswith("[Fallback]") else "fallback"
    return TopicChallengeForStudent(
        challenge=CodingChallengeResponse.model_validate(challenge),
        source=source,
        student_level=student_level,
    )


@router.get("/challenge/{challenge_id}", response_model=CodingChallengeResponse)
async def get_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single coding challenge by ID."""
    result = await db.execute(
        select(CodingChallenge).where(CodingChallenge.id == challenge_id)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Desafío no encontrado")

    return CodingChallengeResponse.model_validate(challenge)


@router.post("/challenge/{challenge_id}/submit", response_model=CodingEvaluationResponse)
async def submit_code(
    challenge_id: int,
    body: CodingSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """Submit code for evaluation by the LLM."""
    # Get challenge
    result = await db.execute(
        select(CodingChallenge).where(CodingChallenge.id == challenge_id)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Desafío no encontrado")

    # Sequential-unlock gate: a passing submission completes the topic, which feeds
    # the unlock rule — refuse so a locked module can't be unlocked by the back door.
    await assert_topic_unlocked(challenge.topic_id, current_user.id, db)

    # Evaluate code with LLM (adapted to student level)
    student_level = await get_user_level(db, current_user.id)
    try:
        evaluation = await evaluate_code(
            title=challenge.title,
            description=challenge.description,
            student_code=body.code,
            language=challenge.language,
            solution_code=challenge.solution_code,
            student_level=student_level,
            initial_code=challenge.initial_code,
        )
    except Exception as e:
        logger.error(f"Error evaluando código para desafío {challenge_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de evaluación de código no está disponible en este momento.",
        )

    # Save submission
    submission = CodingSubmission(
        user_id=current_user.id,
        challenge_id=challenge_id,
        code=body.code,
        score=evaluation["score"],
        feedback=evaluation["feedback"],
        strengths=evaluation["strengths"],
        improvements=evaluation["improvements"],
    )
    db.add(submission)
    await db.flush()

    logger.info(f"Código evaluado: desafío {challenge_id}, usuario {current_user.id}, score {evaluation['score']}")

    # If score >= 60, check if topic can be fully completed (quiz + all coding)
    if evaluation["score"] >= 60:
        await check_and_complete_topic(current_user.id, challenge.topic_id, db)

    level_change_payload: LevelChange | None = None
    try:
        change = await auto_apply_reassessment(db, current_user.id)
        if change is not None:
            logger.info(
                f"Nivel auto-aplicado usuario {current_user.id}: "
                f"{change['previous_level']} → {change['new_level']} ({change['reason']})"
            )
            level_change_payload = LevelChange(**change)
    except Exception as e:
        logger.warning(f"Error aplicando re-asignación automática: {e}")

    await db.commit()

    # El diagnóstico del companion cambia tras una entrega de código
    await invalidate_companion(redis_client, current_user.id)
    await invalidate_resource_recs(redis_client, current_user.id)

    return CodingEvaluationResponse(
        submission_id=submission.id,
        score=evaluation["score"],
        feedback=evaluation["feedback"],
        strengths=evaluation["strengths"],
        improvements=evaluation["improvements"],
        level_change=level_change_payload,
    )


@router.get("/challenge/{challenge_id}/history", response_model=list[CodingSubmissionHistory])
async def get_submission_history(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get submission history for a challenge."""
    result = await db.execute(
        select(CodingSubmission)
        .where(
            CodingSubmission.challenge_id == challenge_id,
            CodingSubmission.user_id == current_user.id,
        )
        .order_by(CodingSubmission.submitted_at.desc())
        .limit(10)
    )
    submissions = result.scalars().all()

    return [CodingSubmissionHistory.model_validate(s) for s in submissions]


@router.get("/challenge/{challenge_id}/best", response_model=CodingSubmissionHistory | None)
async def get_best_submission(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the best submission for a challenge."""
    result = await db.execute(
        select(CodingSubmission)
        .where(
            CodingSubmission.challenge_id == challenge_id,
            CodingSubmission.user_id == current_user.id,
        )
        .order_by(CodingSubmission.score.desc())
        .limit(1)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        return None

    return CodingSubmissionHistory.model_validate(submission)


@router.get("/topic/{topic_id}/completion-status", response_model=dict)
async def get_completion_status(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed completion status for a topic (quiz + coding requirements)."""
    return await get_topic_completion_status(current_user.id, topic_id, db)
