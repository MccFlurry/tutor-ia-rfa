"""services/tutor_service.py — Motor determinista de nudges proactivos.

build_nudges() es una función pura: recibe un StudentSnapshot ya resuelto
y el contexto de pantalla, devuelve los nudges aplicables. Sin BD ni LLM.
gather_snapshot()/get_nudges() (Task 3) resuelven el estado desde BD.
"""
from datetime import datetime, timezone

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_level import UserLevel
from app.models.topic import Topic
from app.models.module import Module
from app.models.progress import UserTopicProgress
from app.models.quiz import QuizAttempt
from app.schemas.tutor import Nudge, StudentSnapshot
from app.services.progress_service import compute_streak

# Días de racha que disparan felicitación
STREAK_MILESTONES = (3, 7, 14, 30)
# Días sin actividad para considerar inactivo
INACTIVE_DAYS = 7
# Máximo de nudges en el dashboard (evita saturar)
DASHBOARD_MAX = 3
# Contextos de resultado — deterministas por score, sin snapshot
RESULT_CONTEXTS = ("quiz_result", "coding_result", "assessment_result")


def _result_nudges(context: str, score: float | None, topic_id: int | None) -> list[Nudge]:
    """Refuerzo determinista por banda de puntaje (0-100). Fase 4."""
    if score is None:
        return []

    if context == "quiz_result":
        if score >= 80:
            return [Nudge(
                id="quiz_result_high", tone="success", icon="trophy",
                title="¡Excelente trabajo!",
                message="Dominas este tema. Mantén el ritmo y sigue avanzando.",
            )]
        if score >= 60:
            return [Nudge(
                id="quiz_result_pass", tone="success", icon="check",
                title="¡Aprobaste!",
                message="Buen trabajo. Repasa los puntos que fallaste para afianzar lo aprendido.",
                cta_label="Repasar el tema" if topic_id else None,
                cta_route=f"/topics/{topic_id}" if topic_id else None,
            )]
        return [Nudge(
            id="quiz_result_low", tone="warning", icon="repeat",
            title="Casi lo logras",
            message="No alcanzaste el 60%. Repasa el contenido y vuelve a intentarlo; cada intento te acerca.",
            cta_label="Repasar el tema" if topic_id else None,
            cta_route=f"/topics/{topic_id}" if topic_id else None,
        )]

    if context == "coding_result":
        if score >= 80:
            return [Nudge(
                id="coding_result_high", tone="success", icon="trophy",
                title="¡Código sólido!",
                message="Gran solución. Anímate con un desafío de mayor dificultad.",
            )]
        if score >= 60:
            return [Nudge(
                id="coding_result_mid", tone="encourage", icon="rocket",
                title="Buen avance",
                message="Tu código funciona; revisa las mejoras sugeridas para pulirlo aún más.",
            )]
        return [Nudge(
            id="coding_result_low", tone="warning", icon="repeat",
            title="Sigamos puliendo",
            message="Revisa la retroalimentación y las pistas, ajusta tu código y vuelve a enviarlo.",
        )]

    if context == "assessment_result":
        if score < 40:
            msg = "Empezarás por las bases. Sigue el orden de los módulos desde el M1, a tu ritmo."
        elif score <= 75:
            msg = "Tienes buenas bases. Enfócate en los temas que más se te dificulten."
        else:
            msg = "¡Gran dominio! Reta tus habilidades con los módulos más avanzados."
        return [Nudge(
            id="assessment_result", tone="info", icon="compass",
            title="Tu ruta de aprendizaje",
            message=msg, cta_label="Ver módulos", cta_route="/modules",
        )]

    return []


