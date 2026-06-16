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
