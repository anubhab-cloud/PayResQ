"""
worker/main.py
================
Entry point for the PayResQ recovery worker process.

Run with:
    python -m worker.main

This is a separate process from the FastAPI server.
It connects to the same PostgreSQL database and Redis instance.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import signal
from pathlib import Path

# Ensure repo root is on the path when running as a module
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from redis.asyncio import from_url

from app.core.config import settings
from worker.recovery_worker import RecoveryWorker

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker.main")


async def run() -> None:
    logger.info("=== PayResQ Recovery Worker Starting ===")
    logger.info("Queue: %s | DB: %s", settings.RECOVERY_QUEUE_NAME, settings.POSTGRES_DB)

    # Database session factory
    engine = create_async_engine(settings.async_database_url, echo=False)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Redis connection
    redis = from_url(
        settings.async_redis_url,
        encoding="utf-8",
        decode_responses=True,
        protocol=2,
    )

    worker = RecoveryWorker(session_factory=session_factory, redis=redis)

    # Graceful shutdown on SIGTERM/SIGINT
    loop = asyncio.get_running_loop()

    def _shutdown(signum, frame):
        logger.info("Received signal %s — shutting down worker", signum)
        asyncio.create_task(worker.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(worker.stop()))
        except NotImplementedError:
            # Windows doesn't support add_signal_handler for all signals
            signal.signal(sig, _shutdown)

    try:
        await worker.start()
    finally:
        await redis.close()
        await engine.dispose()
        logger.info("=== PayResQ Recovery Worker Stopped ===")


if __name__ == "__main__":
    asyncio.run(run())
