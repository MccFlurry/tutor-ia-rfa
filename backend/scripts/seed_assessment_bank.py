"""
seed_assessment_bank.py — Carga el banco de preguntas fallback para la
evaluación de entrada. Idempotente: skip si ya hay preguntas activas.
Ejecutar:
    docker compose exec backend python /app/scripts/seed_assessment_bank.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.user import User
from app.models.assessment_bank import EntryAssessmentBank

# Import the data from seed_db (defined there to keep a single source of truth)
from scripts.seed_db import ASSESSMENT_BANK_BY_MODULE


engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(EntryAssessmentBank))
        if existing.scalars().first():
            print("Banco ya tiene preguntas. Nada que hacer.")
            return

        admin_result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        admin = admin_result.scalar_one_or_none()
        if not admin:
            print("ERROR: admin no encontrado. Corre primero seed_db.py")
            return

        # module_order (1-5) is same as module_id in the seeded schema
        # (modules are created with id = SERIAL starting at 1 in order)
        total = 0
        for module_id, items in ASSESSMENT_BANK_BY_MODULE.items():
            for item in items:
                db.add(EntryAssessmentBank(
                    module_id=module_id,
                    question_text=item["question_text"],
                    options=item["options"],
                    correct_index=item["correct_index"],
                    difficulty=item["difficulty"],
                    created_by=admin.id,
                    is_active=True,
                ))
                total += 1
        await db.commit()
        print(f"Banco sembrado: {total} preguntas")


if __name__ == "__main__":
    asyncio.run(seed())
