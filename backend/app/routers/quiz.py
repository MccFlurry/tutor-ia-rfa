import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.topic import Topic
from app.models.quiz import QuizQuestion, QuizAttempt
from app.models.ai_quiz_session import AIQuizSession
from app.schemas.quiz import (
    QuizQuestionResponse,
    QuizGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizFeedbackItem,
    QuizAttemptResponse,
    LevelChange,
)
from app.services.llm_service import generate_quiz_questions, QuizGenerationError
from app.services.topic_completion_service import check_and_complete_topic
from app.services.leveling_service import get_user_level, auto_apply_reassessment
from app.services.module_service import assert_module_unlocked, assert_topic_unlocked
from app.utils.logger import logger

router = APIRouter(prefix="/quiz", tags=["quiz"])


def _serialize_questions_for_student(questions: dict) -> list[QuizQuestionResponse]:
    """Strip correct_index + explanation before sending to the client."""
    return [
        QuizQuestionResponse(
            id=qid,
            question_text=q["question_text"],
            options=q["options"],
        )
        for qid, q in questions.items()
    ]


async def _build_from_db_catalogue(
    topic_id: int, db: AsyncSession
) -> dict | None:
    """
    Build the questions payload from static catalogue QuizQuestion rows.
    Returns the dict keyed by q0..qN or None if no catalogue questions exist.
    """
    result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.topic_id == topic_id)
        .order_by(QuizQuestion.order_index)
    )
    db_questions = result.scalars().all()
    if not db_questions:
        return None

    payload: dict = {}
    for i, q in enumerate(db_questions):
        payload[f"q{i}"] = {
            "question_text": q.question_text,
            "options": q.options,
            "correct_index": q.correct_option_index,
            "explanation": q.explanation or "Sin explicación disponible.",
        }
    return payload


async def _get_active_session(
    db: AsyncSession, user_id: uuid.UUID, topic_id: int
) -> AIQuizSession | None:
    """Find the user's active (unsubmitted) session for this topic, if any."""
    result = await db.execute(
        select(AIQuizSession).where(
            AIQuizSession.user_id == user_id,
            AIQuizSession.topic_id == topic_id,
            AIQuizSession.is_submitted == False,
        )
    )
    return result.scalar_one_or_none()


@router.get("/topic/{topic_id}", response_model=QuizGenerateResponse)
async def get_quiz(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the student's active quiz session for this topic. If none exists yet,
    generate one with the LLM (or fall back to the catalogue) and persist it so
    that re-entering the topic returns the SAME questions until submission.
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

    # Sequential-unlock gate: don't generate/persist a quiz for a locked module.
    await assert_module_unlocked(topic.module_id, current_user.id, db)

    # 1. Reuse the active session if one exists (persists across logout / navigation)
    existing = await _get_active_session(db, current_user.id, topic_id)
    if existing is not None:
        logger.info(
            f"Quiz sesión persistente recuperada (id={existing.id}) "
            f"para usuario {current_user.id}, tema {topic_id}"
        )
        return QuizGenerateResponse(
            session_id=str(existing.id),
            questions=_serialize_questions_for_student(existing.questions),
        )

    # 2. Try LLM generation
    student_level = await get_user_level(db, current_user.id)
    payload: dict | None = None
    source = "ai"
    try:
        generated = await generate_quiz_questions(topic.content, student_level=student_level)
        payload = {}
        for i, q in enumerate(generated):
            payload[f"q{i}"] = {
                "question_text": q.question_text,
                "options": q.options,
                "correct_index": q.correct_option_index,
                "explanation": q.explanation,
            }
    except QuizGenerationError as e:
        logger.warning(f"LLM fallo generando quiz para tema {topic_id}: {e}")
    except Exception as e:
        logger.error(f"Error inesperado generando quiz para tema {topic_id}: {e}")

    # 3. Fall back to DB catalogue
    if payload is None:
        payload = await _build_from_db_catalogue(topic_id, db)
        source = "fallback"

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de generación de preguntas no está disponible y no hay preguntas de respaldo.",
        )

    # 4. Persist the session — this is the source of truth.
    session = AIQuizSession(
        user_id=current_user.id,
        topic_id=topic_id,
        questions=payload,
        student_level=student_level,
        source=source,
    )
    db.add(session)
    await db.flush()
    await db.commit()

    logger.info(
        f"Quiz {source} generado y persistido (id={session.id}) "
        f"para usuario {current_user.id}, tema {topic_id}"
    )
    return QuizGenerateResponse(
        session_id=str(session.id),
        questions=_serialize_questions_for_student(payload),
    )


@router.post("/topic/{topic_id}/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    topic_id: int,
    body: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit quiz answers. Grades against the persisted answer key."""
    try:
        session_uuid = uuid.UUID(body.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id inválido",
        )

    # Sequential-unlock gate: passing a quiz completes the topic, which feeds the
    # unlock rule — refuse so a locked module can't be unlocked by the back door.
    await assert_topic_unlocked(topic_id, current_user.id, db)

    result = await db.execute(
        select(AIQuizSession).where(
            AIQuizSession.id == session_uuid,
            AIQuizSession.user_id == current_user.id,
            AIQuizSession.topic_id == topic_id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión de autoevaluación no encontrada",
        )
    if session.is_submitted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Esta autoevaluación ya fue enviada. Genera una nueva.",
        )

    questions = session.questions

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
            options=q_data["options"],
            selected_index=selected,
            correct_index=correct_idx,
            is_correct=is_correct,
            explanation=q_data.get("explanation"),
        ))

    total = len(questions)
    score = correct_count / total if total > 0 else 0.0
    is_passed = score >= 0.60

    attempt = QuizAttempt(
        user_id=current_user.id,
        topic_id=topic_id,
        score=score,
        answers=body.answers,
        is_passed=is_passed,
    )
    db.add(attempt)

    session.is_submitted = True
    session.submitted_at = datetime.now(timezone.utc)

    await db.flush()

    if is_passed:
        await check_and_complete_topic(current_user.id, topic_id, db)

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

    return QuizSubmitResponse(
        score=round(score * 100, 1),
        is_passed=is_passed,
        feedback=feedback,
        attempt_id=attempt.id,
        level_change=level_change_payload,
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
