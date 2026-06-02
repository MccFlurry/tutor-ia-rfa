"""Corrige user_levels.history al shape válido que exige UserLevelResponse
({level, score, changed_at, reason}). La data demo se sembró con un shape viejo
({level, score, at}) que rompía GET /users/me/level con HTTP 500 -> el frontend
mandaba a los alumnos al examen de entrada aunque ya tuvieran nivel.

Reconstruye una entrada de history a partir de las columnas existentes.
Idempotente: omite filas que ya tienen el shape correcto.

Uso (dentro del contenedor backend, o local):
    python scripts/fix_level_history.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REQUIRED = {"level", "score", "changed_at", "reason"}


async def main() -> None:
    sys.path.insert(0, str(BACKEND_DIR))
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.models.user_level import UserLevel

    engine = create_async_engine(settings.DATABASE_URL)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    fixed = ok = 0
    async with Session() as db:
        rows = (await db.execute(select(UserLevel))).scalars().all()
        for lvl in rows:
            hist = lvl.history or []
            valid = bool(hist) and all(
                isinstance(h, dict) and REQUIRED <= set(h.keys()) for h in hist
            )
            if valid:
                ok += 1
                continue
            ts = (lvl.assessed_at or lvl.last_reassessed_at)
            lvl.history = [{
                "level": lvl.level,
                "score": lvl.entry_score,
                "changed_at": ts.isoformat() if ts else None,
                "reason": "entry",
            }]
            fixed += 1
        await db.commit()
    await engine.dispose()
    print(f"user_levels corregidos: {fixed} | ya válidos: {ok}")


if __name__ == "__main__":
    asyncio.run(main())
