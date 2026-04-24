#!/usr/bin/env python3
"""
export_corpus.py — Exporta los chunks del corpus desde PostgreSQL+pgvector
a un archivo JSON plano para el benchmark de embeddings.

Conecta a tu base de datos (misma que usa el backend) y extrae el texto
de cada chunk. Los vectores embedding NO se exportan porque los vamos
a recalcular con los dos modelos a comparar.

Uso:
    # 1. asegúrate de tener tu DATABASE_URL en entorno o editarla abajo
    export DATABASE_URL="postgresql://user:pass@localhost:5432/tutor_db"
    python export_corpus.py

Produce: results/corpus_chunks.json
    [{"id": 1, "text": "...", "document_name": "...", "source": "..."}]

Requisitos:
    pip install asyncpg
"""

import asyncio
import json
import os
import sys
from pathlib import Path

try:
    import asyncpg
except ImportError:
    sys.exit("❌ falta asyncpg. Ejecuta: pip install asyncpg")


# Edita aquí si prefieres no usar variable de entorno:
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/tutor_db",
)

# Nombre de la tabla según CLAUDE.md; ajusta si tu esquema difiere
TABLE_CANDIDATES = ["document_chunks", "corpus_chunks"]


async def detect_table(conn):
    for t in TABLE_CANDIDATES:
        exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
            t,
        )
        if exists:
            return t
    raise RuntimeError(
        f"No se encontró ninguna de las tablas esperadas: {TABLE_CANDIDATES}. "
        "Edita export_corpus.py con el nombre correcto de tu tabla de chunks."
    )


async def main():
    here = Path(__file__).parent
    out_dir = here / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "corpus_chunks.json"

    print(f"🔌 Conectando a {DATABASE_URL.rsplit('@', 1)[-1]}")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        table = await detect_table(conn)
        print(f"📦 Tabla detectada: {table}")

        columns = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = $1",
            table,
        )
        col_names = {c["column_name"] for c in columns}
        print(f"   columnas: {sorted(col_names)}")

        # Columna de texto probable
        text_col = next(
            (c for c in ("content", "chunk_text", "text", "body") if c in col_names),
            None,
        )
        if not text_col:
            sys.exit(f"❌ No encuentro una columna de texto en {table}. Columnas: {col_names}")

        # Columnas opcionales
        doc_col = next(
            (c for c in ("document_name", "source", "source_file", "document_id") if c in col_names),
            None,
        )

        select_parts = ["id", f'"{text_col}" AS text']
        if doc_col:
            select_parts.append(f'"{doc_col}" AS document_name')
        query = f"SELECT {', '.join(select_parts)} FROM {table} ORDER BY id"

        rows = await conn.fetch(query)
        print(f"📄 Extraídos {len(rows)} chunks")

        data = [dict(r) for r in rows]
        # asyncpg devuelve algunos tipos como Record, JSON no los serializa directo
        clean = []
        for d in data:
            clean.append({k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v) for k, v in d.items()})

        out_path.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ Guardado en {out_path}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
