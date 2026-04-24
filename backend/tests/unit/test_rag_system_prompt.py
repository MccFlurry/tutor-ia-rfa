"""
Unit tests sobre el system prompt del RAG.
Verifican que las cláusulas anti-alucinación introducidas en Sprint 4 estén presentes.
"""

from app.services.rag_service import SYSTEM_PROMPT, NO_CONTEXT_RESPONSE


class TestSystemPrompt:
    def test_contains_antihallucination_clause(self):
        assert "ANTI-ALUCINACIÓN" in SYSTEM_PROMPT or "anti-alucinación" in SYSTEM_PROMPT.lower()

    def test_instructs_to_admit_missing_info(self):
        # Debe indicar al LLM decir "no está en el contexto" cuando corresponde
        assert any(
            phrase in SYSTEM_PROMPT.lower()
            for phrase in ["no cubre", "no cubra", "contexto no", "material del curso"]
        )

    def test_forbids_inventing_code(self):
        assert "NO inventes snippets" in SYSTEM_PROMPT or "NO inventes" in SYSTEM_PROMPT

    def test_no_context_response_rejects_educationally(self):
        assert NO_CONTEXT_RESPONSE
        assert len(NO_CONTEXT_RESPONSE) > 30
        # Es respuesta educativa, no error técnico
        assert "error" not in NO_CONTEXT_RESPONSE.lower()

    def test_spanish_peruvian(self):
        # Mantiene instrucción idioma
        assert "español peruano" in SYSTEM_PROMPT.lower()

    def test_has_context_and_history_placeholders(self):
        assert "{context}" in SYSTEM_PROMPT
        assert "{history}" in SYSTEM_PROMPT
