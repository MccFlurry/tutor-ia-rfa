"""Genera ACTIVIDAD DEMO para las cuentas de estudiantes: nivel, progreso por
tema, intentos de quiz, conversaciones de chat y logros. Sirve para que los
dashboards y el panel admin se vean poblados durante la demostracion en vivo.

============================  ADVERTENCIA  ============================
ESTO ES DATA DEMO / DE DEMOSTRACION. NO son resultados reales de uso por
parte de los estudiantes ni evidencia del OE4 (rendimiento academico). El
OE4 se mide aparte con un instrumento pretest/postest aplicado al piloto.
No usar estas cifras como resultado empirico en la tesis.
=======================================================================

Caracteristicas:
- Determinista (semilla fija) -> reproducible.
- Idempotente: omite estudiantes que ya tienen progreso (salvo --reset).
- Timestamps anclados al periodo del curso (06-abr-2026 .. 02-jun-2026); no usa
  la hora actual, para que el resultado sea estable.
- Respeta el desbloqueo secuencial: cada alumno completa un prefijo de los temas.

Uso (dentro del contenedor backend, o local con la BD levantada):
    python scripts/seed_demo_activity.py
    python scripts/seed_demo_activity.py --max-students 49 --reset
"""
from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
COURSE_START = datetime(2026, 4, 6, 9, 0, tzinfo=timezone.utc)
NOW_REF = datetime(2026, 6, 2, 18, 0, tzinfo=timezone.utc)  # ancla fija (no now())
SEED = 42

# Distribucion de profundidad de avance: (rango_temas, peso). Total 22 temas.
PROGRESS_BUCKETS = [
    ((0, 1), 10),    # recien empiezan
    ((2, 4), 20),    # dentro de M1
    ((5, 9), 26),    # M2
    ((10, 13), 20),  # M3
    ((14, 18), 14),  # M4
    ((19, 22), 10),  # casi completan / completan
]

CHAT_QUESTIONS = [
    "Cual es la diferencia entre val y var en Kotlin?",
    "Como creo una funcion con parametros por defecto?",
    "Que es un data class y cuando lo uso?",
    "Como funciona un RecyclerView en Android?",
    "Para que sirve el ciclo de vida de una Activity?",
    "Como hago una peticion HTTP con Retrofit?",
    "Que es una corrutina y como la lanzo?",
    "Como guardo datos localmente con Room?",
    "Cual es la diferencia entre let, run y apply?",
    "Como manejo valores nulos de forma segura?",
    "Que es un sealed class y un ejemplo de uso?",
    "Como navego entre fragments con Navigation Component?",
]


def pick_completed_count(rng: random.Random) -> int:
    ranges = [b[0] for b in PROGRESS_BUCKETS]
    weights = [b[1] for b in PROGRESS_BUCKETS]
    lo, hi = rng.choices(ranges, weights=weights, k=1)[0]
    return rng.randint(lo, hi)


def level_for(score: float) -> str:
    if score < 40:
        return "beginner"
    if score <= 75:
        return "intermediate"
    return "advanced"


