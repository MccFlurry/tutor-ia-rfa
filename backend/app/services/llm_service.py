"""
llm_service.py — Cliente Ollama para generación de quizzes con IA.
Genera preguntas de opción múltiple basadas en el contenido del tema.
"""

import json
import re
from dataclasses import dataclass

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.utils.logger import logger


@dataclass
class GeneratedQuestion:
    question_text: str
    options: list[str]
    correct_option_index: int
    explanation: str


class QuizGenerationError(Exception):
    """Raised when quiz generation fails."""
    pass


LEVEL_GUIDANCE = {
    "beginner": (
        "NIVEL DEL ESTUDIANTE: Principiante.\n"
        "- Enfócate en preguntas conceptuales y sintaxis básica.\n"
        "- Un solo concepto por pregunta.\n"
        "- Usa lenguaje sencillo y ejemplos directos.\n"
        "- Evita edge cases, optimizaciones o combinaciones complejas.\n"
        "- Incluye pistas contextuales dentro del enunciado cuando sea apropiado."
    ),
    "intermediate": (
        "NIVEL DEL ESTUDIANTE: Intermedio.\n"
        "- Combina hasta 2 conceptos relacionados por pregunta.\n"
        "- Aplica situaciones prácticas realistas del desarrollo Android.\n"
        "- Menos pistas explícitas; el estudiante debe razonar.\n"
        "- Incluye preguntas de lectura de código de complejidad moderada."
    ),
    "advanced": (
        "NIVEL DEL ESTUDIANTE: Avanzado.\n"
        "- Incluye edge cases, trampas sutiles y consideraciones de eficiencia.\n"
        "- Pregunta sobre diseño, refactorización y trade-offs arquitectónicos.\n"
        "- Exige que el estudiante combine múltiples conceptos y detecte errores no obvios.\n"
        "- Sin pistas; las opciones distractoras deben ser plausibles."
    ),
}


QUIZ_SYSTEM_PROMPT = """Eres un generador de autoevaluaciones para un curso de Aplicaciones Móviles \
del IESTP República Federal de Alemania (RFA) en Chiclayo, Perú.

Tu tarea es generar preguntas de opción múltiple basadas EXCLUSIVAMENTE en el contenido \
de la lección que se te proporciona, adaptadas al nivel del estudiante.

{level_guidance}

REGLAS ESTRICTAS:
1. Genera exactamente {num_questions} preguntas.
2. Cada pregunta debe tener exactamente 4 opciones.
3. Solo una opción es correcta por pregunta.
4. correct_option_index es el índice (0, 1, 2 o 3) de la opción correcta.
5. La explicación debe ser breve y clara (1-2 oraciones).
6. Todo debe estar en español.
7. Las preguntas deben evaluar comprensión, no memorización textual.
8. Ajusta la dificultad al nivel del estudiante indicado arriba.
9. Responde ÚNICAMENTE con un objeto JSON con la clave "questions".

FORMATO DE RESPUESTA (JSON objeto):
{{
  "questions": [
    {{
      "question_text": "¿Pregunta aquí?",
      "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
      "correct_option_index": 0,
      "explanation": "Explicación breve de por qué es correcta."
    }}
  ]
}}"""


def _truncate_content(content: str, max_chars: int = 3500) -> str:
    """Truncate topic content to fit within LLM context window."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n\n[Contenido truncado...]"


def _parse_llm_response(raw: str, num_questions: int) -> list[GeneratedQuestion]:
    """Parse and validate the LLM JSON response into GeneratedQuestion objects."""
    # Strip markdown code fences if present
    cleaned = raw.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Try to extract JSON array from the response
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise QuizGenerationError(f"LLM devolvió JSON inválido: {e}")

    # Handle wrapper object: {"questions": [...]}
    if isinstance(data, dict):
        if "questions" in data and isinstance(data["questions"], list):
            data = data["questions"]
        else:
            raise QuizGenerationError("LLM devolvió un objeto JSON sin la clave 'questions'")

    if not isinstance(data, list):
        raise QuizGenerationError("LLM no devolvió un array JSON")

    if len(data) < num_questions:
        logger.warning(f"LLM generó {len(data)} preguntas, se esperaban {num_questions}")

    questions = []
    for i, item in enumerate(data[:num_questions]):
        # Validate required fields
        if not isinstance(item, dict):
            raise QuizGenerationError(f"Pregunta {i} no es un objeto JSON")

        q_text = item.get("question_text", "").strip()
        options = item.get("options", [])
        correct_idx = item.get("correct_option_index", -1)
        explanation = item.get("explanation", "").strip()

        if not q_text:
            raise QuizGenerationError(f"Pregunta {i} sin texto")
        if not isinstance(options, list) or len(options) != 4:
            raise QuizGenerationError(f"Pregunta {i} no tiene exactamente 4 opciones")
        if not isinstance(correct_idx, int) or correct_idx < 0 or correct_idx > 3:
            raise QuizGenerationError(f"Pregunta {i} tiene correct_option_index inválido: {correct_idx}")

        questions.append(GeneratedQuestion(
            question_text=q_text,
            options=[str(o).strip() for o in options],
            correct_option_index=correct_idx,
            explanation=explanation or "Sin explicación disponible.",
        ))

    if len(questions) == 0:
        raise QuizGenerationError("No se pudieron extraer preguntas válidas")

    return questions


async def generate_quiz_questions(
    topic_content: str,
    num_questions: int | None = None,
    student_level: str = "intermediate",
) -> list[GeneratedQuestion]:
    """
    Generate quiz questions using Ollama LLM based on topic content, adapted to student level.

    student_level: "beginner" | "intermediate" | "advanced"
    Raises QuizGenerationError if generation fails.
    """
    if num_questions is None:
        num_questions = settings.QUIZ_NUM_QUESTIONS

    if len(topic_content.strip()) < 100:
        raise QuizGenerationError("Contenido del tema demasiado corto para generar preguntas")

    truncated = _truncate_content(topic_content, max_chars=2500)

    level_guidance = LEVEL_GUIDANCE.get(student_level, LEVEL_GUIDANCE["intermediate"])
    system_prompt = QUIZ_SYSTEM_PROMPT.format(
        num_questions=num_questions,
        level_guidance=level_guidance,
    )
    human_prompt = (
        f"--- CONTENIDO DE LA LECCIÓN ---\n\n{truncated}\n\n--- FIN DEL CONTENIDO ---\n\n"
        f"Genera {num_questions} preguntas de autoevaluación basadas en este contenido, "
        f"adaptadas al nivel {student_level}."
    )

    try:
        llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.7,
            num_ctx=8192,
            num_predict=4096,
            format="json",
        )

        logger.info(f"Generando {num_questions} preguntas via Ollama (nivel={student_level})...")
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])

        raw_content = response.content
        logger.debug(f"Respuesta LLM (primeros 200 chars): {raw_content[:200]}")

        questions = _parse_llm_response(raw_content, num_questions)
        logger.info(f"Quiz generado exitosamente: {len(questions)} preguntas")
        return questions

    except QuizGenerationError:
        raise
    except Exception as e:
        logger.error(f"Error al comunicarse con Ollama: {e}")
        raise QuizGenerationError(f"No se pudo conectar con el servicio de IA: {e}")
