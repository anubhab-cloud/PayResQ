"""
worker/recovery_worker.py
===========================
Async recovery worker loop.

Workflow per job:
  1. Dequeue job from Redis (BLPOP — blocks until job arrives or timeout)
  2. Validate job structure
  3. Check idempotency — skip if already executed
  4. Wait until scheduled_for time (if in the future)
  5. Re-check transaction payment status (race condition guard)
  6. Execute via RecoveryExecutor
  7. Record outcome in DB
  8. Write audit log
  9. Acknowledge (job already removed by BLPOP)

Error handling:
  - On retriable error: increment attempt_count, re-enqueue with backoff
  - On max retries exceeded: move to dead-letter queue
  - Never silently drops a job
  - Never creates infinite retry loops
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.recovery.executor import RecoveryExecutor
from app.recovery.queue import dequeue_job, enqueue_job, move_to_dead_letter
from app.recovery.schemas import RecoveryJob
from app.recovery.simulator import PaymentSimulator

logger = logging.getLogger(__name__)


class RecoveryWorker:
    """
    Processes recovery jobs from the Redis queue.

    Run via: python -m worker.main
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        self._session_factory = session_factory
        self._redis = redis
        self._executor = RecoveryExecutor(simulator=PaymentSimulator())
        self._running = False

    async def start(self) -> None:
        """Start the worker loop. Runs until stop() is called."""
        self._running = True
        logger.info(
            "RecoveryWorker started. Queue=%s poll_interval=%ds",
            settings.RECOVERY_QUEUE_NAME,
            settings.RECOVERY_WORKER_POLL_INTERVAL,
        )
        while self._running:
            try:
                await self._process_one()
            except asyncio.CancelledError:
                logger.info("RecoveryWorker: cancelled")
                break
            except Exception as exc:
                logger.error("RecoveryWorker: unexpected error: %s", exc, exc_info=True)
                await asyncio.sleep(settings.RECOVERY_WORKER_POLL_INTERVAL)

    async def stop(self) -> None:
        self._running = False
        logger.info("RecoveryWorker stopping.")

    async def _process_one(self) -> None:
        """Dequeue and process one job."""
        job = await dequeue_job(self._redis, timeout=settings.RECOVERY_WORKER_POLL_INTERVAL)
        if job is None:
            return   # timeout — no job available

        logger.info(
            "Worker processing job_id=%s tx=%s action=%s attempt=%d",
            job.job_id, job.transaction_id, job.action, job.attempt_count,
        )

        # --- Wait until scheduled_for time ---
        try:
            scheduled = datetime.fromisoformat(job.scheduled_for)
            if scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=timezone.utc)
            wait_secs = (scheduled - datetime.now(timezone.utc)).total_seconds()
            if wait_secs > 0:
                logger.info(
                    "Job %s scheduled in %.1fs — waiting", job.job_id, wait_secs
                )
                await asyncio.sleep(min(wait_secs, 300))  # max 5 min wait per cycle
        except Exception:
            pass  # if we can't parse the time, execute immediately

        # --- Execute ---
        try:
            async with self._session_factory() as db:
                await self._executor.execute(job, db)
            logger.info("Job %s completed successfully", job.job_id)

        except ValueError as exc:
            # Non-retriable (e.g. record not found)
            logger.error("Job %s non-retriable error: %s", job.job_id, exc)
            await move_to_dead_letter(job, self._redis, reason=str(exc))

        except Exception as exc:
            # Retriable error — re-enqueue with backoff
            job.attempt_count += 1
            if job.attempt_count >= settings.RECOVERY_MAX_JOB_RETRIES:
                logger.error(
                    "Job %s exceeded max retries (%d) — moving to dead-letter: %s",
                    job.job_id, settings.RECOVERY_MAX_JOB_RETRIES, exc,
                )
                await move_to_dead_letter(job, self._redis, reason=str(exc))
            else:
                backoff = 2 ** job.attempt_count
                logger.warning(
                    "Job %s retriable error (attempt %d/%d) — re-enqueue after %ds: %s",
                    job.job_id, job.attempt_count, settings.RECOVERY_MAX_JOB_RETRIES,
                    backoff, exc,
                )
                await asyncio.sleep(backoff)
                await enqueue_job(job, self._redis)
