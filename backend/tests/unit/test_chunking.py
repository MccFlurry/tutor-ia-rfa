"""
Unit tests para app/utils/chunking.py.
Verifica que el splitter respete chunk_size/overlap configurados y conserve
contenido textual al dividir.
"""

from app.config import settings
from app.utils.chunking import get_text_splitter


def test_splitter_uses_configured_size():
    s = get_text_splitter()
    assert s._chunk_size == settings.CHUNK_SIZE
    assert s._chunk_overlap == settings.CHUNK_OVERLAP


def test_splitter_separators_priority():
    s = get_text_splitter()
    # Order matters — paragraphs first, then lines, sentences, words, chars
    assert s._separators == ["\n\n", "\n", ". ", " ", ""]


def test_splitter_splits_long_text():
    s = get_text_splitter()
    text = ("Frase de prueba. " * 200).strip()  # >> chunk_size
    chunks = s.split_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= settings.CHUNK_SIZE + 100 for c in chunks)  # tolerancia


def test_splitter_short_text_single_chunk():
    s = get_text_splitter()
    chunks = s.split_text("Pequeño contenido")
    assert chunks == ["Pequeño contenido"]
