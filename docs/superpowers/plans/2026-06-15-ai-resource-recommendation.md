# AI Resource Recommendation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an AI layer that re-ranks and explains the existing curated learning resources per student (level + weakness), without ever inventing URLs, surfaced on Dashboard and TopicPage.

**Architecture:** New `resource_recommender_service.py` (isolated from the deterministic companion). A `GET /resources/recommended` endpoint resolves curated candidates from the DB, builds a student signal (level + weakness, reusing companion logic), and asks the LLM to permute *real resource IDs* + write a 1-line reason. A pure `merge_ranking` validates the LLM output (drops invented IDs, appends omitted candidates) so the result is always a permutation of real resources. Any LLM/parse failure or <2 candidates falls back to the curated order (`ai_ranked=false`). Redis caches per scope; the same student mutations that invalidate the companion also invalidate these.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Pydantic v2, langchain-ollama (`ChatOllama`, `format="json"`), Redis, React 18 + TanStack Query, Vitest + RTL.

**Conventions:** Spec at `docs/superpowers/specs/2026-06-15-ai-resource-recommendation-design.md`. Out of the ISO 25010 matrix (33 RF frozen). All commits use Conventional Commits and append the project's `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` trailer. No DB migration — `learning_resources` already exists. Backend tests run from `backend/` with `python -m pytest`; frontend from `frontend/` with `npx vitest run`.

---

### Task 1: Pydantic schemas for recommendations

**Files:**
- Modify: `backend/app/schemas/learning_resource.py`

- [ ] **Step 1: Add the response schemas**

Append to `backend/app/schemas/learning_resource.py`:

```python
class RecommendedResource(LearningResourceResponse):
    """A curated resource plus the LLM's 1-line rationale (None in fallback)."""
    reason: str | None = None


class RecommendationResponse(BaseModel):
    ai_ranked: bool
    level: str
    recommendations: list[RecommendedResource]
```

- [ ] **Step 2: Verify it imports and constructs**

