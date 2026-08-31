"""
app/recovery/schemas.py
========================
Pydantic schemas for recovery jobs.

RecoveryJob is the serialized message that travels through Redis.
It contains everything the worker needs to execute the action safely.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class RecoveryJob(BaseModel):
    """
    A serialized recovery job stored in the Redis queue.

    Redis is the transport layer. PostgreSQL (RecoveryAction) is the
    persistent source of truth. The job references the DB record
    via recovery_action_id.
    """
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str
    recovery_action_id: str
    action: str                    # RecoveryActionType value
    delay_minutes: int = 0
    agent_confidence: float = 0.0
    agent_reason: str = ""
    idempotency_key: str           # sha256(recovery_action_id) — set at creation
    scheduled_for: str             # ISO datetime string
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    attempt_count: int = 0         # worker retry counter
