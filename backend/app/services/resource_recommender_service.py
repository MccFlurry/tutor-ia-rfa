"""resource_recommender_service.py — Capa de IA que reordena y justifica los
recursos curados por estudiante (nivel + debilidad). El LLM SOLO permuta IDs
reales del banco; nunca emite URLs ni títulos. Todo fallo → orden curado.
"""
import json
import re
from dataclasses import dataclass

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.schemas.learning_resource import LearningResourceResponse, RecommendedResource
from app.utils.logger import logger

REASON_MAX_CHARS = 120


def _cap_reason(reason: str | None) -> str | None:
    if not reason or not str(reason).strip():
        return None
    return str(reason).strip()[:REASON_MAX_CHARS]


def merge_ranking(
    candidates: list[LearningResourceResponse],
    llm_ranking: list[dict],
) -> list[RecommendedResource]:
    """Valida la salida del LLM contra los candidatos reales. Devuelve SIEMPRE
    una permutación del conjunto candidato: descarta IDs inventados, deduplica,
    recorta razones y anexa los candidatos que el LLM omitió en su orden curado."""
    by_id = {c.id: c for c in candidates}
    ordered: list[RecommendedResource] = []
    seen: set[int] = set()
    for item in llm_ranking:
        rid = item.get("id")
        if not isinstance(rid, int) or rid in seen or rid not in by_id:
            continue
        seen.add(rid)
        ordered.append(RecommendedResource(
            **by_id[rid].model_dump(), reason=_cap_reason(item.get("reason")),
        ))
    for c in candidates:
        if c.id not in seen:
            ordered.append(RecommendedResource(**c.model_dump(), reason=None))
    return ordered


def _parse_ranking(raw: str) -> list[dict]:
    """Parsea la respuesta JSON del LLM a [{'id': int, 'reason': str|None}].
    Acepta wrapper {'ranking':[...]} o array desnudo; tolera code fences."""
    cleaned = (raw or "").strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r'\[.*?\]', cleaned, re.DOTALL)
        if not m:
            return []
        try:
            data = json.loads(m.group())
        except json.JSONDecodeError:
            return []
    if isinstance(data, dict):
        data = data.get("ranking", [])
    if not isinstance(data, list):
        return []
    out: list[dict] = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("id"), int):
            out.append({"id": item["id"], "reason": item.get("reason")})
    return out


@dataclass
class StudentSignal:
    level: str
    weakness_label: str


RECOMMEND_SYSTEM_PROMPT = """Eres un tutor del curso de Aplicaciones Móviles del IESTP \
República Federal de Alemania (RFA), Chiclayo, Perú.

Recibes una lista de RECURSOS DE APRENDIZAJE ya curados (cada uno con su id) y el perfil \
del estudiante. Tu tarea: ORDENAR los recursos del más al menos útil para ESTE estudiante \
y dar una razón breve por cada uno.

REGLAS ABSOLUTAS:
1. SOLO puedes usar los id que aparecen en la lista. NUNCA inventes recursos, títulos ni URLs.
2. Devuelve TODOS los id recibidos, sin repetir, ordenados por utilidad para el estudiante.
3. La razón es 1 frase corta (máx ~15 palabras), en español peruano, motivadora y concreta.
4. Prioriza lo que ayude con la debilidad indicada y se ajuste al nivel del estudiante.
5. Responde ÚNICAMENTE con un objeto JSON con la clave "ranking".

FORMATO (JSON objeto):
{"ranking": [{"id": 3, "reason": "Empieza aquí: explica el emulador paso a paso."}]}"""


def _build_human_prompt(candidates: list[LearningResourceResponse], signal: StudentSignal) -> str:
    items = [
        {"id": c.id, "kind": c.kind, "title": c.title,
         "description": (c.description or "")[:200]}
        for c in candidates
    ]
    return (
        f"PERFIL DEL ESTUDIANTE:\n- Nivel: {signal.level}\n- Estado: {signal.weakness_label}\n\n"
        f"RECURSOS DISPONIBLES (JSON):\n{json.dumps(items, ensure_ascii=False)}\n\n"
        "Ordena estos recursos para este estudiante y justifica cada uno."
    )


async def _rank_with_llm(
    candidates: list[LearningResourceResponse], signal: StudentSignal
) -> list[dict]:
    """Invoca Ollama para reordenar. Devuelve [] ante cualquier fallo (→ fallback)."""
    try:
        llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.3,
            num_ctx=4096,
            num_predict=600,
            format="json",
            timeout=settings.OLLAMA_TIMEOUT,
        )
        response = await llm.ainvoke([
            SystemMessage(content=RECOMMEND_SYSTEM_PROMPT),
            HumanMessage(content=_build_human_prompt(candidates, signal)),
        ])
        return _parse_ranking(response.content)
    except Exception as e:
        logger.warning(f"[recommender] LLM falló, fallback a orden curado: {e}")
        return []
