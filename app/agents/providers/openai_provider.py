"""
app/agents/providers/openai_provider.py
=========================================
OpenAI LLM provider implementation.

Uses httpx directly (no openai SDK) to keep dependencies minimal.
Sends the prompt as a user message and expects JSON in the response.

Fails gracefully: raises LLMProviderError on timeout, HTTP error, or
when the API key is not configured.
"""
from __future__ import annotations

import json
import logging

import httpx

from app.agents.providers.base import LLMProvider, LLMProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are PayResQ, an AI payment recovery specialist. "
    "You analyze failed payment transactions and recommend the single best "
    "recovery action. You MUST respond with a valid JSON object only — "
    "no markdown, no extra text. The JSON must follow the exact schema provided."
)


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT provider.

    Requires LLM_API_KEY to be set in environment/settings.
    Falls back to LLMProviderError if the API is unavailable.
    """

    def __init__(self) -> None:
        if not settings.LLM_API_KEY:
            raise LLMProviderError(
                "LLM_API_KEY is not configured. "
                "Set LLM_PROVIDER=fake for development or provide an API key."
            )
        self._api_key = settings.LLM_API_KEY
        self._model = settings.LLM_MODEL
        self._timeout = settings.LLM_TIMEOUT_SECONDS

    async def generate_decision(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,        # low temperature for consistent structured output
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(OPENAI_CHAT_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                logger.info("OpenAI response received (model=%s)", self._model)
                return content

        except httpx.TimeoutException as exc:
            logger.error("OpenAI request timed out after %ds", self._timeout)
            raise LLMProviderError(f"OpenAI timeout after {self._timeout}s") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("OpenAI HTTP error: %s", exc.response.status_code)
            raise LLMProviderError(f"OpenAI HTTP {exc.response.status_code}") from exc
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.error("OpenAI response parsing failed: %s", exc)
            raise LLMProviderError(f"OpenAI response malformed: {exc}") from exc

    @property
    def provider_name(self) -> str:
        return f"openai/{self._model}"
