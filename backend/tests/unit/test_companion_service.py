"""Unit tests del motor companion (puro, sin BD ni LLM)."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from types import SimpleNamespace

from app.schemas.companion import CompanionPosition, TopicStat
from app.services.companion_service import (
    _gather_topic_stats,
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


# --- _gather_topic_stats: escala de score (regresión) ---

def _rows(rows):
    r = MagicMock()
    r.all = MagicMock(return_value=rows)
    return r


@pytest.mark.asyncio
async def test_gather_topic_stats_converts_fraction_score_to_0_100():
    # QuizAttempt.score se guarda 0-1; el diagnóstico trabaja 0-100.
    db = MagicMock()
    quiz_row = SimpleNamespace(topic_id=9, best=0.45, attempts=2, failed=2)
    db.execute = AsyncMock(side_effect=[
        _rows([(9, "Layouts", 0)]),        # topics del módulo
        _rows([(9, False)]),               # progreso (visitado, no completado)
        _rows([quiz_row]),                 # agregado de quiz (fracción 0-1)
        _rows([]),                         # desafíos de catálogo → ninguno
    ])
    user = SimpleNamespace(id="00000000-0000-0000-0000-000000000001")
    stats = await _gather_topic_stats(user, module_id=3, db=db)
    assert len(stats) == 1
    assert stats[0].best_score == 45.0  # 0.45 → 45.0, cae en banda «repasar»
    assert stats[0].failed_attempts == 2
