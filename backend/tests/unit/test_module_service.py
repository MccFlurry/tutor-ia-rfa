"""Unit tests para la regla de desbloqueo secuencial de módulos.

`compute_locks` es la única fuente de verdad del invariante:
un módulo queda bloqueado hasta que el módulo anterior esté 100% completo.
"""

from app.services.module_service import compute_locks


def test_empty_returns_empty():
    assert compute_locks([]) == []


def test_first_module_always_unlocked():
    # El primer módulo nunca depende de nadie → siempre desbloqueado.
    assert compute_locks([(4, 0)]) == [False]


def test_module_locked_until_previous_complete():
    # M1 al 50% (2/4) → M2 bloqueado.
    assert compute_locks([(4, 2), (4, 0)]) == [False, True]


def test_module_unlocks_when_previous_fully_complete():
    # M1 100% → M2 desbloqueado; M2 al 0% → M3 bloqueado.
    assert compute_locks([(4, 4), (4, 0), (4, 0)]) == [False, False, True]


def test_all_unlocked_when_all_complete():
    assert compute_locks([(2, 2), (2, 2), (2, 2)]) == [False, False, False]


def test_zero_topic_module_does_not_unlock_next():
    # Un módulo sin temas nunca cuenta como completo → el siguiente queda bloqueado.
    assert compute_locks([(0, 0), (4, 0)]) == [False, True]
