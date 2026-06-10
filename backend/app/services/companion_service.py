"""services/companion_service.py — Posición del estudiante + diagnóstico determinista (Fase 5).

El sistema «sigue» al estudiante: pick_current_index/build_diagnostic/build_greeting
son funciones puras (sin BD ni LLM). gather_companion resuelve el estado desde BD
reutilizando el invariante de desbloqueo secuencial de module_service.compute_locks.
"""
from app.schemas.companion import (
    CompanionPosition,
    ModuleDiagnostic,
    NextAction,
    TopicDiagnostic,
    TopicStat,
)
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
