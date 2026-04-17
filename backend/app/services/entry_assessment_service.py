"""
entry_assessment_service.py — Generación de evaluación de entrada para
personalización CRISP-DM. LLM genera 10-15 preguntas cubriendo M1-M5,
con fallback al banco del docente si Ollama falla.
"""

import json
import re
import random
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.module import Module
from app.models.assessment_bank import EntryAssessmentBank
from app.utils.logger import logger


NUM_ASSESSMENT_QUESTIONS = 12  # cubre M1-M5 con dificultad mixta


@dataclass
class AssessmentQuestion:
    question_text: str
    options: list[str]
    correct_index: int
    module_id: int
    difficulty: str  # easy | medium | hard


class AssessmentGenerationError(Exception):
    """Raised when assessment generation fails."""
    pass


ASSESSMENT_SYSTEM_PROMPT = """Eres un generador de evaluaciones diagnósticas para el curso \
de Aplicaciones Móviles (Android/Kotlin) del IESTP República Federal de Alemania, Chiclayo, Perú.

Tu tarea es generar preguntas diagnósticas de opción múltiple que cubran TODOS los módulos \
del curso, con dificultad mixta, para clasificar al estudiante en nivel \
beginner, intermediate o advanced.

MÓDULOS DEL CURSO:
{modules_list}

REGLAS ESTRICTAS:
1. Genera exactamente {num_questions} preguntas.
2. Cubre TODOS los módulos (al menos 2 preguntas por módulo).
3. Cada pregunta tiene exactamente 4 opciones.
4. Dificultad distribuida: ~35% easy, ~35% medium, ~30% hard.
5. correct_index es 0, 1, 2 o 3.
6. module_id debe coincidir con uno de la lista.
7. difficulty es "easy", "medium" o "hard".
8. Todo en español peruano claro.
9. Las preguntas evalúan: conceptos básicos (easy), aplicación práctica (medium), \
edge cases + optimización (hard).
10. Responde ÚNICAMENTE con JSON con la clave "questions".

FORMATO JSON:
{{
  "questions": [
    {{
      "question_text": "¿Pregunta?",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "module_id": 1,
      "difficulty": "easy"
    }}
  ]
}}"""


def _parse_llm_response(raw: str, valid_module_ids: set[int]) -> list[AssessmentQuestion]:
    """Parse and validate LLM JSON response."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise AssessmentGenerationError(f"LLM devolvió JSON inválido: {e}")

    if isinstance(data, dict):
        if "questions" in data and isinstance(data["questions"], list):
            data = data["questions"]
        else:
            raise AssessmentGenerationError("LLM no incluyó clave 'questions'")

    if not isinstance(data, list) or len(data) == 0:
        raise AssessmentGenerationError("LLM no devolvió lista de preguntas")

    questions: list[AssessmentQuestion] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        q_text = str(item.get("question_text", "")).strip()
        options = item.get("options", [])
        correct_idx = item.get("correct_index", -1)
        module_id = item.get("module_id", 0)
        difficulty = str(item.get("difficulty", "medium")).strip().lower()

        if not q_text:
            continue
        if not isinstance(options, list) or len(options) != 4:
            continue
        if not isinstance(correct_idx, int) or correct_idx < 0 or correct_idx > 3:
            continue
        if not isinstance(module_id, int) or module_id not in valid_module_ids:
            continue
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"

        questions.append(AssessmentQuestion(
            question_text=q_text,
            options=[str(o).strip() for o in options],
            correct_index=correct_idx,
            module_id=module_id,
            difficulty=difficulty,
        ))

    if len(questions) < 5:
        raise AssessmentGenerationError(f"Solo {len(questions)} preguntas válidas generadas")

    return questions


async def _generate_with_llm(modules: list[Module]) -> list[AssessmentQuestion]:
    """Generate assessment questions using Ollama."""
    modules_list = "\n".join(
        f"- module_id={m.id}: {m.title}" for m in modules
    )
    valid_ids = {m.id for m in modules}

    system_prompt = ASSESSMENT_SYSTEM_PROMPT.format(
        modules_list=modules_list,
        num_questions=NUM_ASSESSMENT_QUESTIONS,
    )
    human_prompt = (
        f"Genera {NUM_ASSESSMENT_QUESTIONS} preguntas diagnósticas cubriendo los "
        f"{len(modules)} módulos del curso con dificultad mixta."
    )

    llm = ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.7,
        num_ctx=8192,
        num_predict=4096,
        format="json",
    )

    logger.info(f"Generando {NUM_ASSESSMENT_QUESTIONS} preguntas de evaluación de entrada vía Ollama")
    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ])

    raw = response.content
    logger.debug(f"Respuesta LLM evaluación entrada (200 chars): {raw[:200]}")

    return _parse_llm_response(raw, valid_ids)


async def _fallback_from_bank(db: AsyncSession, modules: list[Module]) -> list[AssessmentQuestion]:
    """Sample questions from teacher-curated bank. Minimum 2 per module when possible."""
    result = await db.execute(
        select(EntryAssessmentBank).where(EntryAssessmentBank.is_active == True)
    )
    bank = result.scalars().all()
    if not bank:
        raise AssessmentGenerationError("Banco de evaluación de entrada vacío")

    # Group by module
    by_module: dict[int, list[EntryAssessmentBank]] = {}
    for q in bank:
        by_module.setdefault(q.module_id, []).append(q)

    selected: list[EntryAssessmentBank] = []
    per_module_target = max(2, NUM_ASSESSMENT_QUESTIONS // max(1, len(modules)))

    for m in modules:
        pool = by_module.get(m.id, [])
        if not pool:
            continue
        random.shuffle(pool)
        selected.extend(pool[:per_module_target])

    # Top-up if under target
    if len(selected) < NUM_ASSESSMENT_QUESTIONS:
        remaining = [q for q in bank if q not in selected]
        random.shuffle(remaining)
        selected.extend(remaining[:NUM_ASSESSMENT_QUESTIONS - len(selected)])

    selected = selected[:NUM_ASSESSMENT_QUESTIONS]
    if len(selected) < 5:
        raise AssessmentGenerationError("Banco tiene muy pocas preguntas activas")

    return [
        AssessmentQuestion(
            question_text=q.question_text,
            options=list(q.options),
            correct_index=q.correct_index,
            module_id=q.module_id,
            difficulty=q.difficulty,
        )
        for q in selected
    ]


async def generate_assessment(
    db: AsyncSession,
) -> tuple[list[AssessmentQuestion], str]:
    """
    Generate entry assessment. Returns (questions, source) where source is "ai" or "bank".
    """
    result = await db.execute(
        select(Module).where(Module.is_active == True).order_by(Module.order_index)
    )
    modules = list(result.scalars().all())
    if not modules:
        raise AssessmentGenerationError("No hay módulos activos en el sistema")

    # Try LLM first
    try:
        questions = await _generate_with_llm(modules)
        logger.info(f"Evaluación entrada generada por IA: {len(questions)} preguntas")
        return questions, "ai"
    except AssessmentGenerationError as e:
        logger.warning(f"Fallo generación IA evaluación entrada, usando banco: {e}")
    except Exception as e:
        logger.error(f"Error inesperado LLM evaluación entrada: {e}")

    # Fallback to teacher bank
    questions = await _fallback_from_bank(db, modules)
    logger.info(f"Evaluación entrada (fallback banco): {len(questions)} preguntas")
    return questions, "bank"
