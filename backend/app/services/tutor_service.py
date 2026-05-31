"""services/tutor_service.py — Motor determinista de nudges proactivos.

build_nudges() es una función pura: recibe un StudentSnapshot ya resuelto
y el contexto de pantalla, devuelve los nudges aplicables. Sin BD ni LLM.
gather_snapshot()/get_nudges() (Task 3) resuelven el estado desde BD.
"""
from app.schemas.tutor import Nudge, StudentSnapshot

# Días de racha que disparan felicitación
STREAK_MILESTONES = (3, 7, 14, 30)
# Días sin actividad para considerar inactivo
INACTIVE_DAYS = 7
# Máximo de nudges en el dashboard (evita saturar)
DASHBOARD_MAX = 3


def build_nudges(
    snap: StudentSnapshot,
    context: str,
    *,
    topic_id: int | None = None,
    module_id: int | None = None,  # reservado para reglas por módulo (Fase 4)
    score: float | None = None,  # usado por quiz_result/coding_result (Fase 4)
) -> list[Nudge]:
    """Aplica las reglas deterministas y devuelve los nudges del contexto."""
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

    # contextos de resultado (quiz_result/coding_result/assessment_result) → Fase 4
    return nudges
