"""
Unit tests para app/services/scheduler_service.py.
Verifican el job de cleanup + el armado del scheduler (jobs registrados,
trigger y zona horaria).
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apscheduler.triggers.cron import CronTrigger

from app.services import scheduler_service


class TestCleanupExpiredQuizSessions:
    @pytest.mark.asyncio
    async def test_executes_delete_and_commits(self):
        result = MagicMock()
        result.rowcount = 5
        db = MagicMock()
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()

        # AsyncSessionLocal is used as a context manager → patch the ctx mgr factory
        session_cm = MagicMock()
        session_cm.__aenter__ = AsyncMock(return_value=db)
        session_cm.__aexit__ = AsyncMock(return_value=None)
        with patch.object(
            scheduler_service, "AsyncSessionLocal", return_value=session_cm
        ):
            count = await scheduler_service.cleanup_expired_quiz_sessions()

        assert count == 5
        db.execute.assert_awaited_once()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_nothing_to_clean(self):
        result = MagicMock()
        result.rowcount = 0
        db = MagicMock()
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()

        session_cm = MagicMock()
        session_cm.__aenter__ = AsyncMock(return_value=db)
        session_cm.__aexit__ = AsyncMock(return_value=None)
        with patch.object(
            scheduler_service, "AsyncSessionLocal", return_value=session_cm
        ):
            count = await scheduler_service.cleanup_expired_quiz_sessions()

        assert count == 0


class TestBuildScheduler:
    def test_registers_cleanup_job_with_cron_trigger(self):
        s = scheduler_service.build_scheduler()
        jobs = s.get_jobs()
        assert len(jobs) == 1
        job = jobs[0]
        assert job.id == "cleanup_expired_quiz_sessions"
        assert isinstance(job.trigger, CronTrigger)
        # Trigger fires at 03:15 UTC
        assert "hour='3'" in str(job.trigger)
        assert "minute='15'" in str(job.trigger)

    def test_scheduler_is_utc(self):
        s = scheduler_service.build_scheduler()
        assert str(s.timezone) == "UTC"

    def test_retention_constant_is_seven_days(self):
        # If this constant changes, update the cron + deploy guide.
        assert scheduler_service.AI_QUIZ_RETENTION_DAYS == 7
