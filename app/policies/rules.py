"""
app/policies/rules.py
======================
Individual deterministic policy rules.

Each rule is a pure function:
    rule(decision, transaction, existing_actions, settings) -> PolicyDecision | None

Returning None means the rule does not apply.
Returning a PolicyDecision short-circuits further evaluation.

Rules are evaluated in order by PolicyEngine.
"""
from __future__ import annotations

from typing import Optional

from app.agents.schemas import AgentDecision
from app.models.transaction import Transaction
from app.models.recovery_action import RecoveryAction
from app.models.enums import RecoveryActionType, RecoveryActionStatus
from app.policies.schemas import PolicyDecision, PolicyOutcome
from app.core.config import settings


def rule_already_successful(
    decision: AgentDecision,
    transaction: Transaction,
    existing_actions: list[RecoveryAction],
) -> Optional[PolicyDecision]:
    """Block if the transaction is already successful."""
    if str(transaction.status).upper() == "SUCCESS":
        return PolicyDecision(
            outcome=PolicyOutcome.BLOCK,
            reason="Transaction is already successful. No recovery needed.",
            rule_triggered="already_successful",
        )
    return None


def rule_unsupported_action(
    decision: AgentDecision,
    transaction: Transaction,
    existing_actions: list[RecoveryAction],
) -> Optional[PolicyDecision]:
    """Block any action not in the explicitly supported list."""
    allowed = {a.value for a in RecoveryActionType}
    if decision.action.value not in allowed:
        return PolicyDecision(
            outcome=PolicyOutcome.BLOCK,
            reason=f"Action '{decision.action}' is not a supported recovery action.",
            rule_triggered="unsupported_action",
        )
    return None


def rule_stop_action(
    decision: AgentDecision,
    transaction: Transaction,
    existing_actions: list[RecoveryAction],
) -> Optional[PolicyDecision]:
    """STOP action is always allowed but should be recorded — not executed."""
    if decision.action == RecoveryActionType.STOP:
        return PolicyDecision(
            outcome=PolicyOutcome.BLOCK,
            reason="Agent recommended STOP. No recovery action will be executed.",
            rule_triggered="stop_action",
        )
    return None


def rule_duplicate_recovery(
    decision: AgentDecision,
    transaction: Transaction,
    existing_actions: list[RecoveryAction],
) -> Optional[PolicyDecision]:
    """Block if an equivalent recovery action is already pending or completed."""
    blocking_statuses = {
        RecoveryActionStatus.PENDING.value,
        RecoveryActionStatus.APPROVED.value,
        RecoveryActionStatus.EXECUTING.value,
        RecoveryActionStatus.COMPLETED.value,
    }
    for ra in existing_actions:
        if (
            str(ra.action_type).upper() == decision.action.value
            and str(ra.status).upper() in blocking_statuses
        ):
            return PolicyDecision(
                outcome=PolicyOutcome.BLOCK,
                reason=(
                    f"A recovery action of type '{decision.action}' is already "
                    f"'{ra.status}' (id={ra.id}). Duplicate execution prevented."
                ),
                rule_triggered="duplicate_recovery",
            )
    return None


def rule_retry_limit(
    decision: AgentDecision,
    transaction: Transaction,
    existing_actions: list[RecoveryAction],
) -> Optional[PolicyDecision]:
    """Block automatic retries if the maximum retry count is reached."""
    retry_actions = {
        RecoveryActionType.RETRY_NOW.value,
        RecoveryActionType.RETRY_AFTER_DELAY.value,
    }
    if decision.action.value in retry_actions:
        completed_retries = sum(
            1 for ra in existing_actions
            if str(ra.action_type).upper() in retry_actions
            and str(ra.status).upper() == RecoveryActionStatus.COMPLETED.value
        )
        if completed_retries >= settings.MAX_AUTOMATIC_RETRIES:
            return PolicyDecision(
                outcome=PolicyOutcome.BLOCK,
                reason=(
                    f"Maximum automatic retry limit reached "
                    f"({completed_retries}/{settings.MAX_AUTOMATIC_RETRIES}). "
                    "Manual review required."
                ),
                rule_triggered="retry_limit",
            )
    return None


def rule_invalid_delay(
    decision: AgentDecision,
    transaction: Transaction,
    existing_actions: list[RecoveryAction],
) -> Optional[PolicyDecision]:
    """Block RETRY_AFTER_DELAY with an invalid or unsafe delay value."""
    if decision.action == RecoveryActionType.RETRY_AFTER_DELAY:
        delay = decision.delay_minutes
        if delay is None or delay < 1 or delay > 480:
            return PolicyDecision(
                outcome=PolicyOutcome.BLOCK,
                reason=(
                    f"Invalid delay_minutes={delay} for RETRY_AFTER_DELAY. "
                    "Must be between 1 and 480 minutes."
                ),
                rule_triggered="invalid_delay",
            )
    return None


def rule_high_value_transaction(
    decision: AgentDecision,
    transaction: Transaction,
    existing_actions: list[RecoveryAction],
) -> Optional[PolicyDecision]:
    """Require human approval for high-value transactions."""
    if float(transaction.amount) > settings.MAX_AUTOMATIC_RECOVERY_AMOUNT:
        return PolicyDecision(
            outcome=PolicyOutcome.HUMAN_APPROVAL,
            reason=(
                f"Transaction amount ₹{float(transaction.amount):,.2f} exceeds "
                f"automatic recovery threshold ₹{settings.MAX_AUTOMATIC_RECOVERY_AMOUNT:,.0f}. "
                "Human approval required."
            ),
            rule_triggered="high_value_transaction",
        )
    return None


def rule_low_confidence(
    decision: AgentDecision,
    transaction: Transaction,
    existing_actions: list[RecoveryAction],
) -> Optional[PolicyDecision]:
    """Require human approval when agent confidence is below the configured threshold."""
    if decision.confidence < settings.AGENT_CONFIDENCE_THRESHOLD:
        return PolicyDecision(
            outcome=PolicyOutcome.HUMAN_APPROVAL,
            reason=(
                f"Agent confidence {decision.confidence:.2f} is below "
                f"threshold {settings.AGENT_CONFIDENCE_THRESHOLD:.2f}. "
                "Human review recommended."
            ),
            rule_triggered="low_confidence",
        )
    return None


# Ordered list of rules evaluated by PolicyEngine
ALL_RULES = [
    rule_already_successful,
    rule_unsupported_action,
    rule_stop_action,
    rule_duplicate_recovery,
    rule_retry_limit,
    rule_invalid_delay,
    rule_high_value_transaction,
    rule_low_confidence,
]
