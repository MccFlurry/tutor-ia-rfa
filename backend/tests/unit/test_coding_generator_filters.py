"""
Unit tests para coding_generator_service.

Verifica:
- `_get_existing_unused` excluye desafíos que el estudiante ya aprobó.
- `regenerate_for_student` cae a fallback ante Exception genérico (no sólo
  ChallengeGenerationError), evitando 500s que dejan en blanco el frontend.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import coding_generator_service as cgs
from app.services.challenge_generator_service import ChallengeGenerationError


class TestExistingUnusedQueryShape:
    """
    No podemos correr la query real sin Postgres; pero podemos verificar que el
    helper hace UN execute() y devuelve el resultado de scalar_one_or_none().
    El test de regresión sirve para detectar cambios en la firma del helper.
    """

    @pytest.mark.asyncio
    async def test_returns_value_from_scalar_one_or_none(self):
        sentinel = MagicMock(id=999, title="Desafío X")
        db = MagicMock()
        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=sentinel)
        db.execute = AsyncMock(return_value=result)

        out = await cgs._get_existing_unused(db, uuid.uuid4(), topic_id=3)
        assert out is sentinel
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_no_match(self):
        db = MagicMock()
        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=None)
        db.execute = AsyncMock(return_value=result)
        out = await cgs._get_existing_unused(db, uuid.uuid4(), 1)
        assert out is None


class TestRegenerateFallsBackOnGenericError:
    """
    Antes del fix, `regenerate_for_student` sólo capturaba ChallengeGenerationError.
    Cualquier otro Exception se propagaba como 500 → pantalla en blanco en el frontend.
    Estos tests bloquean esa regresión.
    """

    @pytest.mark.asyncio
    async def test_generic_exception_uses_fallback(self):
        # Fallback challenge that the helper will return
        fallback_challenge = MagicMock(
            id=123,
            title="[Fallback] Lista mutable",
            is_ai_generated=True,
        )

        topic = MagicMock(id=1, content="contenido del tema con bastante texto para superar 100 chars. " * 5)
        user = MagicMock(id=uuid.uuid4())

        with patch.object(cgs, "generate_challenge", AsyncMock(side_effect=RuntimeError("boom"))), \
             patch.object(cgs, "_clone_from_fallback", AsyncMock(return_value=fallback_challenge)):
            db = MagicMock()
            db.add = MagicMock()
            db.flush = AsyncMock()
            out = await cgs.regenerate_for_student(db, topic, user, "intermediate")

        assert out is fallback_challenge

    @pytest.mark.asyncio
    async def test_challenge_generation_error_still_uses_fallback(self):
        fallback_challenge = MagicMock(id=124, title="[Fallback] Otro")
        topic = MagicMock(id=1, content="contenido suficientemente largo. " * 10)
        user = MagicMock(id=uuid.uuid4())

        with patch.object(
            cgs, "generate_challenge",
            AsyncMock(side_effect=ChallengeGenerationError("JSON inválido")),
        ), patch.object(cgs, "_clone_from_fallback", AsyncMock(return_value=fallback_challenge)):
            db = MagicMock()
            db.add = MagicMock()
            db.flush = AsyncMock()
            out = await cgs.regenerate_for_student(db, topic, user, "beginner")

        assert out is fallback_challenge

    @pytest.mark.asyncio
    async def test_no_fallback_raises_runtime_error(self):
        topic = MagicMock(id=1, content="contenido suficientemente largo. " * 10)
        user = MagicMock(id=uuid.uuid4())

        with patch.object(cgs, "generate_challenge", AsyncMock(side_effect=RuntimeError("boom"))), \
             patch.object(cgs, "_clone_from_fallback", AsyncMock(return_value=None)):
            db = MagicMock()
            db.add = MagicMock()
            db.flush = AsyncMock()
            with pytest.raises(RuntimeError):
                await cgs.regenerate_for_student(db, topic, user, "advanced")


class TestGetOrGenerateReusesExisting:
    """
    Si ya existe un desafío IA persistido no aprobado, se reutiliza sin volver a llamar
    al LLM. Esto cubre el requisito del usuario: "una vez creados, quedan grabados".
    """

    @pytest.mark.asyncio
    async def test_reuses_existing_challenge_without_calling_llm(self):
        existing = MagicMock(id=42, title="Reto persistido", is_ai_generated=True)
        topic = MagicMock(id=1, content="x" * 200)
        user = MagicMock(id=uuid.uuid4())
        llm_spy = AsyncMock()

        with patch.object(cgs, "_get_existing_unused", AsyncMock(return_value=existing)), \
             patch.object(cgs, "generate_challenge", llm_spy):
            db = MagicMock()
            out = await cgs.get_or_generate_for_student(db, topic, user, "intermediate")

        assert out is existing
        llm_spy.assert_not_called()
