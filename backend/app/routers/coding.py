"""
routers/coding.py — Desafíos de programación con evaluación por IA.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.coding import CodingChallenge, CodingSubmission
from app.schemas.coding import (
    CodingChallengeResponse,
    CodingSubmitRequest,
    CodingEvaluationResponse,
    CodingSubmissionHistory,
    TopicChallengesResponse,
)
from app.services.code_eval_service import evaluate_code
from app.services.topic_completion_service import check_and_complete_topic, get_topic_completion_status
from app.utils.logger import logger

router = APIRouter(prefix="/coding", tags=["coding"])


@router.get("/topic/{topic_id}", response_model=TopicChallengesResponse)
async def get_challenges_for_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all coding challenges for a topic."""
    result = await db.execute(
        select(CodingChallenge)
        .where(CodingChallenge.topic_id == topic_id)
        .order_by(CodingChallenge.order_index)
    )
    challenges = result.scalars().all()

    return TopicChallengesResponse(
        topic_id=topic_id,
        challenges=[CodingChallengeResponse.model_validate(c) for c in challenges],
        has_challenges=len(challenges) > 0,
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
):
    """Submit code for evaluation by the LLM."""
    # Get challenge
    result = await db.execute(
        select(CodingChallenge).where(CodingChallenge.id == challenge_id)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Desafío no encontrado")

    # Evaluate code with LLM
    try:
        evaluation = await evaluate_code(
            title=challenge.title,
            description=challenge.description,
            student_code=body.code,
            language=challenge.language,
            solution_code=challenge.solution_code,
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

    await db.commit()

    return CodingEvaluationResponse(
        submission_id=submission.id,
        score=evaluation["score"],
        feedback=evaluation["feedback"],
        strengths=evaluation["strengths"],
        improvements=evaluation["improvements"],
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