Run (from `backend/`):
```bash
python -c "from app.schemas.learning_resource import RecommendedResource, RecommendationResponse; print(RecommendationResponse(ai_ranked=False, level='beginner', recommendations=[]).model_dump())"
```
Expected: prints `{'ai_ranked': False, 'level': 'beginner', 'recommendations': []}`

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/learning_resource.py
git commit -m "feat(resources): add RecommendedResource + RecommendationResponse schemas"
```

---

### Task 2: Pure core — merge_ranking + parsing

**Files:**
- Create: `backend/app/services/resource_recommender_service.py`
- Create: `backend/tests/unit/test_resource_recommender_service.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/test_resource_recommender_service.py`:

```python
"""Unit tests del recomendador de recursos (núcleo puro + límites LLM)."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.schemas.learning_resource import LearningResourceResponse
from app.services.resource_recommender_service import (
    merge_ranking,
    _parse_ranking,
    REASON_MAX_CHARS,
)


def _res(id, order_index=0, **over):
    base = dict(
        id=id, module_id=1, topic_id=None, kind="video",
        title=f"R{id}", url=f"http://x/{id}", author=None,
        description=None, order_index=order_index, is_active=True,
    )
    base.update(over)
    return LearningResourceResponse(**base)


# --- merge_ranking: siempre una permutación de recursos reales ---

def test_merge_orders_by_llm_and_attaches_reason():
    cands = [_res(1, 0), _res(2, 1), _res(3, 2)]
    out = merge_ranking(cands, [{"id": 3, "reason": "primero"}, {"id": 1, "reason": "luego"}])
    assert [r.id for r in out] == [3, 1, 2]  # 2 omitido → anexado en orden curado
    assert out[0].reason == "primero"
    assert out[2].reason is None


def test_merge_drops_invented_ids():
    cands = [_res(1), _res(2)]
    out = merge_ranking(cands, [{"id": 99, "reason": "x"}, {"id": 2, "reason": "y"}])
    assert [r.id for r in out] == [2, 1]


def test_merge_dedupes_ids():
    cands = [_res(1), _res(2)]
    out = merge_ranking(cands, [{"id": 1}, {"id": 1}, {"id": 2}])
    assert [r.id for r in out] == [1, 2]


def test_merge_truncates_reason():
    out = merge_ranking([_res(1)], [{"id": 1, "reason": "a" * 200}])
    assert len(out[0].reason) == REASON_MAX_CHARS


def test_merge_empty_ranking_keeps_curated_order():
    out = merge_ranking([_res(2, 0), _res(1, 1)], [])
    assert [r.id for r in out] == [2, 1]
    assert all(r.reason is None for r in out)


# --- _parse_ranking: robusto a wrapper, array, fences, basura ---

def test_parse_wrapper_object():
    assert _parse_ranking('{"ranking":[{"id":1,"reason":"x"}]}') == [{"id": 1, "reason": "x"}]


def test_parse_bare_array():
    assert _parse_ranking('[{"id":2,"reason":"y"}]') == [{"id": 2, "reason": "y"}]


def test_parse_code_fences():
    assert _parse_ranking('```json\n{"ranking":[{"id":1}]}\n```') == [{"id": 1, "reason": None}]


def test_parse_invalid_returns_empty():
    assert _parse_ranking("no json aquí") == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run (from `backend/`):
```bash
python -m pytest tests/unit/test_resource_recommender_service.py -v
```
Expected: FAIL — `ModuleNotFoundError: app.services.resource_recommender_service`

- [ ] **Step 3: Write the pure core**

Create `backend/app/services/resource_recommender_service.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run (from `backend/`):
```bash
python -m pytest tests/unit/test_resource_recommender_service.py -v
```
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/resource_recommender_service.py backend/tests/unit/test_resource_recommender_service.py
git commit -m "feat(resources): pure merge_ranking + LLM ranking parser with tests"
```

---

### Task 3: LLM boundary — prompt + _rank_with_llm

**Files:**
- Modify: `backend/app/services/resource_recommender_service.py`
- Modify: `backend/tests/unit/test_resource_recommender_service.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/unit/test_resource_recommender_service.py`:

```python
from app.services.resource_recommender_service import _rank_with_llm, StudentSignal


@pytest.mark.asyncio
async def test_rank_with_llm_returns_empty_on_failure(monkeypatch):
    class Boom:
        def __init__(self, *a, **k): ...
        async def ainvoke(self, *a, **k):
            raise RuntimeError("ollama down")
    monkeypatch.setattr(
        "app.services.resource_recommender_service.ChatOllama", Boom
    )
    out = await _rank_with_llm([_res(1), _res(2)], StudentSignal("beginner", "x"))
    assert out == []


@pytest.mark.asyncio
async def test_rank_with_llm_parses_success(monkeypatch):
    class OK:
        def __init__(self, *a, **k): ...
        async def ainvoke(self, *a, **k):
            return MagicMock(content='{"ranking":[{"id":2,"reason":"hazlo"}]}')
    monkeypatch.setattr(
        "app.services.resource_recommender_service.ChatOllama", OK
    )
    out = await _rank_with_llm([_res(1), _res(2)], StudentSignal("beginner", "x"))
    assert out == [{"id": 2, "reason": "hazlo"}]
```

- [ ] **Step 2: Run tests to verify they fail**

Run (from `backend/`):
```bash
python -m pytest tests/unit/test_resource_recommender_service.py -k rank_with_llm -v
```
Expected: FAIL — `ImportError: cannot import name '_rank_with_llm'`

- [ ] **Step 3: Add the LLM boundary**

Add to the TOP imports of `backend/app/services/resource_recommender_service.py` (after `import re`):

```python
from dataclasses import dataclass

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
```

Append to `backend/app/services/resource_recommender_service.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run (from `backend/`):
```bash
python -m pytest tests/unit/test_resource_recommender_service.py -v
```
Expected: PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/resource_recommender_service.py backend/tests/unit/test_resource_recommender_service.py
git commit -m "feat(resources): LLM ranking boundary with curated-order fallback"
```

---

### Task 4: DB layer — candidates, signal, gather

**Files:**
- Modify: `backend/app/services/resource_recommender_service.py`
- Modify: `backend/tests/unit/test_resource_recommender_service.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/unit/test_resource_recommender_service.py`:

```python
from types import SimpleNamespace
import app.services.resource_recommender_service as mod
from app.services.resource_recommender_service import (
    weakness_label_for_score, select_candidates, gather_recommendations,
)


# --- weakness_label_for_score: bandas puras (reusa umbrales del companion) ---

def test_weakness_label_bands():
    assert "dificultades" in weakness_label_for_score(40, 0)
    assert "afianzar" in weakness_label_for_score(70, 0)
    assert "domina" in weakness_label_for_score(90, 0)
    assert "no evaluado" in weakness_label_for_score(None, 0)


def test_weakness_label_failed_attempts_is_weak():
    # ≥2 intentos fallidos sin dominar → dificultades, aunque score esté en banda media
    assert "dificultades" in weakness_label_for_score(70, 2)


# --- select_candidates: por topic_id une los recursos del módulo del tema ---

@pytest.mark.asyncio
async def test_select_candidates_topic_unions_module():
    db = MagicMock(); db.execute = AsyncMock()
    r1 = MagicMock(); r1.scalar_one_or_none = MagicMock(return_value=1)  # Topic.module_id
    orm = SimpleNamespace(
        id=5, module_id=1, topic_id=None, kind="doc", title="T",
        url="http://x", author=None, description=None, order_index=0, is_active=True,
    )
    r2 = MagicMock()
    r2.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[orm])))
    db.execute.side_effect = [r1, r2]
    out = await select_candidates(db, module_id=None, topic_id=9)
    assert [r.id for r in out] == [5]


# --- gather_recommendations: flag ai_ranked + corto-circuito <2 candidatos ---

@pytest.mark.asyncio
async def test_gather_short_circuits_when_few_candidates(monkeypatch):
    monkeypatch.setattr(mod, "select_candidates", AsyncMock(return_value=[_res(1)]))
    monkeypatch.setattr(mod, "build_student_signal",
                        AsyncMock(return_value=StudentSignal("beginner", "x")))
    rank = AsyncMock()
    monkeypatch.setattr(mod, "_rank_with_llm", rank)
    resp = await gather_recommendations(SimpleNamespace(id="u"), MagicMock(),
                                        module_id=1, topic_id=None)
    assert resp.ai_ranked is False
    rank.assert_not_called()


@pytest.mark.asyncio
async def test_gather_ai_ranked_true_when_llm_returns(monkeypatch):
    monkeypatch.setattr(mod, "select_candidates",
                        AsyncMock(return_value=[_res(1), _res(2)]))
    monkeypatch.setattr(mod, "build_student_signal",
                        AsyncMock(return_value=StudentSignal("beginner", "x")))
    monkeypatch.setattr(mod, "_rank_with_llm",
                        AsyncMock(return_value=[{"id": 2, "reason": "r"}]))
    resp = await gather_recommendations(SimpleNamespace(id="u"), MagicMock(),
                                        module_id=1, topic_id=None)
    assert resp.ai_ranked is True
    assert resp.recommendations[0].id == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run (from `backend/`):
```bash
python -m pytest tests/unit/test_resource_recommender_service.py -k "weakness or select_candidates or gather" -v
```
Expected: FAIL — `ImportError: cannot import name 'weakness_label_for_score'`

- [ ] **Step 3: Implement the DB layer**

Add to the imports of `backend/app/services/resource_recommender_service.py`:

```python
from sqlalchemy import func, or_, select

from app.models.learning_resource import LearningResource
from app.models.quiz import QuizAttempt
from app.models.topic import Topic
from app.models.user_level import UserLevel
from app.schemas.learning_resource import RecommendationResponse
from app.services.companion_service import (
    WEAK_SCORE, PRACTICE_SCORE, WEAK_FAILED_ATTEMPTS,
    _gather_topic_stats, build_diagnostic,
)
```

Append to `backend/app/services/resource_recommender_service.py`:

```python
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
    q = select(LearningResource).where(LearningResource.is_active == True)  # noqa: E712
    if topic_id is not None:
        mod_id = (
            await db.execute(select(Topic.module_id).where(Topic.id == topic_id))
        ).scalar_one_or_none()
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run (from `backend/`):
```bash
python -m pytest tests/unit/test_resource_recommender_service.py -v
```
Expected: PASS (17 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/resource_recommender_service.py backend/tests/unit/test_resource_recommender_service.py
git commit -m "feat(resources): DB candidate selection, student signal, gather orchestration"
```

---

### Task 5: Cache prefix invalidation

**Files:**
- Modify: `backend/app/utils/cache.py`
- Modify: `backend/app/services/resource_recommender_service.py`
- Modify: `backend/tests/unit/test_resource_recommender_service.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/test_resource_recommender_service.py`:

```python
from app.services.resource_recommender_service import invalidate_resource_recs


class _FakeRedis:
    def __init__(self, keys):
        self.store = set(keys)
    async def scan_iter(self, match=None):
        import fnmatch
        for k in list(self.store):
            if match is None or fnmatch.fnmatch(k, match):
                yield k
    async def delete(self, k):
        self.store.discard(k)


@pytest.mark.asyncio
async def test_invalidate_resource_recs_only_touches_user_prefix():
    redis = _FakeRedis({
        "resource_rec:u1:m1", "resource_rec:u1:t9", "resource_rec:u2:m1", "other:key",
    })
    await invalidate_resource_recs(redis, "u1")
    assert redis.store == {"resource_rec:u2:m1", "other:key"}
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `backend/`):
```bash
python -m pytest tests/unit/test_resource_recommender_service.py -k invalidate -v
```
Expected: FAIL — `ImportError: cannot import name 'invalidate_resource_recs'`

- [ ] **Step 3: Add prefix invalidation helper**

Append to `backend/app/utils/cache.py`:

```python
async def invalidate_prefix(redis_client, prefix: str) -> None:
    """Delete every key starting with `prefix` (SCAN-based). Errors swallowed
    (degraded mode): a flaky cache must never break the mutation that triggers it."""
    try:
        async for key in redis_client.scan_iter(match=f"{prefix}*"):
            await redis_client.delete(key)
    except Exception as e:
        logger.warning(f"[cache] Redis invalidate_prefix falló para {prefix}: {e}")
```

Add to the imports of `backend/app/services/resource_recommender_service.py`:

```python
from app.utils.cache import invalidate_prefix
```

Append to `backend/app/services/resource_recommender_service.py`:

```python
RESOURCE_REC_PREFIX = "resource_rec:"


def resource_rec_cache_key(user_id, scope: str) -> str:
    return f"{RESOURCE_REC_PREFIX}{user_id}:{scope}"


async def invalidate_resource_recs(redis_client, user_id) -> None:
    """Punto único de invalidación: borra todas las keys del estudiante. Lo llaman
    los mismos eventos que invalidan el companion (cambian nivel/debilidad)."""
    await invalidate_prefix(redis_client, f"{RESOURCE_REC_PREFIX}{user_id}:")
```

- [ ] **Step 4: Run test to verify it passes**

Run (from `backend/`):
```bash
python -m pytest tests/unit/test_resource_recommender_service.py -k invalidate -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/cache.py backend/app/services/resource_recommender_service.py backend/tests/unit/test_resource_recommender_service.py
git commit -m "feat(cache): prefix invalidation + per-student resource-rec invalidation"
```

---

### Task 6: Endpoint `GET /resources/recommended`

**Files:**
- Modify: `backend/app/routers/resources.py`
- Modify: `backend/tests/integration/test_router_resources.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/integration/test_router_resources.py` (ensure the file has `import pytest` and `from unittest.mock import AsyncMock, patch` near the top — add them if missing):

```python
from app.schemas.learning_resource import RecommendationResponse, RecommendedResource


def _rec(reason):
    return RecommendedResource(
        id=1, module_id=1, topic_id=None, kind="video", title="R1",
        url="http://x/1", author=None, description=None, order_index=0,
        is_active=True, reason=reason,
    )


@pytest.mark.asyncio
async def test_recommended_ai_ranked(client):
    payload = RecommendationResponse(
        ai_ranked=True, level="beginner", recommendations=[_rec("empieza aquí")],
    )
    with patch("app.routers.resources.gather_recommendations",
               new=AsyncMock(return_value=payload)):
        r = await client.get("/api/v1/resources/recommended?module_id=1")
    assert r.status_code == 200
    body = r.json()
    assert body["ai_ranked"] is True
    assert body["recommendations"][0]["reason"] == "empieza aquí"


@pytest.mark.asyncio
async def test_recommended_fallback(client):
    payload = RecommendationResponse(
        ai_ranked=False, level="beginner", recommendations=[_rec(None)],
    )
    with patch("app.routers.resources.gather_recommendations",
               new=AsyncMock(return_value=payload)):
        r = await client.get("/api/v1/resources/recommended?topic_id=9")
    assert r.status_code == 200
    assert r.json()["ai_ranked"] is False


@pytest.mark.asyncio
async def test_recommended_requires_exactly_one_param(client):
    none = await client.get("/api/v1/resources/recommended")
    both = await client.get("/api/v1/resources/recommended?module_id=1&topic_id=2")
    assert none.status_code == 422
    assert both.status_code == 422


@pytest.mark.asyncio
async def test_recommended_served_from_cache(client, mock_redis_pipe):
    import json as _json
    mock_redis_pipe.get = AsyncMock(
        return_value=_json.dumps({"ai_ranked": True, "level": "beginner", "recommendations": []})
    )
    with patch("app.routers.resources.gather_recommendations", new=AsyncMock()) as svc:
        r = await client.get("/api/v1/resources/recommended?module_id=1")
    svc.assert_not_called()
    assert r.json()["ai_ranked"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run (from `backend/`):
```bash
python -m pytest tests/integration/test_router_resources.py -k recommended -v
```
Expected: FAIL — 404 (route not defined) / import error

- [ ] **Step 3: Add the endpoint**

Replace the import block at the top of `backend/app/routers/resources.py` with:

```python
"""routers/resources.py — Recursos de aprendizaje (lectura para estudiantes)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.models.user import User
from app.models.learning_resource import LearningResource
from app.schemas.learning_resource import LearningResourceResponse, RecommendationResponse
from app.services.resource_recommender_service import (
    gather_recommendations, resource_rec_cache_key,
)
from app.utils.cache import cached_json

