"""
Unit tests para los internals de app/services/rag_service.py.
Cubre cache key determinism, context/history builders, NO_CONTEXT path y
query_rag end-to-end con todos los externos mockeados.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

import pytest

from app.services import rag_service


class TestCacheKey:
    def test_normalizes_case_and_whitespace(self):
        a = rag_service._cache_key("¿Qué es Kotlin?")
        b = rag_service._cache_key("  ¿qué es kotlin?  ")
        assert a == b

    def test_different_questions_yield_different_keys(self):
        a = rag_service._cache_key("¿Qué es Kotlin?")
        b = rag_service._cache_key("¿Qué es Java?")
        assert a != b

    def test_key_prefix(self):
        assert rag_service._cache_key("x").startswith("rag:")


class TestBuildContext:
    def test_empty_chunks(self):
        assert rag_service._build_context([]) == ""

    def test_formats_each_fragment_with_source(self):
        chunks = [
            {"content": "Texto 1", "metadata": {"source": "modulo-1.md"}},
            {"content": "Texto 2", "metadata": {}},  # default label
        ]
        out = rag_service._build_context(chunks)
        assert "[Fragmento 1 — Fuente: modulo-1.md]" in out
        assert "[Fragmento 2 — Fuente: Material del curso]" in out
        assert "Texto 1" in out
        assert "Texto 2" in out
        assert "---" in out


class TestBuildHistory:
    def test_empty_history_returns_default(self):
        assert rag_service._build_history([]) == "Sin historial previo."

    def test_formats_user_and_assistant(self):
        msgs = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Buen día"},
        ]
        out = rag_service._build_history(msgs)
        assert "Estudiante: Hola" in out
        assert "Tutor: Buen día" in out

    def test_truncates_long_content_to_300(self):
        msg = {"role": "user", "content": "x" * 1000}
        out = rag_service._build_history([msg])
        assert len(out) <= len("Estudiante: ") + 300


class TestSemanticSearch:
    @pytest.mark.asyncio
    async def test_uses_threshold_and_top_k_settings(self):
        db = MagicMock()
        row = SimpleNamespace(content="c", meta={"source": "s"}, similarity=0.9)
        result = MagicMock()
        result.fetchall = MagicMock(return_value=[row])
        db.execute = AsyncMock(return_value=result)

        out = await rag_service._semantic_search([0.1] * 1024, db)
        assert len(out) == 1
        assert out[0]["similarity"] == 0.9
        params = db.execute.call_args.args[1]
        assert "threshold" in params
        assert "top_k" in params

    @pytest.mark.asyncio
    async def test_handles_none_metadata(self):
        db = MagicMock()
        row = SimpleNamespace(content="c", meta=None, similarity=0.7)
        result = MagicMock()
        result.fetchall = MagicMock(return_value=[row])
        db.execute = AsyncMock(return_value=result)
        out = await rag_service._semantic_search([0.0] * 1024, db)
        assert out[0]["metadata"] == {}


class TestQueryRag:
    @pytest.mark.asyncio
    async def test_cache_hit_short_circuits(self):
        cached = {"content": "respuesta cacheada", "sources": []}
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=json.dumps(cached))
        redis_client.setex = AsyncMock()

        out = await rag_service.query_rag("hola", [], db=MagicMock(), redis_client=redis_client)
        assert out == cached
        redis_client.setex.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_chunks_returns_educational_rejection(self):
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=None)
        redis_client.setex = AsyncMock()

        db = MagicMock()
        result = MagicMock()
        result.fetchall = MagicMock(return_value=[])
        db.execute = AsyncMock(return_value=result)

        with patch.object(rag_service, "embed_query", new=AsyncMock(return_value=[0.0] * 1024)):
            out = await rag_service.query_rag("xyz", [], db=db, redis_client=redis_client)
        assert out["content"] == rag_service.NO_CONTEXT_RESPONSE
        assert out["sources"] == []
        redis_client.setex.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_happy_path_includes_high_sim_sources_and_caches(self):
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=None)
        redis_client.setex = AsyncMock()

        # Two chunks: one above 0.75 threshold for sources, one below
        rows = [
            SimpleNamespace(content="A", meta={"source": "m1"}, similarity=0.9),
            SimpleNamespace(content="B", meta={"source": "m2"}, similarity=0.6),
        ]
        db = MagicMock()
        result = MagicMock()
        result.fetchall = MagicMock(return_value=rows)
        db.execute = AsyncMock(return_value=result)

        fake_llm = MagicMock()
        fake_llm.ainvoke = AsyncMock(return_value=SimpleNamespace(content="Respuesta"))

        with patch.object(rag_service, "embed_query", new=AsyncMock(return_value=[0.1] * 1024)), \
             patch.object(rag_service, "ChatOllama", return_value=fake_llm):
            out = await rag_service.query_rag("¿x?", [], db=db, redis_client=redis_client)

        assert out["content"] == "Respuesta"
        # Solo el chunk de similarity ≥ 0.75 entra en sources
        assert len(out["sources"]) == 1
        assert out["sources"][0]["similarity"] == 0.9
        redis_client.setex.assert_awaited_once()
        # TTL = 3600
        args = redis_client.setex.await_args.args
        assert args[1] == 3600
