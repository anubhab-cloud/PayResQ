"""
app/agents/providers/fake.py
==============================
Deterministic fake LLM provider for tests and local development.

Returns a pre-configured structured JSON decision without making
any network calls. This allows the full agent → policy → worker
pipeline to be tested without an LLM API key.

The FakeLLMProvider can be configured to:
  - return a specific valid decision
  - simulate an LLM failure
  - return malformed output (for error-handling tests)
"""
from __future__ import annotations

import json
from typing import Any

from app.agents.providers.base import LLMProvider, LLMProviderError


DEFAULT_FAKE_DECISION: dict[str, Any] = {
    "action": "RETRY_AFTER_DELAY",
    "delay_minutes": 20,
    "reason": (
        "Root cause analysis indicates temporary bank degradation. "
        "XGBoost predicts RETRY_AFTER_DELAY has the highest recovery "
        "probability (0.71). A 20-minute delay allows the bank to recover."
    ),
    "confidence": 0.91,
    "root_cause": "TEMPORARY_BANK_DEGRADATION",
}


class FakeLLMProvider(LLMProvider):
    """
    Deterministic fake LLM provider.

    Args:
        decision_override: Custom decision dict. Defaults to DEFAULT_FAKE_DECISION.
        should_fail: If True, raises LLMProviderError (simulates unavailability).
        malformed_response: If True, returns invalid JSON (tests error handling).
    """

    def __init__(
        self,
        decision_override: dict[str, Any] | None = None,
        should_fail: bool = False,
        malformed_response: bool = False,
    ) -> None:
        self._decision = decision_override or DEFAULT_FAKE_DECISION
        self._should_fail = should_fail
        self._malformed = malformed_response

    async def generate_decision(self, prompt: str) -> str:
        if self._should_fail:
            raise LLMProviderError("Fake LLM provider: simulated failure")
        if self._malformed:
            return "This is not valid JSON {{{ broken"
        return json.dumps(self._decision)

    @property
    def provider_name(self) -> str:
        return "fake"
