"""rerank_service.py — Re-ranking de candidatos con cross-encoder multilingüe.
Lazy-load + config-gated. Fallback a orden original si el modelo no carga."""
from __future__ import annotations

from app.config import settings
from app.utils.logger import logger

_model = None
_load_failed = False


def _get_model():
    global _model, _load_failed
    if _model is not None or _load_failed:
        return _model
    try:
        from sentence_transformers import CrossEncoder
        _model = CrossEncoder(settings.RERANK_MODEL)
        logger.info(f"Cross-encoder cargado: {settings.RERANK_MODEL}")
    except Exception as e:
        _load_failed = True
        logger.warning(f"No se pudo cargar cross-encoder ({e}); rerank desactivado")
    return _model


def rerank(query: str, candidates: list[dict], top_k: int, model=None) -> list[dict]:
    """Reordena `candidates` (cada uno dict con clave 'content') por relevancia
    query↔content y devuelve los top_k. Si no hay modelo, devuelve el orden
    original truncado a top_k."""
    if not candidates:
        return []
    m = model if model is not None else _get_model()
    if m is None:
        return candidates[:top_k]
    pairs = [(query, c["content"]) for c in candidates]
    scores = m.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: float(x[1]), reverse=True)
    return [{**cand, "rerank_score": float(score)} for cand, score in ranked[:top_k]]
