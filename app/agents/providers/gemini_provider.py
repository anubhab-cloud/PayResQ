"""
app/agents/providers/gemini_provider.py
========================================
Google Gemini LLM provider implementation.

Uses httpx directly to send requests to Google Generative Language REST API.
Compatible with Google Gemini Free Tier API keys.
"""
from __future__ import annotations

import json
import logging
import httpx

from app.agents.providers.base import LLMProvider, LLMProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

SYSTEM_PROMPT = (
    "You are PayResQ, an AI payment recovery specialist. "
    "You analyze failed payment transactions and recommend the single best "
    "recovery action. You MUST respond with a valid JSON object only — "
    "no markdown, no extra text. The JSON must follow the exact schema provided."
)


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM Provider.

    Requires GEMINI_API_KEY (or LLM_API_KEY) set in settings/environment.
    Uses model specified in LLM_MODEL (default: gemini-2.5-flash or gemini-1.5-flash).
    """

    def __init__(self) -> None:
        api_key = getattr(settings, "GEMINI_API_KEY", None) or settings.LLM_API_KEY
        if not api_key:
            raise LLMProviderError(
                "GEMINI_API_KEY or LLM_API_KEY is not configured. "
                "Provide a Gemini API key or use LLM_PROVIDER=fake."
            )
        self._api_key = api_key
        # Default to gemini-2.5-flash or gemini-1.5-flash if not specified or set to openai model
        model = settings.LLM_MODEL
        if "gpt" in model.lower() or "gemini" not in model.lower():
            model = "gemini-2.5-flash"
        self._model = model
        self._timeout = settings.LLM_TIMEOUT_SECONDS

    async def generate_decision(self, prompt: str) -> str:
        url = f"{GEMINI_BASE_URL}/{self._model}:generateContent?key={self._api_key}"
        headers = {"Content-Type": "application/json"}

        full_prompt = f"{SYSTEM_PROMPT}\n\nUser Context & Request:\n{prompt}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                candidates = data.get("candidates", [])
                if not candidates:
                    raise LLMProviderError("Gemini returned empty candidates")

                content = candidates[0]["content"]["parts"][0]["text"]
                logger.info("Gemini response received (model=%s)", self._model)
                return content

        except httpx.TimeoutException as exc:
            logger.error("Gemini request timed out after %ds", self._timeout)
            raise LLMProviderError(f"Gemini timeout after {self._timeout}s") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("Gemini HTTP error %s: %s", exc.response.status_code, exc.response.text)
            raise LLMProviderError(f"Gemini HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.error("Gemini response parsing failed: %s", exc)
            raise LLMProviderError(f"Gemini response malformed: {exc}") from exc

    @property
    def provider_name(self) -> str:
        return f"gemini/{self._model}"
