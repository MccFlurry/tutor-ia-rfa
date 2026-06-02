"""Realinea el nivel de entrada DEMO para que sea coherente con el avance del
alumno (mas temas completados -> nivel mayor). Solo afecta data demo.

Umbrales del sistema: <40 beginner · 40-75 intermediate · >75 advanced.
Bandas por temas completados (de 22):
    <= 6  -> beginner     (score 25-39)
    7-15  -> intermediate (score 45-73)
    >= 16 -> advanced     (score 80-95)

Determinista, idempotente. Reescribe history con el shape valido.

Uso (dentro del contenedor backend, o local):
    python scripts/realign_demo_levels.py
"""
from __future__ import annotations

import asyncio
import random
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
SEED = 43


def level_for(score: float) -> str:
    if score < 40:
        return "beginner"
    if score <= 75:
        return "intermediate"
    return "advanced"


async def main() -> None:
    sys.path.insert(0, str(BACKEND_DIR))
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.models.progress import UserTopicProgress
    from app.models.user import User
    from app.models.user_level import UserLevel

    rng = random.Random(SEED)
    engine = create_async_engine(settings.DATABASE_URL)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    counts = {"beginner": 0, "intermediate": 0, "advanced": 0}
    updated = 0
    async with Session() as db:
        students = (
            await db.execute(select(User).where(User.role == "student").order_by(User.email))
        ).scalars().all()
        for s in students:
            lvl = await db.scalar(select(UserLevel).where(UserLevel.user_id == s.id))
            if not lvl:
                continue
            done = await db.scalar(
                select(func.count(UserTopicProgress.id)).where(
                    UserTopicProgress.user_id == s.id,
                    UserTopicProgress.is_completed == True,  # noqa: E712
                )
            ) or 0
            if done <= 6:
                score = round(rng.uniform(25, 39), 1)
            elif done <= 15:
                score = round(rng.uniform(45, 73), 1)
            else:
                score = round(rng.uniform(80, 95), 1)
            level = level_for(score)
            counts[level] += 1
            ts = lvl.assessed_at or lvl.last_reassessed_at
            lvl.level = level
            lvl.entry_score = score
            lvl.history = [{
                "level": level,
                "score": score,
                "changed_at": ts.isoformat() if ts else None,
                "reason": "entry",
            }]
            updated += 1
        await db.commit()
    await engine.dispose()
    print(f"Niveles realineados: {updated}")
    print(f"Distribución -> {counts}")


if __name__ == "__main__":
    asyncio.run(main())
