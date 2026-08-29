"""
PayResQ Synthetic Data Generator
=================================
Generates realistic, probabilistic payment transaction data with:
  - Customer reliability profiles (Beta distribution)
  - Bank degradation windows (elevated failure rates in specific time windows)
  - Correlated failure types based on bank, method, and customer profile
  - Recovery actions with probabilistic outcomes

Design principles:
  - All patterns are PROBABILISTIC, never deterministic.
  - Data must be reproducible given the same seed.
  - Uses bulk inserts for performance.
"""
from __future__ import annotations

import uuid
import random
import string
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from faker import Faker

from app.models.enums import (
    TransactionStatus,
    PaymentAttemptStatus,
    PaymentMethod,
    FailureReason,
    RecoveryActionType,
    RecoveryActionStatus,
    ActorType,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BANKS = [
    "ICICI", "HDFC", "SBI", "AXIS", "KOTAK",
    "YES", "IDFC", "PAYTM", "PHONEPE",
]

PAYMENT_METHODS = [m.value for m in PaymentMethod]
FAILURE_REASONS = [f.value for f in FailureReason]

# Probability of each payment method being used
PAYMENT_METHOD_WEIGHTS = {
    PaymentMethod.UPI: 0.45,
    PaymentMethod.CARD: 0.30,
    PaymentMethod.NETBANKING: 0.15,
    PaymentMethod.WALLET: 0.10,
}

# Base failure probability by payment method
BASE_FAILURE_PROB = {
    PaymentMethod.UPI: 0.08,
    PaymentMethod.CARD: 0.12,
    PaymentMethod.NETBANKING: 0.10,
    PaymentMethod.WALLET: 0.06,
}

# Failure type distribution when a failure occurs
FAILURE_TYPE_PROBS = {
    FailureReason.TIMEOUT: 0.30,
    FailureReason.BANK_DECLINED: 0.25,
    FailureReason.INSUFFICIENT_FUNDS: 0.20,
    FailureReason.NETWORK_ERROR: 0.15,
    FailureReason.AUTHENTICATION_FAILED: 0.10,
}

# Recovery action success probability by action type (base rate)
RECOVERY_ACTION_BASE_SUCCESS = {
    RecoveryActionType.RETRY_NOW: 0.25,
    RecoveryActionType.RETRY_AFTER_DELAY: 0.60,
    RecoveryActionType.SEND_PAYMENT_LINK: 0.45,
    RecoveryActionType.CHANGE_PAYMENT_METHOD: 0.50,
    RecoveryActionType.NOTIFY_CUSTOMER: 0.30,
    RecoveryActionType.ESCALATE: 0.70,
    RecoveryActionType.STOP: 0.0,
}

# Failure reason → most suitable recovery action (probabilistic)
FAILURE_RECOVERY_AFFINITY = {
    FailureReason.TIMEOUT: [RecoveryActionType.RETRY_AFTER_DELAY, RecoveryActionType.RETRY_NOW],
    FailureReason.BANK_DECLINED: [RecoveryActionType.CHANGE_PAYMENT_METHOD, RecoveryActionType.SEND_PAYMENT_LINK],
    FailureReason.INSUFFICIENT_FUNDS: [RecoveryActionType.SEND_PAYMENT_LINK, RecoveryActionType.NOTIFY_CUSTOMER],
    FailureReason.NETWORK_ERROR: [RecoveryActionType.RETRY_AFTER_DELAY, RecoveryActionType.RETRY_NOW],
    FailureReason.AUTHENTICATION_FAILED: [RecoveryActionType.SEND_PAYMENT_LINK, RecoveryActionType.ESCALATE],
}


# ---------------------------------------------------------------------------
# Internal data containers
# ---------------------------------------------------------------------------

@dataclass
class MerchantRecord:
    id: str
    name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CustomerRecord:
    id: str
    merchant_id: str
    external_customer_id: str
    name: str
    email: str
    success_rate: float  # internal profile, not stored in DB
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BankDegradationWindow:
    bank: str
    payment_method: PaymentMethod
    start_hour: int   # hour of day (0–23)
    end_hour: int
    failure_multiplier: float  # e.g. 3.0 = 3× base failure rate


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class PaymentDataGenerator:
    """
    Generates synthetic payment data with realistic probabilistic patterns.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        self.fake = Faker("en_IN")
        self.fake.seed_instance(seed)

        self._degradation_windows: list[BankDegradationWindow] = []
        self._setup_degradation_windows()

    def _setup_degradation_windows(self) -> None:
        """
        Create 4–6 random bank degradation windows.
        Each window represents a real-world scenario like a bank having
        elevated timeout rates between 11 PM and 1 AM.
        """
        rng = np.random.RandomState(self.seed + 1)
        num_windows = rng.randint(4, 7)
        for _ in range(num_windows):
            bank = rng.choice(BANKS)
            method = rng.choice([PaymentMethod.CARD, PaymentMethod.NETBANKING, PaymentMethod.UPI])
            start_hour = int(rng.choice([0, 1, 11, 22, 23]))
            end_hour = (start_hour + rng.randint(1, 4)) % 24
            multiplier = float(rng.uniform(2.0, 4.5))
            self._degradation_windows.append(
                BankDegradationWindow(bank, method, start_hour, end_hour, multiplier)
            )

    def _is_in_degradation(self, bank: str, method: PaymentMethod, hour: int) -> tuple[bool, float]:
        for w in self._degradation_windows:
            if w.bank == bank and w.payment_method == method:
                if w.start_hour <= w.end_hour:
                    in_window = w.start_hour <= hour < w.end_hour
                else:  # wraps midnight
                    in_window = hour >= w.start_hour or hour < w.end_hour
                if in_window:
                    return True, w.failure_multiplier
        return False, 1.0

    def _make_uuid(self) -> str:
        return str(uuid.uuid4())

    def generate_merchants(self, n: int) -> list[MerchantRecord]:
        merchants = []
        for i in range(n):
            merchants.append(MerchantRecord(
                id=self._make_uuid(),
                name=self.fake.company(),
                is_active=random.random() > 0.05,
            ))
        return merchants

    def generate_customers(
        self, n: int, merchants: list[MerchantRecord]
    ) -> list[CustomerRecord]:
        customers = []
        ext_ids_per_merchant: dict[str, set] = {m.id: set() for m in merchants}

        for i in range(n):
            merchant = random.choice(merchants)
            # Customer success_rate drawn from Beta distribution
            # Most customers are reliable (alpha=8, beta=2) → mean ~0.80
            # Some customers have poor history (alpha=2, beta=5) → mean ~0.29
            if random.random() < 0.15:  # 15% are poor payers
                success_rate = float(np.random.beta(2, 5))
            else:
                success_rate = float(np.random.beta(8, 2))
            success_rate = max(0.05, min(0.99, success_rate))

            # Unique external_customer_id per merchant
            ext_id = f"CUST-{self.fake.bothify('????-####')}"
            while ext_id in ext_ids_per_merchant[merchant.id]:
                ext_id = f"CUST-{self.fake.bothify('????-####')}"
            ext_ids_per_merchant[merchant.id].add(ext_id)

            customers.append(CustomerRecord(
                id=self._make_uuid(),
                merchant_id=merchant.id,
                external_customer_id=ext_id,
                name=self.fake.name(),
                email=self.fake.email(),
                success_rate=success_rate,
            ))
        return customers

    def generate_transactions_and_related(
        self,
        n_transactions: int,
        customers: list[CustomerRecord],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Generate transactions, payment_attempts, failure_events, recovery_actions,
        recovery_outcomes, and audit_logs in memory as plain dicts for bulk insert.
        """
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=90)
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        # Index customers by merchant for realistic assignments
        customer_by_merchant: dict[str, list[CustomerRecord]] = {}
        for c in customers:
            customer_by_merchant.setdefault(c.merchant_id, []).append(c)

        transactions = []
        payment_attempts = []
        failure_events = []
        recovery_actions = []
        recovery_outcomes = []
        audit_logs = []

        ext_tx_ids: set[str] = set()

        for _ in range(n_transactions):
            customer = random.choice(customers)
            merchant_id = customer.merchant_id

            # Random timestamp within the date range
            delta = (end_date - start_date).total_seconds()
            tx_time = start_date + timedelta(seconds=random.uniform(0, delta))
            hour = tx_time.hour

            # Amount: log-normal with mean ~₹2500, range roughly ₹100–₹50,000
            amount = round(float(np.random.lognormal(mean=7.8, sigma=1.0)), 2)
            amount = max(10.0, min(amount, 100000.0))

            # External transaction ID
            ext_id = f"TXN-{self.fake.bothify('??####??####')}"
            while ext_id in ext_tx_ids:
                ext_id = f"TXN-{self.fake.bothify('??####??####')}"
            ext_tx_ids.add(ext_id)

            tx_id = self._make_uuid()

            # Choose payment method (weighted)
            method = random.choices(
                list(PAYMENT_METHOD_WEIGHTS.keys()),
                weights=list(PAYMENT_METHOD_WEIGHTS.values()),
            )[0]
            bank = random.choice(BANKS)

            # Determine failure probability
            base_fail_prob = BASE_FAILURE_PROB[method]
            # Customer reliability modifies failure probability
            # Poor customer (low success_rate) → higher failure
            customer_fail_modifier = 1.0 + (1.0 - customer.success_rate) * 0.8
            fail_prob = base_fail_prob * customer_fail_modifier

            # Check degradation window
            in_degradation, multiplier = self._is_in_degradation(bank, method, hour)
            if in_degradation:
                fail_prob = min(fail_prob * multiplier, 0.95)

            # Attempt 1
            first_attempt_success = random.random() > fail_prob
            n_attempts = 1

            if first_attempt_success:
                tx_status = TransactionStatus.SUCCESS
            else:
                # Determine if retry happens (70% of failures get a retry)
                will_retry = random.random() < 0.70
                if will_retry:
                    n_attempts = random.randint(2, 3)
                    # Each retry has a somewhat better chance
                    final_success = random.random() > (fail_prob * 0.7)
                    tx_status = TransactionStatus.SUCCESS if final_success else TransactionStatus.FAILED
                else:
                    tx_status = TransactionStatus.FAILED

            # Build attempt records
            attempt_failed_reasons: list[FailureReason] = []
            for attempt_num in range(1, n_attempts + 1):
                attempt_id = self._make_uuid()
                attempt_time = tx_time + timedelta(minutes=(attempt_num - 1) * random.uniform(5, 30))

                is_last_attempt = attempt_num == n_attempts
                if attempt_num < n_attempts:
                    # Intermediate attempt always fails
                    attempt_status = PaymentAttemptStatus.FAILED
                else:
                    attempt_status = (
                        PaymentAttemptStatus.SUCCESS
                        if tx_status == TransactionStatus.SUCCESS
                        else PaymentAttemptStatus.FAILED
                    )

                # Failure reason for failed attempts
                failure_reason = None
                if attempt_status == PaymentAttemptStatus.FAILED:
                    # Timeout more likely in degradation windows
                    if in_degradation and random.random() < 0.60:
                        failure_reason = FailureReason.TIMEOUT
                    elif customer.success_rate < 0.3 and random.random() < 0.45:
                        failure_reason = FailureReason.INSUFFICIENT_FUNDS
                    else:
                        failure_reason = random.choices(
                            list(FAILURE_TYPE_PROBS.keys()),
                            weights=list(FAILURE_TYPE_PROBS.values()),
                        )[0]
                    attempt_failed_reasons.append(failure_reason)

                    # Failure event
                    fe_id = self._make_uuid()
                    failure_events.append({
                        "id": fe_id,
                        "payment_attempt_id": attempt_id,
                        "event_type": "PAYMENT_FAILURE",
                        "failure_code": f"{failure_reason.value}_ERR" if failure_reason else "UNKNOWN",
                        "metadata": {
                            "bank": bank,
                            "method": method.value,
                            "hour": hour,
                            "in_degradation": in_degradation,
                        },
                        "occurred_at": attempt_time,
                    })

                payment_attempts.append({
                    "id": attempt_id,
                    "transaction_id": tx_id,
                    "attempt_number": attempt_num,
                    "payment_method": method.value,
                    "bank": bank,
                    "status": attempt_status.value,
                    "failure_reason": failure_reason.value if failure_reason else None,
                    "attempted_at": attempt_time,
                })

            # Recovery action for failed transactions
            if tx_status == TransactionStatus.FAILED and attempt_failed_reasons:
                dominant_failure = attempt_failed_reasons[-1]
                affinity_actions = FAILURE_RECOVERY_AFFINITY.get(
                    dominant_failure, [RecoveryActionType.RETRY_AFTER_DELAY]
                )
                action_type = random.choice(affinity_actions)

                # Confidence is correlated with how clear the failure reason is
                confidence = round(random.uniform(0.55, 0.95), 3)
                # Poor customers get slightly lower confidence
                if customer.success_rate < 0.4:
                    confidence = round(confidence * random.uniform(0.75, 0.95), 3)

                ra_id = self._make_uuid()
                scheduled = tx_time + timedelta(minutes=random.uniform(5, 60))
                executed = (
                    scheduled + timedelta(minutes=random.uniform(0, 5))
                    if random.random() < 0.80
                    else None
                )
                ra_status = (
                    RecoveryActionStatus.COMPLETED if executed else RecoveryActionStatus.PENDING
                )

                recovery_actions.append({
                    "id": ra_id,
                    "transaction_id": tx_id,
                    "action_type": action_type.value,
                    "status": ra_status.value,
                    "reason": f"Failure: {dominant_failure.value}",
                    "confidence": confidence,
                    "scheduled_for": scheduled,
                    "executed_at": executed,
                    "created_at": tx_time + timedelta(seconds=30),
                })

                # Recovery outcome (only if action was executed)
                if executed:
                    base_success_prob = RECOVERY_ACTION_BASE_SUCCESS[action_type]
                    # Better customer profile → better outcome
                    adjusted_prob = base_success_prob * (0.5 + customer.success_rate * 0.5)
                    # Timeout with delayed retry → better odds
                    if dominant_failure == FailureReason.TIMEOUT and action_type == RecoveryActionType.RETRY_AFTER_DELAY:
                        adjusted_prob = min(adjusted_prob * 1.3, 0.95)

                    recovered = random.random() < adjusted_prob
                    recovery_outcomes.append({
                        "id": self._make_uuid(),
                        "recovery_action_id": ra_id,
                        "success": recovered,
                        "recovered_amount": float(amount) if recovered else None,
                        "failure_reason": None if recovered else "Recovery attempt did not succeed",
                        "completed_at": executed + timedelta(minutes=random.uniform(1, 30)),
                    })

                # Audit log for the recovery decision
                audit_logs.append({
                    "id": self._make_uuid(),
                    "transaction_id": tx_id,
                    "event_type": "RECOVERY_DECISION",
                    "actor_type": ActorType.SYSTEM.value,
                    "action": action_type.value,
                    "reason": f"Automated recovery for failure: {dominant_failure.value}",
                    "metadata": {
                        "confidence": confidence,
                        "failure_reason": dominant_failure.value,
                        "attempt_count": n_attempts,
                    },
                    "created_at": tx_time + timedelta(seconds=35),
                })

            transactions.append({
                "id": tx_id,
                "merchant_id": merchant_id,
                "customer_id": customer.id,
                "external_transaction_id": ext_id,
                "amount": amount,
                "currency": "INR",
                "status": tx_status.value,
                "created_at": tx_time,
                "updated_at": tx_time,
            })

        return {
            "transactions": transactions,
            "payment_attempts": payment_attempts,
            "failure_events": failure_events,
            "recovery_actions": recovery_actions,
            "recovery_outcomes": recovery_outcomes,
            "audit_logs": audit_logs,
        }

    def generate_all(
        self,
        n_merchants: int = 5,
        n_customers: int = 100,
        n_transactions: int = 1000,
    ) -> dict[str, list]:
        """
        Generate a complete dataset and return as dict of record lists.
        Merchants and customers are also converted to plain dicts.
        """
        merchant_records = self.generate_merchants(n_merchants)
        customer_records = self.generate_customers(n_customers, merchant_records)
        related = self.generate_transactions_and_related(n_transactions, customer_records)

        merchants_dicts = [
            {
                "id": m.id,
                "name": m.name,
                "is_active": m.is_active,
                "created_at": m.created_at,
                "updated_at": m.updated_at,
            }
            for m in merchant_records
        ]
        customers_dicts = [
            {
                "id": c.id,
                "merchant_id": c.merchant_id,
                "external_customer_id": c.external_customer_id,
                "name": c.name,
                "email": c.email,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in customer_records
        ]

        return {
            "merchants": merchants_dicts,
            "customers": customers_dicts,
            **related,
        }
