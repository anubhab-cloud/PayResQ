"""
app/api/v1/dashboard.py
========================
Dashboard aggregation endpoints for the PayResQ frontend.

GET  /api/v1/dashboard/summary            — KPI summary metrics
GET  /api/v1/dashboard/recovery-trends    — Time-series trend data
GET  /api/v1/dashboard/failure-breakdown — Bank and method failure rates
POST /api/v1/dashboard/demo-run           — Triggers a live E2E demo recovery
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.db import get_db
from app.core.redis import get_redis
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.payment_attempt import PaymentAttempt
from app.models.failure_event import FailureEvent
from app.models.recovery_action import RecoveryAction
from app.models.recovery_outcome import RecoveryOutcome
from app.models.enums import RecoveryActionStatus, RecoveryActionType
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardTrendsResponse,
    DailyTrendPoint,
    DashboardFailureBreakdownResponse,
    BankFailureStat,
    MethodFailureStat,
    DemoRunResponse,
)
from app.agents.providers import get_provider
from app.agents.recovery_agent import RecoveryAgent
from app.policies.engine import PolicyEngine
from app.recovery.executor import RecoveryExecutor
from app.recovery.simulator import PaymentSimulator
from app.services.recovery_service import RecoveryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get top-level dashboard KPI summary metrics",
)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Computes live KPI summary metrics from database records."""
    # Total transactions count & status counts
    tx_res = await db.execute(select(Transaction))
    transactions = tx_res.scalars().all()

    total_tx = len(transactions)
    failed_tx = sum(1 for t in transactions if str(t.status).upper() == "FAILED")
    success_tx = sum(1 for t in transactions if str(t.status).upper() == "SUCCESS")

    # Revenue at Risk = sum of failed transactions
    at_risk = sum(float(t.amount) for t in transactions if str(t.status).upper() == "FAILED")

    # Recovered Revenue = sum of recovered amounts from RecoveryOutcomes
    outcomes_res = await db.execute(select(RecoveryOutcome).where(RecoveryOutcome.success == True))
    outcomes = outcomes_res.scalars().all()
    recovered = sum(float(o.recovered_amount or 0) for o in outcomes)

    # Recovery Rate (%) = recovered / (recovered + at_risk) or success / total
    denom = (recovered + at_risk)
    recovery_rate = round((recovered / denom) * 100, 1) if denom > 0 else 0.0

    # Human approvals pending
    actions_res = await db.execute(
        select(RecoveryAction).where(RecoveryAction.status == RecoveryActionStatus.PENDING)
    )
    pending_approvals = len(actions_res.scalars().all())

    # Active interventions (APPROVED / EXECUTING)
    active_res = await db.execute(
        select(RecoveryAction).where(
            RecoveryAction.status.in_([RecoveryActionStatus.APPROVED, RecoveryActionStatus.EXECUTING])
        )
    )
    active_interventions = len(active_res.scalars().all())

    return DashboardSummaryResponse(
        revenue_at_risk=round(at_risk, 2),
        recovered_revenue=round(recovered, 2),
        recovery_rate=recovery_rate,
        total_transactions=total_tx,
        failed_transactions=failed_tx,
        successful_transactions=success_tx,
        pending_human_approvals=pending_approvals,
        active_interventions=active_interventions,
    )


@router.get(
    "/recovery-trends",
    response_model=DashboardTrendsResponse,
    summary="Get time-series recovery trends over time",
)
async def get_recovery_trends(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Returns daily time-series data for chart visualization."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    tx_res = await db.execute(
        select(Transaction).where(Transaction.created_at >= start).order_by(Transaction.created_at)
    )
    transactions = tx_res.scalars().all()

    # Group by date YYYY-MM-DD
    daily_map: dict[str, dict] = {}
    for i in range(days):
        d_str = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        daily_map[d_str] = {
            "date": d_str,
            "failed_volume": 0.0,
            "recovered_volume": 0.0,
            "failed_count": 0,
            "recovered_count": 0,
        }

    for t in transactions:
        d_str = t.created_at.strftime("%Y-%m-%d") if t.created_at else now.strftime("%Y-%m-%d")
        if d_str in daily_map:
            amt = float(t.amount)
            if str(t.status).upper() == "FAILED":
                daily_map[d_str]["failed_volume"] += amt
                daily_map[d_str]["failed_count"] += 1
            elif str(t.status).upper() == "SUCCESS":
                daily_map[d_str]["recovered_volume"] += amt
                daily_map[d_str]["recovered_count"] += 1

    points = [DailyTrendPoint(**v) for v in daily_map.values()]
    return DashboardTrendsResponse(timeframe_days=days, trends=points)


