"""
tests/test_worker.py
Tests for RecoveryExecutor, PaymentSimulator, and worker idempotency.
"""
import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone

from app.models.transaction import Transaction
from app.models.recovery_action import RecoveryAction
from app.models.enums import RecoveryActionType, RecoveryActionStatus
from app.recovery.schemas import RecoveryJob
from app.recovery.executor import RecoveryExecutor
from app.recovery.simulator import PaymentSimulator, SimulationResult


def test_payment_simulator_outcomes():
    sim = PaymentSimulator()

    res_retry_now = sim.execute("RETRY_NOW", {"amount": 1000.0}, seed=42)
    assert isinstance(res_retry_now, SimulationResult)
    assert isinstance(res_retry_now.success, bool)

    res_stop = sim.execute("STOP", {"amount": 1000.0})
    assert res_stop.success is False
    assert res_stop.recovered_amount == 0.0


@pytest.mark.asyncio
async def test_recovery_executor_success_flow(db_session, async_client):
    # Setup merchant & customer & failed transaction
    m_resp = await async_client.post("/api/v1/merchants", json={"name": "Exec Merchant"})
    m_id = m_resp.json()["id"]

    c_resp = await async_client.post("/api/v1/customers", json={
        "merchant_id": m_id, "external_customer_id": "C-EXEC-1", "name": "Exec User"
    })
    c_id = c_resp.json()["id"]

    tx_resp = await async_client.post("/api/v1/transactions", json={
        "merchant_id": m_id, "customer_id": c_id,
        "external_transaction_id": "TX-EXEC-1", "amount": "3000.00"
    })
    tx_id = tx_resp.json()["id"]

    # Create approved RecoveryAction
    ra = RecoveryAction(
        transaction_id=tx_id,
        action_type=RecoveryActionType.RETRY_AFTER_DELAY,
        status=RecoveryActionStatus.APPROVED,
        confidence=0.9,
        reason="Test execution",
    )
    db_session.add(ra)
    await db_session.commit()
    await db_session.refresh(ra)

    job = RecoveryJob(
        transaction_id=tx_id,
        recovery_action_id=ra.id,
        action="RETRY_AFTER_DELAY",
        delay_minutes=15,
        idempotency_key=f"key-{ra.id}",
        scheduled_for=datetime.now(timezone.utc).isoformat(),
    )

    executor = RecoveryExecutor()
    res = await executor.execute(job, db_session)

    assert isinstance(res, SimulationResult)

    # Check updated action status
    await db_session.refresh(ra)
    assert ra.status in (RecoveryActionStatus.COMPLETED, RecoveryActionStatus.FAILED)
    assert ra.executed_at is not None


@pytest.mark.asyncio
async def test_recovery_executor_idempotency_skip(db_session, async_client):
    m_resp = await async_client.post("/api/v1/merchants", json={"name": "Idem Merchant"})
    m_id = m_resp.json()["id"]

    c_resp = await async_client.post("/api/v1/customers", json={"merchant_id": m_id, "external_customer_id": "C-IDEM-1", "name": "Idem User"})
    c_id = c_resp.json()["id"]

    tx_resp = await async_client.post("/api/v1/transactions", json={"merchant_id": m_id, "customer_id": c_id, "external_transaction_id": "TX-IDEM-1", "amount": "1500.00"})
    tx_id = tx_resp.json()["id"]

    ra = RecoveryAction(
        transaction_id=tx_id,
        action_type=RecoveryActionType.RETRY_NOW,
        status=RecoveryActionStatus.COMPLETED,  # Already completed
        confidence=0.8,
        reason="Already done",
    )
    db_session.add(ra)
    await db_session.commit()

    job = RecoveryJob(
        transaction_id=tx_id,
        recovery_action_id=ra.id,
        action="RETRY_NOW",
        idempotency_key=f"key-{ra.id}",
        scheduled_for=datetime.now(timezone.utc).isoformat(),
    )

    executor = RecoveryExecutor()
    res = await executor.execute(job, db_session)

    assert "Idempotency" in res.simulator_note
