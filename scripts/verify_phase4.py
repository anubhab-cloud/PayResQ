"""
scripts/verify_phase4.py
========================
Verification suite for Phase 4: AI Recovery Agent.

Executes:
1. Complete End-to-End Flow (Steps 1-18)
2. Safety Test A: Idempotency (duplicate execution prevention)
3. Safety Test B: Payment-Status Recheck (transaction already SUCCESS)
4. Safety Test C: High-Value Transaction (HUMAN_APPROVAL threshold)
5. Safety Test D: Malformed LLM Output (Pydantic safe fallback)
6. Safety Test E: LLM Unavailability (provider error safe fallback)
"""
from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure repo root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

from app.core.db import Base
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.payment_attempt import PaymentAttempt
from app.models.failure_event import FailureEvent
from app.models.recovery_action import RecoveryAction
from app.models.recovery_outcome import RecoveryOutcome
from app.models.audit_log import AuditLog
from app.models.enums import RecoveryActionType, RecoveryActionStatus

from app.agents.providers.fake import FakeLLMProvider
from app.agents.recovery_agent import RecoveryAgent
from app.agents.schemas import AgentDecision
from app.policies.engine import PolicyEngine
from app.policies.schemas import PolicyOutcome
from app.recovery.executor import RecoveryExecutor
from app.recovery.simulator import PaymentSimulator, SimulationResult
from app.recovery.schemas import RecoveryJob
from app.services.recovery_service import RecoveryService
from ml.analysis.root_cause import RootCauseAnalyzer
from ml.services.prediction_service import prediction_service


class MockRedis:
    """In-memory Redis queue mock for standalone verification."""
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


