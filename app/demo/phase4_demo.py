"""
app/demo/phase4_demo.py
========================
End-to-end Phase 4 demo scenario.

Demonstrates the full loop:
  FAILED → Agent → Policy → Redis → Worker → Simulator → Outcome

Runs entirely in-memory using SQLite (no PostgreSQL or Redis required).
Uses FakeLLMProvider for determinism.

Run with:
    python -m app.demo.phase4_demo

Expected output:
    Transaction: ₹7,500 CARD / ICICI / TIMEOUT
    Agent:  RETRY_AFTER_DELAY (confidence=0.91)
    Policy: ALLOW
    Queue:  Job enqueued
    Worker: Executing...
    Outcome: SUCCESS — ₹7,500 RECOVERED  (or FAILED depending on simulation)
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.core.db import Base
from app.models import *  # noqa: F401, F403 — ensure all models are registered


async def run_demo() -> None:
    print("\n" + "=" * 60)
    print("  PayResQ Phase 4 — End-to-End Recovery Demo")
    print("  EXPERIMENTAL: Synthetic data / simulated outcomes")
    print("=" * 60 + "\n")

    # --- Setup in-memory SQLite DB ---
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with SessionLocal() as db:
        # --- 1. Create domain objects ---
        from app.models.merchant import Merchant
        from app.models.customer import Customer
        from app.models.transaction import Transaction
        from app.models.payment_attempt import PaymentAttempt
        from app.models.failure_event import FailureEvent

        merchant = Merchant(name="Demo Merchant")
        db.add(merchant)
        await db.flush()

        customer = Customer(
            merchant_id=merchant.id,
            external_customer_id="DEMO-C-001",
            name="Rahul Sharma",
            email="rahul@example.com",
        )
        db.add(customer)
        await db.flush()

        transaction = Transaction(
            merchant_id=merchant.id,
            customer_id=customer.id,
            external_transaction_id=f"DEMO-TX-{uuid.uuid4().hex[:8]}",
            amount="7500.00",
            currency="INR",
            status="FAILED",
        )
        db.add(transaction)
        await db.flush()

        attempt = PaymentAttempt(
            transaction_id=transaction.id,
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
            metadata_={"bank": "ICICI", "error": "Connection timeout after 30s"},
        )
        db.add(fe)
        await db.commit()

        print(f"[1] Transaction created")
        print(f"    ID:      {transaction.id}")
        print(f"    Amount:  ₹{float(transaction.amount):,.0f}")
        print(f"    Method:  {attempt.payment_method} / {attempt.bank}")
        print(f"    Failure: {attempt.failure_reason}")
        print(f"    Status:  {transaction.status}\n")

        # --- 2. Run Agent (FakeLLMProvider) ---
        from app.agents.providers.fake import FakeLLMProvider
        from app.agents.recovery_agent import RecoveryAgent
        from app.policies.engine import PolicyEngine
        from app.services.recovery_service import RecoveryService

        provider = FakeLLMProvider()   # deterministic — no API key needed
        agent = RecoveryAgent(provider=provider)
        policy_engine = PolicyEngine()
        service = RecoveryService(agent=agent, policy_engine=policy_engine)

        # Use a mock Redis (in-memory list)
        class MockRedis:
            def __init__(self):
                self._queue = []
                self._dead = []

            async def rpush(self, key, value):
                if "dead" in key:
                    self._dead.append(value)
                else:
                    self._queue.append(value)
                return len(self._queue)

            async def blpop(self, key, timeout=5):
                if self._queue:
                    return (key, self._queue.pop(0))
                return None

            async def llen(self, key):
                return len(self._queue)

        mock_redis = MockRedis()

        print("[2] Running Agent → Policy pipeline...")
        result = await service.process_transaction(
            transaction_id=transaction.id,
            db=db,
            redis=mock_redis,
        )

        agent_decision = result.get("agent_decision", {})
        print(f"\n[3] Agent Decision")
        print(f"    Action:     {agent_decision.get('action')}")
        print(f"    Confidence: {agent_decision.get('confidence')}")
        print(f"    Reason:     {agent_decision.get('reason', '')[:80]}...")
        print(f"    Root Cause: {agent_decision.get('root_cause')}")

        print(f"\n[4] Policy Engine")
        print(f"    Outcome:    {result.get('policy_outcome')}")
        print(f"    Reason:     {result.get('policy_reason', '')[:80]}")
        print(f"    Status:     {result.get('status')}")

        recovery_action_id = result.get("recovery_action_id")
        job_id = result.get("job_id")
        print(f"\n[5] Recovery Action: {recovery_action_id}")
        print(f"    Job ID:          {job_id or 'N/A (not enqueued)'}")
        print(f"    Queue length:    {len(mock_redis._queue)}")

        # --- 3. Worker execution ---
        if mock_redis._queue or result.get("status") == "ENQUEUED":
            print("\n[6] Worker processing job...")
            from app.recovery.executor import RecoveryExecutor
            from app.recovery.simulator import PaymentSimulator
            from app.recovery.schemas import RecoveryJob
            import json as _json

            executor = RecoveryExecutor(simulator=PaymentSimulator())

            # Get job from mock queue
            if mock_redis._queue:
                raw = mock_redis._queue[0]
            else:
                # Reconstruct from result
                raw = None

            if raw:
                job = RecoveryJob.model_validate(_json.loads(raw))
                sim_result = await executor.execute(job, db)

                print(f"\n[7] Recovery Outcome")
                print(f"    Success:          {sim_result.success}")
                if sim_result.success:
                    print(f"    Recovered Amount: ₹{sim_result.recovered_amount:,.2f}")
                    print(f"    Result:           ✅ ₹7,500 RECOVERED")
                else:
                    print(f"    Failure Reason:   {sim_result.failure_reason}")
                    print(f"    Result:           ❌ Recovery failed (will retry or escalate)")
                print(f"    Note:             {sim_result.simulator_note}")
        else:
            print(f"\n[6] Recovery not enqueued — status: {result.get('status')}")

        # --- 4. Audit trail ---
        from sqlalchemy import select
        from app.models.audit_log import AuditLog
        audit_result = await db.execute(
            select(AuditLog)
            .where(AuditLog.transaction_id == transaction.id)
            .order_by(AuditLog.created_at)
        )
        audit_logs = audit_result.scalars().all()
        print(f"\n[8] Audit Trail ({len(audit_logs)} entries)")
        for log in audit_logs:
            print(f"    [{log.actor_type}] {log.event_type}: {log.action} — {log.reason[:60]}")

    print("\n" + "=" * 60)
    print("  Phase 4 Demo Complete")
    print("  EXPERIMENTAL — synthetic simulation only")
    print("=" * 60 + "\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_demo())
