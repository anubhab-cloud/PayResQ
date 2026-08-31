"""
app/api/v1/recovery.py
========================
Recovery management API endpoints.

POST /api/v1/recovery/policy-check/{transaction_id}
POST /api/v1/recovery/execute/{transaction_id}
GET  /api/v1/recovery/{recovery_action_id}
GET  /api/v1/transactions/{transaction_id}/audit
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.db import get_db
from app.core.redis import get_redis
from app.agents.providers import get_provider
from app.agents.recovery_agent import RecoveryAgent
from app.agents.schemas import AgentDecision
from app.models.recovery_action import RecoveryAction
from app.models.audit_log import AuditLog
from app.policies.engine import PolicyEngine
from app.services.recovery_service import RecoveryService
from app.services.transaction_service import get_transaction_by_id, get_recovery_actions

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recovery"])


# -----------------------------------------------------------------------
# Request/Response schemas
# -----------------------------------------------------------------------

class PolicyCheckRequest(BaseModel):
    action: str
    delay_minutes: int | None = None
    confidence: float = 0.8
    reason: str = "Manual policy check request"


# -----------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------

@router.post(
    "/recovery/policy-check/{transaction_id}",
    summary="Run deterministic policy check for a proposed recovery action",
)
async def policy_check(
    transaction_id: str,
    request: PolicyCheckRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Validates a proposed recovery action against all policy rules.
    Returns ALLOW, BLOCK, or HUMAN_APPROVAL with a reason.
    Does not create any DB records or enqueue jobs.
    """
    from app.models.enums import RecoveryActionType
    try:
        action = RecoveryActionType(request.action.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {request.action}",
        )

    decision = AgentDecision(
        action=action,
        delay_minutes=request.delay_minutes,
        confidence=request.confidence,
        reason=request.reason,
        transaction_id=transaction_id,
    )

    service = RecoveryService(agent=None, policy_engine=PolicyEngine())
    result = await service.policy_check_only(transaction_id, decision, db)
    return result.model_dump()


@router.post(
    "/recovery/execute/{transaction_id}",
    summary="Full Agent→Policy→Queue pipeline for a transaction",
)
async def execute_recovery(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Runs the complete recovery pipeline:
    1. Agent analyzes the transaction
    2. Policy engine validates the decision
    3. If ALLOW → enqueue job for worker execution
    4. If HUMAN_APPROVAL → record for manual review
    5. If BLOCK → record with reason

    IMPORTANT: This endpoint does NOT directly execute the recovery action.
    Execution happens asynchronously in the worker process.
    """
    provider = get_provider()
    agent = RecoveryAgent(provider=provider)
    service = RecoveryService(agent=agent, policy_engine=PolicyEngine())

    result = await service.process_transaction(
        transaction_id=transaction_id,
        db=db,
        redis=redis,
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    return result


@router.get(
    "/recovery/{recovery_action_id}",
    summary="Get current recovery action status",
)
async def get_recovery_status(
    recovery_action_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns current state of a recovery action including outcome if available."""
    result = await db.execute(
        select(RecoveryAction).where(RecoveryAction.id == recovery_action_id)
    )
    ra = result.scalar_one_or_none()
    if ra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery action {recovery_action_id} not found",
        )

    outcome_data: dict[str, Any] = {}
    if ra.outcome:
        outcome_data = {
            "success": ra.outcome.success,
            "recovered_amount": float(ra.outcome.recovered_amount or 0),
            "failure_reason": ra.outcome.failure_reason,
            "completed_at": ra.outcome.completed_at.isoformat() if ra.outcome.completed_at else None,
        }

    return {
        "recovery_action_id": ra.id,
        "transaction_id": ra.transaction_id,
        "action_type": ra.action_type,
        "status": ra.status,
        "confidence": ra.confidence,
        "reason": ra.reason,
        "scheduled_for": ra.scheduled_for.isoformat() if ra.scheduled_for else None,
        "executed_at": ra.executed_at.isoformat() if ra.executed_at else None,
        "created_at": ra.created_at.isoformat() if ra.created_at else None,
        "outcome": outcome_data if outcome_data else None,
    }


@router.get(
    "/transactions/{transaction_id}/audit",
    summary="Get audit trail for a transaction",
)
async def get_audit_trail(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns all audit log entries for a transaction in chronological order."""
    tx = await get_transaction_by_id(db, transaction_id)
    if tx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.transaction_id == transaction_id)
        .order_by(AuditLog.created_at)
    )
    logs = result.scalars().all()

    return {
        "transaction_id": transaction_id,
        "audit_count": len(logs),
        "audit_trail": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "actor_type": log.actor_type,
                "action": log.action,
                "reason": log.reason,
                "metadata": log.metadata_,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }
