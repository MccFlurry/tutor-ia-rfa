"""
scheduler_service.py — APScheduler jobs ejecutándose junto a la API.

Jobs:
- cleanup_expired_quiz_sessions: borra AIQuizSession submitted hace > 7 días
  (ventana de auditoría suficiente para Sprint 8 SUS sin acumular basura).

Se monta vía FastAPI lifespan en `app.main`. En dev (uvicorn --reload con
N workers > 1) APScheduler corre en CADA worker; en prod usamos 2 workers
y el job es idempotente (DELETE por timestamp), así que duplicar es seguro.
"""

from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.models.ai_quiz_session import AIQuizSession
from app.utils.logger import logger


AI_QUIZ_RETENTION_DAYS = 7


async def cleanup_expired_quiz_sessions() -> int:
    """Delete AIQuizSession rows submitted more than N days ago.

    Returns the count of rows deleted (for observability).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=AI_QUIZ_RETENTION_DAYS)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(AIQuizSession).where(
                AIQuizSession.is_submitted == True,
                AIQuizSession.submitted_at.is_not(None),
                AIQuizSession.submitted_at < cutoff,
            )
        )
        await db.commit()
        count = result.rowcount or 0
        if count:
            logger.info(f"[scheduler] AIQuizSession cleanup: {count} filas borradas (>{AI_QUIZ_RETENTION_DAYS}d)")
        return count


def build_scheduler() -> AsyncIOScheduler:
    """Build the scheduler with all jobs registered. Caller must .start()."""
    scheduler = AsyncIOScheduler(timezone="UTC")
    # Daily at 03:15 UTC (~10:15 PM Lima the previous day, off-peak).
    scheduler.add_job(
        cleanup_expired_quiz_sessions,
        trigger=CronTrigger(hour=3, minute=15),
        id="cleanup_expired_quiz_sessions",
        name="Cleanup AIQuizSession >7d",
        replace_existing=True,
        misfire_grace_time=3600,  # if scheduler down at trigger time, run within 1h
    )
    return scheduler
