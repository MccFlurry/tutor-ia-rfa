"""
ingest_service.py — Procesamiento de documentos para el corpus RAG.
Pipeline: parseo → limpieza → chunking → embeddings → almacenamiento en pgvector.
"""

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pypdf
import docx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.config import settings
from app.models.document import Document, DocumentChunk
from app.services.embed_service import embed_documents
from app.utils.chunking import get_text_splitter
from app.utils.logger import logger


async def process_document(document_id: uuid.UUID, file_path: str, db: AsyncSession) -> None:
    """
    Pipeline completo de ingesta: parsear → limpiar → dividir → embeddings → guardar.
    Se ejecuta como BackgroundTask en FastAPI.
    """
    try:
        # 1. Actualizar estado a 'processing'
        await _update_status(document_id, "processing", db)

        # 2. Parsear el documento
        raw_text = _parse_file(file_path)
        if not raw_text or len(raw_text.strip()) < 50:
            raise ValueError("El documento no contiene texto suficiente para procesar")

        logger.info(f"Documento {document_id}: {len(raw_text)} caracteres extraídos")

        # 3. Limpiar texto
        clean_text = _clean_text(raw_text)

        # 4. Dividir en chunks
        splitter = get_text_splitter()
        chunks = splitter.split_text(clean_text)
        logger.info(f"Documento {document_id}: {len(chunks)} chunks generados")

        if not chunks:
            raise ValueError("No se generaron chunks del documento")

        # 5. Generar embeddings
        embeddings = await embed_documents(chunks)

        # 6. Guardar chunks en BD
        source_name = Path(file_path).name
        await _save_chunks(document_id, chunks, embeddings, source_name, db)

        # 7. Marcar como activo
        await _update_status(
            document_id, "active", db,
            chunk_count=len(chunks),
            processed_at=datetime.now(timezone.utc),
        )
        logger.info(f"Documento {document_id} procesado exitosamente: {len(chunks)} chunks")

    except Exception as e:
        logger.error(f"Error procesando documento {document_id}: {e}")
        await _update_status(document_id, "error", db, error_message=str(e))


def _parse_file(file_path: str) -> str:
    """Extract raw text from PDF, DOCX, or TXT file."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        reader = pypdf.PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix == ".docx":
        doc = docx.Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    elif suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Tipo de archivo no soportado: {suffix}")


def _clean_text(text: str) -> str:
    """Normalize whitespace and clean up extracted text."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


async def _save_chunks(
    document_id: uuid.UUID,
    chunks: list[str],
    embeddings: list[list[float]],
    source_name: str,
    db: AsyncSession,
) -> None:
    """Persist document chunks with their embeddings to the database."""
    for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=document_id,
            content=chunk_text,
            embedding=embedding,
            chunk_index=i,
            metadata_={"source": source_name},
        )
        db.add(chunk)

    await db.commit()


async def _update_status(
    document_id: uuid.UUID,
    status: str,
    db: AsyncSession,
    *,
    chunk_count: int | None = None,
    error_message: str | None = None,
    processed_at: datetime | None = None,
) -> None:
    """Update document processing status in the database."""
    values: dict = {"status": status}
    if chunk_count is not None:
        values["chunk_count"] = chunk_count
    if error_message is not None:
        values["error_message"] = error_message
    if processed_at is not None:
        values["processed_at"] = processed_at

    await db.execute(
        update(Document).where(Document.id == document_id).values(**values)
    )
    await db.commit()
