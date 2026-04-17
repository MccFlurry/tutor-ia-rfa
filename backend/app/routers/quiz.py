import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.config import settings
from app.models.user import User
from app.models.topic import Topic
from app.models.quiz import QuizQuestion, QuizAttempt
from app.schemas.quiz import (
    QuizQuestionResponse,
    QuizGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizFeedbackItem,
    QuizAttemptResponse,
)
from app.services.llm_service import generate_quiz_questions, QuizGenerationError
from app.services.topic_completion_service import check_and_complete_topic
from app.services.leveling_service import get_user_level, check_reassessment
from app.utils.logger import logger

router = APIRouter(prefix="/quiz", tags=["quiz"])


async def _build_session_from_db(
    topic_id: int, user_id: uuid.UUID, db: AsyncSession, redis_client
) -> QuizGenerateResponse | None:
    """Fallback: build a quiz session from static DB questions."""
    result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.topic_id == topic_id)
        .order_by(QuizQuestion.order_index)
    )
    db_questions = result.scalars().all()

    if not db_questions:
        return None

    session_id = str(uuid.uuid4())
    session_data = {"topic_id": topic_id, "questions": {}}
    response_questions = []

    for i, q in enumerate(db_questions):
        qid = f"q{i}"
        session_data["questions"][qid] = {
            "question_text": q.question_text,
            "options": q.options,
            "correct_index": q.correct_option_index,
            "explanation": q.explanation or "Sin explicación disponible.",
        }
        response_questions.append(QuizQuestionResponse(
            id=qid,
            question_text=q.question_text,
            options=q.options,
        ))

    await _save_session(session_id, session_data, user_id, topic_id, redis_client)

    return QuizGenerateResponse(session_id=session_id, questions=response_questions)


def _active_key(user_id: uuid.UUID, topic_id: int) -> str:
    """Redis key that points to the user's active (unsubmitted) quiz session for a topic."""
    return f"quiz_active:{user_id}:{topic_id}"


async def _recover_active_session(
    user_id: uuid.UUID, topic_id: int, redis_client
) -> QuizGenerateResponse | None:
    """Return the existing unsubmitted quiz session if one exists."""
    active_key = _active_key(user_id, topic_id)
    session_id = await redis_client.get(active_key)
    if not session_id:
        return None

    raw = await redis_client.get(f"quiz_session:{session_id}")
    if not raw:
        # Session expired but pointer remained — clean up
        await redis_client.delete(active_key)
        return None

    session_data = json.loads(raw)
    questions = session_data["questions"]

    response_questions = [
        QuizQuestionResponse(
            id=qid,
            question_text=q["question_text"],
            options=q["options"],
        )
        for qid, q in questions.items()
    ]

    logger.info(f"Quiz sesión activa recuperada para tema {topic_id}, sesión {session_id}")
    return QuizGenerateResponse(session_id=session_id, questions=response_questions)


async def _save_session(
    session_id: str, session_data: dict, user_id: uuid.UUID, topic_id: int, redis_client
) -> None:
    """Save quiz session and set the active pointer for the user+topic."""
    await redis_client.setex(
        f"quiz_session:{session_id}",
        settings.QUIZ_SESSION_TTL,
        json.dumps(session_data, ensure_ascii=False),
    )
    await redis_client.setex(
        _active_key(user_id, topic_id),
        settings.QUIZ_SESSION_TTL,
        session_id,
    )


