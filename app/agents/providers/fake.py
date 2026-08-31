"""
app/agents/providers/fake.py
==============================
Deterministic fake LLM provider for tests and local development.

Parses the prompt to extract actual XGBoost predictions and context,
ensuring the generated decision and reasoning are 100% consistent
with the actual model output passed in the prompt.
"""
from __future__ import annotations

import json
import re
import logging
from typing import Any

from app.agents.providers.base import LLMProvider, LLMProviderError

logger = logging.getLogger(__name__)


class FakeLLMProvider(LLMProvider):
    """
    Deterministic fake LLM provider.

    Args:
        decision_override: Custom decision dict.
        should_fail: If True, raises LLMProviderError (simulates unavailability).
        malformed_response: If True, returns invalid JSON (tests error handling).
    """

    def __init__(
        self,
        decision_override: dict[str, Any] | None = None,
        should_fail: bool = False,
        malformed_response: bool = False,
    ) -> None:
        self._decision_override = decision_override
        self._should_fail = should_fail
        self._malformed = malformed_response

    async def generate_decision(self, prompt: str) -> str:
        if self._should_fail:
            raise LLMProviderError("Fake LLM provider: simulated failure")
        if self._malformed:
            return "This is not valid JSON {{{ broken"
        if self._decision_override:
            return json.dumps(self._decision_override)

        # Dynamically extract XGBoost predictions from the prompt if present
        preds_data = self._extract_predictions_from_prompt(prompt)

        if preds_data and "predictions" in preds_data:
            predictions = preds_data["predictions"]
            recommended = preds_data.get("recommended_action") or max(predictions, key=predictions.__getitem__)
            prob = predictions.get(recommended, 0.5)

            # Build consistent response using actual predictions
            decision = {
                "action": recommended,
                "reason": (
                    f"XGBoost model predicts '{recommended}' has the highest recovery "
                    f"probability ({prob:.4f}). Selected based on payment context."
                ),
                "confidence": round(float(prob), 2),
                "selected_probability": round(float(prob), 4),
                "root_cause": "TEMPORARY_BANK_DEGRADATION",
            }
            if recommended == "RETRY_AFTER_DELAY":
                decision["delay_minutes"] = 20

            return json.dumps(decision)

        # Default fallback decision
        default_decision = {
            "action": "RETRY_AFTER_DELAY",
            "delay_minutes": 20,
            "reason": (
                "Root cause analysis indicates temporary bank degradation. "
                "RETRY_AFTER_DELAY selected to allow acquiring bank recovery."
            ),
            "confidence": 0.91,
            "root_cause": "TEMPORARY_BANK_DEGRADATION",
        }
        return json.dumps(default_decision)

    def _extract_predictions_from_prompt(self, prompt: str) -> dict | None:
        """Extract JSON block under === XGBOOST RECOVERY PREDICTIONS ==="""
        try:
            match = re.search(
                r"=== XGBOOST RECOVERY PREDICTIONS ===\s*(\{.*?\})\s*===",
                prompt,
                re.DOTALL,
            )
            if match:
                return json.loads(match.group(1))
        except Exception as exc:
            logger.debug("Could not parse XGBoost block from prompt: %s", exc)
        return None

    @property
    def provider_name(self) -> str:
        return "fake"
