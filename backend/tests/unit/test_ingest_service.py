"""
Unit tests para app/services/ingest_service.py.
Cubren _parse_file (txt/md/pdf/docx + ext desconocida), _clean_text (normalización
de whitespace y line endings), y _update_status / process_document flow con DB
y embeddings mockeados.
"""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import ingest_service


class TestParseFile:
    def test_parse_txt(self, tmp_path: Path):
        p = tmp_path / "x.txt"
        p.write_text("Hola mundo", encoding="utf-8")
        assert ingest_service._parse_file(str(p)) == "Hola mundo"

    def test_parse_md_same_as_txt(self, tmp_path: Path):
        p = tmp_path / "x.md"
        p.write_text("# Título\nCuerpo", encoding="utf-8")
        out = ingest_service._parse_file(str(p))
        assert "Título" in out

    def test_parse_pdf_uses_pypdf(self, tmp_path: Path, monkeypatch):
        p = tmp_path / "fake.pdf"
        p.write_bytes(b"%PDF-1.4 fake")
        page = MagicMock()
        page.extract_text.return_value = "page-1-text"
        reader = MagicMock()
        reader.pages = [page, page]
        monkeypatch.setattr(ingest_service.pypdf, "PdfReader", lambda _: reader)
        out = ingest_service._parse_file(str(p))
        assert out == "page-1-text\npage-1-text"

    def test_parse_docx_uses_python_docx(self, tmp_path: Path, monkeypatch):
        p = tmp_path / "fake.docx"
        p.write_bytes(b"PK fake docx")
        para1 = MagicMock(text="Primer párrafo")
        para_empty = MagicMock(text="   ")  # filtered out
        para2 = MagicMock(text="Segundo")
        doc = MagicMock()
        doc.paragraphs = [para1, para_empty, para2]
        monkeypatch.setattr(ingest_service.docx, "Document", lambda _: doc)
        out = ingest_service._parse_file(str(p))
        assert out == "Primer párrafo\nSegundo"

    def test_unknown_extension_raises(self, tmp_path: Path):
        p = tmp_path / "x.zip"
        p.write_bytes(b"zip")
        with pytest.raises(ValueError, match="no soportado"):
            ingest_service._parse_file(str(p))


class TestCleanText:
    def test_normalizes_crlf(self):
        assert ingest_service._clean_text("a\r\nb") == "a\nb"

    def test_collapses_triple_newlines(self):
        out = ingest_service._clean_text("a\n\n\n\nb")
        assert out == "a\n\nb"

    def test_collapses_internal_spaces(self):
        out = ingest_service._clean_text("a    \t  b")
        assert out == "a b"

    def test_strips_outer_whitespace(self):
        assert ingest_service._clean_text("  hola  ") == "hola"

    def test_idempotent_on_clean_text(self):
        text = "Línea 1\nLínea 2\n\nLínea 3"
        assert ingest_service._clean_text(text) == text


class TestUpdateStatus:
    @pytest.mark.asyncio
    async def test_writes_status_and_commits(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        doc_id = uuid.uuid4()
        await ingest_service._update_status(doc_id, "processing", db)
        db.execute.assert_awaited_once()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_accepts_optional_fields(self):
        from datetime import datetime, timezone

        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        await ingest_service._update_status(
            uuid.uuid4(),
            "active",
            db,
            chunk_count=42,
            processed_at=datetime.now(timezone.utc),
        )
        # Build values from call args; ensure all extras flowed through
        call = db.execute.call_args
        # Update statement uses .values(**values) — captured in compiled form;
        # we only assert it was called once + commit.
        assert call is not None
        db.commit.assert_awaited_once()


class TestProcessDocument:
    @pytest.mark.asyncio
    async def test_marks_error_when_text_too_short(self, tmp_path, monkeypatch):
        p = tmp_path / "tiny.txt"
        p.write_text("hi", encoding="utf-8")

        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()

        await ingest_service.process_document(uuid.uuid4(), str(p), db)
        # _update_status('processing') + _update_status('error') = 2 execute calls
        assert db.execute.await_count >= 2

    @pytest.mark.asyncio
    async def test_marks_error_on_unknown_extension(self, tmp_path):
        p = tmp_path / "broken.zip"
        p.write_bytes(b"x")

        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        await ingest_service.process_document(uuid.uuid4(), str(p), db)
        # processing → error
        assert db.execute.await_count >= 2

    @pytest.mark.asyncio
    async def test_happy_path_persists_chunks(self, tmp_path, monkeypatch):
        long_text = ("Lorem ipsum dolor sit amet, consectetur. " * 30)
        p = tmp_path / "doc.txt"
        p.write_text(long_text, encoding="utf-8")

        async def fake_embed(chunks):
            return [[0.1] * 1024 for _ in chunks]

        monkeypatch.setattr(ingest_service, "embed_documents", fake_embed)

        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.add = MagicMock()

        doc_id = uuid.uuid4()
        await ingest_service.process_document(doc_id, str(p), db)
        # At least one chunk added
        assert db.add.call_count >= 1
