"""
app/services/recovery_service.py
===================================
Orchestration service for the Agent → Policy → Queue pipeline.

Responsibilities:
  - Run the agent to get a decision
  - Run the policy engine to validate the decision
  - If ALLOW: create RecoveryAction in DB, enqueue RecoveryJob in Redis
  - If HUMAN_APPROVAL: create RecoveryAction with PENDING status, do not enqueue
  - If BLOCK: record a CANCELLED RecoveryAction and audit log
  - Write audit logs for all decisions
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.recovery_agent import RecoveryAgent
from app.agents.schemas import AgentDecision
from app.models.recovery_action import RecoveryAction
from app.models.audit_log import AuditLog
from app.models.enums import RecoveryActionStatus, ActorType
from app.policies.engine import PolicyEngine
from app.policies.schemas import PolicyDecision, PolicyOutcome
from app.recovery.queue import enqueue_job
from app.recovery.schemas import RecoveryJob
from app.services.transaction_service import (
    get_transaction_by_id,
    get_recovery_actions,
)

logger = logging.getLogger(__name__)


class RecoveryService:
    """
    Orchestrates: Agent → Policy → Queue.

    Does not execute recovery directly — execution is handled by the worker.
    """

    def __init__(self, agent: RecoveryAgent, policy_engine: PolicyEngine) -> None:
        self._agent = agent
        self._policy = policy_engine

    async def process_transaction(
        self,
        transaction_id: str,
        db: AsyncSession,
        redis: Redis,
    ) -> dict:
        """
        Full pipeline: analyze → policy check → enqueue or record.

        Returns a summary dict with decision, policy outcome, and job info.
        """
        # --- Load transaction ---
        transaction = await get_transaction_by_id(db, transaction_id)
        if transaction is None:
            return {"error": f"Transaction {transaction_id} not found"}

        existing_actions = await get_recovery_actions(db, transaction_id)

        # --- Agent analysis ---
        decision: AgentDecision = await self._agent.analyze(transaction_id, db)

        # --- Policy evaluation ---
        policy_result: PolicyDecision = self._policy.evaluate(
            decision, transaction, existing_actions
        )

        # --- Audit: agent decision ---
        await self._audit(
            db,
            transaction_id=transaction_id,
            event_type="AGENT_DECISION",
            actor_type=ActorType.AI_AGENT,
            action=decision.action.value,
            reason=decision.reason,
            metadata={
                "action": decision.action.value,
                "confidence": decision.confidence,
                "delay_minutes": decision.delay_minutes,
                "root_cause": decision.root_cause,
                "selected_probability": decision.selected_probability,
                "provider": self._agent._provider.provider_name,
                "model_version": decision.model_version,
            },
        )

        # --- Audit: policy decision ---
        await self._audit(
            db,
            transaction_id=transaction_id,
            event_type="POLICY_DECISION",
            actor_type=ActorType.POLICY_ENGINE,
            action=policy_result.outcome.value,
            reason=policy_result.reason,
            metadata={
                "outcome": policy_result.outcome.value,
                "rule_triggered": policy_result.rule_triggered,
                "policy_version": policy_result.policy_version,
            },
        )

        if policy_result.outcome == PolicyOutcome.ALLOW:
            recovery_action, job = await self._create_and_enqueue(
                db, redis, transaction_id, decision, policy_result
            )
            await db.commit()
            return {
                "transaction_id": transaction_id,
                "agent_decision": decision.model_dump(),
                "policy_outcome": policy_result.outcome.value,
                "policy_reason": policy_result.reason,
                "recovery_action_id": recovery_action.id,
                "job_id": job.job_id,
                "status": "ENQUEUED",
            }

        elif policy_result.outcome == PolicyOutcome.HUMAN_APPROVAL:
            recovery_action = await self._create_recovery_action(
                db, transaction_id, decision,
                status=RecoveryActionStatus.PENDING,
            )
            await db.commit()
            return {
                "transaction_id": transaction_id,
                "agent_decision": decision.model_dump(),
                "policy_outcome": policy_result.outcome.value,
                "policy_reason": policy_result.reason,
                "recovery_action_id": recovery_action.id,
                "status": "AWAITING_HUMAN_APPROVAL",
            }

        else:  # BLOCK
            recovery_action = await self._create_recovery_action(
                db, transaction_id, decision,
                status=RecoveryActionStatus.CANCELLED,
            )
            await db.commit()
            return {
                "transaction_id": transaction_id,
                "agent_decision": decision.model_dump(),
                "policy_outcome": policy_result.outcome.value,
                "policy_reason": policy_result.reason,
                "recovery_action_id": recovery_action.id,
                "status": "BLOCKED",
            }

    async def policy_check_only(
        self,
        transaction_id: str,
        decision: AgentDecision,
        db: AsyncSession,
    ) -> PolicyDecision:
        """Run policy check only — does not create DB records or enqueue jobs."""
        transaction = await get_transaction_by_id(db, transaction_id)
        if transaction is None:
            from app.policies.schemas import PolicyOutcome
            return PolicyDecision(
                outcome=PolicyOutcome.BLOCK,
                reason=f"Transaction {transaction_id} not found",
                rule_triggered="transaction_not_found",
            )
        existing_actions = await get_recovery_actions(db, transaction_id)
        return self._policy.evaluate(decision, transaction, existing_actions)

    async def _create_recovery_action(
        self,
        db: AsyncSession,
        transaction_id: str,
        decision: AgentDecision,
        status: RecoveryActionStatus,
    ) -> RecoveryAction:
        delay = decision.delay_minutes
        scheduled_for = None
        if delay and delay > 0:
            scheduled_for = datetime.now(timezone.utc) + timedelta(minutes=delay)

        ra = RecoveryAction(
            transaction_id=transaction_id,
            action_type=decision.action,
            status=status,
            reason=decision.reason,
            confidence=decision.confidence,
            scheduled_for=scheduled_for,
        )
        db.add(ra)
        await db.flush()   # get id without full commit
        return ra

    async def _create_and_enqueue(
        self,
        db: AsyncSession,
        redis: Redis,
        transaction_id: str,
        decision: AgentDecision,
        policy_result: PolicyDecision,
    ):
        ra = await self._create_recovery_action(
            db, transaction_id, decision, status=RecoveryActionStatus.APPROVED
        )

        idempotency_key = hashlib.sha256(ra.id.encode()).hexdigest()
        delay = decision.delay_minutes or 0
        scheduled_for = (
            datetime.now(timezone.utc) + timedelta(minutes=delay)
        ).isoformat()

        job = RecoveryJob(
            transaction_id=transaction_id,
            recovery_action_id=ra.id,
            action=decision.action.value,
            delay_minutes=delay,
            agent_confidence=decision.confidence,
            agent_reason=decision.reason,
            idempotency_key=idempotency_key,
            scheduled_for=scheduled_for,
        )

        await enqueue_job(job, redis)
        return ra, job

    async def _audit(
        self,
        db: AsyncSession,
        transaction_id: str,
        event_type: str,
        actor_type: ActorType,
        action: str,
        reason: str,
        metadata: Optional[dict] = None,
    ) -> None:
        log = AuditLog(
            transaction_id=transaction_id,
            event_type=event_type,
            actor_type=actor_type,
            action=action,
            reason=reason,
            metadata_=metadata or {},
        )
        db.add(log)
