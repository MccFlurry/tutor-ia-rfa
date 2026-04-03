"""
code_eval_service.py — Evaluación de código con LLM.
El LLM actúa como revisor de código: evalúa corrección, estilo,
buenas prácticas y sugiere mejoras.
"""

import json
import re

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.utils.logger import logger


CODE_EVAL_PROMPT = """Eres un evaluador experto de código para un curso de Aplicaciones Móviles \
del IESTP República Federal de Alemania (RFA) en Chiclayo, Perú. \
Tu rol es revisar el código que envían los estudiantes y darles retroalimentación constructiva.

DESAFÍO:
Título: {title}
Descripción: {description}
Lenguaje: {language}

{solution_section}

CÓDIGO DEL ESTUDIANTE:
```{language}
{student_code}
```

Evalúa el código del estudiante y responde con un objeto JSON con esta estructura exacta:
{{
  "score": <número de 0 a 100>,
  "feedback": "<evaluación detallada en Markdown, 3-5 párrafos en español>",
  "strengths": ["<punto fuerte 1>", "<punto fuerte 2>"],
  "improvements": ["<mejora sugerida 1>", "<mejora sugerida 2>"]
}}

CRITERIOS DE EVALUACIÓN:
1. **Corrección** (40%): ¿El código resuelve el problema correctamente?
2. **Buenas prácticas** (25%): ¿Sigue convenciones de {language}? Nombres descriptivos, código limpio.
3. **Eficiencia** (20%): ¿Es una solución eficiente? ¿Hay redundancias?
4. **Legibilidad** (15%): ¿Es fácil de entender? ¿Está bien estructurado?

REGLAS:
- Responde SOLO con el JSON, sin texto adicional.
- El feedback debe estar en español peruano claro y académico.
- Sé motivador pero honesto. Señala errores con amabilidad.
- Si el código está vacío o no tiene sentido, puntúa 0 y explica por qué.
- Incluye ejemplos de cómo mejorar cuando sea posible (dentro de bloques ```{language}).
- Los strengths e improvements deben ser listas de 2-4 elementos cada una."""


async def evaluate_code(
    title: str,
    description: str,
    student_code: str,
    language: str = "kotlin",
    solution_code: str | None = None,
) -> dict:
    """
    Evaluate student code using the LLM.
    Returns: {"score": float, "feedback": str, "strengths": list, "improvements": list}
    """
    solution_section = ""
    if solution_code:
        solution_section = f"SOLUCIÓN DE REFERENCIA (usa como guía, no como única respuesta válida):\n```{language}\n{solution_code}\n```"

    prompt_text = CODE_EVAL_PROMPT.format(
        title=title,
        description=description,
        language=language,
        student_code=student_code[:5000],  # Limit code length
        solution_section=solution_section,
    )

    llm = ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.3,
        num_ctx=8192,
        num_predict=2048,
        format="json",
    )

    logger.info(f"Evaluando código para: {title}")
    response = await llm.ainvoke([
        SystemMessage(content="Eres un evaluador de código experto. Responde solo en JSON."),
        HumanMessage(content=prompt_text),
    ])

    raw = response.content.strip()
    return _parse_evaluation(raw)


def _parse_evaluation(raw: str) -> dict:
    """Parse and validate the LLM evaluation response."""
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse code evaluation JSON: {raw[:200]}")
        return {
            "score": 0,
            "feedback": "No se pudo evaluar el código en este momento. Intenta de nuevo.",
            "strengths": [],
            "improvements": ["Intenta enviar tu código nuevamente"],
        }

    # Validate and clamp score
    score = data.get("score", 0)
    if not isinstance(score, (int, float)):
        score = 0
    score = max(0, min(100, float(score)))

    feedback = data.get("feedback", "Sin retroalimentación disponible.")
    if not isinstance(feedback, str):
        feedback = str(feedback)

    strengths = data.get("strengths", [])
    if not isinstance(strengths, list):
        strengths = []
    strengths = [str(s) for s in strengths[:5]]

    improvements = data.get("improvements", [])
    if not isinstance(improvements, list):
        improvements = []
    improvements = [str(s) for s in improvements[:5]]

    return {
        "score": score,
        "feedback": feedback,
        "strengths": strengths,
        "improvements": improvements,
    }
