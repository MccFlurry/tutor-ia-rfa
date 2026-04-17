"""
leveling_service.py — Clasificador de nivel + lógica de re-asignación.
Implementa rule-based v1 del pipeline CRISP-DM.
"""

from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.user_level import UserLevel
from app.models.quiz import QuizAttempt
from app.utils.logger import logger


# CRISP-DM feature engineering weights
MODULE_WEIGHTS: dict[int, float] = {1: 1.0, 2: 1.2, 3: 1.1, 4: 1.3, 5: 1.5}
DIFFICULTY_WEIGHTS: dict[str, float] = {"easy": 1.0, "medium": 1.5, "hard": 2.0}

# Level thresholds on 0-100 normalized score
LEVEL_THRESHOLDS = {"beginner_max": 40.0, "intermediate_max": 75.0}

# Reassessment rules
REASSESS_STREAK = 3  # consecutive quizzes
REASSESS_UP_THRESHOLD = 0.90
REASSESS_DOWN_THRESHOLD = 0.50


@dataclass
class LevelComputation:
    level: str
    score: float  # 0-100
    confidence: float  # 0-1
    module_breakdown: dict[int, dict]  # {module_id: {correct, total, percentage}}


def _level_from_score(score: float) -> str:
    """Map normalized score → level."""
    if score < LEVEL_THRESHOLDS["beginner_max"]:
        return "beginner"
    if score < LEVEL_THRESHOLDS["intermediate_max"]:
        return "intermediate"
    return "advanced"


def compute_level(
    questions: list[dict],
    answers: dict[str, int],
) -> LevelComputation:
    """
    Compute level from assessment answers.

    questions: list of dicts with keys id, correct_index, module_id, difficulty
    answers:   {question_id: selected_index}

    Returns LevelComputation with level, normalized score (0-100), confidence,
    and per-module breakdown.
    """
    total_weight = 0.0
    earned_weight = 0.0
    module_stats: dict[int, dict] = {}

    for q in questions:
        qid = q["id"]
        correct_idx = q["correct_index"]
        module_id = q["module_id"]
        difficulty = q["difficulty"]

        m_weight = MODULE_WEIGHTS.get(module_id, 1.0)
        d_weight = DIFFICULTY_WEIGHTS.get(difficulty, 1.0)
        weight = m_weight * d_weight
        total_weight += weight

        selected = answers.get(qid, -1)
        is_correct = selected == correct_idx

        if is_correct:
            earned_weight += weight

        stats = module_stats.setdefault(module_id, {"correct": 0, "total": 0})
        stats["total"] += 1
        if is_correct:
            stats["correct"] += 1

    score_pct = (earned_weight / total_weight * 100.0) if total_weight > 0 else 0.0
    score_pct = round(score_pct, 2)

    # Confidence = fraction of answered questions + coverage of modules
    answered = sum(1 for q in questions if q["id"] in answers)
    coverage = min(1.0, len(module_stats) / 5.0)
    answer_rate = answered / len(questions) if questions else 0.0
    confidence = round((coverage * 0.5 + answer_rate * 0.5), 2)

    for mid, s in module_stats.items():
        s["percentage"] = round(s["correct"] / s["total"] * 100.0, 1) if s["total"] > 0 else 0.0

    return LevelComputation(
        level=_level_from_score(score_pct),
        score=score_pct,
        confidence=confidence,
        module_breakdown=module_stats,
    )


async def get_user_level(db: AsyncSession, user_id) -> str:
    """Return the student's current level, defaulting to 'beginner' if not assessed."""
    result = await db.execute(select(UserLevel).where(UserLevel.user_id == user_id))
    lvl = result.scalar_one_or_none()
    if lvl and lvl.level in ("beginner", "intermediate", "advanced"):
        return lvl.level
    return "beginner"


async def upsert_user_level(
    db: AsyncSession,
    user_id,
    level: str,
    score: float,
    reason: str,
) -> UserLevel:
    """Create or update user level. Appends to history JSONB."""
    result = await db.execute(select(UserLevel).where(UserLevel.user_id == user_id))
    existing = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    history_entry = {
        "level": level,
        "score": score,
        "changed_at": now.isoformat(),
        "reason": reason,
    }

    if existing:
        new_history = list(existing.history or [])
        new_history.append(history_entry)
        existing.level = level
        existing.entry_score = score
        existing.last_reassessed_at = now
        existing.history = new_history
        record = existing
    else:
        record = UserLevel(
            user_id=user_id,
            level=level,
            entry_score=score,
            assessed_at=now,
            history=[history_entry],
        )
        db.add(record)

    await db.flush()
    return record


async def check_reassessment(
    db: AsyncSession,
    user_id,
) -> dict:
    """
    Analyze last N quiz attempts to propose level change.
    Returns dict: {should_reassess, direction, current_level, proposed_level, reason}
    """
    # Current level
    lvl_result = await db.execute(select(UserLevel).where(UserLevel.user_id == user_id))
    lvl = lvl_result.scalar_one_or_none()
    if not lvl:
        return {"should_reassess": False}

    current = lvl.level

    # Last N quiz attempts (any topic)
    attempts_result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.user_id == user_id)
        .order_by(desc(QuizAttempt.attempted_at))
        .limit(REASSESS_STREAK)
    )
    attempts = list(attempts_result.scalars().all())
    if len(attempts) < REASSESS_STREAK:
        return {"should_reassess": False, "current_level": current}

    all_high = all(a.score >= REASSESS_UP_THRESHOLD for a in attempts)
    all_low = all(a.score < REASSESS_DOWN_THRESHOLD for a in attempts)

    if all_high and current != "advanced":
        proposed = "intermediate" if current == "beginner" else "advanced"
        return {
            "should_reassess": True,
            "direction": "up",
            "current_level": current,
            "proposed_level": proposed,
            "reason": f"{REASSESS_STREAK} quizzes consecutivos ≥90%",
        }

    if all_low and current != "beginner":
        proposed = "intermediate" if current == "advanced" else "beginner"
        return {
            "should_reassess": True,
            "direction": "down",
            "current_level": current,
            "proposed_level": proposed,
            "reason": f"{REASSESS_STREAK} quizzes consecutivos <50%",
        }

    return {"should_reassess": False, "current_level": current}


async def apply_reassessment(
    db: AsyncSession,
    user_id,
    proposal: dict,
) -> UserLevel | None:
    """Apply a reassessment proposal (after user confirms)."""
    if not proposal.get("should_reassess"):
        return None
    new_level = proposal.get("proposed_level")
    direction = proposal.get("direction")
    if not new_level or not direction:
        return None

    # Keep entry_score; reassessment doesn't recompute, just changes level
    result = await db.execute(select(UserLevel).where(UserLevel.user_id == user_id))
    lvl = result.scalar_one_or_none()
    if not lvl:
        return None

    reason = f"reassess_{direction}"
    record = await upsert_user_level(db, user_id, new_level, lvl.entry_score, reason)
    logger.info(f"Usuario {user_id} re-asignado a nivel {new_level} ({reason})")
    return record
