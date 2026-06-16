"""resource_recommender_service.py — Capa de IA que reordena y justifica los
recursos curados por estudiante (nivel + debilidad). El LLM SOLO permuta IDs
reales del banco; nunca emite URLs ni títulos. Todo fallo → orden curado.
"""
import json
import re

from app.schemas.learning_resource import LearningResourceResponse, RecommendedResource
from app.utils.logger import logger

REASON_MAX_CHARS = 120


def _cap_reason(reason) -> str | None:
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
        m = re.search(r'\[.*\]', cleaned, re.DOTALL)
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
