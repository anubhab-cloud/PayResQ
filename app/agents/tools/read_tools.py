"""
app/agents/tools/read_tools.py
================================
Bounded read-only tools for the recovery agent.

Each tool:
  - validates its input
  - returns a structured dict (not raw ORM objects)
  - fails gracefully (returns {"error": "..."} on exception)
  - never exposes DB credentials or internal implementation details

The LLM/agent receives ONLY the output of these tools — never direct
database access, credentials, or arbitrary query capability.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.payment_attempt import PaymentAttempt
from app.models.failure_event import FailureEvent
from app.models.recovery_action import RecoveryAction
from app.models.recovery_outcome import RecoveryOutcome

logger = logging.getLogger(__name__)


async def get_transaction(transaction_id: str, db: AsyncSession) -> dict[str, Any]:
    """Return core transaction details."""
    try:
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        tx = result.scalar_one_or_none()
        if tx is None:
            return {"error": f"Transaction {transaction_id} not found"}
        return {
            "transaction_id": tx.id,
            "merchant_id": tx.merchant_id,
            "customer_id": tx.customer_id,
            "amount": float(tx.amount),
            "currency": tx.currency,
            "status": tx.status,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
    except Exception as exc:
        logger.error("get_transaction error: %s", exc)
        return {"error": str(exc)}


async def get_customer_history(customer_id: str, db: AsyncSession) -> dict[str, Any]:
    """Return customer historical payment statistics."""
    try:
        cust_result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = cust_result.scalar_one_or_none()
        if customer is None:
            return {"error": f"Customer {customer_id} not found"}

        # Compute stats from transactions
        tx_result = await db.execute(
            select(Transaction).where(Transaction.customer_id == customer_id)
        )
        transactions = tx_result.scalars().all()
        total = len(transactions)
        successes = sum(1 for t in transactions if t.status == "SUCCESS")
        amounts = [float(t.amount) for t in transactions]

        return {
            "customer_id": customer_id,
            "name": customer.name,
            "total_transactions": total,
            "successful_transactions": successes,
            "success_rate": round(successes / total, 3) if total > 0 else 0.5,
            "average_amount": round(sum(amounts) / len(amounts), 2) if amounts else 0.0,
            "failed_transactions": total - successes,
        }
    except Exception as exc:
        logger.error("get_customer_history error: %s", exc)
        return {"error": str(exc)}


async def get_failure_context(transaction_id: str, db: AsyncSession) -> dict[str, Any]:
    """Return failure context from the last payment attempt."""
    try:
        attempts_result = await db.execute(
            select(PaymentAttempt)
            .where(PaymentAttempt.transaction_id == transaction_id)
            .order_by(PaymentAttempt.attempt_number.desc())
        )
        attempts = attempts_result.scalars().all()
        if not attempts:
            return {"error": "No payment attempts found"}

        last = attempts[0]
        failed_attempts = [a for a in attempts if a.status == "FAILED"]

        # Get failure event for last failed attempt
        failure_event_data: dict = {}
        if last.status == "FAILED":
            fe_result = await db.execute(
                select(FailureEvent)
                .where(FailureEvent.payment_attempt_id == last.id)
                .limit(1)
            )
            fe = fe_result.scalar_one_or_none()
            if fe:
                failure_event_data = {
                    "event_type": fe.event_type,
                    "failure_code": fe.failure_code,
                    "metadata": fe.metadata_ or {},
                }

        return {
            "transaction_id": transaction_id,
            "total_attempts": len(attempts),
            "failed_attempts": len(failed_attempts),
            "last_attempt_number": last.attempt_number,
            "last_bank": last.bank,
            "last_payment_method": last.payment_method,
            "last_failure_reason": last.failure_reason,
            "last_attempt_status": last.status,
            "last_attempted_at": last.attempted_at.isoformat() if last.attempted_at else None,
            "failure_event": failure_event_data,
        }
    except Exception as exc:
        logger.error("get_failure_context error: %s", exc)
        return {"error": str(exc)}


async def get_recovery_predictions(transaction_id: str, db: AsyncSession) -> dict[str, Any]:
    """
    Return XGBoost recovery probability predictions for all candidate actions.
    Requires the trained model artifact to exist. Falls back gracefully if not available.
    """
    try:
        # Get transaction context needed for prediction
        tx_ctx = await get_transaction(transaction_id, db)
        if "error" in tx_ctx:
            return tx_ctx

        failure_ctx = await get_failure_context(transaction_id, db)

        context = {
            "amount": tx_ctx.get("amount", 1000),
            "payment_method": failure_ctx.get("last_payment_method", "UNKNOWN"),
            "bank": failure_ctx.get("last_bank", "UNKNOWN"),
            "failure_reason": failure_ctx.get("last_failure_reason", "UNKNOWN"),
            "attempt_number": failure_ctx.get("last_attempt_number", 1),
            "retry_count": max(failure_ctx.get("failed_attempts", 1) - 1, 0),
        }

        from ml.services.prediction_service import prediction_service
        if not prediction_service.is_loaded:
            try:
                prediction_service.load()
            except FileNotFoundError:
                return {
                    "predictions": {
                        "RETRY_NOW": 0.25,
                        "RETRY_AFTER_DELAY": 0.60,
                        "SEND_PAYMENT_LINK": 0.45,
                        "CHANGE_PAYMENT_METHOD": 0.50,
                    },
                    "note": "Model not available — using baseline estimates",
                    "model_version": "fallback",
                }

        result = prediction_service.predict(context)
        return {
            "transaction_id": transaction_id,
            "predictions": result["predictions"],
            "recommended_action": result["recommended_action"],
            "model_version": result.get("model_version", "unknown"),
            "note": result.get("note", ""),
        }
    except Exception as exc:
        logger.error("get_recovery_predictions error: %s", exc)
        return {"error": str(exc)}


async def get_merchant_context(merchant_id: str, db: AsyncSession) -> dict[str, Any]:
    """Return merchant transaction volume and failure rate."""
    try:
        merch_result = await db.execute(
            select(Merchant).where(Merchant.id == merchant_id)
        )
        merchant = merch_result.scalar_one_or_none()
        if merchant is None:
            return {"error": f"Merchant {merchant_id} not found"}

        tx_result = await db.execute(
            select(Transaction).where(Transaction.merchant_id == merchant_id)
        )
        transactions = tx_result.scalars().all()
        total = len(transactions)
        failed = sum(1 for t in transactions if t.status == "FAILED")

        return {
            "merchant_id": merchant_id,
            "name": merchant.name,
            "is_active": merchant.is_active,
            "total_transactions": total,
            "failed_transactions": failed,
            "failure_rate": round(failed / total, 3) if total > 0 else 0.0,
        }
    except Exception as exc:
        logger.error("get_merchant_context error: %s", exc)
        return {"error": str(exc)}


async def get_previous_recovery_actions(
    transaction_id: str, db: AsyncSession
) -> dict[str, Any]:
    """Return all previous recovery actions and their outcomes."""
    try:
        ra_result = await db.execute(
            select(RecoveryAction)
            .where(RecoveryAction.transaction_id == transaction_id)
            .order_by(RecoveryAction.created_at)
        )
        actions = ra_result.scalars().all()

        action_list = []
        for ra in actions:
            # Get outcome if exists
            outcome_result = await db.execute(
                select(RecoveryOutcome)
                .where(RecoveryOutcome.recovery_action_id == ra.id)
            )
            outcome = outcome_result.scalar_one_or_none()
            action_list.append({
                "recovery_action_id": ra.id,
                "action_type": ra.action_type,
                "status": ra.status,
                "confidence": ra.confidence,
                "reason": ra.reason,
                "scheduled_for": ra.scheduled_for.isoformat() if ra.scheduled_for else None,
                "executed_at": ra.executed_at.isoformat() if ra.executed_at else None,
                "outcome": {
                    "success": outcome.success,
                    "recovered_amount": float(outcome.recovered_amount) if outcome.recovered_amount else None,
                    "failure_reason": outcome.failure_reason,
                } if outcome else None,
            })

        return {
            "transaction_id": transaction_id,
            "recovery_action_count": len(action_list),
            "recovery_actions": action_list,
        }
    except Exception as exc:
        logger.error("get_previous_recovery_actions error: %s", exc)
        return {"error": str(exc)}
