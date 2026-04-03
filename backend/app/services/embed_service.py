"""
embed_service.py — Cliente Ollama para generación de embeddings.
Usa el modelo mxbai-embed-large (1024 dimensiones).
"""

from langchain_ollama import OllamaEmbeddings

from app.config import settings
from app.utils.logger import logger


_embeddings_model: OllamaEmbeddings | None = None


def get_embeddings_model() -> OllamaEmbeddings:
    """Return a singleton OllamaEmbeddings instance."""
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = OllamaEmbeddings(
            model=settings.OLLAMA_EMBED_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
    return _embeddings_model


async def embed_query(text: str) -> list[float]:
    """Generate embedding vector for a single query string."""
    model = get_embeddings_model()
    logger.debug(f"Generando embedding para query ({len(text)} chars)")
    vector = await model.aembed_query(text)
    return vector


async def embed_documents(texts: list[str]) -> list[list[float]]:
    """Generate embedding vectors for a list of document chunks."""
    model = get_embeddings_model()
    logger.info(f"Generando embeddings para {len(texts)} chunks")
    vectors = await model.aembed_documents(texts)
    logger.info(f"Embeddings generados: {len(vectors)} vectores de {len(vectors[0])} dimensiones")
    return vectors
