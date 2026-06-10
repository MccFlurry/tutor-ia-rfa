"""Unit tests del motor companion (puro, sin BD ni LLM)."""
from app.schemas.companion import CompanionPosition, TopicStat
from app.services.companion_service import build_diagnostic, pick_current_index


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
