"""
ingest_course_docs.py — Ingesta el contenido de los temas del curso al corpus RAG.

Lee todos los temas de la BD, los divide en chunks, genera embeddings
con Ollama mxbai-embed-large y los almacena en document_chunks (pgvector).

Uso:
  docker exec tutor_backend python scripts/ingest_course_docs.py

Requisitos:
  - PostgreSQL con pgvector corriendo
  - Ollama corriendo con el modelo mxbai-embed-large descargado
  - Tablas ya creadas (alembic upgrade head) y seed ejecutado
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

# Add backend root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.module import Module
from app.models.topic import Topic
from app.models.document import Document, DocumentChunk
from app.utils.chunking import get_text_splitter

# Embedding client (uses langchain_ollama directly since we're in a script)
from langchain_ollama import OllamaEmbeddings


engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


BATCH_SIZE = 5  # chunks per embedding batch (to not overwhelm Ollama)


async def main():
    print("=" * 60)
    print("INGESTA DE CONTENIDO DEL CURSO AL CORPUS RAG")
    print("=" * 60)

    # 1. Initialize embeddings model
    print(f"\n📡 Conectando con Ollama ({settings.OLLAMA_BASE_URL})...")
    print(f"   Modelo de embeddings: {settings.OLLAMA_EMBED_MODEL}")
    embeddings = OllamaEmbeddings(
        model=settings.OLLAMA_EMBED_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )

    # Test connection
    try:
        test_vec = await embeddings.aembed_query("test")
        print(f"   ✅ Conexión exitosa. Dimensiones: {len(test_vec)}")
    except Exception as e:
        print(f"   ❌ Error al conectar con Ollama: {e}")
        print("   Asegúrate de que Ollama esté corriendo y el modelo esté descargado.")
        print("   Ejecuta: docker exec tutor_ollama ollama pull mxbai-embed-large")
        return

    splitter = get_text_splitter()

    async with AsyncSessionLocal() as db:
        # 2. Get all modules and topics
        modules_result = await db.execute(
            select(Module).where(Module.is_active == True).order_by(Module.order_index)
        )
        modules = modules_result.scalars().all()

        topics_result = await db.execute(
            select(Topic).where(Topic.is_active == True).order_by(Topic.module_id, Topic.order_index)
        )
        topics = topics_result.scalars().all()

        print(f"\n📚 Encontrados {len(modules)} módulos y {len(topics)} temas")

        # 3. Create a virtual "document" for the course content
        #    Check if we already have one
        existing_doc = await db.execute(
            select(Document).where(Document.original_filename == "contenido_curso_temas.md")
        )
        doc = existing_doc.scalar_one_or_none()

        if doc:
            # Delete existing chunks to re-ingest
            print(f"\n🗑️  Eliminando chunks anteriores del documento {doc.id}...")
            await db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            )
            await db.commit()
            doc.status = "processing"
            doc.chunk_count = 0
            doc.processed_at = None
        else:
            doc = Document(
                id=uuid.uuid4(),
                original_filename="contenido_curso_temas.md",
                stored_filename="contenido_curso_temas.md",
                file_size_bytes=0,
                mime_type="text/markdown",
                status="processing",
                uploaded_by=None,
            )
            db.add(doc)

        await db.commit()
        await db.refresh(doc)
        print(f"   Documento: {doc.id}")

        # 4. Build module lookup
        module_map = {m.id: m.title for m in modules}

        # 5. Process each topic
        all_chunks = []
        all_metadata = []
        total_chars = 0

        for topic in topics:
            module_title = module_map.get(topic.module_id, "Módulo desconocido")

            # Prepend topic/module context to the content for better retrieval
            enriched_content = (
                f"# {topic.title}\n"
                f"Módulo: {module_title}\n\n"
                f"{topic.content}"
            )

            chunks = splitter.split_text(enriched_content)
            total_chars += len(enriched_content)

            for chunk_text in chunks:
                all_chunks.append(chunk_text)
                all_metadata.append({
                    "source": f"{module_title} > {topic.title}",
                    "module_id": topic.module_id,
                    "topic_id": topic.id,
                    "module_title": module_title,
                    "topic_title": topic.title,
                })

            print(f"   📄 {module_title} > {topic.title}: {len(chunks)} chunks")

        print(f"\n📊 Total: {len(all_chunks)} chunks de {total_chars:,} caracteres")

        # 6. Generate embeddings in batches
        print(f"\n🧮 Generando embeddings ({len(all_chunks)} chunks en lotes de {BATCH_SIZE})...")
        all_embeddings = []

        for i in range(0, len(all_chunks), BATCH_SIZE):
            batch = all_chunks[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (len(all_chunks) + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"   Lote {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ", flush=True)

            try:
                batch_embeddings = await embeddings.aembed_documents(batch)
                all_embeddings.extend(batch_embeddings)
                print("✅")
            except Exception as e:
                print(f"❌ Error: {e}")
                # Fill with None to maintain alignment
                all_embeddings.extend([None] * len(batch))

        # 7. Save chunks to database
        print(f"\n💾 Guardando {len(all_chunks)} chunks en la base de datos...")
        saved_count = 0

        for i, (chunk_text, metadata) in enumerate(zip(all_chunks, all_metadata)):
            embedding = all_embeddings[i] if i < len(all_embeddings) else None
            if embedding is None:
                continue

            chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                content=chunk_text,
                embedding=embedding,
                chunk_index=i,
                metadata_=metadata,
            )
            db.add(chunk)
            saved_count += 1

        await db.commit()

        # 8. Update document status
        doc.status = "active"
        doc.chunk_count = saved_count
        doc.processed_at = datetime.now(timezone.utc)
        doc.file_size_bytes = total_chars
        await db.commit()

        print(f"\n✅ Ingesta completada exitosamente!")
        print(f"   Documento: {doc.id}")
        print(f"   Chunks guardados: {saved_count}")
        print(f"   Estado: {doc.status}")

        # 9. Verify with a test query
        print(f"\n🔍 Verificando búsqueda semántica...")
        try:
            test_query = "¿Cómo crear una aplicación Android en Kotlin?"
            test_vec = await embeddings.aembed_query(test_query)

            result = await db.execute(text("""
                SELECT
                    content,
                    metadata AS meta,
                    1 - (embedding <=> :query_vec::vector) AS similarity
                FROM document_chunks
                WHERE document_id = :doc_id
                ORDER BY embedding <=> :query_vec::vector
                LIMIT 3
            """), {
                "query_vec": str(test_vec),
                "doc_id": str(doc.id),
            })
            rows = result.fetchall()

            print(f"   Query: \"{test_query}\"")
            for j, row in enumerate(rows, 1):
                source = row.meta.get("source", "?") if row.meta else "?"
                print(f"   [{j}] Similitud: {row.similarity:.3f} | Fuente: {source}")
                print(f"       {row.content[:100]}...")

            print(f"\n🎉 ¡Todo listo! El tutor IA puede responder preguntas del curso.")
        except Exception as e:
            print(f"   ⚠️ Error en verificación (los chunks se guardaron igualmente): {e}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
