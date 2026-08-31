"""
tests/test_policy.py
Tests for the deterministic policy engine rules.
"""
import pytest
from app.agents.schemas import AgentDecision
from app.models.transaction import Transaction
from app.models.recovery_action import RecoveryAction
from app.models.enums import RecoveryActionType, RecoveryActionStatus
from app.policies.engine import PolicyEngine
from app.policies.schemas import PolicyOutcome
from app.core.config import settings


def _make_tx(amount=1000.0, status="FAILED"):
    tx = Transaction(amount=amount, status=status)
    return tx


def test_policy_allow_standard_decision():
    engine = PolicyEngine()
    tx = _make_tx(amount=5000.0)
    decision = AgentDecision(
        action=RecoveryActionType.RETRY_AFTER_DELAY,
        delay_minutes=20,
        reason="Temporary outage recovery",
        confidence=0.85,
    )
    result = engine.evaluate(decision, tx, [])
    assert result.outcome == PolicyOutcome.ALLOW
    assert result.rule_triggered is None


def test_policy_block_already_successful():
    engine = PolicyEngine()
    tx = _make_tx(status="SUCCESS")
    decision = AgentDecision(
        action=RecoveryActionType.RETRY_NOW,
        reason="Retry attempt",
        confidence=0.9,
    )
    result = engine.evaluate(decision, tx, [])
    assert result.outcome == PolicyOutcome.BLOCK
    assert result.rule_triggered == "already_successful"


def test_policy_block_stop_action():
    engine = PolicyEngine()
    tx = _make_tx()
    decision = AgentDecision(
        action=RecoveryActionType.STOP,
        reason="Stop action recommended",
        confidence=0.0,
    )
    result = engine.evaluate(decision, tx, [])
    assert result.outcome == PolicyOutcome.BLOCK
    assert result.rule_triggered == "stop_action"


def test_policy_block_duplicate_recovery():
    engine = PolicyEngine()
    tx = _make_tx()
    existing = [
        RecoveryAction(
            action_type=RecoveryActionType.RETRY_AFTER_DELAY,
            status=RecoveryActionStatus.PENDING,
        )
    ]
    decision = AgentDecision(
        action=RecoveryActionType.RETRY_AFTER_DELAY,
        delay_minutes=15,
        reason="Delayed retry",
        confidence=0.8,
    )
    result = engine.evaluate(decision, tx, existing)
    assert result.outcome == PolicyOutcome.BLOCK
    assert result.rule_triggered == "duplicate_recovery"


def test_policy_block_retry_limit():
    engine = PolicyEngine()
    tx = _make_tx()
    existing = [
        RecoveryAction(action_type=RecoveryActionType.RETRY_NOW, status=RecoveryActionStatus.COMPLETED),
        RecoveryAction(action_type=RecoveryActionType.RETRY_NOW, status=RecoveryActionStatus.COMPLETED),
        RecoveryAction(action_type=RecoveryActionType.RETRY_NOW, status=RecoveryActionStatus.COMPLETED),
    ]
    decision = AgentDecision(
        action=RecoveryActionType.RETRY_AFTER_DELAY,
        delay_minutes=15,
        reason="Yet another retry",
        confidence=0.8,
    )
    result = engine.evaluate(decision, tx, existing)
    assert result.outcome == PolicyOutcome.BLOCK
    assert result.rule_triggered == "retry_limit"


def test_policy_human_approval_high_value():
    engine = PolicyEngine()
    tx = _make_tx(amount=100000.0)  # > 50,000 threshold
    decision = AgentDecision(
        action=RecoveryActionType.RETRY_AFTER_DELAY,
        delay_minutes=30,
        reason="High value recovery",
        confidence=0.9,
    )
    result = engine.evaluate(decision, tx, [])
    assert result.outcome == PolicyOutcome.HUMAN_APPROVAL
    assert result.rule_triggered == "high_value_transaction"


def test_policy_human_approval_low_confidence():
    engine = PolicyEngine()
    tx = _make_tx(amount=5000.0)
    decision = AgentDecision(
        action=RecoveryActionType.SEND_PAYMENT_LINK,
        reason="Uncertain outcome",
        confidence=0.4,  # < 0.6 threshold
    )
    result = engine.evaluate(decision, tx, [])
    assert result.outcome == PolicyOutcome.HUMAN_APPROVAL
    assert result.rule_triggered == "low_confidence"
