"""services/companion_service.py — Posición del estudiante + diagnóstico determinista (Fase 5).

El sistema «sigue» al estudiante: pick_current_index/build_diagnostic/build_greeting
son funciones puras (sin BD ni LLM). gather_companion resuelve el estado desde BD
reutilizando el invariante de desbloqueo secuencial de module_service.compute_locks.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import CodingChallenge, CodingSubmission
from app.models.learning_resource import LearningResource
from app.models.module import Module
from app.models.progress import UserTopicProgress
from app.models.quiz import QuizAttempt
from app.models.topic import Topic
from app.models.user import User
from app.models.user_level import UserLevel
from app.schemas.companion import (
    CompanionPosition,
    CompanionResponse,
    ModuleDiagnostic,
    NextAction,
    TopicDiagnostic,
    TopicStat,
)
from app.schemas.learning_resource import LearningResourceResponse
from app.services.module_service import compute_locks

# Bandas de diagnóstico sobre el mejor score de quiz (0-100)
WEAK_SCORE = 60.0        # < 60 → repasar
PRACTICE_SCORE = 80.0    # [60, 80) → afianzar · ≥ 80 → dominado
WEAK_FAILED_ATTEMPTS = 2  # ≥ 2 intentos fallidos (sin dominar) → repasar
CODING_PASS_SCORE = 60.0  # submission ≥ 60 da el desafío por resuelto
MAX_RESOURCES = 3


def pick_current_index(progress_pairs: list[tuple[int, int]]) -> int | None:
    """Índice del módulo actual: primer módulo desbloqueado e incompleto.

    ``progress_pairs`` = (total_topics, completed_topics) por módulo, en orden.
    Devuelve None si todos los módulos están completos (curso terminado).
    """
    locks = compute_locks(progress_pairs)
    for i, ((total, done), locked) in enumerate(zip(progress_pairs, locks)):
        if not locked and (total == 0 or done < total):
            return i
    return None


def build_diagnostic(stats: list[TopicStat], module_id: int) -> ModuleDiagnostic:
    """Clasifica los temas del módulo actual y decide el siguiente paso. Pura."""
    ordered = sorted(stats, key=lambda s: s.order_index)
    weak: list[TopicDiagnostic] = []
    practice: list[TopicDiagnostic] = []
    pending: list[TopicStat] = []
    coding_pending: list[TopicStat] = []

    for s in ordered:
        # Pendiente = no completado (incluye visitados a medio terminar): el
        # companion debe poder retomar donde el estudiante se quedó.
        if not s.completed:
            pending.append(s)
        if s.has_coding_pending:
            coding_pending.append(s)
        if s.best_score is None:
            continue
        diag = TopicDiagnostic(
            topic_id=s.topic_id, title=s.title,
            best_score=s.best_score, attempts=s.attempts,
        )
        # Dominado (≥80) tiene precedencia sobre la regla de intentos fallidos.
        if s.best_score < WEAK_SCORE or (
            s.failed_attempts >= WEAK_FAILED_ATTEMPTS and s.best_score < PRACTICE_SCORE
        ):
            weak.append(diag)
        elif s.best_score < PRACTICE_SCORE:
            practice.append(diag)

    if weak:
        next_action = NextAction(
            kind="retry_quiz",
            label=f"Repasar «{weak[0].title}»",
            route=f"/topics/{weak[0].topic_id}",
        )
    elif pending:
        next_action = NextAction(
            kind="next_topic",
            label=f"Continuar con «{pending[0].title}»",
            route=f"/topics/{pending[0].topic_id}",
        )
    elif coding_pending:
        next_action = NextAction(
            kind="coding_challenge",
            label=f"Resolver el desafío de «{coding_pending[0].title}»",
            route=f"/topics/{coding_pending[0].topic_id}",
        )
    else:
        next_action = NextAction(
            kind="module", label="Ver el módulo", route=f"/modules/{module_id}",
        )

    return ModuleDiagnostic(weak=weak, practice=practice, next_action=next_action)


NEEDS_ASSESSMENT_GREETING = (
    "Antes de empezar, realiza tu evaluación de entrada para personalizar "
    "tu ruta de aprendizaje."
)
EMPTY_COURSE_GREETING = "Aún no hay módulos disponibles. Vuelve pronto."


def build_greeting(position: CompanionPosition, diagnostic: ModuleDiagnostic) -> str:
    """Saludo contextual del tutor por plantillas (español peruano). Pura."""
    if position.course_completed:
        return (
            "¡Felicitaciones! Completaste todos los módulos del curso. "
            "Puedes repasar libremente cualquier tema o desafío."
        )
    pct = round(position.progress_pct)
    if diagnostic.weak:
        return (
            f"Estás en «{position.module_title}» — {pct}% completado. "
            f"Veo que te cuesta «{diagnostic.weak[0].title}», ¿lo repasamos?"
        )
    if position.topics_done == 0:
        return (
            f"Estás comenzando «{position.module_title}». "
            "Te acompaño paso a paso; empieza con el primer tema."
        )
    return (
        f"Estás en «{position.module_title}» — {pct}% completado. "
        f"Tu siguiente paso: {diagnostic.next_action.label}."
    )


async def _gather_topic_stats(user: User, module_id: int, db: AsyncSession) -> list[TopicStat]:
    """Stats por tema del módulo actual: quiz, progreso y coding pendiente."""
    topics = (
        await db.execute(
            select(Topic.id, Topic.title, Topic.order_index)
            .where(Topic.module_id == module_id, Topic.is_active == True)  # noqa: E712
            .order_by(Topic.order_index)
        )
    ).all()
    topic_ids = [t[0] for t in topics]
    if not topic_ids:
        return []

    prog_rows = (
        await db.execute(
            select(UserTopicProgress.topic_id, UserTopicProgress.is_completed).where(
                UserTopicProgress.user_id == user.id,
                UserTopicProgress.topic_id.in_(topic_ids),
            )
        )
    ).all()
    progress = {tid: completed for tid, completed in prog_rows}

    quiz_rows = (
        await db.execute(
            select(
                QuizAttempt.topic_id,
                func.max(QuizAttempt.score).label("best"),
                func.count(QuizAttempt.id).label("attempts"),
                func.count(QuizAttempt.id)
                .filter(QuizAttempt.is_passed == False)  # noqa: E712
                .label("failed"),
            )
            .where(QuizAttempt.user_id == user.id, QuizAttempt.topic_id.in_(topic_ids))
            .group_by(QuizAttempt.topic_id)
        )
    ).all()
    quiz = {row.topic_id: row for row in quiz_rows}

    # Desafíos de catálogo (no AI per-usuario) y cuáles ya aprobó (≥60)
    chal_rows = (
        await db.execute(
            select(CodingChallenge.topic_id, CodingChallenge.id).where(
                CodingChallenge.topic_id.in_(topic_ids),
                CodingChallenge.is_ai_generated == False,  # noqa: E712
            )
        )
    ).all()
    challenge_topics: dict[int, list[int]] = {}
    for tid, cid in chal_rows:
        challenge_topics.setdefault(tid, []).append(cid)
    all_challenge_ids = [cid for ids in challenge_topics.values() for cid in ids]

    passed_challenge_ids: set[int] = set()
    if all_challenge_ids:
        sub_rows = (
            await db.execute(
                select(CodingSubmission.challenge_id).where(
                    CodingSubmission.user_id == user.id,
                    CodingSubmission.challenge_id.in_(all_challenge_ids),
                    CodingSubmission.score >= CODING_PASS_SCORE,
                )
            )
        ).all()
        passed_challenge_ids = {r[0] for r in sub_rows}

    stats: list[TopicStat] = []
    for tid, title, order_index in topics:
        q = quiz.get(tid)
        cids = challenge_topics.get(tid, [])
        stats.append(TopicStat(
            topic_id=tid,
            title=title,
            order_index=order_index,
            visited=tid in progress,
            completed=bool(progress.get(tid)),
            best_score=float(q.best) if q else None,
            attempts=int(q.attempts) if q else 0,
            failed_attempts=int(q.failed) if q else 0,
            has_coding_pending=any(c not in passed_challenge_ids for c in cids),
        ))
    return stats


async def gather_companion(user: User, db: AsyncSession) -> CompanionResponse:
    """Resuelve posición + diagnóstico + recursos desde BD (sin LLM)."""
    # 0. Sin evaluación de entrada → respuesta mínima (consistente con regla R1)
    level_row = await db.execute(
        select(UserLevel.user_id).where(UserLevel.user_id == user.id)
    )
    if level_row.scalar_one_or_none() is None:
        return CompanionResponse(
            needs_assessment=True, position=None, diagnostic=None,
            resources=[], greeting=NEEDS_ASSESSMENT_GREETING,
        )

    # 1. Módulos + progreso (mismas 3 consultas planas que module_service)
    mods_res = await db.execute(
        select(Module).where(Module.is_active == True).order_by(Module.order_index)  # noqa: E712
    )
    modules = list(mods_res.scalars().all())
    if not modules:
        return CompanionResponse(
            needs_assessment=False, position=None, diagnostic=None,
            resources=[], greeting=EMPTY_COURSE_GREETING,
        )

    totals_rows = (
        await db.execute(
            select(Topic.module_id, func.count(Topic.id))
            .where(Topic.is_active == True)  # noqa: E712
            .group_by(Topic.module_id)
        )
    ).all()
    totals = {module_id: count for module_id, count in totals_rows}

    done_rows = (
        await db.execute(
            select(Topic.module_id, func.count(UserTopicProgress.id))
            .join(UserTopicProgress, UserTopicProgress.topic_id == Topic.id)
            .where(
                UserTopicProgress.user_id == user.id,
                UserTopicProgress.is_completed == True,  # noqa: E712
                Topic.is_active == True,  # noqa: E712
            )
            .group_by(Topic.module_id)
        )
    ).all()
    done = {module_id: count for module_id, count in done_rows}

    pairs = [(totals.get(m.id, 0), done.get(m.id, 0)) for m in modules]
    idx = pick_current_index(pairs)
    course_completed = idx is None
    current = modules[-1] if course_completed else modules[idx]
    total, completed = pairs[-1] if course_completed else pairs[idx]

    position = CompanionPosition(
        module_id=current.id,
        module_title=current.title,
        icon_name=current.icon_name,
        color_hex=current.color_hex,
        progress_pct=round(completed / total * 100, 1) if total else 0.0,
        topics_done=completed,
        topics_total=total,
        course_completed=course_completed,
    )

    # 2. Diagnóstico del módulo actual
    stats = await _gather_topic_stats(user, current.id, db)
    diagnostic = build_diagnostic(stats, current.id)

    # 3. Recursos curados del módulo actual (máx 3). Solo nivel módulo a
    # propósito: los recursos por tema ya se muestran en TopicPage (Fase 3)
    # y el seed siempre asigna module_id.
    res_rows = await db.execute(
        select(LearningResource)
        .where(
            LearningResource.is_active == True,  # noqa: E712
            LearningResource.module_id == current.id,
        )
        .order_by(LearningResource.order_index, LearningResource.id)
        .limit(MAX_RESOURCES)
    )
    resources = [
        LearningResourceResponse.model_validate(r) for r in res_rows.scalars().all()
    ]

    return CompanionResponse(
        needs_assessment=False,
        position=position,
        greeting=build_greeting(position, diagnostic),
        diagnostic=diagnostic,
        resources=resources,
    )
