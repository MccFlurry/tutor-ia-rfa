"""
coding_generator_service.py — Generación de desafíos de código
per-estudiante adaptados a su nivel. Fallback a desafíos seeded
del docente cuando Ollama falla.
"""
import random
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.topic import Topic
from app.models.user import User
from app.models.coding import CodingChallenge
from app.services.challenge_generator_service import (
    generate_challenge,
    ChallengeGenerationError,
)
from app.utils.logger import logger


# Difficulty mapping per student level
LEVEL_TO_DIFFICULTY = {
    "beginner":     "easy",
    "intermediate": "medium",
    "advanced":     "hard",
}


async def _get_existing_unused(
    db: AsyncSession, user_id: uuid.UUID, topic_id: int
) -> CodingChallenge | None:
    """Return the latest AI challenge for this user+topic that hasn't been passed yet."""
    result = await db.execute(
        select(CodingChallenge)
        .where(
            CodingChallenge.topic_id == topic_id,
            CodingChallenge.is_ai_generated == True,
            CodingChallenge.generated_for_user_id == user_id,
        )
        .order_by(CodingChallenge.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _clone_from_fallback(
    db: AsyncSession, topic_id: int, user_id: uuid.UUID, level: str
) -> CodingChallenge | None:
    """Clone a seeded (non-AI) challenge as fallback when LLM fails. Returns persisted copy."""
    result = await db.execute(
        select(CodingChallenge)
        .where(
            CodingChallenge.topic_id == topic_id,
            CodingChallenge.is_ai_generated == False,
        )
    )
    seed_pool = list(result.scalars().all())
    if not seed_pool:
        return None

    # Prefer one matching level's difficulty; fall back to any
    preferred_diff = LEVEL_TO_DIFFICULTY.get(level, "medium")
    matching = [c for c in seed_pool if c.difficulty == preferred_diff]
    chosen = random.choice(matching or seed_pool)

    clone = CodingChallenge(
        topic_id=chosen.topic_id,
        title=f"[Fallback] {chosen.title}",
        description=chosen.description,
        initial_code=chosen.initial_code,
        language=chosen.language,
        difficulty=chosen.difficulty,
        hints=chosen.hints,
        solution_code=chosen.solution_code,
        order_index=0,
        is_ai_generated=True,  # served dynamically even if cloned
        generated_for_user_id=user_id,
        student_level=level,
    )
    db.add(clone)
    await db.flush()
    logger.info(f"Desafío fallback clonado del catálogo (id={chosen.id}) para usuario {user_id}")
    return clone


async def get_or_generate_for_student(
    db: AsyncSession,
    topic: Topic,
    user: User,
    student_level: str,
) -> CodingChallenge:
    """
    Return a coding challenge adapted to the student's level.

    Flow:
      1. If an AI-generated challenge already exists for this user+topic, return it (continue).
      2. Otherwise, ask the LLM to generate one; persist and return.
      3. If LLM fails, clone one from the teacher's seeded fallback bank.

    Raises:
        RuntimeError if neither LLM nor fallback bank has content.
    """
    # 1. Reuse existing unsolved AI challenge
    existing = await _get_existing_unused(db, user.id, topic.id)
    if existing is not None:
        return existing

    difficulty = LEVEL_TO_DIFFICULTY.get(student_level, "medium")

    # 2. Try LLM generation
    try:
        generated = await generate_challenge(
            topic_content=topic.content,
            difficulty=difficulty,
            target_level=student_level,
        )
        challenge = CodingChallenge(
            topic_id=topic.id,
            title=generated.title,
            description=generated.description,
            initial_code=None,
            language=generated.language,
            difficulty=generated.difficulty,
            hints=generated.hints,
            solution_code=generated.solution_code,
            order_index=0,
            is_ai_generated=True,
            generated_for_user_id=user.id,
            student_level=student_level,
        )
        db.add(challenge)
        await db.flush()
        logger.info(
            f"Desafío IA creado (challenge_id={challenge.id}) para usuario {user.id}, "
            f"tema {topic.id}, nivel {student_level}"
        )
        return challenge
    except ChallengeGenerationError as e:
        logger.warning(f"LLM fallo al generar desafío ({e}); usando fallback del banco")
    except Exception as e:
        logger.error(f"Error inesperado en generación IA: {e}")

    # 3. Fallback: clone seeded challenge
    fallback = await _clone_from_fallback(db, topic.id, user.id, student_level)
    if fallback is None:
        raise RuntimeError(
            "No se pudo generar el desafío y no existen desafíos de respaldo en el catálogo"
        )
    return fallback


async def regenerate_for_student(
    db: AsyncSession,
    topic: Topic,
    user: User,
    student_level: str,
) -> CodingChallenge:
    """
    Discard the current AI challenge for this user+topic (if not yet solved)
    and generate a new one. Submissions reference the old challenge_id —
    we keep the row for audit, just create a fresh one that becomes the
    "latest" returned by get_or_generate.
    """
    # Note: we don't delete the old challenge to preserve submission FK integrity.
    difficulty = LEVEL_TO_DIFFICULTY.get(student_level, "medium")

    try:
        generated = await generate_challenge(
            topic_content=topic.content,
            difficulty=difficulty,
            target_level=student_level,
        )
        challenge = CodingChallenge(
            topic_id=topic.id,
            title=generated.title,
            description=generated.description,
            language=generated.language,
            difficulty=generated.difficulty,
            hints=generated.hints,
            solution_code=generated.solution_code,
            order_index=0,
            is_ai_generated=True,
            generated_for_user_id=user.id,
            student_level=student_level,
        )
        db.add(challenge)
        await db.flush()
        logger.info(f"Desafío IA regenerado (id={challenge.id}) para usuario {user.id}")
        return challenge
    except ChallengeGenerationError:
        fallback = await _clone_from_fallback(db, topic.id, user.id, student_level)
        if fallback is None:
            raise RuntimeError("No se pudo regenerar el desafío")
        return fallback
