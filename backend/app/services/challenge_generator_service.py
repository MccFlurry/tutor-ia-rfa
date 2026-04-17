"""
challenge_generator_service.py — LLM genera desafíos de programación
a partir del contenido de un tema + nivel objetivo. El docente revisa
y aprueba antes de persistir.
"""
import json
import re
from dataclasses import dataclass

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.utils.logger import logger


@dataclass
class GeneratedChallenge:
    title: str
    description: str
    hints: str
    solution_code: str
    difficulty: str
    language: str = "kotlin"


class ChallengeGenerationError(Exception):
    pass


LEVEL_DIFF_GUIDANCE = {
    "beginner": (
        "El estudiante es Principiante. El desafío debe requerir sintaxis básica, "
        "1 concepto principal, con pistas claras y ejemplos concretos."
    ),
    "intermediate": (
        "El estudiante es Intermedio. El desafío puede combinar 2 conceptos, "
        "requerir lógica moderada y aplicación práctica. Pistas reveladas parcialmente."
    ),
    "advanced": (
        "El estudiante es Avanzado. El desafío debe incluir edge cases, "
        "requerir diseño o refactorización, y ser resolvible con código idiomático sin pistas."
    ),
}


CHALLENGE_PROMPT = """Eres un diseñador de desafíos de programación para un curso de \
Aplicaciones Móviles (Android/Kotlin) del IESTP República Federal de Alemania.

Genera UN desafío de programación basado en el tema del curso proporcionado, \
adaptado al nivel del estudiante.

{level_guidance}

DIFICULTAD OBJETIVO: {difficulty} (easy = 1 concepto simple; medium = combinación moderada; hard = edge cases + optimización).

LENGUAJE: Kotlin.

CONTENIDO DEL TEMA (fragmento):
{topic_content}

Responde ÚNICAMENTE con un objeto JSON con esta estructura exacta (todo en español peruano):
{{
  "title": "<título corto del desafío>",
  "description": "<descripción en Markdown: problema + ejemplos de entrada/salida + criterios>",
  "hints": "<pistas numeradas en Markdown, 2-4 pistas>",
  "solution_code": "<código Kotlin de referencia que resuelva el problema>",
  "difficulty": "{difficulty}",
  "language": "kotlin"
}}

REGLAS:
- La descripción debe ser clara, con sección "Ejemplo:" y sección "Criterios de evaluación:".
- El código solución debe ser idiomático y compilable en Kotlin.
- Las pistas son una cadena Markdown con lista numerada.
- No incluyas texto fuera del JSON."""


def _parse_response(raw: str, difficulty: str) -> GeneratedChallenge:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ChallengeGenerationError(f"LLM devolvió JSON inválido: {e}")

    if not isinstance(data, dict):
        raise ChallengeGenerationError("LLM no devolvió un objeto JSON")

    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    hints = str(data.get("hints", "")).strip()
    solution = str(data.get("solution_code", "")).strip()

    if not title or not description or not solution:
        raise ChallengeGenerationError("Campos obligatorios vacíos en la respuesta LLM")

    return GeneratedChallenge(
        title=title,
        description=description,
        hints=hints or "_Sin pistas disponibles._",
        solution_code=solution,
        difficulty=difficulty,
        language="kotlin",
    )


async def generate_challenge(
    topic_content: str,
    difficulty: str = "medium",
    target_level: str = "intermediate",
) -> GeneratedChallenge:
    """Generate a coding challenge via LLM. Not persisted — admin reviews first."""
    if len(topic_content.strip()) < 100:
        raise ChallengeGenerationError("Contenido del tema demasiado corto")

    trimmed = topic_content[:3500]
    if len(topic_content) > 3500:
        trimmed += "\n\n[Contenido truncado...]"

    level_guidance = LEVEL_DIFF_GUIDANCE.get(target_level, LEVEL_DIFF_GUIDANCE["intermediate"])
    prompt = CHALLENGE_PROMPT.format(
        level_guidance=level_guidance,
        difficulty=difficulty,
        topic_content=trimmed,
    )

    llm = ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.7,
        num_ctx=8192,
        num_predict=4096,
        format="json",
    )

    logger.info(f"Generando desafío IA: nivel={target_level}, dificultad={difficulty}")
    try:
        response = await llm.ainvoke([
            SystemMessage(content="Eres un diseñador de desafíos de programación. Responde solo JSON."),
            HumanMessage(content=prompt),
        ])
    except Exception as e:
        logger.error(f"Error LLM generando desafío: {e}")
        raise ChallengeGenerationError(f"No se pudo conectar con el servicio IA: {e}")

    return _parse_response(response.content, difficulty)
