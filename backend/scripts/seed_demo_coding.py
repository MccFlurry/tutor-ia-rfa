"""Genera ENVIOS de codigo (coding_submissions) DEMO para poblar el historial de
desafios de programacion en los dashboards. Un alumno recibe un envio por cada
desafio cuyo tema ya completo.

============================  ADVERTENCIA  ============================
DATA DEMO / DEMOSTRACION. No son envios reales de los estudiantes ni
evidencia del OE4. Complementa seed_demo_activity.py.
=======================================================================

Determinista (semilla fija), idempotente (omite si ya hay envio para ese par
alumno-desafio), timestamps anclados a la fecha de completado del tema.

Uso (dentro del contenedor backend, o local):
    python scripts/seed_demo_coding.py
    python scripts/seed_demo_coding.py --reset
"""
from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
SEED = 42

FALLBACK_CODE = """fun resolver(input: String): String {
    // Solucion del estudiante (demo)
    val resultado = input.trim().lowercase()
    return resultado
}"""

# Retroalimentacion por banda de puntaje (0-100).
BANDS = [
    (85, "Excelente. La solucion es correcta, legible y usa Kotlin de forma idiomatica.",
        ["Logica correcta", "Codigo legible", "Uso idiomatico de Kotlin"],
        ["Podrias agregar manejo de errores para entradas invalidas"]),
    (70, "Buen trabajo. Resuelve el caso principal; hay detalles menores por pulir.",
        ["Resuelve el caso principal", "Estructura clara"],
        ["Mejora los nombres de variables", "Considera los casos borde"]),
    (60, "Aprobado. Funciona, pero conviene refactorizar y validar la entrada.",
        ["Compila y cumple el objetivo basico"],
        ["Refactoriza para legibilidad", "Falta validacion de entrada"]),
    (0, "Aun no aprueba. Revisa la logica principal y los casos faltantes.",
        ["Intento valido, va por buen camino"],
        ["Corrige la logica central", "Faltan casos", "Revisa el manejo de null"]),
]


def band_for(score: float) -> tuple:
    for threshold, fb, st, imp in BANDS:
        if score >= threshold:
            return fb, st, imp
    return BANDS[-1][1:]


async def main(reset: bool) -> None:
    sys.path.insert(0, str(BACKEND_DIR))
    from sqlalchemy import delete, func, select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.models.coding import CodingChallenge, CodingSubmission
    from app.models.progress import UserTopicProgress
    from app.models.user import User

    print("=" * 60)
    print("SEED DE ENVIOS DE CODIGO DEMO  (NO es evidencia OE4)")
    print(f"BD destino: {settings.DATABASE_URL.split('@')[-1]}")
    print("=" * 60)

    rng = random.Random(SEED)
    engine = create_async_engine(settings.DATABASE_URL)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        challenges = (await db.execute(select(CodingChallenge))).scalars().all()
        if not challenges:
            print("No hay coding_challenges en la BD. Nada que poblar.")
            return
        by_topic: dict[int, list] = {}
        for ch in challenges:
            by_topic.setdefault(ch.topic_id, []).append(ch)

        students = (
            await db.execute(select(User).where(User.role == "student").order_by(User.email))
        ).scalars().all()

        # progreso completado: {(user_id, topic_id): completed_at}
        prog_rows = (
            await db.execute(
                select(UserTopicProgress.user_id, UserTopicProgress.topic_id,
                       UserTopicProgress.completed_at)
                .where(UserTopicProgress.is_completed == True)  # noqa: E712
            )
        ).all()
        completed: dict = {(u, t): c for (u, t, c) in prog_rows}

        if reset:
            await db.execute(delete(CodingSubmission))
            await db.flush()

        created = skipped = 0
        for s in students:
            for ch in challenges:
                done_at = completed.get((s.id, ch.topic_id))
                if done_at is None:
                    continue  # alumno no completo el tema del desafio
                exists = await db.scalar(
                    select(func.count(CodingSubmission.id)).where(
                        CodingSubmission.user_id == s.id,
                        CodingSubmission.challenge_id == ch.id,
                    )
                )
                if exists:
                    skipped += 1
                    continue
                if rng.random() > 0.72:  # no todos entregan todo
                    continue

                # puntaje 0-100, mayoria aprobado, algunos altos/bajos
                roll = rng.random()
                if roll < 0.25:
                    score = float(rng.randint(85, 100))
                elif roll < 0.70:
                    score = float(rng.randint(70, 84))
                elif roll < 0.90:
                    score = float(rng.randint(60, 69))
                else:
                    score = float(rng.randint(40, 59))
                fb, st, imp = band_for(score)
                code = (ch.solution_code or FALLBACK_CODE)[:1500]
                submitted = done_at + timedelta(minutes=rng.randint(5, 240))
                db.add(CodingSubmission(
                    user_id=s.id, challenge_id=ch.id, code=code,
                    score=score, feedback=fb, strengths=st, improvements=imp,
                    submitted_at=submitted,
                ))
                created += 1
        await db.commit()
    await engine.dispose()

    print(f"Envios de codigo creados: {created}")
    print(f"Omitidos (ya existian):   {skipped}")
    print("\nRECORDATORIO: data demo. No es resultado del OE4.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera envios de codigo demo.")
    ap.add_argument("--reset", action="store_true", help="borra y regenera los envios demo")
    args = ap.parse_args()
    asyncio.run(main(args.reset))