def build_nudges(
    snap: StudentSnapshot,
    context: str,
    *,
    topic_id: int | None = None,
    module_id: int | None = None,  # reservado para reglas por módulo (Fase 4)
    score: float | None = None,  # usado por quiz_result/coding_result (Fase 4)
) -> list[Nudge]:
    """Aplica las reglas deterministas y devuelve los nudges del contexto."""
    # Fase 4 — contextos de resultado: deterministas por score, sin snapshot
    if context in RESULT_CONTEXTS:
        return _result_nudges(context, score, topic_id)

    nudges: list[Nudge] = []

    # R1 — sin evaluación de entrada: bloquea todo lo demás
    if not snap.has_level:
        return [Nudge(
            id="no_level", tone="info", icon="compass",
            title="Empecemos por conocerte",
            message="Aún no realizas tu evaluación de entrada. Tómala para "
                    "personalizar tu ruta de aprendizaje.",
            cta_label="Ir a la evaluación", cta_route="/assessment",
        )]

    if context in ("dashboard", "module"):
        # R2 — progreso cero
        if snap.overall_pct <= 0:
            nudges.append(Nudge(
                id="welcome_start", tone="encourage", icon="rocket",
                title="¡Bienvenido a tu curso!",
                message="Comienza con el Módulo 1 para construir tus bases en "
                        "aplicaciones móviles.",
                cta_label="Empezar ahora", cta_route="/modules",
            ))

        # R3 — inactividad
        if snap.overall_pct > 0 and snap.days_inactive is not None and snap.days_inactive >= INACTIVE_DAYS:
            msg = "¡Qué bueno verte de nuevo!"
            cta_label = None
            cta_route = None
            if snap.last_quiz_topic_title:
                msg += f" Retoma donde lo dejaste: «{snap.last_quiz_topic_title}»."
            if snap.last_quiz_topic_id:
                cta_label = "Continuar"
                cta_route = f"/topics/{snap.last_quiz_topic_id}"
            nudges.append(Nudge(
                id="inactive", tone="encourage", icon="hand",
                title="¡Bienvenido de vuelta!", message=msg,
                cta_label=cta_label, cta_route=cta_route,
            ))

        # R4 — módulo casi completo
        if snap.near_complete_module_title and snap.near_complete_module_id is not None:
            nudges.append(Nudge(
                id="near_complete", tone="info", icon="flag",
                title="¡Estás muy cerca!",
                message=f"Te falta poco para terminar «{snap.near_complete_module_title}». "
                        "Termínalo y desbloquea el siguiente.",
                cta_label="Ver módulo",
                cta_route=f"/modules/{snap.near_complete_module_id}",
            ))

        # R5 — hito de racha
        if snap.streak_days in STREAK_MILESTONES:
            nudges.append(Nudge(
                id=f"streak_{snap.streak_days}", tone="success", icon="flame",
                title=f"¡Racha de {snap.streak_days} días!",
                message="Mantén el hábito; la constancia es clave para dominar "
                        "el desarrollo móvil.",
            ))

        return nudges[:DASHBOARD_MAX]

    if context == "topic":
        # R6 — último quiz reprobado en este tema → invitar a repasar/reintentar
        if (
            snap.last_quiz_passed is False
            and snap.last_quiz_topic_id is not None
            and (topic_id is None or topic_id == snap.last_quiz_topic_id)
        ):
            nudges.append(Nudge(
                id="quiz_retry", tone="warning", icon="repeat",
                title="Repasemos juntos",
                message="No aprobaste el último intento. Repasa el contenido y "
                        "vuelve a intentar el quiz; cada intento te acerca.",
                cta_label="Reintentar quiz",
                cta_route=f"/quiz/{snap.last_quiz_topic_id}",
            ))
        return nudges

    # contexto desconocido — sin nudges
    return nudges


# ---------------------------------------------------------------------------
# Umbral de "módulo casi completo" (porcentaje mínimo para disparar R4)
# ---------------------------------------------------------------------------
NEAR_COMPLETE_PCT = 80.0


