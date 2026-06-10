"""Unit tests del motor companion (puro, sin BD ni LLM)."""
from app.schemas.companion import CompanionPosition, TopicStat
from app.services.companion_service import (
    build_diagnostic,
    build_greeting,
    pick_current_index,
)


def _stat(**over):
    base = dict(
        topic_id=1, title="Tema", order_index=0, visited=True, completed=False,
        best_score=None, attempts=0, failed_attempts=0, has_coding_pending=False,
    )
    base.update(over)
    return TopicStat(**base)


# --- pick_current_index: módulo actual = primer desbloqueado e incompleto ---

def test_pick_current_nothing_started_is_first_module():
    assert pick_current_index([(4, 0), (5, 0)]) == 0


def test_pick_current_mid_course():
    assert pick_current_index([(4, 4), (5, 2), (4, 0)]) == 1


def test_pick_current_all_complete_returns_none():
    assert pick_current_index([(4, 4), (5, 5)]) is None


def test_pick_current_empty_module_is_current():
    # módulo sin temas nunca cuenta como completo (regla de compute_locks)
    assert pick_current_index([(4, 4), (0, 0), (4, 0)]) == 1


# --- build_diagnostic: clasificación por bandas ---

def test_low_score_is_weak_with_retry_action():
    d = build_diagnostic(
        [_stat(topic_id=12, title="Layouts", best_score=45, attempts=2, failed_attempts=2)],
        module_id=3,
    )
    assert [t.topic_id for t in d.weak] == [12]
    assert d.next_action.kind == "retry_quiz"
    assert d.next_action.route == "/topics/12"


def test_two_failed_attempts_is_weak_even_if_passed():
    d = build_diagnostic([_stat(best_score=70, attempts=3, failed_attempts=2)], module_id=3)
    assert len(d.weak) == 1


def test_dominated_score_overrides_failed_attempts():
    d = build_diagnostic([_stat(best_score=90, attempts=3, failed_attempts=2)], module_id=3)
    assert d.weak == [] and d.practice == []


def test_mid_band_is_practice():
    d = build_diagnostic([_stat(best_score=70, attempts=1, failed_attempts=0)], module_id=3)
    assert len(d.practice) == 1 and d.weak == []


def test_unvisited_topic_is_next_action():
    d = build_diagnostic(
        [
            _stat(topic_id=1, best_score=85, completed=True),
            _stat(topic_id=2, title="Intents", order_index=1, visited=False),
        ],
        module_id=3,
    )
    assert d.next_action.kind == "next_topic"
    assert d.next_action.route == "/topics/2"


def test_weak_beats_pending_in_priority():
    d = build_diagnostic(
        [
            _stat(topic_id=1, best_score=40, failed_attempts=1),
            _stat(topic_id=2, order_index=1, visited=False),
        ],
        module_id=3,
    )
    assert d.next_action.kind == "retry_quiz"


def test_coding_pending_when_no_weak_nor_pending():
    d = build_diagnostic(
        [_stat(topic_id=1, best_score=85, completed=True, has_coding_pending=True)],
        module_id=3,
    )
    assert d.next_action.kind == "coding_challenge"
    assert d.next_action.route == "/topics/1"


def test_fallback_next_action_is_module():
    d = build_diagnostic([_stat(best_score=85, completed=True)], module_id=3)
    assert d.next_action.kind == "module"
    assert d.next_action.route == "/modules/3"


def test_empty_module_stats():
    d = build_diagnostic([], module_id=3)
    assert d.weak == [] and d.practice == []
    assert d.next_action.kind == "module"


def test_boundary_60_with_two_failed_attempts_is_weak():
    # score exactamente 60 no es <60, pero ≥2 fallidos sin dominar → repasar
    d = build_diagnostic([_stat(best_score=60.0, attempts=3, failed_attempts=2)], module_id=3)
    assert len(d.weak) == 1 and d.practice == []


def test_visited_incomplete_topic_is_pending_next_action():
    # visitado pero no completado y sin quiz → sigue siendo el siguiente paso
    d = build_diagnostic(
        [_stat(topic_id=7, title="Fragments", visited=True, completed=False)],
        module_id=3,
    )
    assert d.next_action.kind == "next_topic"
    assert d.next_action.route == "/topics/7"


# --- build_greeting: plantillas por estado ---

def _pos(**over):
    base = dict(
        module_id=3, module_title="Interfaces de Usuario", icon_name=None,
        color_hex=None, progress_pct=60.0, topics_done=3, topics_total=5,
        course_completed=False,
    )
    base.update(over)
    return CompanionPosition(**base)


def test_greeting_course_completed():
    g = build_greeting(_pos(course_completed=True), build_diagnostic([], module_id=3))
    assert "Felicitaciones" in g


def test_greeting_mentions_weak_topic():
    d = build_diagnostic(
        [_stat(title="Layouts", best_score=45, failed_attempts=2)], module_id=3
    )
    g = build_greeting(_pos(), d)
    assert "Layouts" in g and "Interfaces de Usuario" in g


def test_greeting_fresh_module():
    d = build_diagnostic([_stat(visited=False)], module_id=3)
    assert d.weak == []  # precondición: la rama débil no debe activarse
    g = build_greeting(_pos(topics_done=0, progress_pct=0.0), d)
    assert "comenzando" in g.lower()


def test_greeting_default_mentions_next_step():
    d = build_diagnostic([_stat(best_score=85, completed=True)], module_id=3)
    g = build_greeting(_pos(), d)
    assert "siguiente paso" in g.lower()
    assert d.next_action.label in g  # «Ver el módulo» interpolado
