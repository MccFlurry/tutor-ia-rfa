"""
Unit tests para app/services/embed_service.py.
Verifican singleton + delegación a OllamaEmbeddings sin requerir Ollama vivo.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import embed_service


@pytest.fixture(autouse=True)
def reset_singleton():
    """Cada test arranca con el singleton limpio."""
    embed_service._embeddings_model = None
    yield
    embed_service._embeddings_model = None


class TestSingleton:
    def test_get_embeddings_model_is_cached(self, monkeypatch):
        instances = []

        def fake_ctor(model, base_url):
            inst = MagicMock(model=model, base_url=base_url)
            instances.append(inst)
            return inst

        monkeypatch.setattr(embed_service, "OllamaEmbeddings", fake_ctor)
        a = embed_service.get_embeddings_model()
        b = embed_service.get_embeddings_model()
        assert a is b
        assert len(instances) == 1

    def test_get_embeddings_model_uses_settings(self, monkeypatch):
        captured = {}

        def fake_ctor(model, base_url):
            captured["model"] = model
            captured["base_url"] = base_url
            return MagicMock()

        monkeypatch.setattr(embed_service, "OllamaEmbeddings", fake_ctor)
        embed_service.get_embeddings_model()
        assert captured["model"] == embed_service.settings.OLLAMA_EMBED_MODEL
        assert captured["base_url"] == embed_service.settings.OLLAMA_BASE_URL


class TestEmbedQuery:
    @pytest.mark.asyncio
    async def test_returns_vector_from_model(self, monkeypatch):
        model = MagicMock()
        model.aembed_query = AsyncMock(return_value=[0.1] * 1024)
        monkeypatch.setattr(
            embed_service, "get_embeddings_model", lambda: model
        )
        vec = await embed_service.embed_query("hola")
        assert len(vec) == 1024
        model.aembed_query.assert_awaited_once_with("hola")


class TestEmbedDocuments:
    @pytest.mark.asyncio
    async def test_returns_one_vector_per_chunk(self, monkeypatch):
        model = MagicMock()
        model.aembed_documents = AsyncMock(
            return_value=[[0.0] * 1024, [0.1] * 1024]
        )
        monkeypatch.setattr(
            embed_service, "get_embeddings_model", lambda: model
        )
        out = await embed_service.embed_documents(["chunk1", "chunk2"])
        assert len(out) == 2
        assert all(len(v) == 1024 for v in out)
        model.aembed_documents.assert_awaited_once_with(["chunk1", "chunk2"])
