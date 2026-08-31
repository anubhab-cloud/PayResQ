"""
app/recovery/simulator.py
==========================
Probabilistic payment recovery simulator.

We do not have access to real banking infrastructure.
This simulator models recovery outcomes using probabilistic rules
consistent with the Phase 2/3 synthetic data generator.

Rules:
  - Never deterministic ("ICICI always fails")
  - Never always-succeeds
  - Each action has a base success probability modulated by context
  - Small uniform noise (±5%) is added to prevent pattern memorization

This allows Phase 5 to evaluate recovery strategies under controlled
synthetic conditions.

EXPERIMENTAL: All results are simulated — not real-world performance.
"""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    success: bool
    recovered_amount: float
    failure_reason: str | None
    simulator_note: str = "EXPERIMENTAL — synthetic simulation only"


class PaymentSimulator:
    """
    Probabilistic payment recovery simulator.

    Base success rates by action (consistent with Phase 2/3 generator):
      RETRY_NOW              25%
      RETRY_AFTER_DELAY      60%
      SEND_PAYMENT_LINK      45%
      CHANGE_PAYMENT_METHOD  50%
      NOTIFY_CUSTOMER        30%
      ESCALATE               70%
      STOP                    0%

    Context modifiers adjust probability up/down:
      - Customer reliability (success_rate): +/- 15%
      - Delay adequacy for RETRY_AFTER_DELAY: + 10% if >= 15min
      - Bank degradation: + 5% for delayed retry, - 10% for immediate retry
      - Failure type: different modifiers for insufficient_funds vs timeout
    """

    BASE_RATES: dict[str, float] = {
        "RETRY_NOW": 0.25,
        "RETRY_AFTER_DELAY": 0.60,
        "SEND_PAYMENT_LINK": 0.45,
        "CHANGE_PAYMENT_METHOD": 0.50,
        "NOTIFY_CUSTOMER": 0.30,
        "ESCALATE": 0.70,
        "STOP": 0.0,
    }

    NOISE_RANGE = 0.05   # ± uniform noise

    def execute(
        self,
        action: str,
        context: dict[str, Any] | None = None,
        seed: int | None = None,
    ) -> SimulationResult:
        """
        Simulate a recovery action and return its outcome.

        Args:
            action: The recovery action type string (e.g. "RETRY_AFTER_DELAY").
            context: Optional dict with keys: amount, customer_success_rate,
                     delay_minutes, failure_reason, bank.
            seed: Optional seed for reproducible tests.
        """
        if seed is not None:
            random.seed(seed)

        action_upper = action.upper()
        base = self.BASE_RATES.get(action_upper, 0.3)

        if action_upper == "STOP":
            return SimulationResult(
                success=False,
                recovered_amount=0.0,
                failure_reason="STOP action — no recovery attempted",
            )

        # Apply context modifiers
        prob = self._apply_modifiers(base, action_upper, context or {})

        # Clamp and add noise
        noise = random.uniform(-self.NOISE_RANGE, self.NOISE_RANGE)
        final_prob = max(0.02, min(0.98, prob + noise))

        roll = random.random()
        success = roll < final_prob

        amount = float((context or {}).get("amount", 0.0))

        logger.info(
            "Simulator: action=%s base=%.2f modulated=%.2f roll=%.3f success=%s",
            action_upper, base, final_prob, roll, success,
        )

        if success:
            return SimulationResult(
                success=True,
                recovered_amount=amount,
                failure_reason=None,
            )
        else:
            return SimulationResult(
                success=False,
                recovered_amount=0.0,
                failure_reason=f"Simulated failure — action {action_upper} did not recover payment",
            )

    def _apply_modifiers(
        self, base: float, action: str, context: dict[str, Any]
    ) -> float:
        prob = base
        failure_reason = str(context.get("failure_reason", "")).upper()
        customer_rate = float(context.get("customer_success_rate", 0.5))
        delay_minutes = int(context.get("delay_minutes", 0))

        # Customer reliability modifier (±15%)
        if customer_rate > 0.85:
            prob += 0.15
        elif customer_rate > 0.70:
            prob += 0.08
        elif customer_rate < 0.40:
            prob -= 0.10

        # Action-specific modifiers
        if action == "RETRY_AFTER_DELAY":
            if delay_minutes >= 15:
                prob += 0.10   # adequate delay helps
            if failure_reason in ("TIMEOUT", "NETWORK_ERROR"):
                prob += 0.05   # temporal failures benefit from delay

        elif action == "RETRY_NOW":
            if failure_reason in ("TIMEOUT", "BANK_DECLINED"):
                prob -= 0.10   # immediate retry hurts for bank/timeout failures
            if failure_reason == "INSUFFICIENT_FUNDS":
                prob -= 0.20   # insufficient funds rarely recovers without customer action

        elif action == "CHANGE_PAYMENT_METHOD":
            if failure_reason in ("BANK_DECLINED", "AUTHENTICATION_FAILED"):
                prob += 0.10   # method change helps with bank/auth failures
            if failure_reason == "INSUFFICIENT_FUNDS":
                prob -= 0.10   # insufficient funds won't improve with different method

        elif action == "SEND_PAYMENT_LINK":
            if customer_rate > 0.70:
                prob += 0.08   # reliable customers respond to payment links

        return prob
