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
from app.utils.prompt_security import LLM_GUARD_CLAUSE


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
  "description": "<descripción en Markdown: enunciado del problema + sección 'Ejemplo:' con una ENTRADA de muestra y su SALIDA esperada (no el código solución) + sección 'Criterios de evaluación:'>",
  "hints": "<pistas numeradas en Markdown, 2-4 pistas>",
  "solution_code": "<código Kotlin de referencia que resuelva el problema>",
  "difficulty": "{difficulty}",
  "language": "kotlin"
}}

REGLAS:
- La descripción debe tener una sección "Ejemplo:" y una sección "Criterios de evaluación:".
- La sección "Ejemplo:" debe ilustrar el COMPORTAMIENTO esperado con una ENTRADA de muestra y su SALIDA esperada (p. ej. "Entrada: 1985 → Salida: Tienes 38 años"). NO uses bloques de código en el ejemplo, y NUNCA un bloque que solo contenga un comentario.
- PROHIBIDO FILTRAR LA RESPUESTA: ni el ejemplo ni las pistas deben contener código que por sí solo cumpla los criterios (el estudiante solo lo copiaría y pegaría).
- La respuesta correcta va EXCLUSIVAMENTE en "solution_code"; el estudiante nunca la ve.
- El código solución debe ser idiomático y compilable en Kotlin.
- Las pistas son una cadena Markdown con lista numerada; tampoco deben contener la solución completa.
- No incluyas texto fuera del JSON."""


def _strip_code(s: str) -> str:
    """Núcleo comparable de un fragmento de código: sin code fences, comentarios
    ni espacios en blanco, en minúsculas. Permite detectar copy-paste aunque
    cambien el formato o los comentarios."""
    s = re.sub(r"```[a-zA-Z]*", "", s)                  # cercas ```kotlin / ```
    s = re.sub(r"//[^\n]*", "", s)                      # comentarios de línea
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)    # comentarios de bloque
    s = re.sub(r"\s+", "", s)                           # todo el espacio en blanco
    return s.lower()


def _significant_lines(code: str) -> list[str]:
    """Líneas de código con contenido real (asignaciones/llamadas), normalizadas
    sin comentarios ni espacios. Ignora llaves sueltas y líneas muy cortas que
    no aportan información de la solución."""
    out: list[str] = []
    body = re.sub(r"```[a-zA-Z]*", "", code)
    for ln in body.splitlines():
        ln = re.sub(r"//.*$", "", ln)            # comentario de línea
        core = re.sub(r"\s+", "", ln).lower()
        if len(core) >= 5 and core not in ("{", "}", "})", "});", "})}"):
            out.append(core)
    return out


def _leaks_solution(text: str, solution: str) -> bool:
    """True si `text` (enunciado o pistas) revela la solución al punto de poder
    aprobar copiando y pegando. No basta una línea compartida: marca fuga cuando
    aparece la MAYORÍA (≥50%) de las líneas significativas de la solución. Una
    solución de una sola línea sólo se marca si aparece completa. Un reto de
    lógica real no se ve afectado: su código no aparece literal en la prosa."""
    sol_lines = _significant_lines(solution)
    hay = _strip_code(text)
    if len(sol_lines) < 2:
        return bool(sol_lines) and len(sol_lines[0]) >= 20 and sol_lines[0] in hay
    leaked = sum(1 for ln in sol_lines if ln in hay)
    return leaked / len(sol_lines) >= 0.5


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

    # Anti copy-paste: si el enunciado o las pistas traen la solución completa,
    # el reto es "regalado". Rechazar → el caller cae al banco curado del docente.
    if _leaks_solution(description, solution) or _leaks_solution(hints, solution):
        raise ChallengeGenerationError(
            "El enunciado/pistas generados filtran la solución (se aprobaría copiando)"
        )

    return GeneratedChallenge(
        title=title,
        description=description,
        hints=hints or "_Sin pistas disponibles._",
        solution_code=solution,
        difficulty=difficulty,
        language="kotlin",
    )


MAX_GEN_ATTEMPTS = 3


async def generate_challenge(
    topic_content: str,
    difficulty: str = "medium",
    target_level: str = "intermediate",
) -> GeneratedChallenge:
    """Generate a coding challenge via LLM. Not persisted — admin reviews first.

    Reintenta hasta MAX_GEN_ATTEMPTS si la respuesta trae JSON inválido o filtra la
    solución (temperatura 0.7 da variedad entre intentos). Así una sola petición
    suele lograr un reto IA en vez de caer al banco al primer tropiezo. Un fallo de
    conexión sí corta de inmediato (no tiene sentido reintentar contra un Ollama caído).
    """
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
        num_predict=2048,
        format="json",
        timeout=settings.OLLAMA_TIMEOUT,
    )

    logger.info(f"Generando desafío IA: nivel={target_level}, dificultad={difficulty}")
    last_err: ChallengeGenerationError | None = None
    for attempt in range(1, MAX_GEN_ATTEMPTS + 1):
        try:
            response = await llm.ainvoke([
                SystemMessage(content=LLM_GUARD_CLAUSE + "\n\nEres un diseñador de desafíos de programación. Responde solo JSON."),
                HumanMessage(content=prompt),
            ])
        except Exception as e:
            # Fallo de conexión/servicio: reintentar no ayuda → al fallback.
            logger.error(f"Error LLM generando desafío: {e}")
            raise ChallengeGenerationError(f"No se pudo conectar con el servicio IA: {e}")
        try:
            return _parse_response(response.content, difficulty)
        except ChallengeGenerationError as e:
            # JSON inválido o fuga de solución: reintentar con una nueva generación.
            last_err = e
            logger.warning(f"Generación descartada (intento {attempt}/{MAX_GEN_ATTEMPTS}): {e}")

    raise last_err or ChallengeGenerationError("No se pudo generar un desafío válido")
