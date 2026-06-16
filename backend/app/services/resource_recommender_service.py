"""resource_recommender_service.py — Capa de IA que reordena y justifica los
recursos curados por estudiante (nivel + debilidad). El LLM SOLO permuta IDs
reales del banco; nunca emite URLs ni títulos. Todo fallo → orden curado.
"""
import json
import re
from dataclasses import dataclass

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from sqlalchemy import func, or_, select

from app.config import settings
from app.models.learning_resource import LearningResource
from app.models.quiz import QuizAttempt
from app.models.topic import Topic
from app.models.user_level import UserLevel
from app.schemas.learning_resource import LearningResourceResponse, RecommendedResource, RecommendationResponse
from app.services.companion_service import (
    WEAK_SCORE, PRACTICE_SCORE, WEAK_FAILED_ATTEMPTS,
    _gather_topic_stats, build_diagnostic,
)
from app.utils.cache import invalidate_prefix
from app.utils.logger import logger
from app.utils.prompt_security import LLM_GUARD_CLAUSE

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
        {"id": c.id, "kind": c.kind, "title": c.title[:80],
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
            num_predict=900,
            format="json",
            timeout=settings.OLLAMA_TIMEOUT,
        )
        response = await llm.ainvoke([
            SystemMessage(content=LLM_GUARD_CLAUSE + "\n\n" + RECOMMEND_SYSTEM_PROMPT),
            HumanMessage(content=_build_human_prompt(candidates, signal)),
        ])
        return _parse_ranking(response.content)
    except Exception as e:
        logger.warning(f"[recommender] LLM falló, fallback a orden curado: {e}")
        return []


MAX_CANDIDATES = 6


def weakness_label_for_score(best_score: float | None, failed_attempts: int) -> str:
    """Etiqueta de debilidad por bandas (0-100), consistente con el companion. Pura."""
    if best_score is None:
        return "aún no evaluado en este tema"
    if best_score < WEAK_SCORE or (
        failed_attempts >= WEAK_FAILED_ATTEMPTS and best_score < PRACTICE_SCORE
    ):
        return "tiene dificultades en este tema"
    if best_score < PRACTICE_SCORE:
        return "necesita afianzar este tema"
    return "domina este tema"


async def select_candidates(db, module_id: int | None, topic_id: int | None):
    """Recursos curados candidatos. Por topic_id incluye los del tema Y los del
    módulo del tema (el seed asigna solo module_id), si no la tarjeta queda vacía."""
    if topic_id is None and module_id is None:
        logger.warning("[recommender] select_candidates sin module_id ni topic_id")
        return []
    q = select(LearningResource).where(LearningResource.is_active == True)  # noqa: E712
    if topic_id is not None:
        mod_id = (
            await db.execute(select(Topic.module_id).where(Topic.id == topic_id))
        ).scalar_one_or_none()
        if mod_id is None:
            # Tema inexistente (p. ej. borrado): evita el filtro silencioso
            # ``module_id IS NULL``; quedan solo los recursos del propio tema.
            logger.warning(f"[recommender] tema {topic_id} sin módulo; solo recursos del tema")
            q = q.where(LearningResource.topic_id == topic_id)
        else:
            q = q.where(or_(
                LearningResource.topic_id == topic_id,
                LearningResource.module_id == mod_id,
            ))
    else:
        q = q.where(LearningResource.module_id == module_id)
    q = q.order_by(LearningResource.order_index, LearningResource.id).limit(MAX_CANDIDATES)
    rows = (await db.execute(q)).scalars().all()
    return [LearningResourceResponse.model_validate(r) for r in rows]


async def _module_weakness_label(user, db, module_id: int) -> str:
    stats = await _gather_topic_stats(user, module_id, db)
    diagnostic = build_diagnostic(stats, module_id)
    if diagnostic.weak:
        return f"tiene dificultades en «{diagnostic.weak[0].title}»"
    if diagnostic.practice:
        return f"necesita afianzar «{diagnostic.practice[0].title}»"
    return "avanza bien en el módulo actual"


async def _topic_weakness_label(user, db, topic_id: int) -> str:
    row = (
        await db.execute(
            select(
                func.max(QuizAttempt.score).label("best"),
                func.count(QuizAttempt.id)
                .filter(QuizAttempt.is_passed == False).label("failed"),  # noqa: E712
            ).where(QuizAttempt.user_id == user.id, QuizAttempt.topic_id == topic_id)
        )
    ).first()
    # QuizAttempt.score se persiste como fracción 0-1; las bandas son 0-100.
    best = float(row.best) * 100 if row and row.best is not None else None
    failed = int(row.failed) if row and row.failed is not None else 0
    return weakness_label_for_score(best, failed)


async def build_student_signal(user, db, module_id: int | None, topic_id: int | None) -> StudentSignal:
    level = (
        await db.execute(select(UserLevel.level).where(UserLevel.user_id == user.id))
    ).scalar_one_or_none() or "beginner"
    if topic_id is not None:
        weakness = await _topic_weakness_label(user, db, topic_id)
    else:
        weakness = await _module_weakness_label(user, db, module_id)
    return StudentSignal(level=level, weakness_label=weakness)


async def gather_recommendations(
    user, db, module_id: int | None = None, topic_id: int | None = None
) -> RecommendationResponse:
    """Orquesta candidatos → señal → LLM → merge. Sin caché (la maneja el router)."""
    candidates = await select_candidates(db, module_id, topic_id)
    signal = await build_student_signal(user, db, module_id, topic_id)
    if len(candidates) < 2:
        return RecommendationResponse(
            ai_ranked=False, level=signal.level,
            recommendations=[
                RecommendedResource(**c.model_dump(), reason=None) for c in candidates
            ],
        )
    ranking = await _rank_with_llm(candidates, signal)
    return RecommendationResponse(
        ai_ranked=bool(ranking),
        level=signal.level,
        recommendations=merge_ranking(candidates, ranking),
    )


RESOURCE_REC_PREFIX = "resource_rec:"


def resource_rec_cache_key(user_id, scope: str) -> str:
    return f"{RESOURCE_REC_PREFIX}{user_id}:{scope}"


async def invalidate_resource_recs(redis_client, user_id) -> None:
    """Punto único de invalidación: borra todas las keys del estudiante. Lo llaman
    los mismos eventos que invalidan el companion (cambian nivel/debilidad)."""
    await invalidate_prefix(redis_client, f"{RESOURCE_REC_PREFIX}{user_id}:")
