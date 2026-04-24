"""
Tests de integración ISO/IEC 25010:2023 · Sprint 7.
Matriz RF → casos de prueba para validar cobertura ≥80% y éxito ≥90%.
Este archivo es un skeleton: completar con TestClient httpx + fixtures de usuarios
cuando comience Sprint 7.
"""

import pytest


pytestmark = [pytest.mark.integration]


@pytest.mark.skip(reason="Sprint 7: completar con TestClient + auth real")
class TestFuncionalidadCompletitud:
    """ISO 25010 § Functional suitability / Completeness."""

    def test_registro_login_flow(self):
        # TODO: POST /auth/register → 201, POST /auth/login → token
        pass

    def test_module_listing_with_progress(self):
        # TODO: GET /modules retorna 5 módulos con progress_pct
        pass


@pytest.mark.skip(reason="Sprint 7: completar con Ollama real o mock end-to-end")
class TestFuncionalidadCorrectitud:
    """ISO 25010 § Functional suitability / Correctness."""

    def test_quiz_submit_grades_correctly(self):
        # TODO: sesión IA quiz, submit con N respuestas correctas → score esperado
        pass

    def test_rag_cites_sources_when_available(self):
        # TODO: consulta conocida del corpus → respuesta con ≥1 fuente
        pass


@pytest.mark.skip(reason="Sprint 7: requiere dataset piloto")
class TestFuncionalidadPertinencia:
    """ISO 25010 § Functional suitability / Appropriateness."""

    def test_coding_adapts_to_level(self):
        # TODO: beginner obtiene difficulty=easy; advanced obtiene hard
        pass

    def test_rag_rejects_off_topic_educatively(self):
        # TODO: pregunta fuera del corpus → mensaje educativo de rechazo
        pass
