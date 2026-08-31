"""
app/agents/recovery_agent.py
==============================
LLM-based recovery agent.

Workflow:
  1. Gather context via read tools (transaction, customer, failure, predictions, merchant, prior actions)
  2. Build a structured, minimal prompt (no raw DB dumps)
  3. Call LLMProvider.generate_decision(prompt)
  4. Parse + validate response with AgentDecision Pydantic schema
  5. On any failure → safe fallback (STOP or HUMAN_APPROVAL)

The agent does NOT:
  - execute recovery actions directly
  - bypass the policy engine
  - access the database with arbitrary queries
"""
from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.providers.base import LLMProvider, LLMProviderError
from app.agents.schemas import AgentDecision
from app.agents.tools.read_tools import (
    get_transaction,
    get_customer_history,
    get_failure_context,
    get_recovery_predictions,
    get_merchant_context,
    get_previous_recovery_actions,
)
from app.models.enums import RecoveryActionType
from app.core.config import settings

logger = logging.getLogger(__name__)

DECISION_SCHEMA = """{
    "action": "<RETRY_NOW|RETRY_AFTER_DELAY|SEND_PAYMENT_LINK|CHANGE_PAYMENT_METHOD|NOTIFY_CUSTOMER|ESCALATE|STOP>",
    "delay_minutes": <integer, required only for RETRY_AFTER_DELAY>,
    "reason": "<human-readable explanation, min 10 characters>",
    "confidence": <float 0.0–1.0>,
    "root_cause": "<optional short description>",
    "selected_probability": <optional float 0.0–1.0>
}"""


def _build_prompt(context: dict[str, Any]) -> str:
    return f"""You are PayResQ, an AI payment recovery specialist.

A payment has failed. Analyze the context below and recommend the single best recovery action.

=== TRANSACTION ===
{json.dumps(context.get("transaction", {}), indent=2)}

=== FAILURE CONTEXT ===
{json.dumps(context.get("failure", {}), indent=2)}

=== CUSTOMER HISTORY ===
{json.dumps(context.get("customer", {}), indent=2)}

=== MERCHANT CONTEXT ===
{json.dumps(context.get("merchant", {}), indent=2)}

=== XGBOOST RECOVERY PREDICTIONS ===
{json.dumps(context.get("predictions", {}), indent=2)}

=== PREVIOUS RECOVERY ACTIONS ===
{json.dumps(context.get("previous_actions", {}), indent=2)}

=== DECISION CONSTRAINTS ===
- Maximum automatic retries: {settings.MAX_AUTOMATIC_RETRIES}
- High-value transaction threshold: ₹{settings.MAX_AUTOMATIC_RECOVERY_AMOUNT:,.0f}
- Confidence threshold for auto-execution: {settings.AGENT_CONFIDENCE_THRESHOLD}

=== INSTRUCTIONS ===
1. Consider root cause, XGBoost probabilities, customer reliability, and retry history.
2. Select the action most likely to recover revenue safely.
3. If the bank is in degradation, prefer RETRY_AFTER_DELAY.
4. If retry count is near the limit, prefer SEND_PAYMENT_LINK or ESCALATE.
5. If confidence is low, set ESCALATE or STOP.
6. You MUST respond with a single JSON object matching this exact schema:

{DECISION_SCHEMA}

Respond with JSON only. No markdown. No explanation outside the JSON.
"""


class RecoveryAgent:
    """
    AI recovery agent that uses an LLM to reason over transaction context
    and produce a validated structured decision.
    """

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def analyze(
        self, transaction_id: str, db: AsyncSession
    ) -> AgentDecision:
        """
        Gather context, call LLM, validate decision.

        Returns AgentDecision. On any failure, returns a safe fallback.
        """
        logger.info(
            "RecoveryAgent.analyze: transaction_id=%s provider=%s",
            transaction_id,
            self._provider.provider_name,
        )

        # --- 1. Gather context ---
        context = await self._gather_context(transaction_id, db)

        # --- 2. Build prompt ---
        prompt = _build_prompt(context)

        # --- 3. Call LLM ---
        try:
            raw_response = await self._provider.generate_decision(prompt)
        except LLMProviderError as exc:
            logger.error(
                "LLM provider unavailable: %s — returning safe fallback", exc
            )
            return self._safe_fallback(
                transaction_id, reason=f"LLM provider unavailable: {exc}"
            )

        # --- 4. Parse + validate ---
        try:
            raw_json = self._extract_json(raw_response)
            raw_json["transaction_id"] = transaction_id

            # Attach model version if available
            preds = context.get("predictions", {})
            raw_json.setdefault("model_version", preds.get("model_version"))
            raw_json.setdefault(
                "selected_probability",
                preds.get("predictions", {}).get(raw_json.get("action"), None),
            )

            decision = AgentDecision.model_validate(raw_json)
            logger.info(
                "AgentDecision: action=%s confidence=%.2f tx=%s",
                decision.action,
                decision.confidence,
                transaction_id,
            )
            return decision

        except (json.JSONDecodeError, ValueError, ValidationError) as exc:
            logger.error(
                "LLM response failed validation: %s\nRaw response: %s",
                exc,
                raw_response[:500],
            )
            return self._safe_fallback(
                transaction_id,
                reason=f"LLM response failed Pydantic validation: {exc}",
            )

    async def _gather_context(
        self, transaction_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        tx = await get_transaction(transaction_id, db)
        failure = await get_failure_context(transaction_id, db)
        predictions = await get_recovery_predictions(transaction_id, db)
        previous = await get_previous_recovery_actions(transaction_id, db)

        customer: dict = {}
        merchant: dict = {}
        if "customer_id" in tx:
            customer = await get_customer_history(tx["customer_id"], db)
        if "merchant_id" in tx:
            merchant = await get_merchant_context(tx["merchant_id"], db)

        return {
            "transaction": tx,
            "failure": failure,
            "customer": customer,
            "merchant": merchant,
            "predictions": predictions,
            "previous_actions": previous,
        }

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from raw LLM response (strips markdown fences if present)."""
        text = text.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return json.loads(text)

    def _safe_fallback(self, transaction_id: str, reason: str) -> AgentDecision:
        """Return a safe STOP decision when the agent cannot produce a valid output."""
        logger.warning("Safe fallback triggered for tx=%s: %s", transaction_id, reason)
        return AgentDecision(
            action=RecoveryActionType.STOP,
            reason=f"Agent fallback — manual review required. {reason}",
            confidence=0.0,
            transaction_id=transaction_id,
        )