async def gather_snapshot(
    user, db: AsyncSession, *, topic_id: int | None = None
) -> StudentSnapshot:
    """Resuelve el estado del estudiante desde BD (sin LLM)."""
    # 1. Nivel del estudiante
    level_row = await db.execute(
        select(UserLevel).where(UserLevel.user_id == user.id)
    )
    level = level_row.scalar_one_or_none()
    if level is None:
        return StudentSnapshot(
            has_level=False, level=None, overall_pct=0.0,
            last_quiz_passed=None, last_quiz_topic_title=None,
            last_quiz_topic_id=None, days_inactive=None,
            near_complete_module_title=None, near_complete_module_id=None,
            streak_days=0,
        )

    # 2. Progreso global (temas activos totales vs completados por el usuario)
    total_q = await db.execute(
        select(func.count(Topic.id)).where(Topic.is_active == True)  # noqa: E712
    )
    total = total_q.scalar() or 0
    done_q = await db.execute(
        select(func.count(UserTopicProgress.id))
        .join(Topic, Topic.id == UserTopicProgress.topic_id)
        .where(
            UserTopicProgress.user_id == user.id,
            UserTopicProgress.is_completed == True,  # noqa: E712
            Topic.is_active == True,  # noqa: E712
        )
    )
    done = done_q.scalar() or 0
    overall_pct = round(done / total * 100, 1) if total else 0.0

    # 3. Último intento de quiz (para reglas R3/R6)
    last_quiz_q = await db.execute(
        select(QuizAttempt, Topic)
        .join(Topic, Topic.id == QuizAttempt.topic_id)
        .where(QuizAttempt.user_id == user.id)
        .order_by(desc(QuizAttempt.attempted_at))
        .limit(1)
    )
    lq = last_quiz_q.first()
    last_quiz_passed = lq[0].is_passed if lq else None
    last_quiz_topic_title = lq[1].title if lq else None
    last_quiz_topic_id = lq[1].id if lq else None

    # 4. Días sin actividad (último acceso a cualquier tema)
    last_acc_q = await db.execute(
        select(UserTopicProgress.last_accessed_at)
        .where(UserTopicProgress.user_id == user.id)
        .order_by(desc(UserTopicProgress.last_accessed_at))
        .limit(1)
    )
    last_acc = last_acc_q.first()
    days_inactive = None
    if last_acc and last_acc[0]:
        delta = datetime.now(timezone.utc) - last_acc[0]
        days_inactive = delta.days

    # 5. Módulo casi completo (mayor porcentaje en [NEAR_COMPLETE_PCT, 100))
    near_title = None
    near_id = None
    mod_rows = await db.execute(
        select(
            Module.id, Module.title,
            func.count(Topic.id).label("total"),
            func.count(UserTopicProgress.id).filter(
                UserTopicProgress.is_completed == True  # noqa: E712
            ).label("done"),
        )
        .join(Topic, Topic.module_id == Module.id)
        .outerjoin(
            UserTopicProgress,
            (UserTopicProgress.topic_id == Topic.id)
            & (UserTopicProgress.user_id == user.id),
        )
        .where(Module.is_active == True, Topic.is_active == True)  # noqa: E712
        .group_by(Module.id, Module.title)
        .order_by(Module.order_index)
    )
    best_pct = 0.0
    for mid, mtitle, mtotal, mdone in mod_rows.all():
        pct = round((mdone or 0) / mtotal * 100, 1) if mtotal else 0.0
        if NEAR_COMPLETE_PCT <= pct < 100 and pct > best_pct:
            best_pct, near_title, near_id = pct, mtitle, mid

    # 6. Racha (delega a compute_streak; retorna dict con clave "current_streak")
    streak = await compute_streak(user.id, db)
    streak_days = streak.get("current_streak", 0) if streak else 0

    return StudentSnapshot(
        has_level=True, level=level.level, overall_pct=overall_pct,
        last_quiz_passed=last_quiz_passed,
        last_quiz_topic_title=last_quiz_topic_title,
        last_quiz_topic_id=last_quiz_topic_id,
        days_inactive=days_inactive,
        near_complete_module_title=near_title,
        near_complete_module_id=near_id,
        streak_days=streak_days,
    )


async def get_nudges(
    user, db: AsyncSession, context: str, *,
    topic_id: int | None = None, module_id: int | None = None,
    score: float | None = None,
) -> list[Nudge]:
    """Resuelve el snapshot desde BD y aplica las reglas deterministas."""
    # Fase 4 — result contexts are score-only; skip the DB round-trip
    if context in RESULT_CONTEXTS:
        return build_nudges(None, context, topic_id=topic_id, module_id=module_id, score=score)
    snap = await gather_snapshot(user, db, topic_id=topic_id)
    return build_nudges(
        snap, context, topic_id=topic_id, module_id=module_id, score=score
    )
