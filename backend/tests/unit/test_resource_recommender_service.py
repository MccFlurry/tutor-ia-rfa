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


@pytest.mark.asyncio
async def test_gather_ai_ranked_false_when_llm_fails(monkeypatch):
    # ≥2 candidatos pero el LLM cae (_rank_with_llm devuelve []) → orden curado.
    monkeypatch.setattr(mod, "select_candidates",
                        AsyncMock(return_value=[_res(1), _res(2)]))
    monkeypatch.setattr(mod, "build_student_signal",
                        AsyncMock(return_value=StudentSignal("beginner", "x")))
    monkeypatch.setattr(mod, "_rank_with_llm", AsyncMock(return_value=[]))
    resp = await gather_recommendations(SimpleNamespace(id="u"), MagicMock(),
                                        module_id=1, topic_id=None)
    assert resp.ai_ranked is False
    assert [r.id for r in resp.recommendations] == [1, 2]  # orden curado intacto


@pytest.mark.asyncio
async def test_select_candidates_module_only():
    # topic_id=None → un solo execute, filtro por module_id.
    db = MagicMock(); db.execute = AsyncMock()
    orm = SimpleNamespace(
        id=7, module_id=2, topic_id=None, kind="video", title="V",
        url="http://x", author=None, description=None, order_index=0, is_active=True,
    )
    r = MagicMock()
    r.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[orm])))
    db.execute.return_value = r
    out = await select_candidates(db, module_id=2, topic_id=None)
    assert [x.id for x in out] == [7]


@pytest.mark.asyncio
async def test_topic_weakness_label_normalizes_score():
    # Trampa de escala: QuizAttempt.score 0-1 → bandas 0-100. 0.70→70 = "afianzar"
    # (sin ×100 sería 0.70 < 60 → "dificultades": este test protege el ×100).
    from app.services.resource_recommender_service import _topic_weakness_label
    row = SimpleNamespace(best=0.70, failed=0)
    result_mock = MagicMock()
    result_mock.first = MagicMock(return_value=row)
    db = MagicMock(); db.execute = AsyncMock(return_value=result_mock)
    label = await _topic_weakness_label(SimpleNamespace(id="u"), db, topic_id=1)
    assert "afianzar" in label


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
