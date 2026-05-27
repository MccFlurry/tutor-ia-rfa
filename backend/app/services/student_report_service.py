"""student_report_service — aggregations + AI narrative for the admin reports screen.

This file only contains helpers in Task 2; aggregation and AI calls are added in
Tasks 3-7.
"""

import hashlib
import json
import re
from datetime import datetime, timezone

from app.schemas.admin_reports import StudentDetail, AIReport
from app.utils.logger import logger
from app.services import llm_service


class InsufficientActivityError(Exception):
    """Raised when a student has no quiz/coding activity yet."""
    pass


class LLMReportError(Exception):
    """Raised when the LLM cannot produce a valid report after retry."""
    pass


def _has_minimum_activity(detail: StudentDetail) -> bool:
    """A student qualifies for an AI report once they've completed at least one
    quiz attempt or one coding submission. Pure progress without graded work is
    not enough signal for the LLM."""
    return bool(detail.recent_quizzes) or bool(detail.recent_coding)


def _detail_hash(detail: StudentDetail) -> str:
    """Stable sha256 over volatile fields. Changes whenever the student advances
    so the Redis cache key auto-invalidates."""
    payload = {
        "progress_pct": round(detail.overall_progress_pct, 2),
        "quiz_count": len(detail.recent_quizzes),
        "last_quiz_score": detail.recent_quizzes[0].score if detail.recent_quizzes else None,
        "coding_count": len(detail.recent_coding),
        "last_coding_score": detail.recent_coding[0].score if detail.recent_coding else None,
        "chat_count": detail.chat_messages_count,
        "last_activity": detail.last_activity_at.isoformat() if detail.last_activity_at else None,
        "level": detail.level,
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


async def _safe_redis_get(redis_client, key: str) -> str | None:
    """Redis GET with degraded mode — swallows exceptions and returns None."""
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.warning(f"[student_report] Redis GET falló para {key}: {e}")
        return None


async def _safe_redis_setex(redis_client, key: str, ttl: int, value: str) -> None:
    """Redis SETEX with degraded mode — swallows exceptions."""
    try:
        await redis_client.setex(key, ttl, value)
    except Exception as e:
        logger.warning(f"[student_report] Redis SETEX falló para {key}: {e}")


# ---------------------------------------------------------------------------
# Task 3: get_students_overview
# ---------------------------------------------------------------------------

from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_level import UserLevel
from app.models.module import Module
from app.models.topic import Topic
from app.models.progress import UserTopicProgress
from app.models.quiz import QuizAttempt
from app.models.coding import CodingSubmission, CodingChallenge
from app.models.chat import ChatMessage
from app.models.achievement import Achievement, UserAchievement
from app.schemas.admin_reports import (
    StudentRow,
    StudentDetail,
    ModuleProgress,
    QuizAttemptRow,
    CodingSubmissionRow,
    AchievementRow,
    LevelHistoryEntry,
)


async def get_students_overview(db: AsyncSession) -> list[StudentRow]:
    """Build the admin reports table in a single query with subqueries.

    Aggregations:
      - overall_progress_pct = completed topics / total topics * 100
      - avg_quiz_score       = AVG(quiz_attempts.score)
      - avg_coding_score     = AVG(coding_submissions.score)
      - last_activity_at     = MAX over (progress, quiz, coding, chat) timestamps
      - last_location        = title of the topic touched last, or "Chat IA" /
                               "Quiz" / "Desafío de código" when one of those
                               events is the most recent.
    """
    topics_total_sq = select(func.count(Topic.id)).where(Topic.is_active.is_(True)).scalar_subquery()

    completed_sq = (
        select(func.count(UserTopicProgress.topic_id))
        .where(
            UserTopicProgress.user_id == User.id,
            UserTopicProgress.is_completed.is_(True),
        )
        .correlate(User)
        .scalar_subquery()
    )

    avg_quiz_sq = (
        select(func.avg(QuizAttempt.score))
        .where(QuizAttempt.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    avg_coding_sq = (
        select(func.avg(CodingSubmission.score))
        .where(CodingSubmission.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    last_progress_sq = (
        select(func.max(UserTopicProgress.last_accessed_at))
        .where(UserTopicProgress.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    last_quiz_sq = (
        select(func.max(QuizAttempt.attempted_at))
        .where(QuizAttempt.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    last_coding_sq = (
        select(func.max(CodingSubmission.submitted_at))
        .where(CodingSubmission.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    last_chat_sq = (
        select(func.max(ChatMessage.created_at))
        .where(ChatMessage.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    query = (
        select(
            User,
            UserLevel,
            completed_sq.label("completed"),
            topics_total_sq.label("topics_total"),
            avg_quiz_sq.label("avg_quiz"),
            avg_coding_sq.label("avg_coding"),
            last_progress_sq.label("last_progress"),
            last_quiz_sq.label("last_quiz"),
            last_coding_sq.label("last_coding"),
            last_chat_sq.label("last_chat"),
        )
        .outerjoin(UserLevel, UserLevel.user_id == User.id)
        .where(User.role == "student")
        .order_by(User.full_name)
    )

    rows = (await db.execute(query)).all()

    # Batch-resolve last topic location for each user (single extra query).
    user_ids = [r[0].id for r in rows]
    topic_title_by_user: dict = {}
    if user_ids:
        topic_q = (
            select(UserTopicProgress.user_id, Module.title, Topic.title)
            .join(Topic, Topic.id == UserTopicProgress.topic_id)
            .join(Module, Module.id == Topic.module_id)
            .where(UserTopicProgress.user_id.in_(user_ids))
            .order_by(UserTopicProgress.last_accessed_at.desc())
        )
        topic_rows = (await db.execute(topic_q)).all()
        for uid, module_title, topic_title in topic_rows:
            topic_title_by_user.setdefault(uid, f"{module_title} - {topic_title}")

    out: list[StudentRow] = []
    for user, lvl, completed, total, avg_quiz, avg_coding, lp, lq, lc, lch in rows:
        candidates = [
            (lp, topic_title_by_user.get(user.id)),
            (lq, "Quiz"),
            (lc, "Desafío de código"),
            (lch, "Chat IA"),
        ]
        candidates = [(t, label) for t, label in candidates if t is not None]
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            last_at, last_label = candidates[0]
        else:
            last_at, last_label = None, None

        progress_pct = 0.0
        if total and total > 0 and completed is not None:
            progress_pct = round((completed / total) * 100.0, 2)

        out.append(StudentRow(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            level=lvl.level if lvl else None,
            entry_score=lvl.entry_score if lvl else None,
            overall_progress_pct=progress_pct,
            avg_quiz_score=float(avg_quiz) if avg_quiz is not None else None,
            avg_coding_score=float(avg_coding) if avg_coding is not None else None,
            last_activity_at=last_at,
            last_location=last_label,
            is_active=user.is_active,
        ))
    return out


# ---------------------------------------------------------------------------
# Task 4: get_student_detail
# ---------------------------------------------------------------------------

async def get_student_detail(db: AsyncSession, user_id: UUID) -> StudentDetail:
    """Return everything we know about a student for the detail page.

    Raises LookupError if the user does not exist or is not a student. The
    router maps this to 404.
    """
    # 1) user + level
    row = (
        await db.execute(
            select(User, UserLevel)
            .outerjoin(UserLevel, UserLevel.user_id == User.id)
            .where(User.id == user_id, User.role == "student")
        )
    ).first()
    if row is None:
        raise LookupError("student_not_found")
    user, lvl = row

    # 2) modules + per-module progress
    module_q = (
        select(
            Module,
            func.count(UserTopicProgress.topic_id).filter(
                UserTopicProgress.is_completed.is_(True),
                UserTopicProgress.user_id == user_id,
            ).label("completed"),
            func.count(Topic.id).label("topics_total"),
            func.avg(QuizAttempt.score).filter(QuizAttempt.user_id == user_id).label("avg_quiz"),
            func.avg(CodingSubmission.score).filter(CodingSubmission.user_id == user_id).label("avg_coding"),
        )
        .join(Topic, Topic.module_id == Module.id)
        .outerjoin(UserTopicProgress, and_(
            UserTopicProgress.topic_id == Topic.id,
            UserTopicProgress.user_id == user_id,
        ))
        .outerjoin(QuizAttempt, and_(
            QuizAttempt.topic_id == Topic.id,
            QuizAttempt.user_id == user_id,
        ))
        .group_by(Module.id)
        .order_by(Module.order_index)
    )
    module_rows = (await db.execute(module_q)).all()

    modules: list[ModuleProgress] = []
    for mod, completed, total, avg_q, avg_c in module_rows:
        pct = round((completed / total) * 100.0, 2) if total else 0.0
        modules.append(ModuleProgress(
            module_id=mod.id,
            module_title=mod.title,
            topics_total=total or 0,
            topics_completed=completed or 0,
            progress_pct=pct,
            avg_quiz_score=float(avg_q) if avg_q is not None else None,
            avg_coding_score=float(avg_c) if avg_c is not None else None,
        ))

    # 3) recent quizzes (last 10)
    quiz_q = (
        select(QuizAttempt, Topic.title)
        .join(Topic, Topic.id == QuizAttempt.topic_id)
        .where(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(10)
    )
    quizzes = [
        QuizAttemptRow(
            attempt_id=q.id,
            topic_id=q.topic_id,
            topic_title=t_title,
            score=q.score,
            is_passed=q.is_passed,
            attempted_at=q.attempted_at,
        )
        for q, t_title in (await db.execute(quiz_q)).all()
    ]

    # 4) recent coding (last 10)
    coding_q = (
        select(CodingSubmission, CodingChallenge.title)
        .join(CodingChallenge, CodingChallenge.id == CodingSubmission.challenge_id)
        .where(CodingSubmission.user_id == user_id)
        .order_by(CodingSubmission.submitted_at.desc())
        .limit(10)
    )
    coding = [
        CodingSubmissionRow(
            submission_id=s.id,
            challenge_id=s.challenge_id,
            challenge_title=c_title,
            score=s.score,
            submitted_at=s.submitted_at,
        )
        for s, c_title in (await db.execute(coding_q)).all()
    ]

    # 5) chat counts
    chat_count, chat_last = (
        await db.execute(
            select(func.count(ChatMessage.id), func.max(ChatMessage.created_at))
            .where(ChatMessage.user_id == user_id, ChatMessage.role == "user")
        )
    ).first() or (0, None)

    # 6) achievements
    ach_q = (
        select(Achievement, UserAchievement.earned_at)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .where(UserAchievement.user_id == user_id)
        .order_by(UserAchievement.earned_at.desc())
    )
    achievements = [
        AchievementRow(
            achievement_id=a.id,
            name=a.name,
            badge_emoji=a.badge_emoji,
            earned_at=earned,
        )
        for a, earned in (await db.execute(ach_q)).all()
    ]

    # 7) total time
    total_time = (
        await db.execute(
            select(func.coalesce(func.sum(UserTopicProgress.time_spent_seconds), 0))
            .where(UserTopicProgress.user_id == user_id)
        )
    ).scalar() or 0

    # Last activity = max over quiz, coding, chat (progress timestamps are not in detail).
    last_at = max(
        (x for x in [
            chat_last,
            quizzes[0].attempted_at if quizzes else None,
            coding[0].submitted_at if coding else None,
        ] if x is not None),
        default=None,
    )

    # Level history from JSONB
    history: list[LevelHistoryEntry] = []
    if lvl and lvl.history:
        for entry in lvl.history:
            try:
                history.append(LevelHistoryEntry(**entry))
            except Exception:
                continue

    overall_pct = (
        round(sum(m.progress_pct * m.topics_total for m in modules)
              / sum(m.topics_total for m in modules), 2)
        if modules and sum(m.topics_total for m in modules) > 0
        else 0.0
    )

    return StudentDetail(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        created_at=user.created_at,
        is_active=user.is_active,
        level=lvl.level if lvl else None,
        entry_score=lvl.entry_score if lvl else None,
        level_history=history,
        overall_progress_pct=overall_pct,
        modules=modules,
        recent_quizzes=quizzes,
        recent_coding=coding,
        chat_messages_count=chat_count or 0,
        chat_last_at=chat_last,
        achievements_earned=achievements,
        total_time_seconds=int(total_time),
        last_activity_at=last_at,
        last_location=None,
    )


# ---------------------------------------------------------------------------
# Task 5: LLM prompt + JSON parser
# ---------------------------------------------------------------------------

REPORT_SYSTEM_PROMPT = """Eres un tutor pedagógico evaluador del curso de Aplicaciones Móviles \
(Android/Kotlin) del IESTP República Federal de Alemania (RFA), Chiclayo. Tu rol es analizar \
el desempeño de un estudiante y entregar un reporte breve y accionable.

REGLAS ESTRICTAS:
1. Responde ÚNICAMENTE con un objeto JSON válido (sin texto extra, sin markdown fences).
2. Estructura EXACTA del objeto:
{
  "report": {
    "summary": "Resumen narrativo de 3 a 4 párrafos en español peruano.",
    "strengths": ["máximo 4 ítems"],
    "weaknesses": ["máximo 4 ítems"],
    "risk_level": "bajo" | "medio" | "alto",
    "risk_reason": "Una oración explicando el riesgo.",
    "interventions": ["máximo 5 acciones concretas para el docente"]
  }
}
3. Basa toda inferencia en los datos provistos. No inventes eventos ni números.
4. Si la evidencia es insuficiente para concluir, indícalo en risk_reason.
5. risk_level "alto" requiere: progreso <30% Y promedio quiz <0.5, o más de 14 días sin actividad."""


def _build_report_prompt(detail: StudentDetail) -> str:
    """Compact serialization of the student detail (kept under 3 500 chars)."""
    modules_lines = "\n".join(
        f"  - {m.module_title}: {m.progress_pct}% completado, "
        f"quiz={m.avg_quiz_score if m.avg_quiz_score is not None else 'n/a'}, "
        f"coding={m.avg_coding_score if m.avg_coding_score is not None else 'n/a'}"
        for m in detail.modules
    )
    last_quizzes = "\n".join(
        f"  - {q.topic_title}: {q.score:.2f} ({'aprobado' if q.is_passed else 'no aprobado'})"
        for q in detail.recent_quizzes[:5]
    )
    last_coding = "\n".join(
        f"  - {c.challenge_title}: {c.score:.0f}/100"
        for c in detail.recent_coding[:5]
    )
    last_activity = (
        detail.last_activity_at.astimezone(timezone.utc).isoformat()
        if detail.last_activity_at else "sin registros"
    )

    user_block = f"""DATOS DEL ESTUDIANTE
- Nombre: {detail.full_name}
- Nivel actual: {detail.level or 'sin asignar'}
- Puntaje de entrada: {detail.entry_score if detail.entry_score is not None else 'n/a'}
- Progreso global: {detail.overall_progress_pct}%
- Tiempo total invertido: {detail.total_time_seconds // 60} minutos
- Logros desbloqueados: {len(detail.achievements_earned)}
- Mensajes de chat al tutor IA: {detail.chat_messages_count}
- Última actividad: {last_activity}

PROGRESO POR MÓDULO
{modules_lines or '  (sin módulos)'}

ÚLTIMOS QUIZZES
{last_quizzes or '  (sin intentos)'}

ÚLTIMOS DESAFÍOS DE CÓDIGO
{last_coding or '  (sin entregas)'}

INSTRUCCIONES
Analiza estos datos y devuelve el reporte JSON solicitado."""

    if len(user_block) > 3500:
        user_block = user_block[:3500] + "\n[...truncado]"
    return user_block


_VALID_RISKS = {"bajo", "medio", "alto"}
_REQUIRED_KEYS = {"summary", "strengths", "weaknesses", "risk_level", "risk_reason", "interventions"}


def _parse_report(raw: str) -> dict:
    """Strict parser for the LLM JSON object. Tolerates `{"report": {...}}`
    wrapper and markdown code fences."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMReportError(f"JSON inválido del LLM: {e}")

    if isinstance(data, dict) and "report" in data and isinstance(data["report"], dict):
        data = data["report"]
    if not isinstance(data, dict):
        raise LLMReportError("La respuesta del LLM no es un objeto")

    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        raise LLMReportError(f"Faltan campos en el reporte LLM: {sorted(missing)}")

    risk = str(data["risk_level"]).strip().lower()
    if risk not in _VALID_RISKS:
        raise LLMReportError(f"risk_level inválido: {data['risk_level']!r}")
    data["risk_level"] = risk

    for key in ("strengths", "weaknesses", "interventions"):
        if not isinstance(data[key], list):
            raise LLMReportError(f"{key} debe ser lista")
        data[key] = [str(x).strip() for x in data[key] if str(x).strip()]

    data["summary"] = str(data["summary"]).strip()
    data["risk_reason"] = str(data["risk_reason"]).strip()
    return data


# ---------------------------------------------------------------------------
# Task 6: generate_ai_report (cache + retry + activity gate)
# ---------------------------------------------------------------------------

async def generate_ai_report(db: AsyncSession, redis_client, user_id: UUID) -> AIReport:
    """Generate (or fetch cached) AI narrative report for a single student."""
    detail = await get_student_detail(db, user_id)
    if not _has_minimum_activity(detail):
        raise InsufficientActivityError(
            "Sin actividad suficiente. Esperar primer quiz."
        )

    key = f"student_report:{user_id}:{_detail_hash(detail)}"

    cached_raw = await _safe_redis_get(redis_client, key)
    if cached_raw:
        try:
            payload = json.loads(cached_raw)
            return AIReport(**payload, cached=True)
        except Exception as e:
            logger.warning(f"[student_report] cache corrupto para {key}: {e}")

    system_prompt = REPORT_SYSTEM_PROMPT
    user_prompt = _build_report_prompt(detail)

    try:
        raw = await llm_service.generate_student_report_text(
            system_prompt, user_prompt, temperature=0.3,
        )
        parsed = _parse_report(raw)
    except (LLMReportError, json.JSONDecodeError):
        try:
            raw = await llm_service.generate_student_report_text(
                system_prompt, user_prompt, temperature=0.1,
            )
            parsed = _parse_report(raw)
        except (LLMReportError, json.JSONDecodeError) as e:
            logger.error(f"LLM falló tras reintento para {user_id}: {e}")
            raise LLMReportError("LLM no produjo JSON válido tras reintento") from e
    except Exception as e:
        logger.error(f"Error de Ollama generando reporte para {user_id}: {e}")
        raise LLMReportError(f"Ollama indisponible: {e}") from e

    parsed["generated_at"] = datetime.now(timezone.utc).isoformat()
    await _safe_redis_setex(redis_client, key, 3600, json.dumps(parsed))
    return AIReport(**parsed, cached=False)
