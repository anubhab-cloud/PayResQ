"""
app/api/v1/agent.py
====================
Agent analysis API endpoints.

POST /api/v1/agent/analyze/{transaction_id}
  - Runs the full agent + policy pipeline
  - Enqueues job if approved
  - Returns decision + policy outcome + job info
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.db import get_db
from app.core.redis import get_redis
from app.agents.providers import get_provider
from app.agents.recovery_agent import RecoveryAgent
from app.policies.engine import PolicyEngine
from app.services.recovery_service import RecoveryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post(
    "/analyze/{transaction_id}",
    summary="Run AI recovery agent for a failed transaction",
)
async def analyze_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Runs the full pipeline:
    1. Agent gathers context and produces a structured decision
    2. Policy engine validates the decision
    3. If ALLOW → creates RecoveryAction + enqueues job → worker executes
    4. If HUMAN_APPROVAL → creates RecoveryAction in PENDING state
    5. If BLOCK → records cancelled action + reason

    Returns the full decision, policy outcome, and job information.

    NOTE: Uses LLM_PROVIDER from settings (default: 'fake' — no API key required).
    """
    try:
        provider = get_provider()
        agent = RecoveryAgent(provider=provider)
        policy_engine = PolicyEngine()
        service = RecoveryService(agent=agent, policy_engine=policy_engine)

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

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Agent analyze error for tx=%s: %s", transaction_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent analysis failed: {str(exc)}",
        )
