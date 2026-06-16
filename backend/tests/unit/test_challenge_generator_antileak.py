"""
Unit tests para el guardia anti copy-paste de challenge_generator_service.

Bug observado (16-jun-2026): el LLM ponía la solución completa dentro de la
sección "### Ejemplo:" del enunciado; el estudiante la copiaba y obtenía ~95.
El guardia detecta esa fuga y rechaza el reto (→ fallback al banco curado).
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import challenge_generator_service as gen
from app.services.challenge_generator_service import ChallengeGenerationError


SOLUTION = "```kotlin\nandroid {\n  compileSdk = 34\n  minSdk = 24\n}\n```"


def _clean_payload():
    return MagicMock(content=json.dumps({
        "title": "Suma",
        "description": "Suma dos enteros.\n## Ejemplo:\nEntrada: 2, 3 → Salida: 5\n## Criterios:\n- Debe sumar",
        "hints": "1. Usa +",
        "solution_code": "```kotlin\nfun suma(a: Int, b: Int) = a + b\n```",
        "difficulty": "easy",
        "language": "kotlin",
    }))


def test_strip_code_ignores_comments_and_whitespace():
    a = "android {\n  minSdk = 24 // mínimo\n}"
    b = "android{minSdk=24}"
    assert gen._strip_code(a) == gen._strip_code(b)


def test_leaks_when_solution_embedded_in_description():
    desc = f"Completa el archivo.\n### Ejemplo:\n{SOLUTION}\n### Criterios:\n- minSdk 24"
    assert gen._leaks_solution(desc, SOLUTION) is True


def test_partial_leak_majority_values_flagged():
    # Caso real (reto 59): el ejemplo deja minSdk como ___ pero filtra los otros
    # 3 valores graderados → el alumno copia y sólo rellena uno. Debe marcarse.
    full_solution = (
        "```kotlin\ndefaultConfig {\n  minSdk = 24\n  targetSdk = 34\n"
        "  versionCode = 1\n  versionName = \"1.0\"\n}\n```"
    )
    desc = (
        "## Ejemplo:\n```kotlin\ndefaultConfig {\n  minSdk = ___\n  targetSdk = 34\n"
        "  versionCode = 1\n  versionName = \"1.0\"\n}\n```\n"
        "## Criterios:\n- minSdk 24"
    )
    assert gen._leaks_solution(desc, full_solution) is True


def test_logic_challenge_not_flagged():
    # Reto de lógica: la solución (algoritmo) no aparece en el enunciado/ejemplo.
    solution = "```kotlin\nfun suma(a: Int, b: Int): Int {\n  return a + b\n}\n```"
    desc = (
        "Escribe una función `suma` que sume dos enteros.\n"
        "## Ejemplo:\nsuma(2, 3) retorna 5\n## Criterios:\n- Debe sumar correctamente"
    )
    assert gen._leaks_solution(desc, solution) is False


def test_no_leak_with_placeholders():
    desc = (
        "Completa el archivo.\n### Ejemplo (formato):\n"
        "```kotlin\nandroid {\n  compileSdk = ___\n  minSdk = ___\n}\n```\n"
        "### Criterios:\n- minSdk 24"
    )
    assert gen._leaks_solution(desc, SOLUTION) is False


def test_trivial_solution_not_flagged():
    # Solución muy corta (<20 chars de núcleo) no debe marcarse como fuga.
    assert gen._leaks_solution("usa println(x)", "println(x)") is False


def test_parse_response_raises_on_leak():
    payload = json.dumps({
        "title": "build.gradle",
        "description": f"Completa el archivo.\n### Ejemplo:\n{SOLUTION}\n### Criterios:\n- minSdk 24",
        "hints": "1. Revisa el SDK",
        "solution_code": SOLUTION,
        "difficulty": "easy",
        "language": "kotlin",
    })
    with pytest.raises(ChallengeGenerationError):
        gen._parse_response(payload, "easy")


def test_parse_response_ok_when_clean():
    payload = json.dumps({
        "title": "build.gradle",
        "description": (
            "Completa el archivo.\n### Ejemplo (formato):\n"
            "```kotlin\nandroid {\n  compileSdk = ___\n  minSdk = ___\n}\n```\n"
            "### Criterios:\n- minSdk 24"
        ),
        "hints": "1. Revisa el SDK",
        "solution_code": SOLUTION,
        "difficulty": "easy",
        "language": "kotlin",
    })
    out = gen._parse_response(payload, "easy")
    assert out.solution_code == SOLUTION
    assert out.title == "build.gradle"


class TestGenerationRetry:
    """Reintentar ante JSON inválido o fuga reduce las caídas al fallback."""

    @pytest.mark.asyncio
    async def test_retries_on_invalid_json_then_succeeds(self):
        llm = MagicMock()
        llm.ainvoke = AsyncMock(side_effect=[MagicMock(content="no json"), _clean_payload()])
        with patch.object(gen, "ChatOllama", return_value=llm):
            out = await gen.generate_challenge("x" * 200, "easy", "beginner")
        assert out.title == "Suma"
        assert llm.ainvoke.await_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_all_attempts_leak(self):
        leaking = MagicMock(content=json.dumps({
            "title": "build.gradle",
            "description": f"## Ejemplo:\n{SOLUTION}\n## Criterios:\n- x",
            "hints": "1. pista",
            "solution_code": SOLUTION,
            "difficulty": "easy",
            "language": "kotlin",
        }))
        llm = MagicMock()
        llm.ainvoke = AsyncMock(return_value=leaking)
        with patch.object(gen, "ChatOllama", return_value=llm):
            with pytest.raises(ChallengeGenerationError):
                await gen.generate_challenge("x" * 200, "easy", "beginner")
        assert llm.ainvoke.await_count == gen.MAX_GEN_ATTEMPTS

    @pytest.mark.asyncio
    async def test_connection_error_fails_fast(self):
        llm = MagicMock()
        llm.ainvoke = AsyncMock(side_effect=RuntimeError("conexión rechazada"))
        with patch.object(gen, "ChatOllama", return_value=llm):
            with pytest.raises(ChallengeGenerationError):
                await gen.generate_challenge("x" * 200, "easy", "beginner")
        assert llm.ainvoke.await_count == 1
