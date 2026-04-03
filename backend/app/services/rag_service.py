"""
rag_service.py — Pipeline RAG principal.
Embed query → pgvector similarity search → prompt aumentado → Ollama → caché Redis.
"""

import json
import hashlib

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import settings
from app.services.embed_service import embed_query
from app.utils.logger import logger


SYSTEM_PROMPT = """Eres un tutor académico experto en el curso de Aplicaciones Móviles \
del IESTP República Federal de Alemania (RFA) en Chiclayo, Perú.

Tu especialidad es guiar a los estudiantes en el aprendizaje de desarrollo de \
aplicaciones Android usando Kotlin. Enseñas con paciencia, claridad y con ejemplos \
prácticos adaptados al nivel técnico del IESTP.

REGLAS:
1. Responde SIEMPRE en español peruano claro y académico.
2. Basa tus respuestas en el CONTEXTO DEL CURSO que se te provee.
3. Si la pregunta no está relacionada con el curso, indícalo amablemente y redirige.
4. Incluye ejemplos de código Kotlin cuando sea útil (dentro de bloques ```kotlin).
5. Si el contexto no tiene información suficiente, admítelo honestamente.
6. NUNCA inventes información técnica ni cites fuentes que no estén en el contexto.
7. Sé motivador y reconoce el esfuerzo del estudiante.

CONTEXTO DEL CURSO (material recuperado):
{context}

HISTORIAL DE LA CONVERSACIÓN:
{history}"""


NO_CONTEXT_RESPONSE = (
    "No encontré información específica sobre eso en el material del curso. "
    "¿Podrías reformular tu pregunta o consultarme sobre un tema "
    "específico del curso de Aplicaciones Móviles?"
)


async def query_rag(
    question: str,
    session_history: list[dict],
    db: AsyncSession,
    redis_client,
) -> dict:
    """
    Execute the full RAG pipeline.
    Returns: {"content": str, "sources": list[dict]}
    """
    # 1. Check Redis cache
    cache_key = _cache_key(question)
    cached = await redis_client.get(cache_key)
    if cached:
        logger.info(f"RAG cache hit: {question[:50]}")
        return json.loads(cached)

    # 2. Generate query embedding
    query_vector = await embed_query(question)

    # 3. Semantic search in pgvector
    chunks = await _semantic_search(query_vector, db)

    if not chunks:
        return {"content": NO_CONTEXT_RESPONSE, "sources": []}

    # 4. Build context from retrieved chunks
    context = _build_context(chunks)

    # 5. Build conversation history (last N rounds)
    max_messages = settings.RAG_CONTEXT_WINDOW * 2  # 5 rounds = 10 messages
    history_text = _build_history(session_history[-max_messages:])

    # 6. Build augmented prompt
    system_content = SYSTEM_PROMPT.format(context=context, history=history_text)

    # 7. Call LLM
    llm = ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.3,
        num_ctx=4096,
        timeout=settings.OLLAMA_TIMEOUT,
    )

    logger.info(f"RAG query: {question[:80]}... ({len(chunks)} chunks)")
    response = await llm.ainvoke([
        SystemMessage(content=system_content),
        HumanMessage(content=question),
    ])

    # 8. Prepare cited sources (only high-similarity ones)
    sources = [
        {
            "content_preview": chunk["content"][:150] + "...",
            "document_name": chunk["metadata"].get("source", "Material del curso"),
            "similarity": round(chunk["similarity"], 3),
        }
        for chunk in chunks
        if chunk["similarity"] >= 0.75
    ]

    result = {"content": response.content, "sources": sources}

    # 9. Cache response (TTL: 1 hour)
    await redis_client.setex(cache_key, 3600, json.dumps(result))

    return result


async def _semantic_search(
    query_vector: list[float],
    db: AsyncSession,
    top_k: int | None = None,
    threshold: float | None = None,
) -> list[dict]:
    """Cosine similarity search in pgvector."""
    top_k = top_k or settings.RAG_TOP_K
    threshold = threshold or settings.RAG_SIMILARITY_THRESHOLD

    vec_literal = "[" + ",".join(str(v) for v in query_vector) + "]"

    sql = text(f"""
        SELECT
            content,
            metadata AS meta,
            1 - (embedding <=> '{vec_literal}'::vector) AS similarity
        FROM document_chunks
        WHERE 1 - (embedding <=> '{vec_literal}'::vector) >= :threshold
        ORDER BY embedding <=> '{vec_literal}'::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, {
        "threshold": threshold,
        "top_k": top_k,
    })
    rows = result.fetchall()

    return [
        {
            "content": row.content,
            "metadata": row.meta or {},
            "similarity": float(row.similarity),
        }
        for row in rows
    ]


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context string for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk["metadata"].get("source", "Material del curso")
        parts.append(f"[Fragmento {i} — Fuente: {source}]\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


def _build_history(messages: list[dict]) -> str:
    """Format conversation history for the LLM context."""
    if not messages:
        return "Sin historial previo."
    parts = []
    for msg in messages:
        role = "Estudiante" if msg["role"] == "user" else "Tutor"
        parts.append(f"{role}: {msg['content'][:300]}")
    return "\n".join(parts)


def _cache_key(question: str) -> str:
    """Generate a deterministic Redis cache key for a RAG query."""
    normalized = question.strip().lower()
    h = hashlib.sha256(normalized.encode()).hexdigest()[:16]
    return f"rag:{h}"