async def main(max_students: int | None, reset: bool) -> None:
    sys.path.insert(0, str(BACKEND_DIR))
    from sqlalchemy import delete, func, select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.models.achievement import UserAchievement
    from app.models.chat import ChatMessage, ChatSession
    from app.models.progress import UserTopicProgress
    from app.models.quiz import QuizAttempt
    from app.models.topic import Topic
    from app.models.user import User
    from app.models.user_level import UserLevel
    from app.services.achievement_service import check_and_grant_achievements

    print("=" * 60)
    print("SEED DE ACTIVIDAD DEMO  (NO es evidencia OE4)")
    print(f"BD destino: {settings.DATABASE_URL.split('@')[-1]}")
    print("=" * 60)

    rng = random.Random(SEED)
    engine = create_async_engine(settings.DATABASE_URL)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        topics = (
            await db.execute(select(Topic).order_by(Topic.module_id, Topic.order_index))
        ).scalars().all()
        seq = [(t.id, t.module_id, bool(t.has_quiz)) for t in topics]
        if not seq:
            print("No hay temas en la BD. Corre seed_db.py primero.")
            return

        students = (
            await db.execute(
                select(User).where(User.role == "student").order_by(User.email)
            )
        ).scalars().all()
        if max_students:
            students = students[:max_students]
        print(f"Estudiantes objetivo: {len(students)} | temas: {len(seq)}\n")

        created = skipped = 0
        level_counts = {"beginner": 0, "intermediate": 0, "advanced": 0}
        total_badges = 0

        for s in students:
            existing = await db.scalar(
                select(func.count(UserTopicProgress.id)).where(
                    UserTopicProgress.user_id == s.id
                )
            )
            if existing and not reset:
                skipped += 1
                continue
            if existing and reset:
                await db.execute(delete(UserAchievement).where(UserAchievement.user_id == s.id))
                await db.execute(delete(QuizAttempt).where(QuizAttempt.user_id == s.id))
                await db.execute(delete(UserTopicProgress).where(UserTopicProgress.user_id == s.id))
                await db.execute(delete(UserLevel).where(UserLevel.user_id == s.id))
                await db.execute(delete(ChatSession).where(ChatSession.user_id == s.id))  # cascade msgs
                await db.flush()

            # --- nivel (evaluacion de entrada) ---
            entry = round(rng.uniform(20, 95), 1)
            lvl = level_for(entry)
            level_counts[lvl] += 1
            assessed = COURSE_START + timedelta(days=rng.randint(0, 3), hours=rng.randint(0, 8))
            db.add(UserLevel(
                user_id=s.id, level=lvl, entry_score=entry, assessed_at=assessed,
                history=[{"level": lvl, "score": entry, "at": assessed.isoformat()}],
            ))

            # --- progreso por tema (prefijo secuencial) ---
            k = pick_completed_count(rng)
            day = COURSE_START + timedelta(days=rng.randint(0, 2))
            completed = []
            for i in range(k):
                tid, _mid, has_quiz = seq[i]
                day = day + timedelta(days=rng.randint(1, 3), hours=rng.randint(0, 6))
                if day > NOW_REF:
                    day = NOW_REF - timedelta(hours=(k - i))
                first_visit = day - timedelta(minutes=rng.randint(15, 90))
                db.add(UserTopicProgress(
                    user_id=s.id, topic_id=tid, is_completed=True,
                    time_spent_seconds=rng.randint(300, 2400),
                    first_visited_at=first_visit, completed_at=day, last_accessed_at=day,
                ))
                completed.append((tid, has_quiz, day))

            # --- tema actual en progreso (no completado) ---
            if k < len(seq):
                tid = seq[k][0]
                vday = min(day + timedelta(days=rng.randint(1, 3)), NOW_REF)
                db.add(UserTopicProgress(
                    user_id=s.id, topic_id=tid, is_completed=False,
                    time_spent_seconds=rng.randint(60, 600),
                    first_visited_at=vday, last_accessed_at=vday,
                ))

            # --- intentos de quiz (solo temas con quiz) ---
            for tid, has_quiz, qday in completed:
                if not has_quiz:
                    continue
                perfect = rng.random() < 0.18
                score = 1.0 if perfect else round(rng.uniform(0.6, 0.95), 2)
                db.add(QuizAttempt(
                    user_id=s.id, topic_id=tid, score=score,
                    answers={"demo": True}, is_passed=score >= 0.6, attempted_at=qday,
                ))

            # --- chat (subconjunto con avance suficiente) -> logro Explorador ---
            if k >= 5 and rng.random() < 0.45:
                created_at = COURSE_START + timedelta(days=rng.randint(5, 40))
                sess = ChatSession(
                    user_id=s.id, title="Dudas de Kotlin",
                    created_at=created_at, last_message_at=created_at,
                )
                db.add(sess)
                await db.flush()
                t = created_at
                for _ in range(rng.randint(10, 16)):  # >=10 mensajes de usuario
                    t = t + timedelta(minutes=rng.randint(1, 8))
                    db.add(ChatMessage(
                        session_id=sess.id, user_id=s.id, role="user",
                        content=rng.choice(CHAT_QUESTIONS), created_at=t,
                    ))
                    t = t + timedelta(seconds=rng.randint(20, 90))
                    db.add(ChatMessage(
                        session_id=sess.id, user_id=s.id, role="assistant",
                        content="(respuesta del tutor IA — contenido demo)",
                        sources=[], created_at=t,
                    ))
                sess.last_message_at = t

            await db.flush()
            granted = await check_and_grant_achievements(s.id, db)
            total_badges += len(granted)
            created += 1

        await db.commit()
    await engine.dispose()

    print(f"Estudiantes con actividad creada: {created}")
    print(f"Omitidos (ya tenian progreso):    {skipped}")
    print(f"Niveles -> {level_counts}")
    print(f"Logros otorgados (total):         {total_badges}")
    print("\nRECORDATORIO: data demo. No es resultado del OE4.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera actividad demo para estudiantes.")
    ap.add_argument("--max-students", type=int, default=None, help="limita nº de estudiantes")
    ap.add_argument("--reset", action="store_true", help="borra y regenera la actividad demo")
    args = ap.parse_args()
    asyncio.run(main(args.max_students, args.reset))