@router.get(
    "/failure-breakdown",
    response_model=DashboardFailureBreakdownResponse,
    summary="Get bank and payment method failure distributions",
)
async def get_failure_breakdown(db: AsyncSession = Depends(get_db)):
    """Computes failure rates grouped by bank and payment method."""
    attempts_res = await db.execute(select(PaymentAttempt))
    attempts = attempts_res.scalars().all()

    bank_counts: dict[str, dict] = {}
    method_counts: dict[str, dict] = {}

    for a in attempts:
        bank = a.bank or "UNKNOWN"
        method = a.payment_method or "UNKNOWN"

        # Bank stats
        if bank not in bank_counts:
            bank_counts[bank] = {"failed": 0, "total": 0}
        bank_counts[bank]["total"] += 1
        if str(a.status).upper() == "FAILED":
            bank_counts[bank]["failed"] += 1

        # Method stats
        if method not in method_counts:
            method_counts[method] = {"failed": 0, "total": 0}
        method_counts[method]["total"] += 1
        if str(a.status).upper() == "FAILED":
            method_counts[method]["failed"] += 1

    by_bank = [
        BankFailureStat(
            bank=b,
            failed_count=v["failed"],
            total_count=v["total"],
            failure_rate=round(v["failed"] / v["total"], 3) if v["total"] > 0 else 0.0,
        )
        for b, v in bank_counts.items()
    ]
    by_method = [
        MethodFailureStat(
            payment_method=m,
            failed_count=v["failed"],
            total_count=v["total"],
            failure_rate=round(v["failed"] / v["total"], 3) if v["total"] > 0 else 0.0,
        )
        for m, v in method_counts.items()
    ]

    return DashboardFailureBreakdownResponse(by_bank=by_bank, by_method=by_method)


@router.post(
    "/demo-run",
    response_model=DemoRunResponse,
    summary="Trigger a real end-to-end recovery scenario through backend",
)
async def run_demo_scenario(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Creates a failed payment transaction, passes it through the real
    Agent → Policy → Queue → Worker simulation, and returns the full result.
    """
    try:
        # Get or create merchant
        m_res = await db.execute(select(Merchant).limit(1))
        merchant = m_res.scalar_one_or_none()
        if not merchant:
            merchant = Merchant(name="Demo Merchant")
            db.add(merchant)
            await db.flush()

        # Get or create customer
        c_res = await db.execute(select(Customer).where(Customer.merchant_id == merchant.id).limit(1))
        customer = c_res.scalar_one_or_none()
        if not customer:
            customer = Customer(
                merchant_id=merchant.id,
                external_customer_id=f"DEMO-C-{uuid.uuid4().hex[:4]}",
                name="Anubhab Sen",
                email="demo@example.com",
            )
            db.add(customer)
            await db.flush()

        # Create failed transaction
        tx = Transaction(
            merchant_id=merchant.id,
            customer_id=customer.id,
            external_transaction_id=f"DEMO-TX-{uuid.uuid4().hex[:6]}",
            amount="7500.00",
            currency="INR",
            status="FAILED",
        )
        db.add(tx)
        await db.flush()

        attempt = PaymentAttempt(
            transaction_id=tx.id,
            attempt_number=1,
            payment_method="CARD",
            bank="ICICI",
            status="FAILED",
            failure_reason="TIMEOUT",
            attempted_at=datetime.now(timezone.utc),
        )
        db.add(attempt)
        await db.flush()

        fe = FailureEvent(
            payment_attempt_id=attempt.id,
            event_type="PAYMENT_FAILED",
            failure_code="BANK_TIMEOUT",
            metadata_={"bank": "ICICI", "error": "Gateway timeout after 30000ms"},
        )
        db.add(fe)
        await db.commit()

        # Run RecoveryService pipeline
        provider = get_provider()
        agent = RecoveryAgent(provider=provider)
        service = RecoveryService(agent=agent, policy_engine=PolicyEngine())

        pipeline_res = await service.process_transaction(tx.id, db, redis)

        agent_dec = pipeline_res.get("agent_decision", {})
        job_id = pipeline_res.get("job_id")

        # Execute simulation via executor for immediate demo feedback
        exec_outcome = None
        recovered_amt = None
        exec_success = None

        if pipeline_res.get("status") == "ENQUEUED" and job_id:
            from app.recovery.schemas import RecoveryJob
            job = RecoveryJob(
                transaction_id=tx.id,
                recovery_action_id=pipeline_res["recovery_action_id"],
                action=agent_dec.get("action", "RETRY_AFTER_DELAY"),
                idempotency_key=f"demo-{pipeline_res['recovery_action_id']}",
                scheduled_for=datetime.now(timezone.utc).isoformat(),
            )
            executor = RecoveryExecutor(simulator=PaymentSimulator())
            exec_outcome = await executor.execute(job, db)
            exec_success = exec_outcome.success
            recovered_amt = exec_outcome.recovered_amount if exec_outcome.success else 0.0

        return DemoRunResponse(
            transaction_id=tx.id,
            amount=7500.0,
            bank="ICICI",
            payment_method="CARD",
            failure_reason="TIMEOUT",
            agent_action=agent_dec.get("action", "RETRY_AFTER_DELAY"),
            agent_confidence=agent_dec.get("confidence", 0.91),
            policy_outcome=pipeline_res.get("policy_outcome", "ALLOW"),
            job_id=job_id,
            execution_success=exec_success,
            recovered_amount=recovered_amt,
            status=pipeline_res.get("status", "COMPLETED"),
        )
    except Exception as exc:
        logger.error("Demo run error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo execution failed: {str(exc)}",
        )
