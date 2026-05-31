"""
seed_learning_resources.py — Carga recursos de aprendizaje curados
(videos/libros) por módulo. Idempotente: skip si ya hay recursos.

⚠️  URLs DE EJEMPLO — VERIFICAR MANUALMENTE antes de usar en producción.
    El sistema NUNCA inventa recursos vía LLM; este seed es un punto de
    partida que un docente/admin debe revisar y completar.

Ejecutar:
    docker compose exec backend python /app/scripts/seed_learning_resources.py
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
from app.models.learning_resource import LearningResource

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ⚠️ PLACEHOLDERS — el admin debe verificar/reemplazar estas URLs.
RESOURCES_BY_MODULE = {
    1: [
        {"kind": "video", "title": "Introducción a Android y Kotlin (verificar URL)",
         "url": "https://www.youtube.com/results?search_query=introduccion+android+kotlin+espanol",
         "author": "Pendiente de verificación", "order_index": 0},
        {"kind": "book", "title": "Bibliografía del sílabo M1 (completar)",
         "url": "https://developer.android.com/courses", "author": "Android Developers", "order_index": 1},
    ],
    2: [
        {"kind": "video", "title": "Fundamentos de Kotlin (verificar URL)",
         "url": "https://www.youtube.com/results?search_query=kotlin+fundamentos+espanol",
         "author": "Pendiente de verificación", "order_index": 0},
    ],
    3: [
        {"kind": "doc", "title": "Guía oficial de layouts (Android Developers)",
         "url": "https://developer.android.com/develop/ui", "author": "Android Developers", "order_index": 0},
    ],
    4: [
        {"kind": "doc", "title": "Room + APIs REST (Android Developers)",
         "url": "https://developer.android.com/training/data-storage/room", "author": "Android Developers", "order_index": 0},
    ],
    5: [
        {"kind": "doc", "title": "Publicación en Play Store (verificar)",
         "url": "https://developer.android.com/distribute", "author": "Android Developers", "order_index": 0},
    ],
}


async def seed():
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(LearningResource))
        if existing.scalars().first():
            print("Ya hay recursos. Nada que hacer.")
            return
        admin_result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        admin = admin_result.scalar_one_or_none()
        created_by = admin.id if admin else None
        total = 0
        for module_id, items in RESOURCES_BY_MODULE.items():
            for item in items:
                db.add(LearningResource(
                    module_id=module_id, topic_id=None,
                    kind=item["kind"], title=item["title"], url=item["url"],
                    author=item.get("author"), description=item.get("description"),
                    order_index=item.get("order_index", 0),
                    created_by=created_by, is_active=True,
                ))
                total += 1
        await db.commit()
        print(f"Recursos sembrados: {total}")
        print("⚠️  RECUERDA: verifica/reemplaza las URLs placeholder en el panel admin.")


if __name__ == "__main__":
    asyncio.run(seed())
