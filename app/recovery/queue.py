"""
app/recovery/queue.py
======================
Redis-backed recovery job queue.

Uses a Redis list (RPUSH / BLPOP) as a simple, reliable FIFO queue.
Redis is the transport layer only — PostgreSQL is the persistent source of truth.

Queue key:   settings.RECOVERY_QUEUE_NAME  (default: "recovery:jobs")
Dead-letter: settings.RECOVERY_DEAD_LETTER_KEY  (default: "recovery:dead")
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from redis.asyncio import Redis

from app.core.config import settings
from app.recovery.schemas import RecoveryJob

logger = logging.getLogger(__name__)


async def enqueue_job(job: RecoveryJob, redis: Redis) -> None:
    """Serialize and push a RecoveryJob to the tail of the queue."""
    payload = job.model_dump_json()
    await redis.rpush(settings.RECOVERY_QUEUE_NAME, payload)
    logger.info(
        "Enqueued recovery job: job_id=%s tx=%s action=%s",
        job.job_id,
        job.transaction_id,
        job.action,
    )


async def dequeue_job(redis: Redis, timeout: int = 5) -> Optional[RecoveryJob]:
    """
    Block-pop a job from the queue. Returns None on timeout.

    Args:
        timeout: Seconds to wait for a job before returning None.
    """
    result = await redis.blpop(settings.RECOVERY_QUEUE_NAME, timeout=timeout)
    if result is None:
        return None

    _, payload = result
    try:
        data = json.loads(payload)
        job = RecoveryJob.model_validate(data)
        logger.info(
            "Dequeued recovery job: job_id=%s tx=%s action=%s",
            job.job_id,
            job.transaction_id,
            job.action,
        )
        return job
    except Exception as exc:
        logger.error("Failed to deserialize job from queue: %s | payload=%s", exc, payload)
        # Move malformed payload to dead-letter queue
        await redis.rpush(settings.RECOVERY_DEAD_LETTER_KEY, payload)
        return None


async def move_to_dead_letter(job: RecoveryJob, redis: Redis, reason: str) -> None:
    """Move a permanently failed job to the dead-letter queue."""
    payload = json.dumps({**job.model_dump(), "dead_letter_reason": reason})
    await redis.rpush(settings.RECOVERY_DEAD_LETTER_KEY, payload)
    logger.warning(
        "Job moved to dead-letter: job_id=%s tx=%s reason=%s",
        job.job_id,
        job.transaction_id,
        reason,
    )


async def get_queue_length(redis: Redis) -> int:
    """Return current number of pending jobs in the queue."""
    return await redis.llen(settings.RECOVERY_QUEUE_NAME)


async def get_dead_letter_length(redis: Redis) -> int:
    """Return number of permanently failed jobs in dead-letter queue."""
    return await redis.llen(settings.RECOVERY_DEAD_LETTER_KEY)