@router.get("/topic/{topic_id}", response_model=QuizGenerateResponse)
async def get_quiz(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """
    Generate a quiz for a topic using AI (Ollama).
    If the user already has an active (unsubmitted) session, returns it.
    Falls back to static DB questions if LLM is unavailable.
    """
    # Verify topic exists and has quiz
    topic_result = await db.execute(
        select(Topic).where(Topic.id == topic_id, Topic.is_active == True)
    )
    topic = topic_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema no encontrado")
    if not topic.has_quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Este tema no tiene autoevaluación")

    # Check for existing active session (user left without submitting)
    existing = await _recover_active_session(current_user.id, topic_id, redis_client)
    if existing:
        return existing

    # Try AI generation (adapted to student level)
    student_level = await get_user_level(db, current_user.id)
    try:
        generated = await generate_quiz_questions(topic.content, student_level=student_level)

        session_id = str(uuid.uuid4())
        session_data = {"topic_id": topic_id, "questions": {}}
        response_questions = []

        for i, q in enumerate(generated):
            qid = f"q{i}"
            session_data["questions"][qid] = {
                "question_text": q.question_text,
                "options": q.options,
                "correct_index": q.correct_option_index,
                "explanation": q.explanation,
            }
            response_questions.append(QuizQuestionResponse(
                id=qid,
                question_text=q.question_text,
                options=q.options,
            ))

        await _save_session(session_id, session_data, current_user.id, topic_id, redis_client)

        logger.info(f"Quiz IA generado para tema {topic_id}, sesión {session_id}")
        return QuizGenerateResponse(session_id=session_id, questions=response_questions)

    except QuizGenerationError as e:
        logger.warning(f"Fallback a BD para tema {topic_id}: {e}")

    except Exception as e:
        logger.error(f"Error inesperado generando quiz para tema {topic_id}: {e}")

    # Fallback to DB questions
    fallback = await _build_session_from_db(topic_id, current_user.id, db, redis_client)
    if fallback:
        logger.info(f"Quiz fallback (BD) para tema {topic_id}, sesión {fallback.session_id}")
        return fallback

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="El servicio de generación de preguntas no está disponible y no hay preguntas de respaldo.",
    )


@router.post("/topic/{topic_id}/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    topic_id: int,
    body: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """Submit quiz answers. Grades against Redis-stored answer key."""
    # Fetch session from Redis
    raw = await redis_client.get(f"quiz_session:{body.session_id}")
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="La sesión de autoevaluación ha expirado. Genera una nueva.",
        )

    session_data = json.loads(raw)
    questions = session_data["questions"]

    # Grade answers
    correct_count = 0
    feedback = []

    for qid, q_data in questions.items():
        selected = body.answers.get(qid, -1)
        correct_idx = q_data["correct_index"]
        is_correct = selected == correct_idx

        if is_correct:
            correct_count += 1

        feedback.append(QuizFeedbackItem(
            question_id=qid,
            question_text=q_data["question_text"],
            selected_index=selected,
            correct_index=correct_idx,
            is_correct=is_correct,
            explanation=q_data.get("explanation"),
        ))

    total = len(questions)
    score = correct_count / total if total > 0 else 0.0
    is_passed = score >= 0.60

    # Save attempt
    attempt = QuizAttempt(
        user_id=current_user.id,
        topic_id=topic_id,
        score=score,
        answers=body.answers,
        is_passed=is_passed,
    )
    db.add(attempt)
    await db.flush()

    # If passed, check if topic can be fully completed (quiz + coding if needed)
    if is_passed:
        await check_and_complete_topic(current_user.id, topic_id, db)

    # Check reassessment proposal (logs only; frontend fetches via GET /users/me/reassessment)
    try:
        proposal = await check_reassessment(db, current_user.id)
        if proposal.get("should_reassess"):
            logger.info(
                f"Propuesta re-asignación usuario {current_user.id}: "
                f"{proposal['current_level']} → {proposal['proposed_level']} ({proposal['reason']})"
            )
    except Exception as e:
        logger.warning(f"Error evaluando re-asignación: {e}")

    await db.commit()

    # Delete session and active pointer from Redis (single-use)
    await redis_client.delete(f"quiz_session:{body.session_id}")
    await redis_client.delete(_active_key(current_user.id, topic_id))

    return QuizSubmitResponse(
        score=round(score * 100, 1),
        is_passed=is_passed,
        feedback=feedback,
        attempt_id=attempt.id,
    )


@router.get("/topic/{topic_id}/history", response_model=list[QuizAttemptResponse])
async def get_quiz_history(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get quiz attempt history for a topic."""
    result = await db.execute(
        select(QuizAttempt)
        .where(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.topic_id == topic_id,
        )
        .order_by(QuizAttempt.attempted_at.desc())
    )
    attempts = result.scalars().all()

    return [
        QuizAttemptResponse(
            attempted_at=a.attempted_at,
            score=round(a.score * 100, 1),
            is_passed=a.is_passed,
        )
        for a in attempts
    ]
