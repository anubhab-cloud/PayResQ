"""
app/recovery/executor.py
==========================
Recovery executor — executes pre-approved recovery actions.

The executor:
  1. Verifies the transaction is still in a recoverable state
  2. Checks idempotency (skips if already completed)
  3. Runs the PaymentSimulator
  4. Persists RecoveryOutcome in DB
  5. Updates RecoveryAction.status and executed_at
  6. Updates Transaction.status if recovery succeeded
  7. Writes an AuditLog entry

The executor does NOT:
  - make business decisions
  - call the LLM
  - run policy checks (those already happened upstream)
  - execute actions that bypassed the policy engine
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.recovery_action import RecoveryAction
from app.models.recovery_outcome import RecoveryOutcome
from app.models.audit_log import AuditLog
from app.models.enums import RecoveryActionStatus, ActorType
from app.recovery.schemas import RecoveryJob
from app.recovery.simulator import PaymentSimulator, SimulationResult

logger = logging.getLogger(__name__)


class RecoveryExecutor:
    """Executes a pre-approved RecoveryJob."""

    def __init__(self, simulator: PaymentSimulator | None = None) -> None:
        self._simulator = simulator or PaymentSimulator()

    async def execute(self, job: RecoveryJob, db: AsyncSession) -> SimulationResult:
        """
        Execute a recovery job.

        Returns the SimulationResult. Writes outcome to DB regardless of success/failure.

        Raises:
            ValueError: If the job references a missing RecoveryAction or Transaction.
        """
        logger.info(
            "Executor: starting job_id=%s tx=%s action=%s",
            job.job_id, job.transaction_id, job.action,
        )

        # --- Load RecoveryAction ---
        ra_result = await db.execute(
            select(RecoveryAction).where(RecoveryAction.id == job.recovery_action_id)
        )
        recovery_action = ra_result.scalar_one_or_none()
        if recovery_action is None:
            raise ValueError(f"RecoveryAction {job.recovery_action_id} not found")

        # --- Idempotency check ---
        if str(recovery_action.status).upper() == RecoveryActionStatus.COMPLETED.value:
            logger.warning(
                "Idempotency: job_id=%s already COMPLETED — skipping", job.job_id
            )
            outcome_result = await db.execute(
                select(RecoveryOutcome).where(
                    RecoveryOutcome.recovery_action_id == job.recovery_action_id
                )
            )
            existing_outcome = outcome_result.scalar_one_or_none()
            if existing_outcome:
                return SimulationResult(
                    success=existing_outcome.success,
                    recovered_amount=float(existing_outcome.recovered_amount or 0),
                    failure_reason=existing_outcome.failure_reason,
                    simulator_note="Idempotency: already executed",
                )
            return SimulationResult(
                success=False,
                recovered_amount=0.0,
                failure_reason="Idempotency: action already completed but no outcome record found",
                simulator_note="Idempotency skip",
            )

        # --- Load Transaction ---
        tx_result = await db.execute(
            select(Transaction).where(Transaction.id == job.transaction_id)
        )
        transaction = tx_result.scalar_one_or_none()
        if transaction is None:
            raise ValueError(f"Transaction {job.transaction_id} not found")

        # --- Payment status re-check (race condition guard) ---
        if str(transaction.status).upper() == "SUCCESS":
            logger.info(
                "Transaction %s already SUCCESS — cancelling recovery job %s",
                job.transaction_id, job.job_id,
            )
            await self._update_recovery_action(
                db, recovery_action,
                status=RecoveryActionStatus.CANCELLED,
            )
            await self._write_audit(
                db, job,
                event_type="RECOVERY_SKIPPED",
                action="cancel_recovery",
                reason="Transaction already successful — recovery cancelled",
            )
            await db.commit()
            return SimulationResult(
                success=False,
                recovered_amount=0.0,
                failure_reason="Transaction already SUCCESS — recovery not needed",
            )

        # --- Mark as EXECUTING ---
        await self._update_recovery_action(
            db, recovery_action, status=RecoveryActionStatus.EXECUTING
        )
        await db.commit()

        # --- Build simulator context ---
        sim_context: dict[str, Any] = {
            "amount": float(transaction.amount),
            "delay_minutes": job.delay_minutes,
        }

        # --- Execute via simulator ---
        sim_result = self._simulator.execute(action=job.action, context=sim_context)

        # --- Persist outcome ---
        outcome = RecoveryOutcome(
            recovery_action_id=job.recovery_action_id,
            success=sim_result.success,
            recovered_amount=sim_result.recovered_amount if sim_result.success else 0,
            failure_reason=sim_result.failure_reason,
        )
        db.add(outcome)

        # --- Update RecoveryAction status ---
        final_status = (
            RecoveryActionStatus.COMPLETED if sim_result.success else RecoveryActionStatus.FAILED
        )
        now = datetime.now(timezone.utc)
        await self._update_recovery_action(
            db, recovery_action,
            status=final_status,
            executed_at=now,
        )

        # --- Update Transaction status if recovered ---
        if sim_result.success:
            transaction.status = "SUCCESS"
            transaction.updated_at = now
            db.add(transaction)

        # --- Write audit log ---
        await self._write_audit(
            db, job,
            event_type="RECOVERY_EXECUTED",
            action=job.action,
            reason=(
                f"Simulation result: {'SUCCESS' if sim_result.success else 'FAILED'}. "
                f"{sim_result.failure_reason or ''}"
            ),
            metadata={
                "job_id": job.job_id,
                "idempotency_key": job.idempotency_key,
                "success": sim_result.success,
                "recovered_amount": sim_result.recovered_amount,
                "simulator_note": sim_result.simulator_note,
            },
        )

        await db.commit()

        logger.info(
            "Executor: job_id=%s tx=%s action=%s success=%s amount=%.2f",
            job.job_id, job.transaction_id, job.action,
            sim_result.success, sim_result.recovered_amount,
        )
        return sim_result

    async def _update_recovery_action(
        self,
        db: AsyncSession,
        ra: RecoveryAction,
        status: RecoveryActionStatus,
        executed_at: datetime | None = None,
    ) -> None:
        ra.status = status
        if executed_at:
            ra.executed_at = executed_at
        db.add(ra)

    async def _write_audit(
        self,
        db: AsyncSession,
        job: RecoveryJob,
        event_type: str,
        action: str,
        reason: str,
        metadata: dict | None = None,
    ) -> None:
        log = AuditLog(
            transaction_id=job.transaction_id,
            event_type=event_type,
            actor_type=ActorType.SYSTEM,
            action=action,
            reason=reason,
            metadata_=metadata or {},
        )
        db.add(log)
