"""
app/policies/engine.py
========================
Deterministic policy engine.

Evaluates agent decisions against a set of ordered rules.
The LLM is NEVER consulted here — this is entirely deterministic.

Usage:
    engine = PolicyEngine()
    result = engine.evaluate(decision, transaction, existing_actions)
    # result.outcome in {ALLOW, BLOCK, HUMAN_APPROVAL}
"""
from __future__ import annotations

import logging

from app.agents.schemas import AgentDecision
from app.models.transaction import Transaction
from app.models.recovery_action import RecoveryAction
from app.policies.rules import ALL_RULES
from app.policies.schemas import PolicyDecision, PolicyOutcome

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Deterministic policy engine.

    Evaluates rules in order. The first rule that returns a
    PolicyDecision short-circuits evaluation.
    If all rules pass → ALLOW.
    """

    POLICY_VERSION = "v1"

    def evaluate(
        self,
        decision: AgentDecision,
        transaction: Transaction,
        existing_actions: list[RecoveryAction],
    ) -> PolicyDecision:
        """
        Evaluate all rules and return a PolicyDecision.

        Args:
            decision: The AgentDecision to validate.
            transaction: The SQLAlchemy Transaction object.
            existing_actions: All existing RecoveryActions for this transaction.

        Returns:
            PolicyDecision with outcome ALLOW, BLOCK, or HUMAN_APPROVAL.
        """
        for rule_fn in ALL_RULES:
            result = rule_fn(decision, transaction, existing_actions)
            if result is not None:
                result.policy_version = self.POLICY_VERSION
                logger.info(
                    "Policy rule triggered: rule=%s outcome=%s tx=%s reason=%s",
                    result.rule_triggered,
                    result.outcome,
                    getattr(decision, "transaction_id", "unknown"),
                    result.reason,
                )
                return result

        # All rules passed → ALLOW
        allow = PolicyDecision(
            outcome=PolicyOutcome.ALLOW,
            reason="Action satisfies all automated recovery policies.",
            policy_version=self.POLICY_VERSION,
            rule_triggered=None,
        )
        logger.info(
            "Policy engine ALLOW: action=%s tx=%s",
            decision.action,
            getattr(decision, "transaction_id", "unknown"),
        )
        return allow