router = APIRouter(prefix="/resources", tags=["resources"])

RECOMMEND_CACHE_TTL = 1800
```

Append to `backend/app/routers/resources.py`:

```python
async def _recommendations_payload(user, db, module_id, topic_id) -> dict:
    resp = await gather_recommendations(user, db, module_id, topic_id)
    return resp.model_dump(mode="json")


@router.get("/recommended", response_model=RecommendationResponse)
async def recommended_resources(
    module_id: int | None = Query(None),
    topic_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """Recursos curados reordenados y justificados por IA (fallback al orden
    curado). Exactamente uno de module_id | topic_id."""
    if (module_id is None) == (topic_id is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Especifica exactamente uno: module_id o topic_id.",
        )
    scope = f"m{module_id}" if module_id is not None else f"t{topic_id}"
    return await cached_json(
        redis_client,
        resource_rec_cache_key(user.id, scope),
        ttl=RECOMMEND_CACHE_TTL,
        loader=lambda: _recommendations_payload(user, db, module_id, topic_id),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run (from `backend/`):
```bash
python -m pytest tests/integration/test_router_resources.py -v
```
Expected: PASS (existing tests + 4 new)

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/resources.py backend/tests/integration/test_router_resources.py
git commit -m "feat(resources): GET /resources/recommended endpoint with Redis cache + fallback"
```

---

### Task 7: Wire invalidation into student mutations

**Files:**
- Modify: `backend/app/routers/quiz.py:270` area
- Modify: `backend/app/routers/coding.py:218` area
- Modify: `backend/app/routers/topics.py:157` area
- Modify: `backend/app/routers/assessment.py:162` area
- Modify: `backend/app/routers/users.py:108` area
- Modify: `backend/app/routers/admin.py:290` area

- [ ] **Step 1: Add the import + call at each callsite**

In each of the six routers, find the existing line `from app.services.companion_service import invalidate_companion` and add directly below it:

```python
from app.services.resource_recommender_service import invalidate_resource_recs
```

Then find each existing `await invalidate_companion(redis_client, <ID>)` call and add immediately below it (matching the exact `<ID>` already used at that site — `current_user.id` in quiz/coding/topics/assessment/users, `user_id` in admin):

```python
await invalidate_resource_recs(redis_client, <ID>)
```

- [ ] **Step 2: Verify the app imports cleanly**

Run (from `backend/`):
```bash
python -c "from app.main import app; print('ok')"
```
Expected: prints `ok`

- [ ] **Step 3: Run the affected router test suites**

Run (from `backend/`):
```bash
python -m pytest tests/integration/test_router_quiz.py tests/integration/test_router_coding.py tests/integration/test_router_topics.py tests/integration/test_router_assessment.py tests/integration/test_router_users.py tests/integration/test_router_admin.py -q
```
Expected: PASS (mutations still work; `scan_iter` on the MagicMock redis is swallowed by `invalidate_prefix`'s degraded mode, so no regressions).

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/quiz.py backend/app/routers/coding.py backend/app/routers/topics.py backend/app/routers/assessment.py backend/app/routers/users.py backend/app/routers/admin.py
git commit -m "feat(resources): invalidate AI recommendations on quiz/coding/topic/level mutations"
```

---

### Task 8: Frontend types + API client

**Files:**
- Modify: `frontend/src/types/resource.ts`
- Modify: `frontend/src/api/resources.ts`

- [ ] **Step 1: Add the types**

Append to `frontend/src/types/resource.ts`:

```ts
export interface RecommendedResource extends LearningResource {
  reason: string | null
}

export interface RecommendationResponse {
  ai_ranked: boolean
  level: string
  recommendations: RecommendedResource[]
}
```

- [ ] **Step 2: Add the API method**

Replace `frontend/src/api/resources.ts` with:

```ts
import apiClient from './client'
import type { LearningResource, RecommendationResponse } from '@/types/resource'

export const resourcesApi = {
  list: (params: { moduleId?: number; topicId?: number }) =>
    apiClient.get<LearningResource[]>('/resources', {
      params: { module_id: params.moduleId, topic_id: params.topicId },
    }),
  recommended: (params: { moduleId?: number; topicId?: number }) =>
    apiClient.get<RecommendationResponse>('/resources/recommended', {
      params: { module_id: params.moduleId, topic_id: params.topicId },
    }),
}
```

- [ ] **Step 3: Verify the type-check passes**

Run (from `frontend/`):
```bash
npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/resource.ts frontend/src/api/resources.ts
git commit -m "feat(resources): frontend types + recommended() API method"
```

---

### Task 9: useRecommendedResources hook

**Files:**
- Create: `frontend/src/hooks/useRecommendedResources.ts`

- [ ] **Step 1: Create the hook**

Create `frontend/src/hooks/useRecommendedResources.ts`:

```ts
import { useQuery } from '@tanstack/react-query'
import { resourcesApi } from '@/api/resources'

export function useRecommendedResources(params: { moduleId?: number; topicId?: number }) {
  const hasId = params.moduleId != null || params.topicId != null
  return useQuery({
    queryKey: ['resources-recommended', params.moduleId, params.topicId],
    queryFn: async () => {
      const { data } = await resourcesApi.recommended(params)
      return data
    },
    enabled: hasId,
    staleTime: 60_000,
  })
}
```

- [ ] **Step 2: Verify the type-check passes**

Run (from `frontend/`):
```bash
npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useRecommendedResources.ts
git commit -m "feat(resources): useRecommendedResources query hook"
```

---

### Task 10: RecommendedResources component

**Files:**
- Create: `frontend/src/components/resources/RecommendedResources.tsx`
- Create: `frontend/src/components/resources/RecommendedResources.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/resources/RecommendedResources.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import RecommendedResources from './RecommendedResources'

vi.mock('@/hooks/useRecommendedResources', () => ({
  useRecommendedResources: vi.fn(),
}))
import { useRecommendedResources } from '@/hooks/useRecommendedResources'

const mockHook = useRecommendedResources as unknown as ReturnType<typeof vi.fn>

const rec = (over = {}) => ({
  id: 1, module_id: 1, topic_id: null, kind: 'video', title: 'Video del emulador',
  url: 'http://x/1', author: null, description: null, order_index: 0, is_active: true,
  reason: 'Empieza por aquí', ...over,
})

describe('RecommendedResources', () => {
  it('renders the AI chip and reason when ai_ranked', () => {
    mockHook.mockReturnValue({
      data: { ai_ranked: true, level: 'beginner', recommendations: [rec()] },
    })
    render(<RecommendedResources moduleId={1} />)
    expect(screen.getByText(/Recomendado por IA/)).toBeInTheDocument()
    expect(screen.getByText('Empieza por aquí')).toBeInTheDocument()
  })

  it('hides chip and reasons in fallback', () => {
    mockHook.mockReturnValue({
      data: { ai_ranked: false, level: 'beginner', recommendations: [rec()] },
    })
    render(<RecommendedResources moduleId={1} />)
    expect(screen.queryByText(/Recomendado por IA/)).toBeNull()
    expect(screen.queryByText('Empieza por aquí')).toBeNull()
  })

  it('renders nothing when there are no recommendations', () => {
    mockHook.mockReturnValue({
      data: { ai_ranked: true, level: 'beginner', recommendations: [] },
    })
    const { container } = render(<RecommendedResources moduleId={1} />)
    expect(container).toBeEmptyDOMElement()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`):
```bash
npx vitest run src/components/resources/RecommendedResources.test.tsx
```
Expected: FAIL — cannot resolve `./RecommendedResources`

- [ ] **Step 3: Create the component**

Create `frontend/src/components/resources/RecommendedResources.tsx`:

```tsx
import { BookOpen, Sparkles } from 'lucide-react'
import ResourceCard from './ResourceCard'
import { useRecommendedResources } from '@/hooks/useRecommendedResources'

const LEVEL_LABEL: Record<string, string> = {
  beginner: 'principiante',
  intermediate: 'intermedio',
  advanced: 'avanzado',
}

interface Props {
  moduleId?: number
  topicId?: number
  title?: string
  headingLevel?: 2 | 3 | 4
}

export default function RecommendedResources({
  moduleId,
  topicId,
  title = 'Recomendado para ti',
  headingLevel = 2,
}: Props) {
  const { data } = useRecommendedResources({ moduleId, topicId })
  if (!data || data.recommendations.length === 0) return null
  const Heading = (`h${headingLevel}`) as 'h2' | 'h3' | 'h4'

  return (
    <section aria-label={title} className="space-y-2 mb-8">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Heading className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <BookOpen className="h-4 w-4 text-primary" aria-hidden="true" />
          {title}
        </Heading>
        {data.ai_ranked && (
          <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
            <Sparkles className="h-3 w-3" aria-hidden="true" />
            Recomendado por IA · nivel {LEVEL_LABEL[data.level] ?? data.level}
          </span>
        )}
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {data.recommendations.map((r) => (
          <div key={r.id} className="space-y-1">
            <ResourceCard resource={r} />
            {data.ai_ranked && r.reason && (
              <p className="flex items-start gap-1 pl-1 text-xs text-primary/90">
                <Sparkles className="mt-0.5 h-3 w-3 shrink-0" aria-hidden="true" />
                <span>{r.reason}</span>
              </p>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

Run (from `frontend/`):
```bash
npx vitest run src/components/resources/RecommendedResources.test.tsx
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/resources/RecommendedResources.tsx frontend/src/components/resources/RecommendedResources.test.tsx
git commit -m "feat(resources): RecommendedResources component with AI chip + rationale"
```

---

### Task 11: Mount on Dashboard + TopicPage (remove companion duplication)

**Files:**
- Modify: `frontend/src/components/tutor/CompanionPanel.tsx`
- Modify: `frontend/src/components/tutor/CompanionPanel.test.tsx` (if it asserts resources)
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/pages/TopicPage.tsx`

- [ ] **Step 1: Remove the resource block from CompanionPanel**

In `frontend/src/components/tutor/CompanionPanel.tsx`:
- Delete the import line: `import ResourceList from '@/components/resources/ResourceList'`
- Change the destructure `const { position, diagnostic, greeting, resources } = data` to `const { position, diagnostic, greeting } = data`
- Delete this block (the AI card on the Dashboard now owns resources):

```tsx
      {resources.length > 0 && (
        <ResourceList
          resources={resources}
          title="Recursos de tu módulo actual"
          headingLevel={3}
        />
      )}
```

- [ ] **Step 2: Mount the AI card on the Dashboard**

In `frontend/src/pages/DashboardPage.tsx`:
- Add the import (near the other component imports, line ~29):

```tsx
import RecommendedResources from '@/components/resources/RecommendedResources'
```

- Replace the companion branch:

```tsx
      {showCompanion ? (
        <CompanionPanel data={companion} />
      ) : (
```

with:

```tsx
      {showCompanion ? (
        <>
          <CompanionPanel data={companion} />
          {companion.position && (
            <RecommendedResources
              moduleId={companion.position.module_id}
              title="Recursos de tu módulo actual"
              headingLevel={3}
            />
          )}
        </>
      ) : (
```

- [ ] **Step 3: Swap ResourceList for the AI card on TopicPage**

In `frontend/src/pages/TopicPage.tsx`:
- Change the import line (line ~14) from `import ResourceList from '@/components/resources/ResourceList'` to:

```tsx
import RecommendedResources from '@/components/resources/RecommendedResources'
```

- Change the mount (line ~312) from `{!isNaN(topicId) && <ResourceList topicId={topicId} />}` to:

```tsx
      {!isNaN(topicId) && <RecommendedResources topicId={topicId} />}
```

- [ ] **Step 4: Fix the CompanionPanel test if needed**

Run (from `frontend/`):
```bash
npx vitest run src/components/tutor/CompanionPanel.test.tsx
```
If it fails because it asserted rendered resources, remove those specific assertions (and any `resources: [...]` expectations) — the panel no longer renders resources. Re-run until PASS.

- [ ] **Step 5: Full frontend type-check + test run**

Run (from `frontend/`):
```bash
npx tsc --noEmit && npx vitest run
```
Expected: type-check clean; all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/tutor/CompanionPanel.tsx frontend/src/components/tutor/CompanionPanel.test.tsx frontend/src/pages/DashboardPage.tsx frontend/src/pages/TopicPage.tsx
git commit -m "feat(resources): surface AI recommendations on Dashboard + TopicPage"
```

---

## Final verification

- [ ] **Backend full suite** (from `backend/`): `python -m pytest -q` → all PASS.
- [ ] **Frontend full suite** (from `frontend/`): `npx tsc --noEmit && npx vitest run` → clean + PASS.
- [ ] **Manual smoke** (optional, needs Ollama up): log in as a student with an entry level, open Dashboard → "Recomendado para ti" shows the AI chip + reordered resources with reasons; stop Ollama → reload → resources still show in curated order, no chip (`ai_ranked=false`).