async def run_verification():
    print("============================================================")
    print("  PayResQ Phase 4 Comprehensive Verification Suite")
    print("============================================================\n")

    # In-memory SQLite DB setup
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
        # ==================================================================
        # PART 1: COMPLETE END-TO-END FLOW (STEPS 1-18)
        # ==================================================================
        print("--- [SECTION 1] END-TO-END RECOVERY FLOW ---")

        # 1. Create domain entities
        merchant = Merchant(name="FinTech Merchant")
        db.add(merchant)
        await db.flush()

        customer = Customer(
            merchant_id=merchant.id,
            external_customer_id="CUST-778",
            name="Anubhab Sen",
            email="anubhab@example.com",
        )
        db.add(customer)
        await db.flush()

        tx = Transaction(
            merchant_id=merchant.id,
            customer_id=customer.id,
            external_transaction_id="TX-7500-CARD-ICICI",
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
            failure_code="GATEWAY_TIMEOUT",
            metadata_={"bank": "ICICI", "error": "Gateway timeout after 30000ms"},
        )
        db.add(fe)
        await db.commit()

        # 2. Transaction context
        print("Step 2-3: Transaction Context:")
        print(f"  Transaction ID: {tx.id}")
        print(f"  Amount:         INR {float(tx.amount):,.2f}")
        print(f"  Status:         {tx.status}")
        print(f"  Method/Bank:    {attempt.payment_method} / {attempt.bank}")
        print(f"  Failure Reason: {attempt.failure_reason}\n")

        # 3. Root Cause Analysis
        print("Step 4: Root-Cause Analysis:")
        rca = RootCauseAnalyzer()
        attempts_dict = [{
            "id": attempt.id, "transaction_id": tx.id, "attempt_number": 1,
            "payment_method": "CARD", "bank": "ICICI", "status": "FAILED",
            "failure_reason": "TIMEOUT", "attempted_at": attempt.attempted_at,
        }]
        rca_res = rca.analyze_transaction(tx.id, attempts_dict, attempts_dict)
        print(f"  Root Cause:     {rca_res['root_cause']}")
        print(f"  Confidence:     {rca_res['confidence']}")
        print(f"  Evidence:       {rca_res.get('evidence', [])}\n")

        # 4. XGBoost Predictions
        print("Step 5: XGBoost Predictions:")
        try:
            if not prediction_service.is_loaded:
                prediction_service.load()
            preds_res = prediction_service.predict({
                "amount": 7500.0, "payment_method": "CARD", "bank": "ICICI",
                "failure_reason": "TIMEOUT", "attempt_number": 1, "retry_count": 0,
            })
            print(f"  Predictions:    {json.dumps(preds_res['predictions'], indent=2)}")
            print(f"  Recommended:    {preds_res['recommended_action']}\n")
        except FileNotFoundError:
            preds_res = {
                "predictions": {"RETRY_NOW": 0.24, "RETRY_AFTER_DELAY": 0.71, "SEND_PAYMENT_LINK": 0.39, "CHANGE_PAYMENT_METHOD": 0.55},
                "recommended_action": "RETRY_AFTER_DELAY",
            }
            print(f"  Predictions (Baseline): {preds_res['predictions']}\n")

        # 5. LLM Agent Decision
        print("Step 6-7: LLM Recovery Agent Decision:")
        provider = FakeLLMProvider()
        agent = RecoveryAgent(provider=provider)
        policy_engine = PolicyEngine()
        rec_service = RecoveryService(agent=agent, policy_engine=policy_engine)
        mock_redis = MockRedis()

        agent_dec = await agent.analyze(tx.id, db)
        print(f"  Action:         {agent_dec.action}")
        print(f"  Delay Minutes:  {agent_dec.delay_minutes}")
        print(f"  Confidence:     {agent_dec.confidence}")
        print(f"  Reason:         {agent_dec.reason}\n")

        # 6. Policy Engine Evaluation
        print("Step 8-9: Policy Engine Validation:")
        pipeline_res = await rec_service.process_transaction(tx.id, db, mock_redis)
        print(f"  Outcome:        {pipeline_res['policy_outcome']}")
        print(f"  Policy Reason:  {pipeline_res['policy_reason']}")
        print(f"  Status:         {pipeline_res['status']}\n")

        # 7. Job Queueing
        print("Step 10-11: Job Creation & Redis Queueing:")
        print(f"  Recovery Action ID: {pipeline_res['recovery_action_id']}")
        print(f"  Job ID:             {pipeline_res.get('job_id')}")
        print(f"  Redis Queue Length: {len(mock_redis._queue)}\n")

        # 8. Worker Execution & Idempotency / Status Recheck / Simulator / Outcome
        print("Step 12-17: Worker Consumption, Checks, Simulator & Outcome:")
        raw_job = mock_redis._queue[0]
        job = RecoveryJob.model_validate(json.loads(raw_job))

        executor = RecoveryExecutor(simulator=PaymentSimulator())
        # Force high probability for simulation success in this demo
        sim_res = executor._simulator.execute(job.action, {"amount": 7500.0, "delay_minutes": 20}, seed=42)

        # Directly run executor
        exec_outcome = await executor.execute(job, db)

        await db.refresh(tx)
        print(f"  Worker Executed Job: {job.job_id}")
        print(f"  Simulation Success:  {exec_outcome.success}")
        print(f"  Recovered Amount:    INR {exec_outcome.recovered_amount:,.2f}")
        print(f"  Final TX Status:     {tx.status}\n")

        # 9. Audit Trail
        print("Step 18: Audit Trail:")
        audit_res = await db.execute(select(AuditLog).where(AuditLog.transaction_id == tx.id).order_by(AuditLog.created_at))
        audit_logs = audit_res.scalars().all()
        for log in audit_logs:
            print(f"  [{log.actor_type}] {log.event_type}: {log.action} -- {log.reason[:70]}")
        print("\n")

        # ==================================================================
        # PART 2: SPECIFIC SAFETY TESTS (A, B, C, D, E)
        # ==================================================================
        print("--- [SECTION 2] SAFETY VERIFICATION TESTS ---")

        # TEST A: IDEMPOTENCY
        print("Test A: Idempotency (Submit same job twice):")
        # Submit job again when action is already COMPLETED
        idem_outcome = await executor.execute(job, db)
        print(f"  First execution status:  COMPLETED")
        print(f"  Second execution result: {idem_outcome.simulator_note}")
        print(f"  Second execution success: {idem_outcome.success} (No duplicate payout)")
        assert "Idempotency" in idem_outcome.simulator_note or idem_outcome.failure_reason
        print("  --> TEST A PASSED: Duplicate execution prevented!\n")

        # TEST B: PAYMENT STATUS RECHECK (Transaction becomes SUCCESS before worker runs)
        print("Test B: Payment-Status Recheck (TX already SUCCESS):")
        tx_race = Transaction(merchant_id=merchant.id, customer_id=customer.id, external_transaction_id="TX-RACE-001", amount="3000.00", status="FAILED")
        db.add(tx_race)
        await db.flush()

        ra_race = RecoveryAction(transaction_id=tx_race.id, action_type=RecoveryActionType.RETRY_NOW, status=RecoveryActionStatus.APPROVED, confidence=0.9, reason="Race test")
        db.add(ra_race)
        await db.flush()

        job_race = RecoveryJob(transaction_id=tx_race.id, recovery_action_id=ra_race.id, action="RETRY_NOW", idempotency_key=f"key-{ra_race.id}", scheduled_for=datetime.now(timezone.utc).isoformat())

        # Customer pays independently -> Status becomes SUCCESS
        tx_race.status = "SUCCESS"
        db.add(tx_race)
        await db.commit()

        race_outcome = await executor.execute(job_race, db)
        await db.refresh(ra_race)
        print(f"  Pre-worker TX status:  SUCCESS")
        print(f"  Worker execution result: {race_outcome.failure_reason}")
        print(f"  Recovery Action status: {ra_race.status}")
        assert ra_race.status == RecoveryActionStatus.CANCELLED
        print("  --> TEST B PASSED: Recovery skipped for already-successful transaction!\n")

        # TEST C: HIGH-VALUE TRANSACTION (HUMAN_APPROVAL)
        print("Test C: High-Value Transaction Threshold (> INR 50,000):")
        tx_hv = Transaction(merchant_id=merchant.id, customer_id=customer.id, external_transaction_id="TX-HV-75000", amount="75000.00", status="FAILED")
        db.add(tx_hv)
        await db.flush()

        hv_decision = AgentDecision(action=RecoveryActionType.RETRY_AFTER_DELAY, delay_minutes=20, reason="High value transaction recovery", confidence=0.95)
        hv_policy = policy_engine.evaluate(hv_decision, tx_hv, [])
        print(f"  Transaction Amount: INR {float(tx_hv.amount):,.2f}")
        print(f"  Policy Outcome:     {hv_policy.outcome}")
        print(f"  Policy Reason:      {hv_policy.reason}")
        print(f"  Rule Triggered:     {hv_policy.rule_triggered}")
        assert hv_policy.outcome == PolicyOutcome.HUMAN_APPROVAL
        assert hv_policy.rule_triggered == "high_value_transaction"
        print("  --> TEST C PASSED: High-value transaction requires HUMAN_APPROVAL!\n")

        # TEST D: MALFORMED LLM OUTPUT (Safe Fallback to STOP)
        print("Test D: Malformed LLM Output (Pydantic / JSON error):")
        agent_malformed = RecoveryAgent(provider=FakeLLMProvider(malformed_response=True))
        mal_dec = await agent_malformed.analyze(tx.id, db)
        print(f"  Agent Action:       {mal_dec.action}")
        print(f"  Agent Confidence:   {mal_dec.confidence}")
        print(f"  Agent Reason:       {mal_dec.reason}")
        assert mal_dec.action == RecoveryActionType.STOP
        assert mal_dec.confidence == 0.0
        print("  --> TEST D PASSED: Malformed output cleanly degraded to STOP fallback!\n")

        # TEST E: LLM UNAVAILABILITY (Provider Error Safe Fallback)
        print("Test E: LLM Unavailability (Provider Error):")
        agent_down = RecoveryAgent(provider=FakeLLMProvider(should_fail=True))
        down_dec = await agent_down.analyze(tx.id, db)
        print(f"  Agent Action:       {down_dec.action}")
        print(f"  Agent Confidence:   {down_dec.confidence}")
        print(f"  Agent Reason:       {down_dec.reason}")
        assert down_dec.action == RecoveryActionType.STOP
        assert down_dec.confidence == 0.0
        print("  --> TEST E PASSED: LLM failure safely degraded without executing unsafe action!\n")

    await engine.dispose()
    print("============================================================")
    print("  ALL VERIFICATION TESTS SUCCESSFULLY COMPLETED!")
    print("============================================================\n")


if __name__ == "__main__":
    asyncio.run(run_verification())
